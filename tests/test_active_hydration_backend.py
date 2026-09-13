"""Execute the active Snowpark query plan against rows and its frozen predecessor."""
import contextlib
import copy
import io
import json
import operator
import sys
import types
import unittest
from decimal import Decimal
from unittest.mock import patch

from test_multi_model_graph import namespace


JSON_NULL = object()


class Expression:
    def __init__(self, evaluate, name=None):
        self.evaluate, self.name = evaluate, name

    def alias(self, name):
        return Expression(self.evaluate, name)

    def binary(self, other, operation):
        other = other if isinstance(other, Expression) else literal(other)
        return Expression(lambda row: operation(self.evaluate(row), other.evaluate(row)))

    def nullable(self, other, operation):
        return self.binary(other, lambda a, b: None if a is None or b is None else operation(a, b))

    def __eq__(self, other):
        return self.nullable(other, operator.eq)

    def __ne__(self, other):
        return self.nullable(other, operator.ne)

    def __gt__(self, other):
        return self.nullable(other, operator.gt)

    def __and__(self, other):
        def conjunction(a, b):
            return False if a is False or b is False else None if a is None or b is None else True
        return self.binary(other, conjunction)

    def __or__(self, other):
        def disjunction(a, b):
            return True if a is True or b is True else None if a is None or b is None else False
        return self.binary(other, disjunction)

    def __invert__(self):
        return Expression(lambda row: None if self.evaluate(row) is None else not self.evaluate(row))

    def is_null(self):
        return Expression(lambda row: self.evaluate(row) is None)

    def is_not_null(self):
        return ~self.is_null()

    def isin(self, *values):
        return Expression(lambda row: None if self.evaluate(row) is None else self.evaluate(row) in values)

    def getItem(self, key):
        def item(row):
            value = self.evaluate(row)
            if not isinstance(value, dict) or key not in value:
                return None
            return JSON_NULL if value[key] is None else value[key]
        return Expression(item)

    def cast(self, kind):
        def cast(row):
            value = self.evaluate(row)
            if value is None:
                return None
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return str(value)
        return Expression(cast, self.name)


class Choice(Expression):
    def __init__(self, cases, fallback=None):
        self.cases, self.fallback = cases, fallback
        super().__init__(self.choose)

    def choose(self, row):
        for condition, value in self.cases:
            if condition.evaluate(row) is True:
                return value.evaluate(row)
        return self.fallback.evaluate(row) if self.fallback is not None else None

    def when(self, condition, value):
        return Choice(self.cases + [(condition, value)], self.fallback)

    def otherwise(self, value):
        return Choice(self.cases, value)


class Aggregate:
    def __init__(self, expression, distinct=False, name=None):
        self.expression, self.distinct, self.name = expression, distinct, name

    def alias(self, name):
        return Aggregate(self.expression, self.distinct, name)

    def evaluate(self, rows):
        values = [self.expression.evaluate(row) for row in rows]
        values = [value for value in values if value is not None]
        return len(set(values)) if self.distinct else len(values)


def literal(value):
    return Expression(lambda row: value)


def column(name):
    return Expression(lambda row: row.get(name), name)


def unary(function):
    def apply(expression):
        return Expression(lambda row: None if expression.evaluate(row) is None
                          else function(expression.evaluate(row)))
    return apply


def variant_type(value):
    if value is JSON_NULL:
        return "NULL_VALUE"
    return {dict: "OBJECT", list: "ARRAY", str: "VARCHAR", int: "INTEGER",
            float: "DOUBLE", bool: "BOOLEAN"}[type(value)]


FUNCTIONS = types.ModuleType("snowflake.snowpark.functions")
FUNCTIONS.col, FUNCTIONS.lit = column, literal
FUNCTIONS.count = Aggregate
FUNCTIONS.count_distinct = lambda expression: Aggregate(expression, distinct=True)
FUNCTIONS.when = lambda condition, value: Choice([(condition, value)])
FUNCTIONS.upper = unary(str.upper)
FUNCTIONS.typeof = unary(variant_type)
FUNCTIONS.length = unary(len)
FUNCTIONS.trim = unary(str.strip)
FUNCTIONS.parse_json = unary(lambda value: JSON_NULL if json.loads(value) is None else json.loads(value))


