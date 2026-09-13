"""Cell 2 input contracts exercised with local frames; no Snowflake calls."""
import ast
from collections import Counter
import copy
import csv
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import mock_open, patch
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CELL = ROOT / "notebooks/cells/02_source_mapping_registry_inputs.py"


class Expr:
    def __init__(self, op, *args, name=None):
        self.op, self.args, self.name = op, args, name
    def alias(self, name):
        return Expr(self.op, *self.args, name=name)
    def cast(self, kind):
        return Expr("cast", self, kind, name=self.name)
    def desc_nulls_last(self):
        return self
    def is_not_null(self):
        return Expr("not-null", self)
    def __eq__(self, other):
        return Expr("eq", self, other)
    def over(self, window):
        return Expr(self.op, window)
    def eval(self, row):
        if self.op == "col":
            name = self.args[0]
            return row[name[1:-1].replace('""', '"') if name.startswith('"') and name.endswith('"') else name]
        if self.op == "literal":
            return self.args[0]
        if self.op == "cast":
            value = self.args[0].eval(row)
            return None if value is None else str(value)
        if self.op == "not-null":
            return self.args[0].eval(row) is not None
        if self.op == "eq":
            return self.args[0].eval(row) == self.args[1].eval(row)
        raise AssertionError("Unexpected fake expression operation")


class Window:
    @staticmethod
    def partition_by(*keys):
        return Window(keys)
    def __init__(self, keys):
        self.keys, self.order = keys, ()
    def order_by(self, *expressions):
        self.order = expressions
        return self


class Row(dict):
    def as_dict(self, recursive=True):
        return dict(self)


class Frame:
    def __init__(self, owner, table, rows, columns=None, snapshot=None):
        self.owner, self.table = owner, table
        self.rows = copy.deepcopy(rows)
        self.columns = list(columns) if columns is not None else [
            name if re.fullmatch(r"[A-Z_][A-Z0-9_$]*", name) else '"' + name.replace('"', '""') + '"'
            for name in (rows[0] if rows else [])]
        self.snapshot = snapshot

    def child(self, rows, columns=None):
        return Frame(self.owner, self.table, rows, columns, self.snapshot)

    def select(self, *expressions):
        self.owner.events.append(("select", self.table))
        names = [item if isinstance(item, str) else item.name or item.args[0] for item in expressions]
        values = [{name: row[item] if isinstance(item, str) else item.eval(row)
                   for name, item in zip(names, expressions)} for row in self.rows]
        return self.child(values, names)

    def cache_result(self):
        self.owner.events.append(("cache", self.table))
        self.owner.cache_calls[self.table] += 1
        cached = Frame(self.owner, self.table, self.rows, self.columns)
        cached.snapshot = cached
        self.owner.handles.append(cached)
        return cached

    def count(self):
        if self.snapshot is None:
            raise AssertionError("Counts must use the frozen source snapshot")
        self.owner.events.append(("count", self.table))
        return len(self.rows)

    def filter(self, condition):
        self.owner.events.append(("filter", self.table))
        if isinstance(condition, str):
            if condition != "SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID)) = 0":
                raise AssertionError("Unexpected SQL filter")
            predicate = lambda row: row["SOURCE_RECORD_ID"] is None or not row["SOURCE_RECORD_ID"].strip()
        else:
            predicate = condition.eval
        return self.child([row for row in self.rows if predicate(row)], self.columns)

    def distinct(self):
        found, rows = set(), []
        for row in self.rows:
            signature = json.dumps(row, sort_keys=True)
            if signature not in found:
                rows.append(row)
                found.add(signature)
        return self.child(rows, self.columns)

    def with_column(self, name, expression):
        self.owner.events.append(("rank", self.table))
        if expression.op != "dense-rank":
            raise AssertionError("Unexpected generated source column")
        window = expression.args[0]
        groups = {}
        for row in self.rows:
            groups.setdefault(tuple(row[key] for key in window.keys), []).append(row)
        ranked = []
        for rows in groups.values():
            ordered = sorted(rows, key=lambda row: tuple(
                (expr.eval(row) is not None, expr.eval(row)) for expr in window.order), reverse=True)
            previous, rank = None, 0
            for row in ordered:
                ordering = tuple(expr.eval(row) for expr in window.order)
                if ordering != previous:
                    rank += 1
                    previous = ordering
                ranked.append({**row, name: rank})
        return self.child(ranked, [*self.columns, name])

    def drop(self, *names):
        return self.child([{key: value for key, value in row.items() if key not in names}
                           for row in self.rows], [name for name in self.columns if name not in names])

    def collect(self):
        self.owner.events.append(("collect", self.table))
        return [Row(row) for row in self.rows]


