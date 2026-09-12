"""Canonical graph schemas with strict local Snowpark stand-ins, no SQL."""
import contextlib
import copy
import datetime
import sys
import types
import unittest
from unittest.mock import patch

import test_metadata_driven_contract as metadata
import test_multi_model_graph as graph
import test_registry_metadata_contract as registry_contract

NODE_COLUMNS = (
    "NODE_KEY", "ELEMENT_PATH", "INSTANCE_KEY", "PARENT_INSTANCE_KEY",
    "OSCAL_UUID", "ELEMENT_TYPE", "METADATA_JSON", "SOURCE_SYSTEM_NAME",
    "SOURCE_TABLE_NAME", "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID",
    "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ",
)
EDGE_COLUMNS = (
    "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH",
    "DEPENDENCY_TYPE", "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID",
)

class StringType:
    pass

class TimestampTimeZone:
    TZ = "TZ"

class TimestampType:
    def __init__(self, timezone):
        self.tz = timezone

class StructField:
    def __init__(self, name, datatype, nullable=True):
        self.name, self.datatype, self.nullable = name, datatype, nullable

class StructType:
    def __init__(self, fields):
        self.fields = list(fields)

@contextlib.contextmanager
def snowpark_types_stub():
    """Only import/type construction is mocked; no Snowflake session is created."""
    snowflake = types.ModuleType("snowflake")
    snowflake.__path__ = []
    snowpark = types.ModuleType("snowflake.snowpark")
    snowpark.__path__ = []
    type_module = types.ModuleType("snowflake.snowpark.types")
    for kind in (StringType, TimestampTimeZone, TimestampType, StructField, StructType):
        setattr(type_module, kind.__name__, kind)
    snowflake.snowpark = snowpark
    snowpark.types = type_module
    with patch.dict(sys.modules, {
            "snowflake": snowflake, "snowflake.snowpark": snowpark,
            "snowflake.snowpark.types": type_module}):
        yield type_module

class StrictGraphSession:
    def __init__(self):
        self.calls = []

    def create_dataframe(self, rows, schema=None):
        self.calls.append((rows, schema))
        if not rows and not isinstance(schema, StructType):
            raise ValueError("Cannot infer schema from empty data")
        frame = graph.Frame(rows)
        if schema is not None:
            if not isinstance(schema, StructType) or not schema.fields:
                raise AssertionError("Empty graph transport requires a typed nonempty schema")
            frame.columns = [field.name for field in schema.fields]
        return frame

