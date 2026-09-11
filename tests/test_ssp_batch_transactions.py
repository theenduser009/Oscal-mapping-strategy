"""Bounded multi-record transaction tests using the existing stateful fake."""
import copy
from pathlib import Path
import runpy
import traceback
import unittest


ROOT = Path(__file__).resolve().parents[1]
R = runpy.run_path(str(ROOT / "tests/test_ssp_reconcile_transactions.py"))
P = runpy.run_path(str(ROOT / "notebooks/persistence/PILOT_SSP_TEN_RECORD_BATCH_WRITE.py"))
Error = P["PilotError"]
Row, MERGES, PRIVATE = R["Row"], R["MERGES"], R["PRIVATE"]
DELETES = tuple(R["P"]["_reconcile_delete_sql"]({"DB": "FROZEN_DIM", "FB": "FROZEN_FACT"}))


class BatchSession(R["Session"]):
    def __init__(self, old_counts=(210, 200), new_counts=(190, 180),
                 delete_counts=None, insert_counts=None, **kwargs):
        super().__init__(
            DELETES,
            delete_counts=tuple(reversed(old_counts)) if delete_counts is None else delete_counts,
            insert_counts=(*new_counts, 0, 0) if insert_counts is None else insert_counts,
            **kwargs,
        )
        self.old_counts, self.new_counts = tuple(old_counts), tuple(new_counts)
        self.persisted = {}
        for table, count, prefix in zip(("DIM", "FACT"), old_counts, ("d", "f")):
            self.persisted[table] = {
                **{f"old-{prefix}-{i}": {"payload": {"legacy": i}} for i in range(count)},
                f"other-{prefix}": {"payload": {"untouched": "unrelated"}},
                f"protected-{prefix}": {"payload": {"untouched": "first-root", "uuid": "preserved"}},
            }
        self.original = copy.deepcopy(self.persisted)
        self.pending = copy.deepcopy(self.persisted)

    def sql(self, statement):
        if statement not in MERGES:
            return super().sql(statement)
        kind = "MERGE_DIM" if statement == MERGES[0] else "MERGE_FACT"
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
                index = 0 if kind == "MERGE_DIM" else 1
                table, prefix = ("DIM", "new-d-") if index == 0 else ("FACT", "new-f-")
                for value in range(parent.new_counts[index]):
                    parent.pending[table].setdefault(prefix + str(value), {"mapped": value})
                return [Row({"number of rows inserted": parent.insert_counts.pop(0)})]
        return Plan()


