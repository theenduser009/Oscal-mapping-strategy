"""Real Snowpark local emulator smoke; this does not exercise live Snowflake SQL.

Install snowflake-snowpark-python[localtest]==1.55.0 and pandas==2.3.3.
CI must set REQUIRE_SNOWPARK_TESTS=1 so a missing dependency fails the job.
The emulator does not parse Session.sql or DataFrame.filter SQL strings. Only
those two SQL boundaries are adapted below; projection, snapshots, ranking,
deduplication, schema construction and collection use the installed package.
See https://docs.snowflake.com/en/developer-guide/snowpark/python/testing-locally
"""
from contextlib import contextmanager
import datetime
import json
import os
import unittest
from unittest.mock import patch

from lean_support import namespace


class SnowparkLocalSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from snowflake.snowpark import Session, DataFrame
            from snowflake.snowpark import functions, types
            from snowflake.snowpark.window import Window
        except ImportError:
            if os.environ.get("REQUIRE_SNOWPARK_TESTS") == "1":
                raise
            raise unittest.SkipTest("Snowpark localtest dependency is absent; CI requires this smoke") from None
        cls.Session, cls.DataFrame, cls.functions, cls.types, cls.Window = Session, DataFrame, functions, types, Window

    def setUp(self):
        self.session = self.Session.builder.config("local_testing", True).create()
        self.addCleanup(self.session.close)
        self.ns = namespace()
        self.ns.update(session=self.session, Window=self.Window,
                       **{name: getattr(self.functions, name) for name in ("col", "lit", "dense_rank")},
                       **{name: getattr(self.types, name) for name in (
                           "StructType", "StructField", "StringType", "TimestampType", "TimestampTimeZone")})

    @contextmanager
    def sql_boundaries(self):
        """Adapt the two documented SQL-only emulator limitations, and nothing else."""
        original_filter = self.DataFrame.filter
        types = self.types

        def transaction_sql(statement):
            self.assertEqual("SELECT CURRENT_TRANSACTION() AS TX", statement)
            return self.session.create_dataframe([(None,)], schema=types.StructType([
                types.StructField("TX", types.LongType())]))

        def filter_sql(frame, condition, *args, **kwargs):
            if not isinstance(condition, str):
                return original_filter(frame, condition, *args, **kwargs)
            self.assertEqual("SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID)) = 0", condition)
            missing = [(row["SOURCE_RECORD_ID"],) for row in frame.select("SOURCE_RECORD_ID").collect()
                       if row["SOURCE_RECORD_ID"] is None or not row["SOURCE_RECORD_ID"].strip()]
            return self.session.create_dataframe(missing, schema=types.StructType([
                types.StructField("SOURCE_RECORD_ID", types.StringType())]))

        with patch.object(self.session, "sql", side_effect=transaction_sql), patch.object(self.DataFrame, "filter", new=filter_sql):
            yield

    def source(self, rows, variant=False):
        types = self.types
        schema = types.StructType([
            types.StructField("CONTENT_ID", types.StringType()),
            types.StructField("CURATED_JSON", types.VariantType() if variant else types.StringType()),
            types.StructField("UPDATED", types.LongType()),
        ])
        self.session.create_dataframe(rows, schema=schema).write.save_as_table("SOURCE_SMOKE", mode="overwrite")
        with self.sql_boundaries():
            result, counts, snapshot = self.ns["load_source_input"](
                self.session, {"RAW_TABLE": "SOURCE_SMOKE", "SOURCE_ORDER_CANDIDATES": ("UPDATED",)})
            return result.collect(), counts, snapshot

    def test_actual_dense_rank_retains_latest_and_collapses_equal_latest(self):
        rows, counts, snapshot = self.source([
            ("one", '{"value":"old"}', 1), ("one", '{"value":"new"}', 2),
            ("one", '{"value":"new"}', 2), ("two", '{"value":"separate"}', None),
        ])
        self.assertEqual({"one": "new", "two": "separate"},
                         {row["SOURCE_RECORD_ID"]: json.loads(row["CURATED_JSON"])["value"] for row in rows})
        self.assertEqual({"RAW_ROWS": 4, "SELECTED_ROWS": 2, "DUPLICATE_SOURCE_ROWS_RESOLVED": 2}, counts)
        self.assertEqual(4, snapshot.count())

    def test_actual_variant_projection_preserves_structured_payload(self):
        rows, counts, _ = self.source([
            ("one", {"value": 2}, 2),
        ], variant=True)
        self.assertEqual(1, len(rows))
        payload = rows[0]["CURATED_JSON"]
        self.assertEqual({"value": 2}, json.loads(payload) if isinstance(payload, str) else payload)
        self.assertEqual(0, counts["DUPLICATE_SOURCE_ROWS_RESOLVED"])

    def test_actual_latest_conflicting_payloads_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Conflicting source payloads"):
            self.source([("one", '{"value":1}', 2), ("one", '{"value":2}', 2)])

    def test_explicit_node_schema_preserves_null_parent_fields_and_timestamps(self):
        timestamp = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        row = {"NODE_KEY": "1" * 32, "ELEMENT_PATH": "synthetic-model", "PARENT_NODE_PATH": None,
               "INSTANCE_KEY": "singleton", "PARENT_INSTANCE_KEY": None, "OSCAL_UUID": "2" * 32,
               "ELEMENT_TYPE": "root", "METADATA_JSON": "{}", "SOURCE_SYSTEM_NAME": "SYNTHETIC",
               "SOURCE_TABLE_NAME": "SOURCE", "SOURCE_RECORD_ID": "one", "DW_PIPELINE_RUN_ID": "test",
               "DW_LOAD_TIMESTAMP": timestamp, "DW_LOAD_TIMESTAMP_TZ": timestamp}
        frame = self.ns["_create_canonical_graph_frame"]([row], "nodes")
        actual = frame.collect()[0]
        self.assertIsNone(actual["PARENT_NODE_PATH"])
        self.assertIsNone(actual["PARENT_INSTANCE_KEY"])
        self.assertEqual(timestamp, actual["DW_LOAD_TIMESTAMP_TZ"])
        fields = {field.name: field.datatype for field in frame.schema.fields}
        self.assertIsInstance(fields["NODE_KEY"], self.types.StringType)
        self.assertEqual(self.types.TimestampTimeZone.TZ, fields["DW_LOAD_TIMESTAMP_TZ"].tz)

    def test_empty_edge_frame_retains_the_full_transport_schema(self):
        frame = self.ns["_create_canonical_graph_frame"]([], "edges")
        self.assertEqual([], frame.collect())
        self.assertEqual(["EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE",
                          "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID"], frame.columns)
        self.assertTrue(all(isinstance(field.datatype, self.types.StringType) for field in frame.schema.fields))


if __name__ == "__main__":
    unittest.main()
