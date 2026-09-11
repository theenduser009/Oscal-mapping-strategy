"""Uploaded 2026-09-11 schema regression; SQLite emulation is NOT a Snowflake run."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import runpy
import sqlite3
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import uuid

P = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      "notebooks/persistence/PILOT_SSP_ONE_RECORD_WRITE.py"))


def live_description(kind):
    # Exact names, types and nullability from the owner-uploaded DESC checkpoint.
    dim = [(P["SSP_PILOT_DIM_PK"], "BINARY(16)", "N"),
           ("ELEMENT_TYPE", "VARCHAR(64)", "Y"), ("OSCAL_UUID", "VARCHAR(32)", "Y"),
           ("METADATA_JSON", "VARIANT", "Y"), ("SOURCE_SYSTEM_NAME", "VARCHAR(100)", "Y"),
           ("SOURCE_TABLE_NAME", "VARCHAR(128)", "Y"), ("SOURCE_RECORD_ID", "VARCHAR(128)", "Y"),
           ("DW_PIPELINE_RUN_ID", "VARCHAR(64)", "Y"),
           ("DW_LOAD_TIMESTAMP", "TIMESTAMP_TZ(9)", "Y"),
           ("DW_LOAD_TIMESTAMP_TZ", "TIMESTAMP_TZ(9)", "Y")]
    fact = [(P["SSP_PILOT_FACT_PK"], "BINARY(16)", "N"),
            ("FK_SOURCE_ELEMENT_HASH", "BINARY(16)", "N"),
            ("FK_TARGET_ELEMENT_HASH", "BINARY(16)", "N"),
            ("DEPENDENCY_TYPE", "VARCHAR(32)", "N"),
            ("SOURCE_OSCAL_UUID", "VARCHAR(32)", "N"),
            ("TARGET_OSCAL_UUID", "VARCHAR(32)", "N")]
    return [{"name": n, "type": t, "null?": null, "kind": "COLUMN", "default": None}
            for n, t, null in (dim if kind == "DIM" else fact)]


class LiveSchema(unittest.TestCase):
    def test_exact_uploaded_schemas_and_lossless_expressions(self):
        plans = [P["_pilot_column_plan"](live_description(k), k) for k in ("DIM", "FACT")]
        self.assertEqual([10, 6], [len(p) for p in plans])
        hashes = [c for p in plans for c in p if c["type"] == "BINARY(16)"]
        compact = [c for p in plans for c in p if c["encoding"] == "UUID_TO_COMPACT32"]
        self.assertEqual(4, len(hashes))
        self.assertEqual(3, len(compact))
        for c in hashes:
            self.assertEqual(f'TO_BINARY(s."{c["source"]}", \'HEX\')', c["expression"])
        for c in compact:
            self.assertEqual(f'REPLACE(s."{c["source"]}", \'-\', \'\')', c["expression"])
        self.assertEqual('PARSE_JSON(s."METADATA_JSON")', plans[0][3]["expression"])
        for c in plans[0][-2:]:
            self.assertIn("AS TIMESTAMP_TZ(9)", c["expression"])
        self.assertNotIn("MD5", " ".join(c["expression"] for p in plans for c in p))

    def test_binary_scope_is_only_known_hash_columns_and_exact_width(self):
        for kind in ("DIM", "FACT"):
            for row in live_description(kind):
                if row["type"] == "BINARY(16)":
                    continue
                rows = live_description(kind)
                next(r for r in rows if r["name"] == row["name"])["type"] = "BINARY(16)"
                with self.assertRaises(P["PilotError"]):
                    P["_pilot_column_plan"](rows, kind)
        for dtype in ("BINARY", "BINARY(15)", "BINARY(17)", "BINARY(16); DELETE"):
            with self.assertRaises(P["PilotError"]):
                P["_pilot_safe_type"](dtype)

    def test_wider_uuid_columns_keep_canonical_format(self):
        rows = live_description("DIM")
        rows[2]["type"] = "VARCHAR(36)"
        c = P["_pilot_column_plan"](rows, "DIM")[2]
        self.assertIsNone(c["encoding"])
        self.assertEqual('CAST(s."OSCAL_UUID" AS VARCHAR)', c["expression"])

    def test_schema_failure_prints_actionable_metadata_without_target_dml(self):
        fn = P["run_ssp_one_record_write_pilot"]
        rows = live_description("DIM")
        rows[0]["type"] = "BINARY(17)"
        calls, out = [], io.StringIO()
        with patch.dict(fn.__globals__, {
                "_pilot_contract": lambda *a: None, "_pilot_no_transaction": lambda *a: None,
                "_pilot_query": lambda s, sql: calls.append(sql) or rows}), redirect_stdout(out):
            with self.assertRaises(P["PilotError"]):
                fn(None, {}, {}, None, None, "COMMIT")
        report = json.loads(out.getvalue())
        self.assertFalse(report["TARGET_DML_ATTEMPTED"])
        self.assertFalse(report["PERSISTED"])
        self.assertEqual(P["SSP_PILOT_DIM_PK"], report["ERROR_DETAILS"]["COLUMN"])
        self.assertEqual("BINARY(17)", report["ERROR_DETAILS"]["LIVE_TYPE"])
        self.assertTrue(all(s.startswith("DESC TABLE ") for s in calls))


class GraphMaterialization(unittest.TestCase):
    def test_freeze_materializes_both_frames_before_scoped_queries_without_views(self):
        fn = P["_pilot_freeze_graph"]
        events = []
        class Writer:
            def save_as_table(self, name, *, mode, table_type):
                events.append(("SAVE", name, mode, table_type))
        frames = [SimpleNamespace(write=Writer()), SimpleNamespace(write=Writer())]
        names = {k: "DEV.CURATED.TMP_TEST_" + k for k in ("NV", "EV", "NR", "ER")}
        counts = iter([70102, 67289, 3, 2, 1, 3])
        with patch.dict(fn.__globals__, {
                "_pilot_count": lambda *a: next(counts),
                "_pilot_query": lambda s, sql: events.append(("SQL", sql)),
                "_pilot_zero": lambda *a: None, "_pilot_unique": lambda *a: None}):
            result = fn(None, *frames, names)
        self.assertEqual({"SOURCE_RECORDS": 1, "NODES": 3, "EDGES": 2}, result)
        self.assertEqual([("SAVE", names[k], "errorifexists", "temporary") for k in ("NV", "EV")], events[:2])
        self.assertTrue(all(e[0] == "SQL" and e[1].startswith("CREATE TEMPORARY TABLE") for e in events[2:]))

    def test_materialization_failure_reports_step_without_target_dml_or_source_values(self):
        fn = P["run_ssp_one_record_write_pilot"]
        qid = "01234567-89ab-cdef-0123-456789abcdef"
        for failed_frame in ("NODES", "EDGES"):
            events, out = [], io.StringIO()
            class Writer:
                def __init__(self, label):
                    self.label = label
                def save_as_table(self, name, *, mode, table_type):
                    events.append(self.label)
                    if self.label == failed_frame:
                        error = RuntimeError("private source value and generated SQL")
                        error.sql_error_code, error.sqlstate, error.sfqid = 2003, "42S02", qid
                        raise error
            frames = [SimpleNamespace(write=Writer(label)) for label in ("NODES", "EDGES")]
            def query(session, sql):
                self.assertTrue(sql.startswith("DESC TABLE "))
                return live_description("DIM" if sql.endswith("DIM_OSCAL_SSP_ELEMENT") else "FACT")
            with patch.dict(fn.__globals__, {
                    "_pilot_contract": lambda *a: None, "_pilot_no_transaction": lambda *a: None,
                    "_pilot_query": query}), redirect_stdout(out):
                with self.assertRaisesRegex(P["PilotError"], "GRAPH_TEMP_MATERIALIZATION_FAILED"):
                    fn(None, {}, {}, *frames, mode="PREVIEW")
            report = json.loads(out.getvalue())
            self.assertFalse(report["TARGET_DML_ATTEMPTED"])
            self.assertFalse(report["PERSISTED"])
            self.assertEqual("MATERIALIZE_GRAPH_" + failed_frame, report["ERROR_DETAILS"]["STEP"])
            self.assertEqual(qid, report["ERROR_DETAILS"]["QUERY_ID"])
            self.assertEqual("2003", report["ERROR_DETAILS"]["SQL_ERROR_CODE"])
            self.assertNotIn("private source", out.getvalue())

    def test_only_valid_query_identifier_is_preserved(self):
        error = RuntimeError("private")
        error.sfqid = "private; SELECT source"
        self.assertNotIn("QUERY_ID", P["_pilot_error_details"](error))


class StorageEmulation(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.create_function("REGEXP_LIKE", 2, lambda s, p: None if s is None else bool(re.fullmatch(p, s)))
        self.db.create_function("TO_BINARY", 2, lambda s, fmt: bytes.fromhex(s) if fmt == "HEX" else None)
        self.db.create_function("OCTET_LENGTH", 1, lambda s: None if s is None else len(s))
        self.db.create_function("PARSE_JSON", 1, lambda s: json.dumps(json.loads(s), sort_keys=True))
        self.db.create_function("IS_OBJECT", 1, lambda s: s is not None and isinstance(json.loads(s), dict))
        self.db.execute("CREATE TABLE RAW (NODE_KEY TEXT, OSCAL_UUID TEXT, METADATA_JSON TEXT)")
        self.key = "0123456789abcdef0123456789abcdef"
        self.u = str(uuid.uuid5(uuid.NAMESPACE_URL, "test-ssp-node"))
        self.payload = json.dumps({"uuid": self.u, "props": [{"name": "test", "value": "1"}]})
        self.plan = [c for c in P["_pilot_column_plan"](live_description("DIM"), "DIM")
                     if c["source"] in {"NODE_KEY", "OSCAL_UUID", "METADATA_JSON"}]
        self.sql = []
        def query(session, sql):
            self.sql.append(sql)
            return [dict(r) for r in self.db.execute(sql).fetchall()]
        self.query_patch = patch.dict(P["_pilot_stage"].__globals__, {"_pilot_query": query})
        self.query_patch.start()

    def tearDown(self):
        self.query_patch.stop()
        self.db.close()

    def insert(self, key=None, uid=None):
        self.db.execute("INSERT INTO RAW VALUES (?, ?, ?)",
                        (self.key if key is None else key, self.u if uid is None else uid, self.payload))

    def test_projected_readback_roundtrip_and_unchanged_raw_payload(self):
        self.insert()
        before = tuple(self.db.execute("SELECT * FROM RAW").fetchone())
        P["_pilot_stage"](None, "RAW", "STAGE_DATA", self.plan)
        row = self.db.execute("SELECT * FROM STAGE_DATA").fetchone()
        self.assertEqual(self.key, row[0].hex())
        self.assertEqual(self.u, str(uuid.UUID(hex=row[1])))
        self.assertEqual(self.u, json.loads(row[2])["uuid"])
        self.assertEqual(before, tuple(self.db.execute("SELECT * FROM RAW").fetchone()))
        self.db.execute("CREATE TABLE TARGET AS SELECT * FROM STAGE_DATA")
        sql = P["_pilot_difference_sql"]("TARGET", "STAGE_DATA", P["SSP_PILOT_DIM_PK"], self.plan)
        report = dict(self.db.execute(sql).fetchone())
        self.assertEqual(1, report.pop("STAGED_ROWS"))
        self.assertEqual(1, report.pop("TARGET_ROWS_IN_KEY_SCOPE"))
        self.assertFalse(any(report.values()))
        self.db.execute("UPDATE TARGET SET OSCAL_UUID = ?", ("0" * 32,))
        self.assertEqual(1, dict(self.db.execute(sql).fetchone())["MISMATCHED_KEYS"])

    def test_case_collisions_stop_after_projection_before_any_merge(self):
        self.insert()
        self.insert(key=self.key.upper())
        with self.assertRaisesRegex(P["PilotError"], "NULL_OR_DUPLICATE_KEYS"):
            P["_pilot_stage"](None, "RAW", "STAGED", self.plan)
        self.assertFalse(any(s.startswith("MERGE") for s in self.sql))

    def test_invalid_source_identities_stop_before_stage_creation(self):
        for key, uid in (("a" * 31, self.u), ("g" * 32, self.u), (self.key, self.u + "x"),
                         (self.key, self.u.replace("-", "")), (self.key, "not-a-uuid")):
            with self.subTest(key=key, uid=uid):
                self.db.execute("DELETE FROM RAW")
                self.insert(key, uid)
                self.sql.clear()
                with self.assertRaisesRegex(P["PilotError"], "INVALID_STORAGE_IDENTITY"):
                    P["_pilot_stage"](None, "RAW", "STAGED", self.plan)
                self.assertFalse(any(s.startswith("CREATE") for s in self.sql))

    def test_null_identity_stops_even_when_physical_uuid_column_nullable(self):
        self.insert()
        self.db.execute("UPDATE RAW SET OSCAL_UUID=NULL")
        with self.assertRaisesRegex(P["PilotError"], "INVALID_STORAGE_IDENTITY_OSCAL_UUID"):
            P["_pilot_stage"](None, "RAW", "STAGED", self.plan)


if __name__ == "__main__":
    unittest.main()
