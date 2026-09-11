"""Full-table reload fault tests; mocks do not prove live Snowflake behavior."""
from collections import Counter
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import runpy
import traceback
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "notebooks/persistence/RELOAD_ALL_SSP_DEV.py"
P = runpy.run_path(str(PATH))
Error = P["PilotError"]
PRODUCTION_COUNTS = P["SSP_PILOT_ACCEPTED_COUNTS"]
DIM, FACT = P["SSP_PILOT_DIM"], P["SSP_PILOT_FACT"]
SMALL_COUNTS = (7, 5)
MERGES = tuple(P["_pilot_merge_sql"](table, stage, pk, [{"name": pk}])
               for table, stage, pk in (
                   (DIM, "NEW_DIM", P["SSP_PILOT_DIM_PK"]),
                   (FACT, "NEW_FACT", P["SSP_PILOT_FACT_PK"])))
PRIVATE = "private_record_payload_and_server_message"


class Row(dict):
    def as_dict(self):
        return dict(self)


class ReloadSession:
    def __init__(self, failures=None, transaction=None, insert_counts=None, ineffective=None):
        self.failures = failures or {}
        self.transaction, self.ineffective = transaction, ineffective
        self.insert_counts = list(insert_counts) if insert_counts is not None else None
        self.calls, self.events = Counter(), []
        self.persisted = {
            "DIM": {"legacy": {"value": "old"}, "former-protected": {"value": "old-pilot"},
                    "other-source": {"value": "also-authorized-for-full-clear"}},
            "FACT": {"legacy-edge": {"value": "old"}, "other-edge": {"value": "old-other"}},
        }
        self.original = copy.deepcopy(self.persisted)
        self.pending = copy.deepcopy(self.persisted)
        self.staged = {kind: {f"new-{kind}-{i}": {"value": i} for i in range(count)}
                       for kind, count in zip(("DIM", "FACT"), SMALL_COUNTS)}

    def sql(self, statement):
        if statement == "SELECT CURRENT_TRANSACTION() AS TX":
            kind = "TX"
        elif statement in MERGES:
            kind = "MERGE_DIM" if statement == MERGES[0] else "MERGE_FACT"
        elif statement == "TRUNCATE TABLE " + FACT:
            kind = "TRUNCATE_FACT"
        elif statement == "TRUNCATE TABLE " + DIM:
            kind = "TRUNCATE_DIM"
        elif statement == "SELECT COUNT(*) AS N FROM " + FACT:
            kind = "COUNT_FACT"
        elif statement == "SELECT COUNT(*) AS N FROM " + DIM:
            kind = "COUNT_DIM"
        elif statement in ("BEGIN TRANSACTION", "COMMIT", "ROLLBACK"):
            kind = statement.split()[0]
        else:
            raise AssertionError("Unexpected SQL or DDL in reload transaction")
        self.calls[kind] += 1
        occurrence = self.calls[kind]
        failure = self.failures.get((kind, occurrence, "sql"))
        if failure:
            raise failure(PRIVATE)
        parent = self

        class Plan:
            def collect(self):
                parent.events.append(kind)
                failure = parent.failures.get((kind, occurrence, "collect"))
                if failure:
                    raise failure(PRIVATE)
                if kind == "TX":
                    return [Row(TX=parent.transaction)]
                if kind == "BEGIN":
                    parent.transaction = "active"
                    parent.pending = copy.deepcopy(parent.persisted)
                elif kind.startswith("TRUNCATE_"):
                    table = kind.split("_")[1]
                    if parent.ineffective != table:
                        parent.pending[table].clear()
                    return [Row(status="Statement executed successfully.")]
                elif kind.startswith("COUNT_"):
                    return [Row(N=len(parent.pending[kind.split("_")[1]]))]
                elif kind.startswith("MERGE_"):
                    table = kind.split("_")[1]
                    actual = sum(key not in parent.pending[table] for key in parent.staged[table])
                    for key, value in parent.staged[table].items():
                        parent.pending[table].setdefault(key, copy.deepcopy(value))
                    count = parent.insert_counts.pop(0) if parent.insert_counts is not None else actual
                    return [Row({"number of rows inserted": count})]
                elif kind == "ROLLBACK":
                    parent.pending = copy.deepcopy(parent.persisted)
                    parent.transaction = None
                elif kind == "COMMIT":
                    parent.persisted = copy.deepcopy(parent.pending)
                    parent.transaction = None
                return [Row(status="OK")]
        return Plan()