class QueryFrame:
    def __init__(self, rows, columns=None, events=None):
        self.rows = rows
        self.columns = columns or list(rows[0] if rows else {})
        self.events = events if events is not None else []

    def frame(self, rows, columns=None):
        return QueryFrame(rows, columns, self.events)

    def __getitem__(self, key):
        return column(key)

    def select(self, *expressions):
        return self.frame([{item.name: item.evaluate(row) for item in expressions} for row in self.rows],
                          [item.name for item in expressions])

    def filter(self, condition):
        return self.frame([row for row in self.rows if condition.evaluate(row) is True], self.columns)

    def count(self):
        self.events.append(("count", tuple(self.columns)))
        return len(self.rows)

    def agg(self, *aggregates):
        return self.frame([{item.name: item.evaluate(self.rows) for item in aggregates}])

    def collect(self):
        self.events.append(("collect", tuple(self.columns)))
        return self.rows

    def to_local_iterator(self):
        self.events.append(("iterate", tuple(self.columns)))
        return iter(self.rows)

    def distinct(self):
        unique = {json.dumps(row, sort_keys=True): row for row in self.rows}
        return self.frame(list(unique.values()), self.columns)

    def group_by(self, expression):
        groups = {}
        for row in self.rows:
            groups.setdefault(expression.evaluate(row), []).append(row)
        def aggregate(*items):
            return self.frame([{expression.name: key, **{item.name: item.evaluate(rows) for item in items}}
                               for key, rows in groups.items()])
        return types.SimpleNamespace(agg=aggregate)

    def union_all(self, other):
        return self.frame(self.rows + other.rows, self.columns)

    def join_table_function(self, name, expression):
        assert name == "flatten"
        return self.frame([dict(row, VALUE=value) for row in self.rows for value in expression.evaluate(row)])

    def join(self, other, condition, mode):
        assert mode == "left"
        rows = []
        for left in self.rows:
            matches = [dict(left, **right) for right in other.rows
                       if condition.evaluate(dict(left, **right)) is True]
            rows.extend(matches or [dict(left, **{name: None for name in other.columns})])
        return self.frame(rows)


