"""Focused policy tests; mocked runner checks, not live Snowflake proof."""
import ast
from contextlib import redirect_stdout
import inspect
import io
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


PATH = (Path(__file__).resolve().parents[1] /
        "notebooks/persistence/RECONCILE_SSP_ONE_RECORD_WRITE.py")
P = runpy.run_path(str(PATH))
Error = P["PilotError"]
POLICY = "TRANSACTION_ONLY_DEV"


class NoDurableBackupRoute(unittest.TestCase):
    def run_case(self, mode="COMMIT", fail_rehearsal=False, drift_after_rehearsal=False):
        fn = P["run_ssp_one_record_reconciliation"]
        events, statements, output = [], [], io.StringIO()
        state = {"inside": False, "rehearsed": False, "baseline_calls": 0}

        def query(session, sql):
            statements.append(sql)
            self.assertFalse(state["inside"], "Runner DDL cannot occur in a transaction")
            return []

        def baseline(session, names, queries):
            state["baseline_calls"] += 1
            events.append(("BASELINE", state["inside"]))
            self.assertEqual(("SELECT LIVE_DIM", "SELECT LIVE_FACT"), queries)
            if drift_after_rehearsal and state["rehearsed"] and not state["inside"]:
                raise Error("TARGET_BASELINE_CHANGED")

        def transaction(session, deletes, merges, before_replace, verify,
                        expected_inserts, commit=False):
            self.assertEqual((19, 18), expected_inserts)
            self.assertEqual(("DELETE FACT", "DELETE DIM"), tuple(deletes))
            events.append(("BEGIN", commit))
            state["inside"] = True
            before_replace()
            self.assertEqual(("BASELINE", True), events[-1])
            if fail_rehearsal and not commit:
                state["inside"] = False
                events.append(("ROLLBACK_FAILURE_PATH", False))
                raise Error("TRANSACTION_ROLLED_BACK")
            events.append(("DELETE_AND_INSERT", commit))
            checks = [verify(1), verify(2)]
            state["inside"] = False
            if not commit:
                state["rehearsed"] = True
            events.append(("COMMIT" if commit else "ROLLBACK", commit))
            return {"STATUS": "COMMITTED" if commit else "ROLLED_BACK",
                    "VERIFIED_PASSES": 2, "CHECKS": checks}

        def saved_values(*args):
            events.append(("SAVED_VALUES", state["inside"]))
            return {"MATCHED": True}

        def integrity(session, queries, dependency_type):
            self.assertEqual("CONTAINS", dependency_type)
            events.append(("KEY_INTEGRITY", state["inside"]))
            return {"PASSED": True}

        mocks = {
            "_pilot_contract": lambda *a: None,
            "_pilot_no_transaction": lambda *a: None,
            "_pilot_query": query,
            "_pilot_column_plan": lambda *a: [],
            "_pilot_selection_schema": lambda *a: None,
            "_pilot_freeze_graph": lambda *a: {"NODES": 19, "EDGES": 18, "SOURCE_RECORDS": 1},
            "_pilot_stage": lambda *a: None,
            "_pilot_scope_queries": lambda *a: ("SELECT INITIAL_DIM", "SELECT INITIAL_FACT"),
            "_reconcile_live_scope_queries": lambda *a: ("SELECT LIVE_DIM", "SELECT LIVE_FACT"),
            "_reconcile_validate_baseline": lambda *a: {"BASELINE_DIM": 21, "BASELINE_FACT": 20},
            "_reconcile_create_backups": lambda *a: self.fail("Permanent backup must not be called"),
            "_pilot_baseline_equal": baseline,
            "_reconcile_delete_sql": lambda *a: ("DELETE FACT", "DELETE DIM"),
            "_pilot_merge_sql": lambda *a: "MERGE",
            "_reconcile_transaction": transaction,
            "_pilot_verify": saved_values,
            "_reconcile_integrity": integrity,
        }
        with patch.dict(fn.__globals__, mocks), redirect_stdout(output):
            if fail_rehearsal or drift_after_rehearsal:
                with self.assertRaises(Error):
                    fn(None, {}, {}, None, None, mode, backup_policy=POLICY)
                report = json.loads(output.getvalue())
            else:
                report = fn(None, {}, {}, None, None, mode, backup_policy=POLICY)
        return report, events, statements, state

    def test_approved_route_skips_permanent_backup_but_retains_all_runner_gates(self):
        report, events, statements, state = self.run_case()
        self.assertEqual("ONE_RECORD_RECONCILED_AND_VERIFIED", report["STATUS"])
        self.assertTrue(report["PERSISTED"])
        self.assertEqual(POLICY, report["BACKUP_POLICY"])
        self.assertIs(False, report["BACKUPS_VERIFIED"])
        self.assertEqual({}, report["BACKUP_TABLES"])
        self.assertEqual("NO_DURABLE_COPY_AFTER_COMMIT", report["RECOVERY_LIMITATION"])
        self.assertTrue(report["ROLLBACK_RESTORED_BASELINE"])
        self.assertEqual([("BEGIN", False), ("BEGIN", True)],
                         [event for event in events if event[0] == "BEGIN"])
        self.assertEqual(3, state["baseline_calls"])
        self.assertEqual([("BASELINE", True), ("BASELINE", False), ("BASELINE", True)],
                         [event for event in events if event[0] == "BASELINE"])
        self.assertEqual(5, sum(event[0] == "SAVED_VALUES" for event in events))
        self.assertEqual(5, sum(event[0] == "KEY_INTEGRITY" for event in events))
        self.assertEqual(("KEY_INTEGRITY", False), events[-1])
        ddl = [sql.upper() for sql in statements if sql.lstrip().upper().startswith("CREATE")]
        self.assertEqual(2, len(ddl))
        self.assertTrue(all(sql.startswith("CREATE TEMPORARY TABLE ") for sql in ddl))
        self.assertTrue(any("_DB AS " in sql for sql in ddl))
        self.assertTrue(any("_FB AS " in sql for sql in ddl))
        self.assertFalse(any("BACKUP_SSP_RECONCILE" in sql for sql in statements))

    def test_rehearsal_failure_prevents_commit(self):
        report, events, _, _ = self.run_case(fail_rehearsal=True)
        self.assertEqual("TRANSACTION_ROLLED_BACK", report["STATUS"])
        self.assertFalse(report["PERSISTED"])
        self.assertEqual([("BEGIN", False)], [event for event in events if event[0] == "BEGIN"])
        self.assertFalse(any(event[0] == "COMMIT" for event in events))

    def test_baseline_mismatch_after_rehearsal_prevents_commit(self):
        report, events, _, _ = self.run_case(drift_after_rehearsal=True)
        self.assertEqual("TARGET_BASELINE_CHANGED", report["STATUS"])
        self.assertFalse(report["PERSISTED"])
        self.assertEqual([("BEGIN", False)], [event for event in events if event[0] == "BEGIN"])
        self.assertIn(("ROLLBACK", False), events)
        self.assertFalse(any(event[0] == "COMMIT" for event in events))

    def test_preview_has_no_target_dml_or_transactions(self):
        report, events, statements, _ = self.run_case(mode="PREVIEW")
        self.assertEqual("RECONCILIATION_PREVIEW_PASSED_NO_TARGET_DML", report["STATUS"])
        self.assertFalse(report["TARGET_DML_ATTEMPTED"])
        self.assertFalse(report["PERSISTED"])
        self.assertFalse(any(event[0] == "BEGIN" for event in events))
        self.assertFalse(any(sql.lstrip().upper().startswith(("DELETE", "MERGE", "INSERT", "UPDATE"))
                             for sql in statements))

    def test_invalid_policy_stops_before_any_query(self):
        fn = P["run_ssp_one_record_reconciliation"]
        statements = []
        with patch.dict(fn.__globals__, {
            "_pilot_contract": lambda *a: None,
            "_pilot_query": lambda session, sql: statements.append(sql),
        }):
            with self.assertRaises(Error):
                fn(None, {}, {}, None, None, "COMMIT", backup_policy="SKIP_EVERY_SAFETY_CHECK")
        self.assertEqual([], statements)

    def test_existing_callers_still_default_to_durable_backups(self):
        signature = inspect.signature(P["run_ssp_one_record_reconciliation"])
        self.assertEqual("DURABLE", signature.parameters["backup_policy"].default)

    def test_main_passes_explicit_approved_transaction_only_policy(self):
        self.assertEqual(POLICY, P["SSP_RECONCILE_BACKUP_POLICY"])
        tree = ast.parse(PATH.read_text(encoding="utf-8"))
        main = next(node for node in tree.body
                    if isinstance(node, ast.If) and "__name__" in ast.unparse(node.test))
        call = next(node for node in ast.walk(main)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "run_ssp_one_record_reconciliation")
        policy = next(keyword.value for keyword in call.keywords if keyword.arg == "backup_policy")
        self.assertIsInstance(policy, ast.Name)
        self.assertEqual("SSP_RECONCILE_BACKUP_POLICY", policy.id)


if __name__ == "__main__":
    unittest.main()