class FullReloadTransactions(unittest.TestCase):
    def setUp(self):
        context = patch.dict(P["_reload_transaction"].__globals__,
                             SSP_PILOT_ACCEPTED_COUNTS=SMALL_COUNTS)
        context.start()
        self.addCleanup(context.stop)

    def call(self, session, before=lambda: None, verify=lambda _: None):
        return P["_reload_transaction"](session, MERGES, before, verify, SMALL_COUNTS)

    def clean_error(self, error, code):
        self.assertEqual(code, error.code)
        self.assertNotIn(PRIVATE, "".join(traceback.format_exception(type(error), error, error.__traceback__)))

    def restored(self, session):
        self.assertEqual(session.original, session.persisted)
        self.assertEqual(session.original, session.pending)
        self.assertEqual(0, session.calls["COMMIT"])

    def test_status_only_truncate_fact_first_then_all_rows_replaced_and_committed(self):
        self.assertEqual((70102, 67289), PRODUCTION_COUNTS)
        session, passes = ReloadSession(), []

        def before():
            self.assertEqual("active", session.transaction)
            self.assertEqual(session.original, session.pending)
            session.events.append("BASELINE")

        def verify(number):
            passes.append(number)
            self.assertEqual(session.staged, session.pending)
            session.events.append("VERIFY" + str(number))

        report = self.call(session, before, verify)
        self.assertEqual([1, 2], passes)
        self.assertEqual(["TX", "BEGIN", "BASELINE", "TRUNCATE_FACT", "COUNT_FACT",
                          "TRUNCATE_DIM", "COUNT_DIM", "MERGE_DIM", "MERGE_FACT",
                          "VERIFY1", "MERGE_DIM", "MERGE_FACT", "VERIFY2", "COMMIT"], session.events)
        self.assertEqual(session.staged, session.persisted)
        self.assertNotIn("former-protected", session.persisted["DIM"])
        self.assertEqual([{"PASS": 1, "DIM": 7, "FACT": 5}, {"PASS": 2, "DIM": 0, "FACT": 0}],
                         report["INSERT_COUNTS"])
        self.assertEqual(0, session.calls["ROLLBACK"])

    def test_failure_or_cancellation_after_first_truncate_restores_both_tables(self):
        for stage in ("sql", "collect"):
            for error_type in (RuntimeError, KeyboardInterrupt, SystemExit):
                with self.subTest(stage=stage, error_type=error_type):
                    session = ReloadSession({("TRUNCATE_DIM", 1, stage): error_type})
                    with self.assertRaises(Error) as caught:
                        self.call(session)
                    self.clean_error(caught.exception, "TRANSACTION_ROLLED_BACK")
                    self.assertEqual(1, session.calls["TRUNCATE_FACT"])
                    self.assertEqual(1, session.calls["ROLLBACK"])
                    self.assertEqual(0, session.calls["MERGE_DIM"])
                    self.restored(session)

    def test_truncate_permission_failure_stops_before_second_target(self):
        session = ReloadSession({("TRUNCATE_FACT", 1, "collect"): PermissionError})
        with self.assertRaises(Error) as caught:
            self.call(session)
        self.clean_error(caught.exception, "TRANSACTION_ROLLED_BACK")
        self.assertEqual(0, session.calls["TRUNCATE_DIM"])
        self.assertEqual(0, session.calls["MERGE_DIM"])
        self.restored(session)

    def test_truncate_status_without_empty_table_cannot_continue(self):
        for table in ("DIM", "FACT"):
            with self.subTest(table=table):
                session = ReloadSession(ineffective=table)
                with self.assertRaises(Error) as caught:
                    self.call(session)
                self.assertEqual("TRUNCATE_DID_NOT_EMPTY_" + table, caught.exception.details["CAUSE"])
                self.assertEqual(0, session.calls["MERGE_DIM"])
                self.restored(session)

    def test_baseline_failure_inside_begin_prevents_truncation(self):
        session = ReloadSession()

        def before():
            self.assertEqual("active", session.transaction)
            raise RuntimeError(PRIVATE)

        with self.assertRaises(Error) as caught:
            self.call(session, before=before)
        self.clean_error(caught.exception, "TRANSACTION_ROLLED_BACK")
        self.assertEqual(["TX", "BEGIN", "ROLLBACK"], session.events)
        self.restored(session)

    def test_either_precommit_verification_failure_or_cancellation_rolls_back(self):
        for failure_pass in (1, 2):
            for error_type in (RuntimeError, KeyboardInterrupt):
                with self.subTest(failure_pass=failure_pass, error_type=error_type):
                    session = ReloadSession()

                    def verify(number):
                        if number == failure_pass:
                            raise error_type(PRIVATE)

                    with self.assertRaises(Error) as caught:
                        self.call(session, verify=verify)
                    self.clean_error(caught.exception, "TRANSACTION_ROLLED_BACK")
                    self.restored(session)

    def test_first_and_second_pass_insert_count_mismatches_roll_back(self):
        for counts in ((6, 5, 0, 0), (7, 4, 0, 0), (7, 5, 1, 0), (7, 5, 0, 1)):
            with self.subTest(counts=counts):
                session = ReloadSession(insert_counts=counts)
                with self.assertRaises(Error) as caught:
                    self.call(session)
                self.assertEqual("UNEXPECTED_MERGE_INSERT_COUNT", caught.exception.details["CAUSE"])
                self.restored(session)

    def test_existing_transaction_is_untouched(self):
        session = ReloadSession(transaction="caller")
        with self.assertRaises(Error) as caught:
            self.call(session)
        self.assertEqual("EXISTING_TRANSACTION_STOPPED_PILOT", caught.exception.code)
        self.assertEqual({"TX": 1}, dict(session.calls))
        self.assertEqual("caller", session.transaction)
        self.assertEqual(session.original, session.persisted)

    def test_uncertain_commit_or_rollback_is_not_retried(self):
        for kind, code in (("COMMIT", "COMMIT_OUTCOME_UNKNOWN"), ("ROLLBACK", "ROLLBACK_OUTCOME_UNKNOWN")):
            for stage in ("sql", "collect"):
                with self.subTest(kind=kind, stage=stage):
                    failures = {(kind, 1, stage): RuntimeError}
                    if kind == "ROLLBACK":
                        failures[("MERGE_DIM", 1, "collect")] = RuntimeError
                    session = ReloadSession(failures)
                    with self.assertRaises(Error) as caught:
                        self.call(session)
                    self.clean_error(caught.exception, code)
                    self.assertEqual(1, session.calls[kind])
                    if kind == "COMMIT":
                        self.assertEqual(0, session.calls["ROLLBACK"])


