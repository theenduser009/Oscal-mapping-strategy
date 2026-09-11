"""Local transaction faults and generated SQL checks; not live Snowflake proof."""
from collections import Counter
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import re
import runpy
import sqlite3
import traceback
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "notebooks/cells/06_validation_and_guarded_loader.py"
P = runpy.run_path(str(PATH))
G = P["_load_transaction"].__globals__
Error = P["LoadError"]
PRIVATE = "private_payload_or_database_statement"


class Session:
    def __init__(self, merges, failures=None, transaction=None, counts=None):
        self.merges, self.failures, self.transaction = merges, failures or {}, transaction
        self.counts = iter(counts) if counts is not None else None
        self.calls, self.events = Counter(), []
        self.saved = {k: {"changed": (1, "old"), "same": (2, "old"), "outside": (9, "old")}
                      for k in ("DIM", "FACT")}
        self.stage = {k: {"changed": (3, "new"), "same": (2, "new"), "added": (4, "new")}
                      for k in ("DIM", "FACT")}
        self.original, self.pending = copy.deepcopy(self.saved), copy.deepcopy(self.saved)

    def sql(self, sql):
        if sql == "SELECT CURRENT_TRANSACTION() AS TX":
            kind = "TX"
        elif sql in self.merges:
            kind = "DIM" if sql == self.merges[0] else "FACT"
        elif sql in ("BEGIN TRANSACTION", "COMMIT", "ROLLBACK"):
            kind = sql.split()[0]
        else:
            raise AssertionError("Unexpected DDL/destructive/session SQL in transaction")
        self.calls[kind] += 1
        number = self.calls[kind]
        if (kind, number, "sql") in self.failures:
            raise self.failures[kind, number, "sql"](PRIVATE)
        owner = self

        class Plan:
            def collect(self):
                owner.events.append(kind)
                if (kind, number, "collect") in owner.failures:
                    raise owner.failures[kind, number, "collect"](PRIVATE)
                if kind == "TX":
                    return [{"TX": owner.transaction}]
                if kind == "BEGIN":
                    owner.transaction = "active"
                    owner.pending = copy.deepcopy(owner.saved)
                elif kind in ("DIM", "FACT"):
                    inserted = updated = 0
                    for key, row in owner.stage[kind].items():
                        old = owner.pending[kind].get(key)
                        if old is None:
                            inserted += 1
                            owner.pending[kind][key] = row
                        elif old[0] != row[0]:
                            updated += 1
                            owner.pending[kind][key] = row
                    if owner.counts is not None:
                        inserted, updated = next(owner.counts)
                    return [{"number of rows inserted": inserted, "number of rows updated": updated}]
                elif kind == "ROLLBACK":
                    owner.pending, owner.transaction = copy.deepcopy(owner.saved), None
                elif kind == "COMMIT":
                    owner.saved, owner.transaction = copy.deepcopy(owner.pending), None
                return [{"status": "OK"}]
        return Plan()