class TypedGraphFrameTests(unittest.TestCase):
    def setUp(self):
        self.namespace = metadata.namespace()
        self.session = StrictGraphSession()
        self.namespace["session"] = self.session

    def singleton_context(self):
        registry = [row for row in registry_contract.annotated_registry()
                    if row["NODE_PATH"] == metadata.ROOT_PATH]
        mapping = metadata.mapping(path=metadata.ROOT_PATH + ".title")
        context = self.namespace["compile_mapping_contexts"](
            {"source-one": [mapping]}, registry, [metadata.profile()],
            {metadata.MODEL: registry_contract.strict_contract()})[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        return context, graph.Frame(registry)

    def test_empty_edges_have_all_six_nullable_string_columns(self):
        with snowpark_types_stub():
            frame = self.namespace["_create_canonical_graph_frame"]([], "edges")
        rows, schema = self.session.calls[0]
        self.assertEqual([], rows)
        self.assertEqual(list(EDGE_COLUMNS), frame.columns)
        self.assertEqual(list(EDGE_COLUMNS), [field.name for field in schema.fields])
        self.assertTrue(all(type(field.datatype) is StringType for field in schema.fields))
        self.assertTrue(all(field.nullable is True for field in schema.fields))

    def test_empty_node_schema_preserves_string_and_timezone_aware_timestamp_types(self):
        with snowpark_types_stub():
            frame = self.namespace["_create_canonical_graph_frame"]([], "nodes")
        _, schema = self.session.calls[0]
        self.assertEqual(list(NODE_COLUMNS), frame.columns)
        for field in schema.fields:
            with self.subTest(column=field.name):
                if field.name in {"DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}:
                    self.assertIs(type(field.datatype), TimestampType)
                    self.assertEqual(TimestampTimeZone.TZ, field.datatype.tz)
                else:
                    self.assertIs(type(field.datatype), StringType)
                self.assertIs(field.nullable, True)
        self.assertNotIn("PROCESS_ORDER", frame.columns)

    def test_populated_rows_keep_existing_inference_without_type_import_or_mutation(self):
        timestamp = datetime.datetime(2026, 9, 12, tzinfo=datetime.timezone.utc)
        for kind, rows in (
            ("nodes", [{**{name: "value" for name in NODE_COLUMNS},
                        "PARENT_INSTANCE_KEY": None, "DW_LOAD_TIMESTAMP": timestamp,
                        "DW_LOAD_TIMESTAMP_TZ": timestamp}]),
            ("edges", [{name: "value" for name in EDGE_COLUMNS}]),
        ):
            before = copy.deepcopy(rows)
            with self.subTest(kind=kind), patch.dict(sys.modules, {
                    "snowflake": None, "snowflake.snowpark": None,
                    "snowflake.snowpark.types": None}):
                frame = self.namespace["_create_canonical_graph_frame"](rows, kind)
            self.assertIs(rows, self.session.calls[-1][0])
            self.assertIsNone(self.session.calls[-1][1])
            self.assertEqual(before, rows)
            self.assertEqual(before, frame.rows)

    def test_singleton_only_approved_model_builds_typed_empty_edges(self):
        context, registry = self.singleton_context()
        records = [{"SOURCE_RECORD_ID": "1",
                    "CURATED_JSON": {"NEVER_SEEN_SOURCE_FIELD": "Example"}}]
        with snowpark_types_stub():
            nodes, edges = graph.build(self.namespace, context, records, registry)
        self.assertEqual((1, 0), (len(nodes.rows), len(edges.rows)))
        self.assertEqual(list(EDGE_COLUMNS), edges.columns)
        self.assertIsNone(nodes.rows[0]["PARENT_INSTANCE_KEY"])
        self.assertIsNone(self.session.calls[0][1])
        self.assertIsInstance(self.session.calls[1][1], StructType)
        self.assertFalse(context["config"]["EXECUTE_WRITES"])

    def test_optional_absent_value_keeps_empty_root_and_typed_edges(self):
        context, registry = self.singleton_context()
        with snowpark_types_stub():
            nodes, edges = graph.build(self.namespace, context,
                [{"SOURCE_RECORD_ID": "1", "CURATED_JSON": {}}], registry)
        self.assertEqual((1, 0), (len(nodes.rows), len(edges.rows)))
        self.assertEqual(list(EDGE_COLUMNS), edges.columns)
        self.assertEqual(0, context["graph_report"]["FIELDS"]["NEVER_SEEN_SOURCE_FIELD"]["emitted"])

    def test_empty_source_still_blocks_before_dataframe_creation(self):
        context, registry = self.singleton_context()
        with self.assertRaisesRegex(ValueError, "Metadata mappings rejected source values"):
            graph.build(self.namespace, context, [], registry)
        self.assertEqual([], self.session.calls)
        self.assertEqual("BLOCKED", context["graph_report"]["STATUS"])

    def test_unknown_frame_kind_does_not_reach_transport(self):
        with self.assertRaisesRegex(ValueError, "Unknown canonical graph frame kind"):
            self.namespace["_create_canonical_graph_frame"]([], "other")
        self.assertEqual([], self.session.calls)

    def test_missing_type_support_does_not_fall_back_to_untyped_empty_data(self):
        with patch.dict(sys.modules, {"snowflake": None, "snowflake.snowpark": None,
                                      "snowflake.snowpark.types": None}):
            with self.assertRaises(ImportError):
                self.namespace["_create_canonical_graph_frame"]([], "edges")
        self.assertEqual([], self.session.calls)

if __name__ == "__main__":
    unittest.main()