class FullReloadRunner(unittest.TestCase):
    def run_case(self, mode="COMMIT", postcommit_failure=False):
        fn = P["run_ssp_full_dev_reload"]
        sqls, transactions, checks, output = [], [], [], io.StringIO()

        def saved(*args):
            checks.append("SAVED")
            if postcommit_failure and len(checks) == 3:
                raise Error("POST_COMMIT_SAVED_VALUES_FAILED")
            return {"MATCH": True}

        def transaction(session, merges, before, verify, counts):
            transactions.append("BEGIN")
            self.assertEqual(SMALL_COUNTS, counts)
            before()
            verify(1)
            verify(2)
            transactions.append("COMMIT")
            return {"STATUS": "COMMITTED"}

        mocks = {
            "SSP_PILOT_ACCEPTED_COUNTS": SMALL_COUNTS,
            "_pilot_contract": lambda *a: None, "_pilot_no_transaction": lambda *a: None,
            "_pilot_query": lambda session, sql: sqls.append(sql) or [],
            "_pilot_column_plan": lambda *a: [], "_pilot_selection_schema": lambda *a: None,
            "_reload_freeze": lambda *a: 2, "_pilot_stage": lambda *a: None,
            "_batch_integrity": lambda *a: {"NODES": 7, "EDGES": 5, "SELECTED_RECORDS": 2},
            "_pilot_count": lambda *a: 3, "_pilot_baseline_equal": lambda *a: None,
            "_pilot_merge_sql": lambda target, *a: MERGES[0] if target == DIM else MERGES[1],
            "_reload_transaction": transaction, "_pilot_verify": saved,
        }
        with patch.dict(fn.__globals__, mocks), redirect_stdout(output):
            if postcommit_failure:
                with self.assertRaises(Error):
                    fn(None, {}, {}, None, None, mode)
                report = json.loads(output.getvalue())
            else:
                report = fn(None, {}, {}, None, None, mode)
        return report, sqls, transactions, checks

    def test_preview_never_enters_target_dml(self):
        report, sqls, transactions, _ = self.run_case("PREVIEW")
        self.assertEqual("FULL_RELOAD_PREVIEW_PASSED_NO_TARGET_DML", report["STATUS"])
        self.assertFalse(report["TARGET_DML_ATTEMPTED"])
        self.assertFalse(report["PERSISTED"])
        self.assertEqual([], transactions)
        self.assertFalse(any(sql.startswith(("TRUNCATE", "MERGE", "DELETE", "INSERT", "UPDATE")) for sql in sqls))

    def test_commit_runner_uses_one_transaction_and_postcommit_readback(self):
        report, _, transactions, checks = self.run_case()
        self.assertEqual(["BEGIN", "COMMIT"], transactions)
        self.assertEqual(3, len(checks))
        self.assertEqual("FULL_SSP_RELOAD_COMMITTED_AND_VERIFIED", report["STATUS"])
        self.assertTrue(report["TARGET_DML_ATTEMPTED"])
        self.assertTrue(report["PERSISTED"])

    def test_postcommit_readback_failure_reports_persisted_not_rolled_back(self):
        report, _, transactions, _ = self.run_case(postcommit_failure=True)
        self.assertEqual(["BEGIN", "COMMIT"], transactions)
        self.assertEqual("POST_COMMIT_SAVED_VALUES_FAILED", report["STATUS"])
        self.assertEqual("POST_COMMIT_READBACK", report["PHASE"])
        self.assertIs(True, report["PERSISTED"])
        self.assertNotIn("FAILURE_ROLLBACK_RESTORED_BASELINE", report)


if __name__ == "__main__":
    unittest.main()