class BatchTransactions(unittest.TestCase):
    def call(self, session, before=lambda: None, verify=lambda _: None, commit=False):
        return P["_batch_transaction"](
            session, DELETES, MERGES, before, verify,
            session.old_counts, session.new_counts, commit=commit)

    def clean_error(self, error, code=None):
        self.assertIsInstance(error, Error)
        if code:
            self.assertEqual(code, error.code)
        self.assertNotIn(PRIVATE, "".join(traceback.format_exception(
            type(error), error, error.__traceback__)))

    def assert_untouched(self, session, state):
        for table, prefix in (("DIM", "d"), ("FACT", "f")):
            for kind in ("other", "protected"):
                key = kind + "-" + prefix
                self.assertEqual(session.original[table][key], state[table][key])

    def assert_replaced(self, session, state):
        for table, count in zip(("DIM", "FACT"), session.new_counts):
            self.assertEqual(count + 2, len(state[table]))
            self.assertFalse(any(key.startswith("old-") for key in state[table]))
        self.assert_untouched(session, state)

    def test_dynamic_counts_guard_inside_begin_two_passes_then_rollback(self):
        session, passes = BatchSession(), []

        def before():
            self.assertEqual("active", session.transaction)
            self.assertEqual(0, session.calls["DELETE_FACT"])
            self.assertEqual(0, session.calls["DELETE_DIM"])
            session.events.append("BASELINE")

        def verify(number):
            passes.append(number)
            self.assert_replaced(session, session.pending)
            session.events.append("VERIFY" + str(number))

        self.call(session, before, verify)
        self.assertEqual([1, 2], passes)
        self.assertEqual(
            ["TX", "BEGIN", "BASELINE", "DELETE_FACT", "DELETE_DIM", "MERGE_DIM",
             "MERGE_FACT", "VERIFY1", "MERGE_DIM", "MERGE_FACT", "VERIFY2", "ROLLBACK"],
            session.events)
        self.assertEqual([], session.delete_counts)
        self.assertEqual([], session.insert_counts)
        self.assertEqual(session.original, session.persisted)
        self.assertEqual(session.original, session.pending)

    def test_commit_uses_dynamic_or_zero_old_counts_and_preserves_protected_record(self):
        for old, new in (((210, 200), (190, 180)), ((0, 0), (37, 27))):
            with self.subTest(old=old, new=new):
                session = BatchSession(old, new)
                self.call(session, commit=True)
                self.assert_replaced(session, session.persisted)
                self.assertEqual(1, session.calls["COMMIT"])
                self.assertEqual(0, session.calls["ROLLBACK"])
                self.assertEqual(2, session.calls["MERGE_DIM"])
                self.assertEqual(2, session.calls["MERGE_FACT"])
                self.assertIsNone(session.transaction)

    def test_failure_and_cancellation_after_first_delete_restore_every_record(self):
        for error_type in (RuntimeError, KeyboardInterrupt, SystemExit):
            for stage in ("sql", "collect"):
                with self.subTest(error_type=error_type, stage=stage):
                    session = BatchSession(failure=("DELETE_DIM", 1, stage), error_type=error_type)
                    with self.assertRaises(Error) as caught:
                        self.call(session, commit=True)
                    self.clean_error(caught.exception, "TRANSACTION_ROLLED_BACK")
                    self.assertEqual(1, session.calls["DELETE_FACT"])
                    self.assertEqual(1, session.calls["ROLLBACK"])
                    self.assertEqual(0, session.calls["MERGE_DIM"])
                    self.assertEqual(0, session.calls["COMMIT"])
                    self.assertEqual(session.original, session.pending)
                    self.assertEqual(session.original, session.persisted)

    def test_baseline_failure_inside_begin_prevents_all_dml(self):
        session = BatchSession()

        def before():
            self.assertEqual("active", session.transaction)
            raise RuntimeError(PRIVATE)

        with self.assertRaises(Error) as caught:
            self.call(session, before=before, commit=True)
        self.clean_error(caught.exception, "TRANSACTION_ROLLED_BACK")
        self.assertEqual(["TX", "BEGIN", "ROLLBACK"], session.events)
        self.assertEqual(session.original, session.pending)

    def test_any_delete_or_insert_count_mismatch_rolls_back(self):
        cases = (
            {"delete_counts": (199, 210)}, {"delete_counts": (200, 209)},
            {"insert_counts": (189, 180, 0, 0)}, {"insert_counts": (190, 179, 0, 0)},
            {"insert_counts": (190, 180, 1, 0)}, {"insert_counts": (190, 180, 0, 1)},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                session = BatchSession(**overrides)
                with self.assertRaises(Error) as caught:
                    self.call(session, commit=True)
                self.clean_error(caught.exception, "TRANSACTION_ROLLED_BACK")
                self.assertEqual(1, session.calls["ROLLBACK"])
                self.assertEqual(0, session.calls["COMMIT"])
                self.assertEqual(session.original, session.pending)
                self.assertEqual(session.original, session.persisted)

    def test_either_verification_failure_restores_all_old_rows(self):
        for failure_pass in (1, 2):
            with self.subTest(failure_pass=failure_pass):
                session = BatchSession()

                def verify(number):
                    if number == failure_pass:
                        raise RuntimeError(PRIVATE)

                with self.assertRaises(Error) as caught:
                    self.call(session, verify=verify, commit=True)
                self.clean_error(caught.exception, "TRANSACTION_ROLLED_BACK")
                self.assertEqual(0, session.calls["COMMIT"])
                self.assertEqual(session.original, session.pending)

    def test_existing_transaction_is_not_committed_rolled_back_or_mutated(self):
        session = BatchSession(transaction="caller")
        with self.assertRaises(Error) as caught:
            self.call(session, commit=True)
        self.clean_error(caught.exception)
        self.assertEqual({"TX": 1}, dict(session.calls))
        self.assertEqual("caller", session.transaction)
        self.assertEqual(session.original, session.persisted)

    def test_uncertain_transaction_outcomes_are_not_retried(self):
        for kind, commit, code in (("COMMIT", True, "COMMIT_OUTCOME_UNKNOWN"),
                                   ("ROLLBACK", False, "ROLLBACK_OUTCOME_UNKNOWN")):
            for stage in ("sql", "collect"):
                with self.subTest(kind=kind, stage=stage):
                    session = BatchSession(failure=(kind, 1, stage))
                    with self.assertRaises(Error) as caught:
                        self.call(session, commit=commit)
                    self.clean_error(caught.exception, code)
                    self.assertEqual(1, session.calls[kind])
                    if commit:
                        self.assertEqual(0, session.calls["ROLLBACK"])

    def test_malformed_arguments_fail_before_queries_or_dml(self):
        valid = {"deletes": DELETES, "merges": MERGES, "before_replace": lambda: None,
                 "verify": lambda _: None, "old_counts": (210, 200),
                 "new_counts": (190, 180), "commit": False}
        cases = []
        for parameter in ("old_counts", "new_counts"):
            for value in (None, (), (1,), (1, 2, 3), "12", (-1, 1), (1, -1),
                          (True, 1), (1, False), (1.5, 1), (1, "1")):
                cases.append({parameter: value})
        cases.extend({"commit": value} for value in (None, 0, 1, "COMMIT"))
        cases.extend({parameter: None} for parameter in ("before_replace", "verify"))
        for parameter in ("deletes", "merges"):
            cases.extend({parameter: value} for value in (None, (), ("ONE",), "SQL"))
            cases.append({parameter: ("CREATE TABLE BAD(K INT)", "DROP TABLE BAD")})
            cases.append({parameter: tuple(statement + "; DROP TABLE BAD" for statement in valid[parameter])})
        for override in cases:
            with self.subTest(override=override):
                session = BatchSession()
                with self.assertRaises(Error):
                    P["_batch_transaction"](session, **dict(valid, **override))
                self.assertEqual({}, dict(session.calls))
                self.assertEqual(session.original, session.persisted)


if __name__ == "__main__":
    unittest.main()