class ActiveHydrationBackendTests(unittest.TestCase):
    def run_backend(self, sources=None, lookup=None, context_edit=None, legacy=False,
                    prepare=False, extra_mappings=()):
        events = []
        sources = sources if sources is not None else [{"APPS": [{"ContentId": " 1 "}, "1"], "MORE_APPS": [2]}]
        lookup = lookup if lookup is not None else [
            {"CONTENT_ID": "1", "CURATED_JSON": {"NAME": " First ", "DETAIL": " Description "}},
            {"CONTENT_ID": "2", "CURATED_JSON": {"NAME": "Second", "DETAIL": " "}},
            {"CONTENT_ID": "3", "CURATED_JSON": {"NAME": "Unreferenced"}},
        ]
        source = QueryFrame([{"SOURCE_RECORD_ID": str(i), "CURATED_JSON": json.dumps(value)}
                             for i, value in enumerate(sources)], ["SOURCE_RECORD_ID", "CURATED_JSON"], events)
        lookup_frame = QueryFrame(copy.deepcopy(lookup), ["CONTENT_ID", "CURATED_JSON"], events)
        spec = {"contracts": {"application": {"title_field": "NAME", "description_field": "DETAIL"}},
                "source_types": {"APPS": "application", "MORE_APPS": "application"},
                "routes": {"APPS": "application", "MORE_APPS": "application"}}
        context = {"config": {"EXECUTE_WRITES": False}, "_metadata_hydration_spec": spec}
        if context_edit:
            context_edit(context)
        mappings = [{"SOURCE_FIELD_NAME": field, "REPRESENTATION_PARAMS": {"reference_type": kind}}
                    for field, kind in spec["source_types"].items()]
        frames = {kind: lookup_frame for kind in spec["contracts"]}
        if not legacy:
            # The active query consumes approved rows and source bindings directly.
            # Only the frozen oracle still needs its historical intermediate spec.
            context.pop("_metadata_hydration_spec")
            context["lookups"] = {"component_contract": {
                "lookup-" + kind: contract for kind, contract in spec["contracts"].items()
            }}
            frames = {"lookup-" + kind: frame for kind, frame in frames.items()}
            for row in mappings:
                field = row["SOURCE_FIELD_NAME"]
                if field in spec["routes"]:
                    kind = spec["routes"][field]
                    row["REPRESENTATION_PARAMS"]["hydrate_lookup"] = "lookup-" + kind
                    row["REPRESENTATION_PARAMS"]["description_required"] = spec["contracts"][kind].get("description_required", False)
        snowpark = types.ModuleType("snowflake.snowpark")
        snowpark.functions = FUNCTIONS
        snowflake = types.ModuleType("snowflake")
        snowflake.snowpark = snowpark
        with patch.dict(sys.modules, {"snowflake": snowflake, "snowflake.snowpark": snowpark,
                                      "snowflake.snowpark.functions": FUNCTIONS}), contextlib.redirect_stdout(io.StringIO()):
            helpers = namespace(legacy)
            if prepare:
                context["config"]["OSCAL_MODEL"] = "SYNTHETIC_MODEL"
                context["graph_report"] = {}
                context["lookups"]["component_sources"] = frames
                context["compiled_plan"] = {
                    "elements": {
                        "synthetic.references[]": {"operator": "references"},
                        "synthetic.summary": {"operator": "object"},
                    },
                    "mappings": [dict(row, OWNER_ELEMENT_PATH="synthetic.references[]",
                                      TRANSFORM_ID="direct") for row in mappings] + list(extra_mappings),
                }
                helpers["_metadata_prepare"](source, context)
                result = context["component_hydration_lookups"]
            else:
                result = helpers["_build_component_hydration_lookups"](source, mappings, frames, context)
        return result, events

    def test_prepare_limits_duplicate_checks_to_active_reference_mappings(self):
        ordinary = {"SOURCE_FIELD_NAME": "APPS", "OWNER_ELEMENT_PATH": "synthetic.summary",
                    "TRANSFORM_ID": "direct", "REPRESENTATION_PARAMS": {"target": "source-references"}}
        skipped = {"SOURCE_FIELD_NAME": "APPS", "OWNER_ELEMENT_PATH": "synthetic.references[]",
                   "TRANSFORM_ID": "skip", "REPRESENTATION_PARAMS": {
                       "reference_type": "application", "hydrate_lookup": "lookup-application"}}
        actual, _ = self.run_backend(prepare=True, extra_mappings=[ordinary, skipped])
        self.assertEqual(actual, {"application": {
            "1": {"title": "First", "description": "Description"},
            "2": {"title": "Second", "description": None},
        }})
        duplicate = dict(skipped, TRANSFORM_ID="direct")
        with self.assertRaisesRegex(RuntimeError, "Canonical component mapping is duplicated"):
            self.run_backend(prepare=True, extra_mappings=[ordinary, skipped, duplicate])

    def test_routed_payloads_match_frozen_query_backend(self):
        actual, events = self.run_backend()
        expected, _ = self.run_backend(legacy=True)
        self.assertEqual(actual, expected)
        self.assertEqual(actual, {"application": {"1": {"title": "First", "description": "Description"},
                                                  "2": {"title": "Second", "description": None}}})
        self.assertEqual([columns for action, columns in events if action == "iterate"],
                         [("COMPONENT_ID", "TITLE", "DESCRIPTION")])
        self.assertTrue(all("CURATED_JSON" not in columns for action, columns in events if action == "collect"))

    def test_optional_null_and_missing_descriptions_match(self):
        for description in ({}, {"DETAIL": None}, {"DETAIL": ""}):
            lookup = [{"CONTENT_ID": "1", "CURATED_JSON": {"NAME": "App", **description}}]
            kwargs = dict(sources=[{"APPS": [1]}], lookup=lookup)
            self.assertEqual(self.run_backend(**kwargs)[0], self.run_backend(**kwargs, legacy=True)[0])

    def test_invalid_reference_roots_and_members_match(self):
        cases = [({"APPS": "1"}, "invalid shape"), ({"APPS": [True]}, "invalid ContentId"),
                 ({"APPS": [{}]}, "invalid ContentId"), ({"APPS": [""]}, "invalid ContentId")]
        for source, message in cases:
            for legacy in (False, True):
                with self.subTest(source=source, legacy=legacy), self.assertRaisesRegex(RuntimeError, message):
                    self.run_backend(sources=[source], legacy=legacy)

    def test_lookup_guards_match_for_referenced_and_unreferenced_rows(self):
        cases = [
            ([{"CONTENT_ID": " ", "CURATED_JSON": {}}], "missing ContentId"),
            ([{"CONTENT_ID": "1", "CURATED_JSON": {}}, {"CONTENT_ID": "1", "CURATED_JSON": {}}], "duplicate ContentId"),
            ([{"CONTENT_ID": "9", "CURATED_JSON": []}], "invalid curated JSON"),
            ([{"CONTENT_ID": "9", "CURATED_JSON": {}}], "lookup record is missing"),
            ([{"CONTENT_ID": "1", "CURATED_JSON": {"NAME": 12}}], "title is missing or invalid"),
            ([{"CONTENT_ID": "1", "CURATED_JSON": {"NAME": "App", "DETAIL": []}}], "description is invalid"),
        ]
        for lookup, message in cases:
            for legacy in (False, True):
                with self.subTest(message=message, legacy=legacy), self.assertRaisesRegex(RuntimeError, message):
                    self.run_backend(sources=[{"APPS": [1]}], lookup=lookup, legacy=legacy)

    def test_required_description_stays_required(self):
        def require(context):
            context["_metadata_hydration_spec"]["contracts"]["application"]["description_required"] = True
        for legacy in (False, True):
            with self.assertRaisesRegex(RuntimeError, "description is invalid"):
                self.run_backend(context_edit=require, legacy=legacy)

    def test_type_collision_stays_rejected(self):
        def add_type(context):
            spec = context["_metadata_hydration_spec"]
            spec["source_types"]["MORE_APPS"] = "other"
            spec["routes"]["MORE_APPS"] = "other"
            spec["contracts"]["other"] = spec["contracts"]["application"]
        for legacy in (False, True):
            with self.assertRaisesRegex(RuntimeError, "type collision"):
                self.run_backend(sources=[{"APPS": [1], "MORE_APPS": [1]}], context_edit=add_type, legacy=legacy)

    def test_empty_source_references_produce_empty_lookup(self):
        for legacy in (False, True):
            result, _ = self.run_backend(sources=[{}], legacy=legacy)
            self.assertEqual(result, {"application": {}})

    def test_sql_null_and_variant_null_references_match(self):
        for legacy in (False, True):
            result, _ = self.run_backend(sources=[{}, {"APPS": None}], legacy=legacy)
            self.assertEqual(result, {"application": {}})
            with self.assertRaisesRegex(RuntimeError, "invalid ContentId"):
                self.run_backend(sources=[{"APPS": [None]}], legacy=legacy)

    def test_whole_lookup_sql_null_and_json_null_keep_distinct_behavior(self):
        # An unreferenced SQL NULL follows the existing SQL predicate semantics;
        # the JSON null value has a variant type and is rejected as a non-object.
        for value in (None, "null"):
            lookup = [{"CONTENT_ID": "9", "CURATED_JSON": value}]
            for legacy in (False, True):
                if value is None:
                    self.assertEqual(self.run_backend(sources=[{}], lookup=lookup, legacy=legacy)[0],
                                     {"application": {}})
                else:
                    with self.assertRaisesRegex(RuntimeError, "invalid curated JSON"):
                        self.run_backend(sources=[{}], lookup=lookup, legacy=legacy)

    def test_shared_scalar_normalizer_matches_all_three_original_contracts(self):
        active, frozen = namespace(), namespace(legacy=True)
        values = [None, "", " ", " Alpha ", 0, -3, 1.25, True, False, [], {}, [1],
                  {"Id": 1}, float("nan"), float("inf"), float("-inf"), "NaN", " +inf ",
                  Decimal("12.300"), Decimal("NaN"), Decimal("Infinity"), (1, 2)]
        for name in ("_oscal_property_values", "_canonical_component_content_id", "transform_document_identifier"):
            for value in values:
                with self.subTest(helper=name, value=value):
                    try:
                        expected = frozen[name](value)
                    except ValueError as error:
                        with self.assertRaises(ValueError) as actual:
                            active[name](value)
                        self.assertEqual(str(actual.exception), str(error))
                    else:
                        self.assertEqual(active[name](value), expected)
