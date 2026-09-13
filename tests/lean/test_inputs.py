"""CSV parsing and source selection; local transport doubles, no Snowflake SQL proof."""
import ast
import csv
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import mock_open, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from test_multi_model_inputs import Expr, Session, Window, profile, raw


def input_namespace():
    cells = Path(os.environ.get("LEAN_CELLS_DIR", ROOT / "notebooks/cells"))
    path = cells / "02_source_mapping_registry_inputs.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    namespace = {"csv": csv, "Window": Window, "col": lambda name: Expr("col", name),
                 "lit": lambda value: Expr("literal", value), "dense_rank": lambda: Expr("dense-rank")}
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


class SourceInputTests(unittest.TestCase):
    def setUp(self):
        self.ns = input_namespace()

    def source(self, rows, selected=None):
        return self.ns["load_source_input"](Session({"RAW_ONE": rows}), selected or profile())

    def test_frozen_snapshot_is_retained_and_source_is_read_once(self):
        session = Session({"RAW_ONE": [raw("one", 1), raw("two", 2)]})
        result, counts, snapshot = self.ns["load_source_input"](session, profile())
        self.assertEqual(1, session.cache_calls["RAW_ONE"])
        self.assertIs(snapshot, result.snapshot)
        self.assertEqual({"RAW_ROWS": 2, "SELECTED_ROWS": 2, "DUPLICATE_SOURCE_ROWS_RESOLVED": 0}, counts)
        session.tables["RAW_ONE"].rows[0]["CURATED_JSON"]["value"] = 999
        self.assertEqual(1, result.rows[0]["CURATED_JSON"]["value"])

    def test_existing_or_unverifiable_transaction_blocks_before_snapshot(self):
        for transaction, failure in (("caller-transaction", False), (None, True)):
            session = Session({"RAW_ONE": [raw("one", 1)]})
            session.transaction, session.tx_failure = transaction, failure
            with self.subTest(transaction=transaction, failure=failure), self.assertRaises(ValueError):
                self.ns["load_source_input"](session, profile())
            self.assertEqual([("transaction", None)], session.events)
            self.assertEqual(transaction, session.transaction)

    def test_missing_record_identity_is_rejected(self):
        for identity in (None, "", "   "):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                self.source([raw(identity, 1)])

    def test_ambiguous_source_columns_reject_before_snapshot(self):
        session = Session({"RAW_ONE": [raw("one", 1)]})
        session.tables["RAW_ONE"].columns += ['"CONTENT_ID"']
        with self.assertRaisesRegex(ValueError, "Duplicate normalized"):
            self.ns["load_source_input"](session, profile())
        self.assertEqual({}, dict(session.cache_calls))

    def test_duplicate_records_require_configured_ordering(self):
        with self.assertRaisesRegex(ValueError, "technical ordering"):
            self.source([raw("same", 1), raw("same", 2)])

    def test_latest_conflicting_payloads_block_in_either_input_order(self):
        rows = [raw("same", "first", UPDATED=2), raw("same", "second", UPDATED=2)]
        for records in (rows, rows[::-1]):
            with self.subTest(records=records), self.assertRaisesRegex(ValueError, "Conflicting source payloads"):
                self.source(records)

    def test_equal_latest_payloads_collapse_with_different_object_key_order(self):
        rows = [raw("same", {"a": 1, "b": 2}, UPDATED=2), raw("same", {"b": 2, "a": 1}, UPDATED=2)]
        selected, counts, _ = self.source(rows)
        self.assertEqual(1, len(selected.rows))
        self.assertEqual(1, counts["DUPLICATE_SOURCE_ROWS_RESOLVED"])

    def test_obsolete_conflicts_do_not_block_an_unambiguous_latest_record(self):
        rows = [raw("same", "old-a", UPDATED=1), raw("same", "old-b", UPDATED=1), raw("same", "new", UPDATED=2)]
        selected, _, _ = self.source(rows)
        self.assertEqual("new", selected.rows[0]["CURATED_JSON"]["value"])

    def test_null_latest_payload_is_not_dropped_from_conflict_detection(self):
        rows = [dict(raw("same", 1, UPDATED=2), CURATED_JSON=None), raw("same", 1, UPDATED=2)]
        with self.assertRaisesRegex(ValueError, "Conflicting source payloads"):
            self.source(rows)

    def test_quoted_order_columns_preserve_priority_and_nulls_last(self):
        rows = [raw("same", "old", **{"Updated At": None, "Sequence": 99}),
                raw("same", "other", **{"Updated At": 2, "Sequence": None}),
                raw("same", "chosen", **{"Updated At": 2, "Sequence": 1})]
        selected, _, _ = self.source(rows, {**profile(), "SOURCE_ORDER_CANDIDATES": ("Updated At", "Sequence")})
        self.assertEqual("chosen", selected.rows[0]["CURATED_JSON"]["value"])
        self.assertEqual({"SOURCE_RECORD_ID", "CURATED_JSON"}, set(selected.columns))

    def test_quoted_case_distinct_column_binding_is_exact(self):
        records = [{"CONTENT_ID": "upper", "content_id": "lower", "CURATED_JSON": {}}]
        for configured, expected in (("CONTENT_ID", "upper"), ("content_id", "lower"), ('"content_id"', "lower")):
            selected, _, _ = self.source(records, {**profile(), "CONTENT_ID_COLUMN": configured})
            self.assertEqual(expected, selected.rows[0]["SOURCE_RECORD_ID"])

    def test_embedded_quotes_in_source_columns_are_preserved(self):
        rows = [{'Id"Key': "one", 'Json"Payload': {}}]
        settings = {**profile(), "CONTENT_ID_COLUMN": '"Id""Key"', "CURATED_JSON_COLUMN": 'Json"Payload'}
        result, _, _ = self.source(rows, settings)
        self.assertEqual([{"SOURCE_RECORD_ID": "one", "CURATED_JSON": {}}], result.rows)


