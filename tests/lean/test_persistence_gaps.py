"""Public persistence boundaries and temporary-resource lifetime; no live Snowflake."""
import copy
import unittest
from unittest.mock import patch

import test_loader as loader
from test_runner import runner_namespace, context as route_context, SourceFrame


class PersistenceGaps(unittest.TestCase):
    def setUp(self):
        self.session = loader.Session()
        self.addCleanup(self.session.db.close)
        self.scope = patch.dict(loader.G, {"session": self.session})
        self.scope.start()
        self.addCleanup(self.scope.stop)

    def load(self, commit=False, nodes=None, edges=None, config=None):
        original_nodes, original_edges = loader.graph()
        return loader.P["validate_and_load_oscal"](
            loader.Frame(self.session, original_nodes if nodes is None else nodes, tuple(original_nodes[0])),
            loader.Frame(self.session, original_edges if edges is None else edges, tuple(original_edges[0])),
            dict(loader.config() if config is None else config, EXECUTE_WRITES=commit))

    def temporary_tables(self):
        return self.session.query("SELECT name FROM sqlite_temp_master WHERE type='table'")

    def test_populated_audit_values_are_required_before_target_dml(self):
        changes = [("DW_PIPELINE_RUN_ID", None), ("DW_PIPELINE_RUN_ID", ""),
                   ("DW_PIPELINE_RUN_ID", "  "), ("DW_PIPELINE_RUN_ID", 42),
                   ("DW_LOAD_TIMESTAMP", None), ("DW_LOAD_TIMESTAMP_TZ", None),
                   ("DW_LOAD_TIMESTAMP", ""), ("DW_LOAD_TIMESTAMP_TZ", "  ")]
        for name, value in changes:
            with self.subTest(column=name, value=value):
                nodes, edges = loader.graph()
                nodes[1][name] = value
                with self.assertRaisesRegex(loader.Error, "INVALID_AUDIT_VALUE"):
                    self.load(True, nodes, edges)
        self.assertFalse(any(sql.startswith("MERGE") for sql in self.session.events))

    def test_successful_repeated_previews_release_their_temporary_tables(self):
        for _ in range(3):
            self.assertEqual("PREVIEW_PASSED_NO_TARGET_DML", self.load()["status"])
            self.assertEqual([], self.temporary_tables())
        self.assertFalse(any(sql.startswith("MERGE") for sql in self.session.events))

    def test_commit_releases_staging_only_after_postcommit_readback(self):
        self.assertEqual("COMMITTED_AND_VERIFIED", self.load(True)["status"])
        self.assertEqual([], self.temporary_tables())
        commit = self.session.events.index("COMMIT")
        drops = [index for index, sql in enumerate(self.session.events) if sql.startswith("DROP")]
        self.assertTrue(drops)
        self.assertTrue(all(index > commit for index in drops))
        self.assertTrue(any(sql.startswith("SELECT") for sql in self.session.events[commit + 1:drops[0]]))

    def test_verified_rollback_releases_staging_after_baseline_readback(self):
        self.session.fail = ("FACT_MERGE", 1)
        with self.assertRaisesRegex(loader.Error, "TRANSACTION_ROLLED_BACK") as caught:
            self.load(True)
        self.assertTrue(caught.exception.details["rollback_readback_verified"])
        self.assertEqual([], self.temporary_tables())
        rollback = self.session.events.index("ROLLBACK")
        first_drop = next(index for index, sql in enumerate(self.session.events) if sql.startswith("DROP"))
        self.assertTrue(any(sql.startswith("SELECT") for sql in self.session.events[rollback + 1:first_drop]))

    def test_unknown_commit_keeps_staging_and_never_issues_cleanup_ddl(self):
        self.session.fail = ("COMMIT", 1)
        with self.assertRaisesRegex(loader.Error, "COMMIT_OUTCOME_UNKNOWN_DO_NOT_RETRY") as caught:
            self.load(True)
        self.assertEqual("UNKNOWN", caught.exception.details["persisted"])
        self.assertEqual(6, len(self.temporary_tables()))
        self.assertFalse(any(sql.startswith("DROP") for sql in self.session.events))

    def test_postcommit_readback_failure_retains_inspection_tables(self):
        verify = loader.G["_load_verify"]
        calls = []
        def fail_second(context):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError("private")
            return verify(context)
        with patch.dict(loader.G, {"_load_verify": fail_second}):
            with self.assertRaisesRegex(loader.Error, "POST_COMMIT_READBACK_FAILED") as caught:
                self.load(True)
        self.assertTrue(caught.exception.details["committed"])
        self.assertEqual(6, len(self.temporary_tables()))
        self.assertFalse(any(sql.startswith("DROP") for sql in self.session.events))

    def test_cleanup_failure_does_not_relabel_a_confirmed_commit(self):
        query = self.session.query
        def fail_drop(statement):
            if statement.startswith("DROP"):
                raise RuntimeError("private cleanup failure")
            return query(statement)
        self.session.query = fail_drop
        result = self.load(True)
        self.assertEqual("COMMITTED_AND_VERIFIED", result["status"])
        self.assertTrue(result["committed"])
        self.assertTrue(result["persisted"])
        self.assertEqual("FAILED", result["temporary_cleanup"])
        self.assertEqual(3, query("SELECT COUNT(*) AS N FROM DEV.DEMO.DIM")[0]["N"])

    def test_read_only_verification_releases_its_own_staging(self):
        self.load(True)
        nodes, edges = loader.graph()
        result = loader.P["verify_oscal_load"](loader.Frame(self.session, nodes),
                    loader.Frame(self.session, edges), loader.config())
        self.assertEqual("LOAD_VERIFIED", result["status"])
        self.assertEqual([], self.temporary_tables())

    def test_source_count_cannot_be_satisfied_by_boolean_true(self):
        config = dict(loader.config(), EXPECTED_SOURCE_RECORDS=True)
        with self.assertRaisesRegex(loader.Error, "SOURCE_RECORD_GRAPH_COVERAGE_MISMATCH"):
            self.load(True, config=config)
        self.assertFalse(any(sql.startswith("MERGE") for sql in self.session.events))

    def test_cleanup_does_not_commit_an_active_transaction_started_after_readback(self):
        verify = loader.G["_load_verify"]
        calls = []
        def start_later_transaction(context):
            result = verify(context)
            calls.append(1)
            if len(calls) == 2:
                self.session.query("BEGIN TRANSACTION")
            return result
        with patch.dict(loader.G, {"_load_verify": start_later_transaction}):
            result = self.load(True)
        self.assertEqual("COMMITTED_AND_VERIFIED", result["status"])
        self.assertEqual("FAILED", result["temporary_cleanup"])
        self.assertTrue(self.session.db.in_transaction)
        self.assertEqual(1, self.session.seen["COMMIT"])
        self.assertFalse(any(sql.startswith("DROP") for sql in self.session.events))

    def test_cleanup_failure_does_not_relabel_verified_rollback(self):
        query = self.session.query
        def fail_drop(statement):
            if statement.startswith("DROP"):
                raise RuntimeError("private")
            return query(statement)
        self.session.query = fail_drop
        self.session.fail = ("FACT_MERGE", 1)
        with self.assertRaisesRegex(loader.Error, "TRANSACTION_ROLLED_BACK") as caught:
            self.load(True)
        self.assertEqual("FAILED", caught.exception.details["temporary_cleanup"])
        self.assertTrue(caught.exception.details["rollback_readback_verified"])
        self.assertFalse(caught.exception.details["persisted"])

    def test_root_type_collision_rejects_in_preview_before_any_target_dml(self):
        # This physical profile identifies saved roots by ELEMENT_TYPE, since
        # NODE_PATH is not a target column. A non-root cannot share that type.
        nodes, edges = loader.graph()
        nodes[1]["ELEMENT_TYPE"] = nodes[0]["ELEMENT_TYPE"]
        with self.assertRaisesRegex(loader.Error, "AMBIGUOUS_STORED_ROOT_TYPE"):
            self.load(False, nodes, edges)
        self.assertFalse(any(sql.startswith("MERGE") for sql in self.session.events))

    def test_staging_failure_keeps_inspection_data_and_a_safe_rerun_uses_new_names(self):
        self.session.fail = ("CREATE", 3)
        with self.assertRaisesRegex(loader.Error, "LOAD_OPERATION_FAILED") as caught:
            self.load(True)
        self.assertEqual("PREPARATION", caught.exception.details["phase"])
        self.assertFalse(caught.exception.details["target_dml_attempted"])
        retained = self.temporary_tables()
        self.assertEqual(2, len(retained))
        self.assertEqual("PREVIEW_PASSED_NO_TARGET_DML", self.load()["status"])
        self.assertEqual(retained, self.temporary_tables())
        self.assertFalse(any(sql.startswith("MERGE") for sql in self.session.events))


