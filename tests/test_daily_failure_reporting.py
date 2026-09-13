"""Committed-state reporting and audit-aware readback, without Snowflake."""
import json
import sqlite3
import unittest
from unittest.mock import patch

from tests.test_multi_model_loader import P, G, Error, storage
from tests.test_multi_model_orchestrator import RELEASE, context, namespace


class DailyFailureReporting(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.contexts = [context("one"), context("two")]
        for current in self.contexts:
            current["routing_report"]["LABEL"] = current["source_key"]
        self.sources = {key: {"source_df": key} for key in ("one", "two")}
        self.commits = []

        def mapping(source_df, *args, context, **kwargs):
            context["graph_report"] = {"GROUP": source_df}
            return source_df, source_df, None, {
                "validation_passed": True, "writes_executed": False,
                "storage_verified": True, "source_records": 1,
            }

        self.ns["run_oscal_mapping"] = mapping
        self.set_loader(lambda **kwargs: None)

    def set_loader(self, operation):
        operation._oscal_loader_release = RELEASE
        self.ns["validate_and_load_oscal"] = operation

    def failure(self, mode="COMMIT"):
        with self.assertRaises(self.ns["PipelineError"]) as caught:
            self.ns["run_oscal_pipeline"](self.sources, self.contexts, mode)
        return caught.exception.report

    def test_first_group_committed_readback_failure_is_reported_as_a_write(self):
        class CommittedFailure(RuntimeError):
            details = {"status": "POST_COMMIT_READBACK_FAILED_DO_NOT_RETRY",
                       "writes_executed": True, "persisted": True}

        def commit(**kwargs):
            self.commits.append(kwargs["config"]["SOURCE_TABLE_NAME"])
            raise CommittedFailure("private SQL error")

        self.set_loader(commit)
        report = self.failure()
        self.assertEqual(["SOURCE_ONE"], self.commits)
        self.assertTrue(report["writes_executed"])
        self.assertEqual({"source": "one", "model": "SSP"}, report["active_group"])
        self.assertEqual("one", report["active_routing"]["LABEL"])
        self.assertEqual({"GROUP": "one"}, report["active_graph_report"])
        self.assertEqual("REVIEW_REQUIRED_NO_AUTOMATIC_RETRY", report["failed_commit_outcome"])
        self.assertNotIn("private SQL error", str(report))

    def test_first_preview_failure_has_its_own_routing_report(self):
        def fail(*args, context, **kwargs):
            context["graph_report"] = {"GROUP": context["source_key"]}
            raise RuntimeError("private source value")

        self.ns["run_oscal_mapping"] = fail
        report = self.failure()
        self.assertEqual("one", report["active_routing"]["LABEL"])
        self.assertEqual({"GROUP": "one"}, report["active_graph_report"])
        self.assertFalse(report["commit_attempted"])
        self.assertFalse(report["writes_executed"])
        self.assertNotIn("private source value", str(report))

    def test_cancelled_graph_has_a_report_and_never_attempts_a_commit(self):
        def cancel(*args, **kwargs):
            raise KeyboardInterrupt()

        self.ns["run_oscal_mapping"] = cancel
        report = self.failure()
        self.assertEqual("KeyboardInterrupt", report["error_type"])
        self.assertEqual("PIPELINE_FAILED_NO_TARGET_DML", report["status"])
        self.assertFalse(report["commit_attempted"])

    def test_cancelled_commit_stops_remaining_groups_without_claiming_rollback(self):
        def cancel(**kwargs):
            self.commits.append(kwargs["config"]["SOURCE_TABLE_NAME"])
            raise KeyboardInterrupt()

        self.set_loader(cancel)
        report = self.failure()
        self.assertEqual(["SOURCE_ONE"], self.commits)
        self.assertEqual("KeyboardInterrupt", report["error_type"])
        self.assertEqual("PIPELINE_COMMIT_FAILED_REVIEW_REQUIRED", report["status"])
        self.assertEqual("REVIEW_REQUIRED_NO_AUTOMATIC_RETRY", report["failed_commit_outcome"])


class SavedAuditReadback(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.create_function("TO_VARCHAR", 1, lambda value: value)
        self.db.create_function("TRY_PARSE_JSON", 1, lambda value: (
            None if value is None else json.dumps(json.loads(value), sort_keys=True)))
        self.contract = dict(storage(), TARGET_DIM="TD", TARGET_FACT="TF",
                             DIM_PK_COLUMN="PK", FACT_PK_COLUMN="PK")
        self.names = dict(D="SD", F="SF", DB="BD", FB="BF", IDS="IDS")
        plan = [{"name": name} for name in ("PK", "METADATA_JSON", "DW_PIPELINE_RUN_ID")]
        self.load_context = dict(contract=self.contract, names=self.names, plans=[plan, plan], records=1)
        for table in ("TD", "TF", "SD", "SF", "BD", "BF"):
            self.db.execute("CREATE TABLE " + table + " (PK TEXT, METADATA_JSON TEXT, DW_PIPELINE_RUN_ID TEXT)")
            rows = [("same", '{"a":1,"b":2}', "old"), ("changed", '{"a":1}', "old")]
            if table[0] in ("T", "S"):
                rows[1] = ("changed", '{"a":2}', "new")
                rows.append(("added", '{"a":3}', "new"))
            if table[0] == "S":
                rows[0] = ("same", '{"b":2,"a":1}', "new")
            self.db.executemany("INSERT INTO " + table + " VALUES (?,?,?)", rows)

    def verify(self):
        def query(session, statement):
            cursor = self.db.execute(statement)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        with patch.dict(G, {
            "_load_runtime_contract": lambda value: value,
            "_load_query": query,
            "_load_scope_check": lambda *args: {},
            "_load_integrity": lambda *args, **kwargs: {},
            "_load_unchanged_scope": lambda *args: None,
        }):
            return P["_load_verify_context"](None, self.load_context)

    def test_saved_old_audit_and_new_audit_are_both_verified(self):
        report = self.verify()
        self.assertEqual({"INSERTS": 0, "UPDATES": 0, "UNCHANGED": 3}, report["DIM"])
        self.assertEqual(report["DIM"], report["FACT"])

    def test_audit_rewrite_on_unchanged_row_blocks_readback(self):
        self.db.execute("UPDATE TF SET DW_PIPELINE_RUN_ID='new' WHERE PK='same'")
        with self.assertRaisesRegex(Error, "SAVED_PROJECTION_OR_UNCHANGED_AUDIT_DIFFER"):
            self.verify()

    def test_wrong_audit_on_updated_or_inserted_row_blocks_readback(self):
        for key in ("changed", "added"):
            with self.subTest(key=key):
                self.db.execute("UPDATE TD SET DW_PIPELINE_RUN_ID='old' WHERE PK=?", (key,))
                with self.assertRaisesRegex(Error, "SAVED_PROJECTION_OR_UNCHANGED_AUDIT_DIFFER"):
                    self.verify()
                self.db.execute("UPDATE TD SET DW_PIPELINE_RUN_ID='new' WHERE PK=?", (key,))

    def test_unchanged_rows_preserve_original_json_representation(self):
        self.db.execute("UPDATE TD SET METADATA_JSON='{\"b\":2,\"a\":1}' WHERE PK='same'")
        # An unchanged row must retain its actual stored representation as well as its audit.
        with self.assertRaisesRegex(Error, "SAVED_PROJECTION_OR_UNCHANGED_AUDIT_DIFFER"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