class DailyTransactions(unittest.TestCase):
    def setUp(self):
        self.merges = tuple(P["_build_merge_sql"](target, stage, pk, [pk, "VALUE"])
                            for target, stage, pk in (
                                (P["SSP_LOAD_DIM"], "STAGE_DIM", P["SSP_LOAD_DIM_PK"]),
                                (P["SSP_LOAD_FACT"], "STAGE_FACT", P["SSP_LOAD_FACT_PK"])))

    def run_tx(self, s, before=lambda: None, verify=lambda n: None):
        return P["_load_transaction"](s, self.merges, before, verify, ((1, 1), (1, 1)))

    def assert_clean(self, error, code):
        self.assertEqual(code, error.code)
        self.assertNotIn(PRIVATE, "".join(traceback.format_exception(
            type(error), error, error.__traceback__)))

    def test_new_changed_unchanged_and_repeat_are_atomic(self):
        s, passes = Session(self.merges), []
        def before():
            self.assertEqual("active", s.transaction)
            self.assertEqual(s.original, s.pending)
        def verify(n):
            passes.append(n)
            for k in ("DIM", "FACT"):
                self.assertEqual((3, "new"), s.pending[k]["changed"])
                self.assertEqual((4, "new"), s.pending[k]["added"])
                self.assertEqual(s.original[k]["same"], s.pending[k]["same"])
                self.assertEqual(s.original[k]["outside"], s.pending[k]["outside"])
        report = self.run_tx(s, before, verify)
        self.assertEqual([1, 2], passes)
        self.assertEqual(["TX", "BEGIN", "DIM", "FACT", "DIM", "FACT", "COMMIT"], s.events)
        self.assertEqual(s.saved, s.pending)
        self.assertEqual({"INSERTS": 0, "UPDATES": 0}, report["CHANGE_COUNTS"][1]["DIM"])
        self.assertEqual("COMMITTED", report["STATUS"])

    def test_failures_and_cancellation_at_each_merge_roll_back(self):
        for kind in ("DIM", "FACT"):
            for number in (1, 2):
                for when in ("sql", "collect"):
                    for fault in (RuntimeError, KeyboardInterrupt):
                        with self.subTest(kind=kind, number=number, when=when, fault=fault):
                            s = Session(self.merges, {(kind, number, when): fault})
                            with self.assertRaises(Error) as caught:
                                self.run_tx(s)
                            self.assert_clean(caught.exception, "TRANSACTION_ROLLED_BACK")
                            self.assertEqual(s.original, s.saved)
                            self.assertEqual(s.original, s.pending)
                            self.assertEqual(0, s.calls["COMMIT"])

    def test_before_write_and_each_verify_failure_stop_commit(self):
        def fail(*args):
            raise RuntimeError(PRIVATE)
        for failure in (0, 1, 2):
            s = Session(self.merges)
            def verify(n):
                if n == failure:
                    fail()
            with self.assertRaises(Error):
                self.run_tx(s, fail if failure == 0 else lambda: None, verify)
            self.assertEqual(s.original, s.pending)
            self.assertEqual(0, s.calls["COMMIT"])
            if failure == 0:
                self.assertEqual(0, s.calls["DIM"])

    def test_insert_and_update_count_mismatches_on_both_passes(self):
        for operation in range(4):
            for counter in (0, 1):
                counts = [[1, 1], [1, 1], [0, 0], [0, 0]]
                counts[operation][counter] += 1
                s = Session(self.merges, counts=counts)
                with self.assertRaises(Error):
                    self.run_tx(s)
                self.assertEqual(0, s.calls["COMMIT"])
                self.assertEqual(s.original, s.pending)

    def test_existing_transaction_is_not_committed_or_rolled_back(self):
        s = Session(self.merges, transaction="caller")
        with self.assertRaises(Error) as caught:
            self.run_tx(s)
        self.assert_clean(caught.exception, "EXISTING_TRANSACTION")
        self.assertEqual(["TX"], s.events)

    def test_unknown_begin_commit_or_rollback_is_not_retried(self):
        for kind, code in (("BEGIN", "BEGIN_OUTCOME_UNKNOWN"),
                           ("COMMIT", "COMMIT_OUTCOME_UNKNOWN"),
                           ("ROLLBACK", "ROLLBACK_OUTCOME_UNKNOWN")):
            for when in ("sql", "collect"):
                failures = {(kind, 1, when): RuntimeError}
                if kind == "ROLLBACK":
                    failures["FACT", 1, "collect"] = RuntimeError
                s = Session(self.merges, failures)
                with self.assertRaises(Error) as caught:
                    self.run_tx(s)
                self.assert_clean(caught.exception, code)
                self.assertEqual(1, s.calls[kind])
                if kind in ("BEGIN", "COMMIT"):
                    self.assertEqual(0, s.calls["ROLLBACK"])

    def test_wrong_target_or_destructive_statement_rejected(self):
        for sql in ("DELETE FROM " + P["SSP_LOAD_DIM"], self.merges[0] + "; DROP TABLE T"):
            s = Session(self.merges)
            with self.assertRaises(Error):
                P["_load_transaction"](s, (sql, self.merges[1]), lambda: None, lambda n: None,
                                       ((1, 1), (1, 1)))
            self.assertEqual([], s.events)
        with self.assertRaises(Error):
            P["_build_merge_sql"]("PRODUCTION.DIM", "STAGE", "PK", ["PK", "VALUE"])