class PartialRoutes(unittest.TestCase):
    def test_previous_loader_release_is_rejected_before_any_route_work(self):
        ns = runner_namespace()
        def old_loader(*_args, **_kwargs):
            self.fail("Old loader must not execute")
        old_loader._oscal_loader_release = "oscal-lean-daily-v3"
        ns["validate_and_load_oscal"] = old_loader
        with self.assertRaises(ns["PipelineError"]) as caught:
            ns["run_oscal_pipeline"]({"one": {}}, [route_context("one")], "COMMIT")
        self.assertFalse(caught.exception.report["commit_attempted"])
        self.assertEqual([], caught.exception.report["groups"])

    def test_actual_loader_failure_in_later_preview_prevents_all_route_commits(self):
        session = loader.Session()
        self.addCleanup(session.db.close)
        ns = runner_namespace()
        contexts = [route_context("one", "DEMO"), route_context("two", "DEMO")]
        for route in contexts:
            route["config"] = loader.config()
        sources = {name: {"source_df": SourceFrame(name, 1), "selection": {"SELECTED_ROWS": 1}}
                   for name in ("one", "two")}
        def build(frame, *_args, **_kwargs):
            nodes, edges = loader.graph()
            if frame.name == "two":
                nodes[1]["DW_LOAD_TIMESTAMP_TZ"] = None
            return loader.Frame(session, nodes), loader.Frame(session, edges)
        ns.update(build_oscal_graph=build, validate_and_load_oscal=loader.P["validate_and_load_oscal"])
        before = copy.deepcopy(contexts)
        with patch.dict(loader.G, {"session": session}):
            with self.assertRaises(ns["PipelineError"]) as caught:
                ns["run_oscal_pipeline"](sources, contexts, "COMMIT")
        self.assertFalse(caught.exception.report["commit_attempted"])
        self.assertEqual(("two", "DEMO"), caught.exception.report["failed_route"])
        self.assertFalse(any(sql.startswith("MERGE") for sql in session.events))
        self.assertEqual(before, contexts)


if __name__ == "__main__":
    unittest.main(verbosity=2)