class Session:
    def __init__(self, tables):
        self.events, self.handles, self.cache_calls = [], [], Counter()
        self.transaction, self.tx_failure = None, False
        self.tables = {name: Frame(self, name, rows) for name, rows in tables.items()}
    def table(self, name):
        self.events.append(("table", name))
        return self.tables[name]
    def create_dataframe(self, frame):
        raise AssertionError("Mapping metadata must stay local; no Snowflake upload")
    def sql(self, statement):
        if statement != "SELECT CURRENT_TRANSACTION() AS TX":
            raise AssertionError("Only the read-only transaction-state query is allowed")
        self.events.append(("transaction", None))
        if self.tx_failure:
            raise RuntimeError("synthetic transaction-state query failure")
        return SimpleNamespace(collect=lambda: [Row(TX=self.transaction)])


def namespace():
    tree = ast.parse(CELL.read_text(encoding="utf-8"))
    ns = {"csv": csv, "pd": pd, "Window": Window, "col": lambda name: Expr("col", name),
          "lit": lambda value: Expr("literal", value), "dense_rank": lambda: Expr("dense-rank")}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)],
                           type_ignores=[]), str(CELL), "exec"), ns)
    return ns


def profile(key="one", models=("SSP", "ASSESSMENT_RESULTS")):
    return {
        "SOURCE_KEY": key, "SOURCE_TABLE_NAME": "SOURCE_" + key.upper(),
        "RAW_TABLE": "RAW_" + key.upper(), "MAPPING_FILE": key + ".csv",
        "MODEL_KEYS": models, "SOURCE_ORDER_CANDIDATES": ("UPDATED",),
        "LOOKUP_CONTRACTS": {"software": {
            "source_table": "LOOKUP_" + key.upper(),
            "title_field": "NAME", "description_field": "DESCRIPTION",
        }},
    }


def raw(identity, value, **extra):
    return {"CONTENT_ID": identity, "CURATED_JSON": {"value": value}, **extra}