class MappingCsvTests(unittest.TestCase):
    def setUp(self):
        self.load = input_namespace()["load_mapping_rows"]

    def read(self, text, **settings):
        with patch("builtins.open", mock_open(read_data=text)) as opened:
            rows = self.load({**profile(), **settings})
        opened.assert_called_once_with("one.csv", encoding="utf-8-sig", newline="")
        return rows

    def test_literal_values_and_multiline_unicode_notes_are_preserved(self):
        text = 'FIELD,NOTES\r\nN/A,"Café — first line, comma\nsecond line"\r\nnull,\r\nNaN,""\r\n0,false\r\n'
        rows = self.read(text)
        self.assertEqual(["N/A", "null", "NaN", "0"], [r["FIELD"] for r in rows])
        self.assertEqual(["Café — first line, comma\nsecond line", None, None, "false"], [r["NOTES"] for r in rows])

    def test_blank_lines_and_short_rows_keep_column_alignment(self):
        self.assertEqual([
            {"FIELD": "A", "NOTES": None, "STATUS": None},
            {"FIELD": "B", "NOTES": "two, words", "STATUS": "APPROVED"},
        ], self.read('FIELD,NOTES,STATUS\n  \nA\nB,"two, words",APPROVED\n'))

    def test_extra_values_and_duplicate_or_blank_headers_reject(self):
        for text in ("A,B\nx,y,z\n", "FIELD, field \none,two\n", "A,\na,b\n", "\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.read(text)

    def test_malformed_quoting_cannot_swallow_the_next_mapping(self):
        for text in ('FIELD,NOTES\nFIRST,"unclosed\nSECOND,valid\n', 'FIELD,NOTES\nFIRST,"closed"garbage\nSECOND,valid\n'):
            with self.subTest(text=text), self.assertRaises(csv.Error):
                self.read(text)

    def test_source_binding_is_explicit_and_missing_binding_column_rejects(self):
        rows = self.read("BINDING,FIELD\n approved-one ,A\nSOURCE_ONE,B\n", MAPPING_SOURCE_COLUMN="BINDING",
                         MAPPING_SOURCE_VALUE="approved-one")
        self.assertEqual(["A"], [r["FIELD"] for r in rows])
        with self.assertRaises(ValueError):
            self.read("FIELD\nA\n", MAPPING_SOURCE_COLUMN="MISSING")

    def test_missing_binding_header_rejects_even_without_data_rows(self):
        with self.assertRaisesRegex(ValueError, "source binding column"):
            self.read("FIELD,NOTES\n", MAPPING_SOURCE_COLUMN="SOURCE_KEY")

    def test_released_csv_loads_all_reviewed_occurrences(self):
        selected = {**profile(), "MAPPING_FILE": str(ROOT / "Mapping/ARCHER_OSCAL_MAPPINGS.csv"),
                    "MAPPING_SOURCE_COLUMN": "SOURCE_KEY", "MAPPING_SOURCE_VALUE": "source-one"}
        rows = self.load(selected)
        self.assertEqual(151, len(rows))
        self.assertEqual({"source-one"}, {row["SOURCE_KEY"] for row in rows})
        with open(selected["MAPPING_FILE"], encoding="utf-8-sig", newline="") as handle:
            original = list(csv.DictReader(handle))
        self.assertEqual([row["NOTES"] or None for row in original], [row["NOTES"] for row in rows])


if __name__ == "__main__":
    unittest.main()
