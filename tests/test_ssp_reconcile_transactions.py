"""Local replacement transaction tests; not live Snowflake proof."""
from collections import Counter
import copy
from pathlib import Path
import runpy
import sqlite3
import traceback
import unittest

P = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      "notebooks/persistence/RECONCILE_SSP_ONE_RECORD_WRITE.py"))
Error = P["PilotError"]
DIM, FACT = P["SSP_PILOT_DIM"], P["SSP_PILOT_FACT"]
DK, FK = P["SSP_PILOT_DIM_PK"], P["SSP_PILOT_FACT_PK"]
NAMES = {"DB": "FROZEN_DIM", "FB": "FROZEN_FACT"}
MERGES = (
    f"MERGE INTO {DIM} t USING NEW_DIM s ON t.{DK}=s.{DK} "
    f"WHEN NOT MATCHED THEN INSERT ({DK}) VALUES (s.{DK})",
    f"MERGE INTO {FACT} t USING NEW_FACT s ON t.{FK}=s.{FK} "
    f"WHEN NOT MATCHED THEN INSERT ({FK}) VALUES (s.{FK})",
)
PRIVATE = "private_source_payload_must_not_escape"


class Row(dict):
    def as_dict(self):
        return dict(self)


class Session:
    def __init__(self, deletes, transaction=None, failure=None, error_type=RuntimeError,
                 delete_counts=(20, 21), insert_counts=(19, 18, 0, 0)):
        self.deletes = tuple(deletes)
        self.transaction = transaction
        self.failure, self.error_type = failure, error_type
        self.delete_counts, self.insert_counts = list(delete_counts), list(insert_counts)
        self.calls, self.events = Counter(), []
        self.persisted = {
            "DIM": {**{f"old-d-{i}": {"payload": f"legacy-{i}"} for i in range(21)},
                    "other-d": {"payload": "untouched-dim"}},
            "FACT": {**{f"old-f-{i}": {"payload": f"legacy-edge-{i}"} for i in range(20)},
                     "other-f": {"payload": "untouched-fact"}},
        }
        self.original = copy.deepcopy(self.persisted)
        self.pending = copy.deepcopy(self.persisted)

    def sql(self, statement):
        if statement.strip().rstrip(";") == "SELECT CURRENT_TRANSACTION() AS TX":
            kind = "TX"
        elif statement in self.deletes:
            kind = "DELETE_FACT" if statement == self.deletes[0] else "DELETE_DIM"
        elif statement in MERGES:
            kind = "MERGE_DIM" if statement == MERGES[0] else "MERGE_FACT"
        else:
            kind = statement.strip().split()[0].upper()
            if kind not in {"BEGIN", "COMMIT", "ROLLBACK"}:
                raise AssertionError("Unexpected SQL")
        self.calls[kind] += 1
        occurrence = self.calls[kind]
        if self.failure == (kind, occurrence, "sql"):
            raise self.error_type(PRIVATE)
        parent = self

        class Plan:
            def collect(self):
                parent.events.append(kind)
                if parent.failure == (kind, occurrence, "collect"):
                    raise parent.error_type(PRIVATE)
                if kind == "TX":
                    return [Row(TX=parent.transaction)]
                if kind == "BEGIN":
                    parent.transaction = "active"
                    parent.pending = copy.deepcopy(parent.persisted)
                elif kind.startswith("DELETE_"):
                    table = kind.split("_")[1]
                    prefix = "old-d-" if table == "DIM" else "old-f-"
                    parent.pending[table] = {key: row for key, row in parent.pending[table].items()
                                             if not key.startswith(prefix)}
                    return [Row({"number of rows deleted": parent.delete_counts.pop(0)})]
                elif kind.startswith("MERGE_"):
                    table = kind.split("_")[1]
                    count = 19 if table == "DIM" else 18
                    prefix = "new-d-" if table == "DIM" else "new-f-"
                    for index in range(count):
                        parent.pending[table].setdefault(prefix + str(index), {"payload": "mapped-" + str(index)})
                    return [Row({"number of rows inserted": parent.insert_counts.pop(0)})]
                elif kind == "ROLLBACK":
                    parent.pending = copy.deepcopy(parent.persisted)
                    parent.transaction = None
                elif kind == "COMMIT":
                    parent.persisted = copy.deepcopy(parent.pending)
                    parent.transaction = None
                return [Row()]
        return Plan()


