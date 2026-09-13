"""Synthetic lookup transport tests; these do not claim Snowflake SQL acceptance."""
import copy
import json
import sys
import types
import unittest
from unittest.mock import patch

from lean_support import namespace


class Expression:
    def __init__(self, evaluate, name=None):
        self.evaluate, self.name = evaluate, name

    def alias(self, name):
        return Expression(self.evaluate, name)

    def cast(self, datatype):
        def evaluate(row):
            value = self.evaluate(row)
            return None if value is None else str(value)
        return Expression(evaluate, self.name)

    def isin(self, values):
        return Expression(lambda row: self.evaluate(row) in values)


def column(name):
    return Expression(lambda row: row[name], name)


def trim(expression):
    def evaluate(row):
        value = expression.evaluate(row)
        return value.strip() if value is not None else None
    return Expression(evaluate)


class QueryFrame:
    def __init__(self, rows, events, columns=None):
        self.rows, self.events = rows, events
        self.columns = columns or list(rows[0] if rows else {})

    def filter(self, predicate):
        return QueryFrame([row for row in self.rows if predicate.evaluate(row)], self.events, self.columns)

    def select(self, *expressions):
        rows = [{expression.name: expression.evaluate(row) for expression in expressions} for row in self.rows]
        return QueryFrame(rows, self.events, [expression.name for expression in expressions])

    def to_local_iterator(self):
        self.events.append((tuple(self.columns), len(self.rows)))
        return iter(self.rows)


class HydrationTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.context = {
            "config": {"EXECUTE_WRITES": False}, "compiled_plan": {"options": {}},
            "lookups": {"component_contract": {"apps": {
                "title_field": "NAME", "description_field": "DESC"}}},
        }
        self.mapping = {
            "SOURCE_FIELD_NAME": "APPS", "TRANSFORM_ID": "direct",
            "REPRESENTATION_PARAMS": {"reference_type": "software", "hydrate_lookup": "apps"},
        }
        self.records = [
            {"CONTENT_ID": "1", "CURATED_JSON": {"NAME": " First ", "DESC": " Description "}},
            {"CONTENT_ID": "2", "CURATED_JSON": {"NAME": " Second ", "DESC": " "}},
            {"CONTENT_ID": None, "CURATED_JSON": "malformed unrelated record"},
        ]
        functions = types.ModuleType("snowflake.snowpark.functions")
        functions.col, functions.trim = column, trim
        snowpark = types.ModuleType("snowflake.snowpark")
        snowpark.functions = functions
        self.modules = {"snowflake": types.ModuleType("snowflake"),
                        "snowflake.snowpark": snowpark, "snowflake.snowpark.functions": functions}

    def run_hydration(self, references, records=None, required=False, source_as_text=False,
                      extra_mapping=None, extra_source=None):
        events = []
        source = dict(APPS=references, **(extra_source or {}))
        if source_as_text:
            source = json.dumps(source)
        frame = QueryFrame([{"SOURCE_RECORD_ID": "synthetic", "CURATED_JSON": source}], events)
        lookup = QueryFrame(copy.deepcopy(self.records if records is None else records), events,
                            ["CONTENT_ID", "CURATED_JSON"])
        mapping = copy.deepcopy(self.mapping)
        mapping["REPRESENTATION_PARAMS"]["description_required"] = required
        mappings = [mapping] + ([extra_mapping] if extra_mapping else [])
        with patch.dict(sys.modules, self.modules):
            result = self.ns["_build_component_hydration_lookups"](
                frame, mappings, {"apps": lookup}, copy.deepcopy(self.context))
        return result, events

    def test_duplicate_references_share_one_requested_lookup(self):
        result, events = self.run_hydration([{"ContentId": " 1 "}, 1, "2"], source_as_text=True)
        self.assertEqual(result, {"software": {
            "1": {"title": "First", "description": "Description"},
            "2": {"title": "Second", "description": None},
        }})
        self.assertEqual(events, [(("SOURCE_RECORD_ID", "CURATED_JSON"), 1),
                                  (("CONTENT_ID", "CURATED_JSON"), 2)])

    def test_selected_lookup_failures_abort(self):
        cases = [
            ("missing", ["9"], self.records, False),
            ("duplicate", ["1"], self.records + [self.records[0]], False),
            ("blank title", ["3"], [{"CONTENT_ID": "3", "CURATED_JSON": {"NAME": " "}}], False),
            ("numeric title", ["3"], [{"CONTENT_ID": "3", "CURATED_JSON": {"NAME": 3}}], False),
            ("malformed JSON", ["3"], [{"CONTENT_ID": "3", "CURATED_JSON": "bad"}], False),
            ("array JSON", ["3"], [{"CONTENT_ID": "3", "CURATED_JSON": "[]"}], False),
            ("required description", ["2"], self.records, True),
        ]
        for label, references, records, required in cases:
            with self.subTest(case=label), self.assertRaises(ValueError):
                self.run_hydration(references, records, required)

    def test_invalid_reference_shapes_abort(self):
        for value in ([True], [{}], [None], "1", {"ContentId": "1"}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_hydration(value)

    def test_large_reference_set_uses_bounded_batches(self):
        records = [{"CONTENT_ID": str(index), "CURATED_JSON": {"NAME": "App " + str(index)}}
                   for index in range(1001)]
        result, events = self.run_hydration([str(index) for index in range(1001)], records)
        self.assertEqual(len(result["software"]), 1001)
        self.assertEqual([count for columns, count in events], [1, 1000, 1])

    def test_empty_references_do_not_read_lookup_rows(self):
        result, events = self.run_hydration([])
        self.assertEqual(result, {"software": {}})
        self.assertEqual(events, [(("SOURCE_RECORD_ID", "CURATED_JSON"), 1)])

    def test_same_content_id_cannot_have_two_component_types(self):
        other = copy.deepcopy(self.mapping)
        other["SOURCE_FIELD_NAME"] = "OTHER_APPS"
        other["REPRESENTATION_PARAMS"]["reference_type"] = "interconnection"
        with self.assertRaisesRegex(ValueError, "type collision"):
            self.run_hydration(["1"], extra_mapping=other, extra_source={"OTHER_APPS": ["1"]})

    def test_unhydrated_references_do_not_query_lookup(self):
        self.mapping["REPRESENTATION_PARAMS"].pop("hydrate_lookup")
        result, events = self.run_hydration(["unresolved-partial-component"])
        self.assertEqual(result, {})
        self.assertEqual(events, [])

    def test_required_description_is_trimmed_and_preserved(self):
        result, _ = self.run_hydration(["1"], required=True)
        self.assertEqual(result["software"]["1"]["description"], "Description")


if __name__ == "__main__":
    unittest.main()