class DailyBusinessSQL(unittest.TestCase):
    def setUp(self):
        self.pk = P["SSP_LOAD_DIM_PK"]
        self.columns = [self.pk, "METADATA_JSON", "ELEMENT_TYPE", "SOURCE_RECORD_ID",
                        "DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"]
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.create_function("TO_VARCHAR", 1, lambda v: v)
        self.db.create_function("TRY_PARSE_JSON", 1,
                               lambda v: None if v is None else json.dumps(json.loads(v), sort_keys=True))
        for table in ("TARGET", "STAGE"):
            self.db.execute("CREATE TABLE " + table + " (" +
                            ", ".join(c + " TEXT" for c in self.columns) + ")")

    def rows(self, table, rows):
        self.db.executemany("INSERT INTO " + table + " VALUES (?,?,?,?,?,?,?)", rows)

    def changes(self):
        c = self.db.execute(P["_load_expected_changes_sql"]("TARGET", "STAGE", self.pk, self.columns))
        return dict(zip((d[0] for d in c.description), c.fetchone()))

    def test_generated_predicate_new_changed_unchanged_and_independent_rerun(self):
        self.rows("TARGET", [
            ("same", '{"a":1,"b":2}', "metadata", "r1", "old", "old", "old"),
            ("changed", '{"score":1}', "metadata", "r2", "old", "old", "old"),
            ("outside", '{}', "metadata", "r9", "old", "old", "old")])
        def fresh(audit):
            return [("same", '{"b":2,"a":1}', "metadata", "r1", audit, audit, audit),
                    ("changed", '{"score":2}', "metadata", "r2", audit, audit, audit),
                    ("new", '{"score":3}', "metadata", "r3", audit, audit, audit)]
        self.rows("STAGE", fresh("run1"))
        self.assertEqual({"INSERTS": 1, "UPDATES": 1, "UNCHANGED": 1}, self.changes())
        sql = P["_build_merge_sql"](P["SSP_LOAD_DIM"], "STAGE", self.pk, self.columns)
        pred = re.search(r"WHEN MATCHED AND (.*?) THEN UPDATE SET", sql).group(1)
        for audit in P["_LOAD_AUDIT_COLUMNS"]:
            self.assertNotIn(audit, pred)
        keys = [r[0] for r in self.db.execute(
            f"SELECT t.{self.pk} FROM TARGET t JOIN STAGE s ON t.{self.pk}=s.{self.pk} WHERE {pred}")]
        self.assertEqual(["changed"], keys)
        for key in keys:
            row = self.db.execute(f"SELECT * FROM STAGE WHERE {self.pk}=?", (key,)).fetchone()
            self.db.execute("UPDATE TARGET SET " + ",".join(c + "=?" for c in self.columns[1:]) +
                            f" WHERE {self.pk}=?", (*row[1:], key))
        self.db.execute(f"INSERT INTO TARGET SELECT s.* FROM STAGE s WHERE NOT EXISTS "
                        f"(SELECT 1 FROM TARGET t WHERE t.{self.pk}=s.{self.pk})")
        self.db.execute("DELETE FROM STAGE")
        self.rows("STAGE", fresh("independently-rebuilt-run2"))
        self.assertEqual({"INSERTS": 0, "UPDATES": 0, "UNCHANGED": 3}, self.changes())
        for key in ("same", "outside"):
            self.assertEqual("old", self.db.execute(
                f"SELECT DW_PIPELINE_RUN_ID FROM TARGET WHERE {self.pk}=?", (key,)).fetchone()[0])


class DailyPostcommit(unittest.TestCase):
    def test_postcommit_readback_failure_keeps_committed_status_no_rollback_claim(self):
        context = {
            "names": {"D": "STAGE_D", "F": "STAGE_F", "DB": "OLD_D", "FB": "OLD_F"},
            "plans": ([{"name": P["SSP_LOAD_DIM_PK"]}, {"name": "METADATA_JSON"}],
                      [{"name": P["SSP_LOAD_FACT_PK"]}, {"name": "DEPENDENCY_TYPE"}]),
            "records": 1, "candidate": {"NODES": 7, "EDGES": 6, "DIM_DUPLICATE_KEYS": 0,
                "FACT_DUPLICATE_KEYS": 0, "DANGLING_SOURCE_KEYS": 0, "DANGLING_TARGET_KEYS": 0},
            "scope": {}, "changes": [{"INSERTS": 1, "UPDATES": 1}, {"INSERTS": 1, "UPDATES": 0}]}
        events, checks = [], []
        def tx(session, merges, before, verify, expected):
            before()
            verify(1)
            verify(2)
            events.append("COMMIT")
            return {"STATUS": "COMMITTED", "CHANGE_COUNTS": [
                {"DIM": {"INSERTS": 1, "UPDATES": 1}, "FACT": {"INSERTS": 1, "UPDATES": 0}}]}
        def verify(*args):
            checks.append(1)
            if len(checks) == 3:
                raise Error("SAVED_VALUES_DIFFER")
            return {}
        out = io.StringIO()
        with patch.dict(G, {"session": object(), "_load_prepare": lambda *a: context,
            "_load_verify_context": verify, "_load_baseline_equal": lambda *a: None,
            "_load_scope_check": lambda *a: None, "_load_transaction": tx}), redirect_stdout(out):
            with self.assertRaises(Error) as caught:
                P["validate_and_load_oscal"](object(), object(), {"EXECUTE_WRITES": True})
        self.assertEqual(["COMMIT"], events)
        self.assertEqual("POST_COMMIT_READBACK_FAILED_DO_NOT_RETRY", caught.exception.code)
        self.assertTrue(caught.exception.details["persisted"])
        self.assertTrue(caught.exception.details["writes_executed"])
        self.assertNotIn("TRANSACTION_ROLLED_BACK", out.getvalue())


if __name__ == "__main__":
    unittest.main()