class ReconcileTransactions(unittest.TestCase):
    def setUp(self):
        self.deletes = tuple(P["_reconcile_delete_sql"](NAMES))
        self.assertEqual(2, len(self.deletes))

    def call(self, session, before=lambda: None, verify=lambda _: None, commit=False):
        return P["_reconcile_transaction"](session, self.deletes, MERGES, before, verify, (19, 18), commit=commit)

    def assert_clean_error(self, error, code=None):
        self.assertIsInstance(error, Error)
        if code:
            self.assertEqual(code, error.code)
        rendered = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        self.assertNotIn(PRIVATE, rendered)

    def assert_replacement(self, state, original):
        self.assertEqual(20, len(state["DIM"]))
        self.assertEqual(19, len(state["FACT"]))
        self.assertFalse(any(key.startswith("old-") for rows in state.values() for key in rows))
        self.assertEqual(original["DIM"]["other-d"], state["DIM"]["other-d"])
        self.assertEqual(original["FACT"]["other-f"], state["FACT"]["other-f"])

    def test_generated_deletes_use_only_frozen_keys_and_fact_precedes_dim(self):
        self.assertIn("FACT_OSCAL_SSP_DEPENDENCY", self.deletes[0])
        self.assertIn("DIM_OSCAL_SSP_ELEMENT", self.deletes[1])
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.executescript(f"""
            CREATE TABLE TARGET_DIM ({DK} TEXT);
            CREATE TABLE TARGET_FACT ({FK} TEXT);
            CREATE TABLE FROZEN_DIM ({DK} TEXT);
            CREATE TABLE FROZEN_FACT ({FK} TEXT);
            INSERT INTO TARGET_DIM VALUES ('old-d-1'),('old-d-2'),('other-d');
            INSERT INTO TARGET_FACT VALUES ('old-f-1'),('other-f');
            INSERT INTO FROZEN_DIM VALUES ('old-d-1'),('old-d-2');
            INSERT INTO FROZEN_FACT VALUES ('old-f-1');
        """)
        for statement in self.deletes:
            sql = statement.replace(DIM, "TARGET_DIM").replace(FACT, "TARGET_FACT")
            connection.execute(sql)
        self.assertEqual([("other-d",)], connection.execute("SELECT * FROM TARGET_DIM").fetchall())
        self.assertEqual([("other-f",)], connection.execute("SELECT * FROM TARGET_FACT").fetchall())
        self.assertEqual(2, connection.execute("SELECT COUNT(*) FROM FROZEN_DIM").fetchone()[0])
        self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM FROZEN_FACT").fetchone()[0])

    def test_default_rehearsal_guard_order_two_verifications_and_rollback(self):
        session, passes = Session(self.deletes), []
        def before():
            self.assertEqual("active", session.transaction)
            self.assertEqual(0, session.calls["DELETE_FACT"])
            self.assertEqual(session.original, session.pending)
            session.events.append("BASELINE_CHECK")
        def verify(number):
            passes.append(number)
            self.assert_replacement(session.pending, session.original)
            session.events.append("VERIFY" + str(number))
        self.call(session, before, verify)
        self.assertEqual([1, 2], passes)
        self.assertEqual(["TX", "BEGIN", "BASELINE_CHECK", "DELETE_FACT", "DELETE_DIM",
                          "MERGE_DIM", "MERGE_FACT", "VERIFY1", "MERGE_DIM", "MERGE_FACT",
                          "VERIFY2", "ROLLBACK"], session.events)
        self.assertEqual(session.original, session.persisted)
        self.assertEqual(session.original, session.pending)

    def test_commit_replaces_only_approved_scope_and_preserves_other_full_rows(self):
        session = Session(self.deletes)
        self.call(session, commit=True)
        self.assert_replacement(session.persisted, session.original)
        self.assertEqual(1, session.calls["COMMIT"])
        self.assertEqual(0, session.calls["ROLLBACK"])
        self.assertIsNone(session.transaction)

    def test_failure_or_cancellation_between_deletes_restores_transaction(self):
        for stage in ("sql", "collect"):
            for error_type in (RuntimeError, KeyboardInterrupt):
                with self.subTest(stage=stage, error_type=error_type):
                    session = Session(self.deletes, failure=("DELETE_DIM", 1, stage), error_type=error_type)
                    with self.assertRaises(Error) as caught:
                        self.call(session, commit=True)
                    self.assert_clean_error(caught.exception)
                    self.assertEqual(1, session.calls["DELETE_FACT"])
                    self.assertEqual(1, session.calls["ROLLBACK"])
                    self.assertEqual(0, session.calls["COMMIT"])
                    self.assertEqual(0, session.calls["MERGE_DIM"])
                    self.assertEqual(session.original, session.pending)
                    self.assertEqual(session.original, session.persisted)

    def test_unexpected_delete_count_rolls_back_before_any_insert(self):
        for counts in ((19, 21), (20, 20)):
            with self.subTest(counts=counts):
                session = Session(self.deletes, delete_counts=counts)
                with self.assertRaises(Error) as caught:
                    self.call(session, commit=True)
                self.assert_clean_error(caught.exception)
                self.assertEqual(1, session.calls["ROLLBACK"])
                self.assertEqual(0, session.calls["MERGE_DIM"])
                self.assertEqual(0, session.calls["COMMIT"])
                self.assertEqual(session.original, session.pending)

    def test_existing_caller_transaction_remains_untouched(self):
        session = Session(self.deletes, transaction="caller")
        with self.assertRaises(Error) as caught:
            self.call(session)
        self.assert_clean_error(caught.exception)
        self.assertEqual(Counter(TX=1), session.calls)
        self.assertEqual("caller", session.transaction)

    def test_baseline_drift_after_begin_stops_before_delete(self):
        session = Session(self.deletes)
        def before():
            self.assertEqual("active", session.transaction)
            raise RuntimeError(PRIVATE)
        with self.assertRaises(Error) as caught:
            self.call(session, before=before, commit=True)
        self.assert_clean_error(caught.exception)
        self.assertEqual(["TX", "BEGIN", "ROLLBACK"], session.events)
        self.assertEqual(session.original, session.pending)

    def test_insert_count_mismatch_in_either_pass_restores_old_scope(self):
        for counts in ((18, 18, 0, 0), (19, 17, 0, 0), (19, 18, 1, 0), (19, 18, 0, 1)):
            with self.subTest(counts=counts):
                session = Session(self.deletes, insert_counts=counts)
                with self.assertRaises(Error) as caught:
                    self.call(session, commit=True)
                self.assert_clean_error(caught.exception)
                self.assertEqual(1, session.calls["ROLLBACK"])
                self.assertEqual(0, session.calls["COMMIT"])
                self.assertEqual(session.original, session.pending)

    def test_uncertain_commit_and_rollback_are_not_reported_as_clean_recovery(self):
        for kind, commit, code in (("COMMIT", True, "COMMIT_OUTCOME_UNKNOWN"),
                                   ("ROLLBACK", False, "ROLLBACK_OUTCOME_UNKNOWN")):
            with self.subTest(kind=kind):
                session = Session(self.deletes, failure=(kind, 1, "collect"))
                with self.assertRaises(Error) as caught:
                    self.call(session, commit=commit)
                self.assert_clean_error(caught.exception, code)
                self.assertEqual(1, session.calls[kind])


if __name__ == "__main__":
    unittest.main()