class MultiModelInputs(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()

    def test_source_is_cached_once_before_counts_and_snapshot_is_retained(self):
        session = Session({"RAW_ONE": [raw("a", 1), raw("b", 2)]})
        result, report, handle = self.ns["load_source_input"](session, profile())
        self.assertEqual([("transaction", None), ("table", "RAW_ONE"),
                          ("select", "RAW_ONE"), ("cache", "RAW_ONE")], session.events[:4])
        self.assertEqual(1, session.cache_calls["RAW_ONE"])
        self.assertIs(handle, result.snapshot)
        self.assertEqual({"RAW_ROWS": 2, "SELECTED_ROWS": 2, "DUPLICATE_SOURCE_ROWS_RESOLVED": 0}, report)
        session.tables["RAW_ONE"].rows[0]["CURATED_JSON"]["value"] = 999
        self.assertEqual(1, result.rows[0]["CURATED_JSON"]["value"])
        self.assertEqual({"SOURCE_RECORD_ID", "CURATED_JSON"}, set(result.columns))

    def test_duplicate_selection_is_source_local_and_uses_approved_recency(self):
        session = Session({
            "RAW_ONE": [raw("shared", "old", UPDATED=1), raw("shared", "new", UPDATED=2)],
            "RAW_TWO": [raw("shared", "separate", UPDATED=1)],
        })
        first, r1, h1 = self.ns["load_source_input"](session, profile())
        second, r2, h2 = self.ns["load_source_input"](session, profile("two"))
        self.assertEqual("new", first.rows[0]["CURATED_JSON"]["value"])
        self.assertEqual("separate", second.rows[0]["CURATED_JSON"]["value"])
        self.assertEqual(1, r1["DUPLICATE_SOURCE_ROWS_RESOLVED"])
        self.assertEqual(0, r2["DUPLICATE_SOURCE_ROWS_RESOLVED"])
        self.assertIsNot(h1, h2)
        self.assertEqual({"RAW_ONE": 1, "RAW_TWO": 1}, dict(session.cache_calls))
        self.assertNotIn("_SOURCE_ROW_NUMBER", first.columns)
        self.assertNotIn("UPDATED", first.columns)

    def test_duplicate_identity_without_technical_recency_fails(self):
        session = Session({"RAW_ONE": [raw("same", 1), raw("same", 2)]})
        with self.assertRaisesRegex(ValueError, "approved technical ordering"):
            self.ns["load_source_input"](session, profile())
        self.assertEqual(1, session.cache_calls["RAW_ONE"])
        self.assertFalse(any(event[0] == "rank" for event in session.events))

    def test_null_or_blank_source_identity_is_rejected_after_snapshot(self):
        for bad in (None, "", "   "):
            session = Session({"RAW_ONE": [raw(bad, 1)]})
            with self.subTest(identity=bad), self.assertRaisesRegex(ValueError, "missing record identities"):
                self.ns["load_source_input"](session, profile())
            self.assertEqual(1, session.cache_calls["RAW_ONE"])

    def test_configured_identity_and_json_columns_are_used(self):
        session = Session({"RAW_ONE": [{"Source Id": 42, "Payload": {"x": 1}}]})
        session.tables["RAW_ONE"].columns = ['"Source Id"', '"Payload"']
        selected = profile()
        selected.update(CONTENT_ID_COLUMN="Source Id", CURATED_JSON_COLUMN="Payload")
        result, _, _ = self.ns["load_source_input"](session, selected)
        self.assertEqual([{"SOURCE_RECORD_ID": "42", "CURATED_JSON": {"x": 1}}], result.rows)

    def test_active_or_unknown_transaction_blocks_all_snapshot_ddl(self):
        for method in ("source", "lookups"):
            for active, failed in (("caller-owned", False), (None, True)):
                session = Session({"RAW_ONE": [raw("a", 1)]})
                session.transaction, session.tx_failure = active, failed
                with self.subTest(method=method, active=active, failed=failed), self.assertRaises(ValueError):
                    if method == "source":
                        self.ns["load_source_input"](session, profile())
                    else:
                        self.ns["load_source_lookups"](session, profile(),
                            {"SSP": {"LOOKUP_GROUPS": ()}, "ASSESSMENT_RESULTS": {"LOOKUP_GROUPS": ()}},
                            {"ARCHER_META_VALUE_TABLE": "VALUES"})
                self.assertEqual([("transaction", None)], session.events)
                self.assertEqual({}, dict(session.cache_calls))
                self.assertEqual(active, session.transaction)

    def test_duplicate_source_columns_fail_before_snapshot(self):
        session = Session({"RAW_ONE": [raw("a", 1)]})
        session.tables["RAW_ONE"].columns += ['"CONTENT_ID"']
        with self.assertRaisesRegex(ValueError, "Duplicate normalized source column"):
            self.ns["load_source_input"](session, profile())
        self.assertEqual({}, dict(session.cache_calls))

    def test_mapping_source_column_selects_only_explicit_binding(self):
        text = "Source Table,Archer Field Name\nSOURCE_ONE,ONE\nSOURCE_TWO,TWO\n,UNBOUND\n"
        selected = profile()
        selected["MAPPING_SOURCE_COLUMN"] = "Source Table"
        with patch("builtins.open", mock_open(read_data=text)) as opened:
            frame = self.ns["load_mapping_rows"](selected)
        self.assertEqual(["ONE"], frame["ARCHER FIELD NAME"].tolist())
        opened.assert_called_once_with("one.csv", encoding="cp1252", newline="")

    def test_live_flat_mapping_file_keeps_utf8_notes_and_source_binding(self):
        from tests.test_model_selection import cell_namespace
        selected = copy.deepcopy(cell_namespace()["SOURCE_PROFILES"][0])
        selected["MAPPING_FILE"] = str(ROOT / "Mapping/ARCHER_OSCAL_MAPPINGS.csv")
        actual = self.ns["load_mapping_rows"](selected)
        with open(selected["MAPPING_FILE"], encoding="utf-8", newline="") as handle:
            expected = list(csv.DictReader(handle))
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(actual["NOTES"].fillna("").tolist(),
                         [row["NOTES"] for row in expected])
        self.assertEqual(set(actual["SOURCE_KEY"]), {"source-one"})

    def test_csv_literal_na_and_unicode_are_not_lost(self):
        text = ('SOURCE_FIELD_NAME,NOTES\r\nN/A,"Café — first line, quoted comma\nsecond line"\r\n'
                'null,\r\nNaN,""\r\n0,false\r\n')
        selected = profile()
        selected["MAPPING_ENCODING"] = "utf-8-sig"
        with patch("builtins.open", mock_open(read_data=text)) as opened:
            actual = self.ns["load_mapping_rows"](selected)
        opened.assert_called_once_with("one.csv", encoding="utf-8-sig", newline="")
        self.assertEqual(actual["SOURCE_FIELD_NAME"].tolist(), ["N/A", "null", "NaN", "0"])
        self.assertEqual(actual["NOTES"].tolist(),
                         ["Café — first line, quoted comma\nsecond line", None, None, "false"])

    def test_explicit_mapping_source_value_does_not_default_to_another_source(self):
        selected = profile()
        selected.update(MAPPING_SOURCE_COLUMN="BINDING", MAPPING_SOURCE_VALUE="approved-one")
        text = "BINDING,FIELD\n approved-one ,A\nSOURCE_ONE,B\n"
        with patch("builtins.open", mock_open(read_data=text)):
            self.assertEqual(["A"], self.ns["load_mapping_rows"](selected)["FIELD"].tolist())

    def test_mapping_header_collision_or_missing_binding_fails(self):
        cases = [
            ("FIELD, field \na,b\n", profile()),
            ("FIELD\nA\n", {**profile(), "MAPPING_SOURCE_COLUMN": "MISSING"}),
        ]
        for text, selected in cases:
            with self.subTest(header=text.splitlines()[0]), patch("builtins.open", mock_open(read_data=text)):
                with self.assertRaises(ValueError):
                    self.ns["load_mapping_rows"](selected)

    def test_literal_duplicate_csv_header_fails_before_pandas_can_mangle_it(self):
        for text in ("FIELD,FIELD\none,two\n", '"Field"," FIELD "\none,two\n'):
            with self.subTest(header=text.splitlines()[0]):
                opened = mock_open(read_data=text)
                with patch("builtins.open", opened):
                    with self.assertRaisesRegex(ValueError, "Duplicate normalized mapping columns"):
                        self.ns["load_mapping_rows"](profile())
                opened.assert_called_once_with("one.csv", encoding="cp1252", newline="")

    def test_component_lookup_is_selected_by_contract_group_not_model_name(self):
        tables = {"VALUES": [{"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "High"}],
                  "LOOKUP_ONE": [raw("component", "synthetic")]}
        session = Session(tables)
        selected = profile(models=("CUSTOM_MODEL",))
        lookups = self.ns["load_source_lookups"](
            session, selected, {"CUSTOM_MODEL": {"LOOKUP_GROUPS": ("components",)}},
            {"ARCHER_META_VALUE_TABLE": "VALUES"})
        self.assertEqual({"1": "High"}, lookups["archer_values"])
        self.assertEqual({"1": "High"}, lookups["fips_values"])
        self.assertIn("software", lookups["component_sources"])
        self.assertEqual(1, session.cache_calls["LOOKUP_ONE"])

    def test_csv_blank_lines_and_missing_trailing_cells_preserve_column_alignment(self):
        text = 'FIELD,NOTES,STATUS\n  \nA\nB,"two, words",APPROVED\n'
        with patch("builtins.open", mock_open(read_data=text)):
            frame = self.ns["load_mapping_rows"](profile())
        self.assertEqual(frame.to_dict("records"), [
            {"FIELD": "A", "NOTES": None, "STATUS": None},
            {"FIELD": "B", "NOTES": "two, words", "STATUS": "APPROVED"},
        ])
        with patch("builtins.open", mock_open(read_data='A,B\nx,y,z\n')):
            with self.assertRaisesRegex(ValueError, "more values than header"):
                self.ns["load_mapping_rows"](profile())

    def test_malformed_csv_cannot_swallow_later_mapping_rows(self):
        cases = [
            'FIELD,NOTES\nFIRST,"unclosed note\nSECOND,valid note\n',
            'FIELD,NOTES\nFIRST,"closed note"garbage\nSECOND,valid note\n',
        ]
        for text in cases:
            with self.subTest(text=text), patch("builtins.open", mock_open(read_data=text)):
                with self.assertRaises(csv.Error):
                    self.ns["load_mapping_rows"](profile())

    def test_latest_conflicting_payloads_fail_regardless_of_input_order(self):
        rows = [raw("same", {"a": 0, "b": 1}, UPDATED=2),
                raw("same", {"a": 1, "b": 0}, UPDATED=2)]
        for ordered in (rows, list(reversed(rows))):
            session = Session({"RAW_ONE": ordered})
            with self.subTest(order=ordered), self.assertRaisesRegex(ValueError, "Conflicting source payloads"):
                self.ns["load_source_input"](session, profile())

    def test_identical_latest_payloads_collapse_independent_of_object_key_order(self):
        rows = [raw("same", {"a": 1, "b": 2}, UPDATED=2),
                raw("same", {"b": 2, "a": 1}, UPDATED=2)]
        session = Session({"RAW_ONE": rows})
        result, report, _ = self.ns["load_source_input"](session, profile())
        self.assertEqual([{"SOURCE_RECORD_ID": "same", "CURATED_JSON": {"value": {"a": 1, "b": 2}}}], result.rows)
        self.assertEqual(1, report["DUPLICATE_SOURCE_ROWS_RESOLVED"])

    def test_null_payload_is_not_discarded_when_detecting_latest_conflicts(self):
        rows = [dict(raw("same", 1, UPDATED=2), CURATED_JSON=None), raw("same", 1, UPDATED=2)]
        with self.assertRaisesRegex(ValueError, "Conflicting source payloads"):
            self.ns["load_source_input"](Session({"RAW_ONE": rows}), profile())
        rows[1]["CURATED_JSON"] = None
        result, _, _ = self.ns["load_source_input"](Session({"RAW_ONE": rows}), profile())
        self.assertEqual([{"SOURCE_RECORD_ID": "same", "CURATED_JSON": None}], result.rows)

    def test_conflicting_obsolete_versions_do_not_block_a_unique_latest_row(self):
        rows = [raw("same", "older-a", UPDATED=1), raw("same", "older-b", UPDATED=1),
                raw("same", "latest", UPDATED=2)]
        result, _, _ = self.ns["load_source_input"](Session({"RAW_ONE": rows}), profile())
        self.assertEqual("latest", result.rows[0]["CURATED_JSON"]["value"])

    def test_quoted_recency_columns_keep_priority_and_nulls_last(self):
        rows = [raw("same", "first", **{"Updated At": None, "Sequence": 99}),
                raw("same", "second", **{"Updated At": 2, "Sequence": None}),
                raw("same", "chosen", **{"Updated At": 2, "Sequence": 1})]
        selected = {**profile(), "SOURCE_ORDER_CANDIDATES": ("Updated At", "Sequence")}
        result, _, _ = self.ns["load_source_input"](Session({"RAW_ONE": rows}), selected)
        self.assertEqual("chosen", result.rows[0]["CURATED_JSON"]["value"])
        self.assertEqual({"SOURCE_RECORD_ID", "CURATED_JSON"}, set(result.columns))

    def test_quoted_case_distinct_identifiers_are_resolved_exactly(self):
        session = Session({"RAW_ONE": [{"CONTENT_ID": "upper", "content_id": "lower", "CURATED_JSON": {}}]})
        for configured, expected in (("CONTENT_ID", "upper"), ("content_id", "lower"), ('"content_id"', "lower")):
            with self.subTest(configured=configured):
                selected = {**profile(), "CONTENT_ID_COLUMN": configured}
                result, _, _ = self.ns["load_source_input"](session, selected)
                self.assertEqual(expected, result.rows[0]["SOURCE_RECORD_ID"])

    def test_embedded_quotes_in_identifiers_are_preserved(self):
        session = Session({"RAW_ONE": [{'Id"Key': "one", 'Json"Payload': {}}]})
        selected = {**profile(), "CONTENT_ID_COLUMN": '"Id""Key"', "CURATED_JSON_COLUMN": 'Json"Payload'}
        result, _, _ = self.ns["load_source_input"](session, selected)
        self.assertEqual([{"SOURCE_RECORD_ID": "one", "CURATED_JSON": {}}], result.rows)

    def test_ssp_name_alone_does_not_trigger_component_lookup(self):
        session = Session({"VALUES": [{"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "custom"}]})
        lookups = self.ns["load_source_lookups"](
            session, profile(models=("SSP",)), {"SSP": {"LOOKUP_GROUPS": ()}},
            {"ARCHER_META_VALUE_TABLE": "VALUES"})
        self.assertEqual({}, lookups["component_sources"])
        self.assertEqual({}, lookups["fips_values"])
        self.assertFalse(any(event == ("table", "LOOKUP_ONE") for event in session.events))

    def test_cell_bootstrap_loads_each_source_once_for_both_models_and_keeps_handles(self):
        profiles = [profile(), profile("two")]
        session = Session({
            "RAW_ONE": [raw("same-id", "one")], "RAW_TWO": [raw("same-id", "two")],
            "VALUES": [{"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "Low"}], "REGISTRY": [],
        })
        ns = {**self.ns, "session": session, "SOURCE_PROFILES": profiles,
              "MODEL_CONTRACTS": {"SSP": {"LOOKUP_GROUPS": ()}, "ASSESSMENT_RESULTS": {"LOOKUP_GROUPS": ()}},
              "CONFIG": {"ARCHER_META_VALUE_TABLE": "VALUES", "ELEMENT_REGISTRY_TABLE": "REGISTRY"}}
        tree = ast.parse(CELL.read_text(encoding="utf-8"))
        start = next(index for index, node in enumerate(tree.body)
                     if isinstance(node, ast.Assign) and any(
                         isinstance(target, ast.Name) and target.id == "SOURCE_INPUTS" for target in node.targets))
        artifact = "SOURCE_FIELD_NAME\nSYNTHETIC_FIELD\n"
        with patch("builtins.open", mock_open(read_data=artifact)) as opened, redirect_stdout(io.StringIO()):
            exec(compile(ast.Module(body=tree.body[start:], type_ignores=[]), str(CELL), "exec"), ns)
        self.assertEqual(["one.csv", "two.csv"], [call.args[0] for call in opened.call_args_list])
        self.assertEqual({"one", "two"}, set(ns["SOURCE_INPUTS"]))
        self.assertEqual({"RAW_ONE": 1, "RAW_TWO": 1}, dict(session.cache_calls))
        for selected in profiles:
            key = selected["SOURCE_KEY"]
            entry = ns["SOURCE_INPUTS"][key]
            self.assertIs(entry["snapshot"], entry["source_df"].snapshot)
            self.assertIs(entry["snapshot"], session.handles[0 if key == "one" else 1])
            self.assertEqual(1, sum(event == ("table", selected["RAW_TABLE"]) for event in session.events))
            self.assertEqual(key, entry["source_df"].rows[0]["CURATED_JSON"]["value"])
        self.assertIs(ns["source_df"], ns["SOURCE_INPUTS"]["one"]["source_df"])
        self.assertIsNone(ns["mapping_df"])


if __name__ == "__main__":
    unittest.main()
