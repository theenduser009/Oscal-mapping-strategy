"""Local fault/SQL-shape tests. These do not prove live Snowflake execution."""
from collections import Counter
import copy
import json
from pathlib import Path
import runpy
import sqlite3
import traceback
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io

P = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      "notebooks/persistence/PILOT_SSP_ONE_RECORD_WRITE.py"))
PilotError = P["PilotError"]
MERGES = ("MERGE INTO DEV.TEST.DIM d USING S s ON d.K=s.K WHEN NOT MATCHED THEN INSERT(K) VALUES(s.K)",
          "MERGE INTO DEV.TEST.FACT d USING S s ON d.K=s.K WHEN NOT MATCHED THEN INSERT(K) VALUES(s.K)")
PRIVATE = "private_source_value_and_statement"


class Row(dict):
    def as_dict(self):
        return dict(self)


class Session:
    def __init__(self, failures=(), transaction=None):
        self.failures, self.transaction = set(failures), transaction
        self.calls, self.executed = Counter(), []
        self.persisted = {"preexisting"}
        self.pending = set(self.persisted)

    def sql(self, statement):
        if statement == "SELECT CURRENT_TRANSACTION() AS TX":
            kind = "TX"
        elif statement in MERGES:
            kind = "DIM" if statement == MERGES[0] else "FACT"
        elif statement in ("BEGIN TRANSACTION", "ROLLBACK", "COMMIT"):
            kind = statement.split()[0]
        else:
            raise AssertionError("Unexpected SQL")
        self.calls[kind] += 1
        occurrence = self.calls[kind]
        if (kind, occurrence, "sql") in self.failures:
            raise RuntimeError(PRIVATE)
        parent = self

        class Plan:
            def collect(self):
                parent.executed.append(statement)
                if (kind, occurrence, "collect") in parent.failures:
                    raise RuntimeError(PRIVATE)
                if kind == "TX":
                    return [Row(TX=parent.transaction)]
                if kind == "BEGIN":
                    parent.transaction = "test"
                    parent.pending = set(parent.persisted)
                elif kind in ("DIM", "FACT"):
                    parent.pending.add(kind)
                elif kind == "ROLLBACK":
                    parent.pending = set(parent.persisted)
                    parent.transaction = None
                elif kind == "COMMIT":
                    parent.persisted = set(parent.pending)
                    parent.transaction = None
                return [Row(N=0)]
        return Plan()


class Transactions(unittest.TestCase):
    def call(self, session, callback=lambda n: None, commit=False):
        return P["_pilot_transaction"](session, MERGES, callback, commit=commit)

    def error(self, session, callback=lambda n: None, commit=False, code=None):
        with self.assertRaises(PilotError) as caught:
            self.call(session, callback, commit)
        error = caught.exception
        if code:
            self.assertEqual(code, error.code)
        self.assertNotIn(PRIVATE, "".join(traceback.format_exception(type(error), error, error.__traceback__)))

    def test_rollback_default_and_explicit_commit(self):
        for commit in (False, True):
            s, passes = Session(), []

            def verify(n):
                passes.append(n)
                self.assertEqual("test", s.transaction)
                self.assertEqual(n, s.calls["DIM"])
                self.assertEqual(n, s.calls["FACT"])
                self.assertEqual({"preexisting", "DIM", "FACT"}, s.pending)

            result = self.call(s, verify, commit)
            self.assertEqual([1, 2], passes)
            self.assertEqual([MERGES[0], MERGES[1]] * 2, [x for x in s.executed if x in MERGES])
            self.assertEqual("COMMITTED" if commit else "ROLLED_BACK", result["STATUS"])
            self.assertEqual({"preexisting", "DIM", "FACT"} if commit else {"preexisting"}, s.persisted)
            self.assertEqual(1, s.calls["COMMIT" if commit else "ROLLBACK"])
            self.assertIsNone(s.transaction)

    def test_active_transaction_is_untouched(self):
        s = Session(transaction="caller")
        self.error(s, code="EXISTING_TRANSACTION_STOPPED_PILOT")
        self.assertEqual(Counter(TX=1), s.calls)
        self.assertEqual("caller", s.transaction)

    def test_merge_failures_at_both_passes_and_planning_or_collect_rollback(self):
        for kind in ("DIM", "FACT"):
            for n in (1, 2):
                for phase in ("sql", "collect"):
                    s = Session([(kind, n, phase)])
                    self.error(s, commit=True, code="TRANSACTION_ROLLED_BACK")
                    self.assertEqual(1, s.calls["ROLLBACK"])
                    self.assertEqual(0, s.calls["COMMIT"])
                    self.assertEqual({"preexisting"}, s.pending)

    def test_readback_failure_on_either_pass_rolls_back(self):
        for failure_pass in (1, 2):
            s = Session()

            def verify(n):
                if n == failure_pass:
                    raise RuntimeError(PRIVATE)

            self.error(s, verify, True, "TRANSACTION_ROLLED_BACK")
            self.assertEqual(1, s.calls["ROLLBACK"])
            self.assertEqual(0, s.calls["COMMIT"])

    def test_commit_failure_is_unknown_and_never_retried(self):
        for phase in ("sql", "collect"):
            s = Session([("COMMIT", 1, phase)])
            self.error(s, commit=True, code="COMMIT_OUTCOME_UNKNOWN")
            self.assertEqual(1, s.calls["COMMIT"])
            self.assertEqual(0, s.calls["ROLLBACK"])

    def test_rollback_failure_is_unknown(self):
        for failures in ([('ROLLBACK', 1, 'collect')], [('FACT', 1, 'collect'), ('ROLLBACK', 1, 'collect')]):
            s = Session(failures)
            self.error(s, code="ROLLBACK_OUTCOME_UNKNOWN")
            self.assertEqual(0, s.calls["COMMIT"])

    def test_probe_and_begin_failures_are_sanitized(self):
        for kind, code in (("TX", "TRANSACTION_STATE_UNAVAILABLE"), ("BEGIN", "BEGIN_OUTCOME_UNKNOWN")):
            s = Session([(kind, 1, "collect")])
            self.error(s, code=code)
            self.assertEqual(0, s.calls["DIM"])

    def test_transaction_rejects_ddl_and_ambiguous_mode(self):
        for merges, mode in ((("CREATE TABLE X", MERGES[1]), False), (MERGES, "true"),
                              ((MERGES[0] + "; COMMIT", MERGES[1]), False)):
            with self.assertRaises(PilotError):
                P["_pilot_transaction"](Session(), merges, lambda n: None, commit=mode)

    def test_cancellation_after_writes_rolls_back(self):
        s = Session()

        def cancelled(_):
            raise KeyboardInterrupt()

        self.error(s, cancelled, True, "TRANSACTION_ROLLED_BACK")
        self.assertEqual({"preexisting"}, s.persisted)
        self.assertEqual(s.persisted, s.pending)
        self.assertIsNone(s.transaction)

    def test_safe_verification_cause_is_preserved(self):
        def failed(_):
            raise PilotError("SAVED_VALUES_OR_KEYS_DIFFER_FROM_FROZEN_BATCH")
        with self.assertRaises(PilotError) as caught:
            self.call(Session(), failed, True)
        self.assertEqual("READBACK", caught.exception.details["STEP"])
        self.assertEqual("SAVED_VALUES_OR_KEYS_DIFFER_FROM_FROZEN_BATCH", caught.exception.details["CAUSE"])

    def test_interrupted_transaction_control_is_unknown(self):
        for control, code in (("BEGIN TRANSACTION", "BEGIN_OUTCOME_UNKNOWN"),
                              ("COMMIT", "COMMIT_OUTCOME_UNKNOWN"),
                              ("ROLLBACK", "ROLLBACK_OUTCOME_UNKNOWN")):
            s = Session()
            original = s.sql
            def sql(statement):
                if statement == control:
                    raise KeyboardInterrupt()
                return original(statement)
            s.sql = sql
            self.error(s, commit=control == "COMMIT", code=code)


def description(kind="DIM", payload="VARIANT"):
    sources = P["_PILOT_DIM_SOURCES"] if kind == "DIM" else P["_PILOT_FACT_SOURCES"]
    return [{"name": name, "kind": "COLUMN", "null?": "N", "default": None,
             "type": payload if name == "METADATA_JSON" else (
                 "TIMESTAMP_TZ(9)" if name == "DW_LOAD_TIMESTAMP_TZ" else (
                     "TIMESTAMP_NTZ(9)" if name == "DW_LOAD_TIMESTAMP" else "VARCHAR(64)"))}
            for name in sources]


class Schema(unittest.TestCase):
    def plan(self, rows=None, kind="DIM"):
        return P["_pilot_column_plan"](description(kind) if rows is None else rows, kind)

    def test_complete_projection_preserves_input_without_truncation(self):
        for kind in ("DIM", "FACT"):
            rows = description(kind)
            before = copy.deepcopy(rows)
            plan = self.plan(rows, kind)
            self.assertEqual(before, rows)
            self.assertEqual(len(rows), len(plan))
            self.assertEqual('CAST(s."' + plan[0]["source"] + '" AS VARCHAR)', plan[0]["expression"])

    def test_missing_mapped_columns_stop(self):
        for kind in ("DIM", "FACT"):
            rows = description(kind)
            for i in range(len(rows)):
                if rows[i]["name"].startswith("DW_"):
                    continue
                with self.assertRaises(PilotError):
                    self.plan(rows[:i] + rows[i + 1:], kind)

    def test_optional_audit_columns_are_used_if_present_not_invented_if_absent(self):
        rows = [r for r in description() if not r["name"].startswith("DW_")]
        self.assertEqual(7, len(self.plan(rows)))

    def test_unmapped_required_stops_but_defaulted_nullable_omitted(self):
        extra = {"name": "NEW_REQUIRED", "type": "NUMBER(38,0)", "kind": "COLUMN", "null?": "N", "default": None}
        with self.assertRaises(PilotError):
            self.plan(description() + [extra])
        for update in ({"null?": "Y"}, {"default": "0"}, {"kind": "VIRTUAL"}):
            self.assertEqual(10, len(self.plan(description() + [dict(extra, **update)])))

    def test_json_and_timestamps_explicit(self):
        for dtype in ("VARCHAR(1000)", "STRING", "TEXT", "VARIANT"):
            plan = self.plan(description(payload=dtype))
            expression = next(c["expression"] for c in plan if c["name"] == "METADATA_JSON")
            self.assertEqual('PARSE_JSON(s."METADATA_JSON")' if dtype == 'VARIANT' else
                             'CAST(s."METADATA_JSON" AS VARCHAR)', expression)
        for dtype in ("TIMESTAMP_NTZ", "TIMESTAMP_TZ(3)", "TIMESTAMP_LTZ(9)"):
            rows = description()
            rows[-2]["type"] = dtype
            self.assertIn(" AS " + dtype + ")", self.plan(rows)[-2]["expression"])

    def test_unsafe_types_and_metadata_stop(self):
        for dtype in ("VARCHAR(2); DROP TABLE T", "VARCHAR(2) COLLATE 'en'", "NUMBER(38,0)",
                      "BINARY", "OBJECT", "ARRAY", "VARCHAR(0)", "TIMESTAMP_NTZ(10)"):
            rows = description()
            rows[0]["type"] = dtype
            with self.assertRaises(PilotError):
                self.plan(rows)
        for change in ({"null?": "?"}, {"kind": "VIRTUAL"}, {"expression": "1"}, {"name": "lower_case"}):
            rows = description()
            rows[0].update(change)
            with self.assertRaises(PilotError):
                self.plan(rows)
        with self.assertRaises(PilotError):
            self.plan(description() + [description()[0]])

    def test_readback_covers_all_columns_and_parsed_objects(self):
        for dtype in ("VARIANT", "VARCHAR"):
            plan = self.plan(description(payload=dtype))
            sql = P["_pilot_difference_sql"]("DEV.SCHEMA.DIM", "STAGE_DIM", plan[0]["name"], plan)
            self.assertNotIn("TO_JSON", sql)
            self.assertNotIn("TRY_PARSE_JSON", sql)
            self.assertEqual(dtype == "VARCHAR", "PARSE_JSON(" in sql)
            for c in plan:
                self.assertIn('s."' + c["name"] + '"', sql)
                self.assertIn('t."' + c["name"] + '"', sql)

    def test_readback_rejects_sql_injection_and_missing_pk(self):
        plan = self.plan()
        for name in ("DEV.SCHEMA.T;DELETE", "DEV..T", '"DEV"."SCHEMA"."T"', "DB.T"):
            with self.assertRaises(PilotError):
                P["_pilot_difference_sql"](name, "S", plan[0]["name"], plan)
        for columns in ([], plan + [plan[0]], plan[1:]):
            with self.assertRaises(PilotError):
                P["_pilot_difference_sql"]("T", "S", plan[0]["name"], columns)

    def test_relational_readback_counts(self):
        db = sqlite3.connect(":memory:")
        db.create_function("PARSE_JSON", 1, lambda x: None if x is None else json.dumps(json.loads(x), sort_keys=True))
        db.create_function("IS_OBJECT", 1, lambda x: x is not None and isinstance(json.loads(x), dict))
        for t in ("STAGE", "TARGET"):
            db.execute(f"CREATE TABLE {t}(K TEXT, METADATA_JSON TEXT, LABEL TEXT)")
        db.execute("INSERT INTO STAGE VALUES ('one', '{\"b\":2,\"a\":1}', NULL)")
        db.execute("INSERT INTO TARGET VALUES ('one', '{\"a\":1,\"b\":2}', NULL)")
        db.execute("INSERT INTO TARGET VALUES ('other', '{}', 'ignored')")
        sql = P["_pilot_difference_sql"]("TARGET", "STAGE", "K",
                 [{"name": c, "type": "VARCHAR"} for c in ("K", "METADATA_JSON", "LABEL")])

        def report():
            cursor = db.execute(sql)
            return dict(zip([c[0] for c in cursor.description], cursor.fetchone()))

        r = report()
        self.assertEqual((1, 1), (r.pop("STAGED_ROWS"), r.pop("TARGET_ROWS_IN_KEY_SCOPE")))
        self.assertFalse(any(r.values()))
        db.execute("UPDATE TARGET SET LABEL='changed' WHERE K='one'")
        self.assertEqual(1, report()["MISMATCHED_KEYS"])
        db.execute("UPDATE TARGET SET LABEL=NULL,METADATA_JSON='[]' WHERE K='one'")
        self.assertEqual(1, report()["MISMATCHED_KEYS"])
        db.execute("DELETE FROM TARGET WHERE K='one'")
        self.assertEqual(1, report()["MISSING_KEYS"])
        db.executemany("INSERT INTO TARGET VALUES (?, ?, ?)", [("one", "{}", None)] * 2)
        self.assertEqual(1, report()["TARGET_DUPLICATE_KEYS"])
        db.execute("INSERT INTO STAGE SELECT * FROM STAGE")
        self.assertEqual(1, report()["STAGE_DUPLICATE_KEYS"])
        db.execute("INSERT INTO STAGE VALUES (NULL, '{}', NULL)")
        self.assertEqual(1, report()["STAGE_NULL_KEYS"])
        db.close()


class Orchestration(unittest.TestCase):
    def test_preview_never_invokes_transaction_and_commit_rehearses_first(self):
        fn = P["run_ssp_one_record_write_pilot"]
        for mode in ("PREVIEW", "COMMIT"):
            events = []

            def transaction(session, merges, verify, commit=False):
                events.append("COMMIT" if commit else "ROLLBACK")
                verify(1)
                verify(2)
                return {"STATUS": events[-1], "VERIFIED_PASSES": 2}

            changes = {
                "_pilot_contract": lambda *args: None,
                "_pilot_no_transaction": lambda *args: None,
                "_pilot_column_plan": lambda *args: [],
                "_pilot_query": lambda session, sql: events.append(sql) or [],
                "_pilot_freeze_graph": lambda *args: {"SOURCE_RECORDS": 1, "NODES": 2, "EDGES": 1},
                "_pilot_stage": lambda *args: None,
                "_pilot_scope_queries": lambda *args: ("SELECT D", "SELECT F"),
                "_pilot_check_existing_scope": lambda *args: None,
                "_pilot_baseline_equal": lambda *args: events.append("BASELINE"),
                "_pilot_verify": lambda *args, **kwargs: {"MATCHED": True},
                "_pilot_merge_sql": lambda *args: "MERGE",
                "_pilot_transaction": transaction,
            }
            with patch.dict(fn.__globals__, changes):
                result = fn(None, {}, {}, None, None, mode)
            if mode == "PREVIEW":
                self.assertFalse(result["PERSISTED"])
                self.assertFalse(result["TARGET_DML_ATTEMPTED"])
                self.assertNotIn("ROLLBACK", events)
            else:
                self.assertTrue(result["PERSISTED"])
                self.assertTrue(result["ROLLBACK_RESTORED_BASELINE"])
                self.assertLess(events.index("ROLLBACK"), events.index("COMMIT"))
                self.assertIn("BASELINE", events[events.index("ROLLBACK") + 1:events.index("COMMIT")])
                self.assertFalse(any("CREATE " in x for x in events[events.index("ROLLBACK") + 1:]))

    def test_default_is_preview_and_legacy_writes_cannot_be_enabled(self):
        self.assertEqual("PREVIEW", P["SSP_PILOT_MODE"])
        with self.assertRaises(PilotError):
            P["_pilot_contract"]({"EXECUTE_WRITES": True}, {})

    def test_failed_rerun_clears_previous_success(self):
        path = Path(__file__).resolve().parents[1] / "notebooks/persistence/PILOT_SSP_ONE_RECORD_WRITE.py"
        namespace = {"__name__": "__main__", "ssp_pilot_report": {"PERSISTED": True}}
        with self.assertRaises(RuntimeError):
            exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
        self.assertIsNone(namespace["ssp_pilot_report"])

    def test_scope_includes_incident_edges_and_rejects_extra_rows(self):
        names = {k: k for k in ("D", "F", "NR")}
        queries = P["_pilot_scope_queries"](names)
        self.assertIn("SOURCE_RECORD_ID", queries[0])
        self.assertIn("FK_SOURCE_ELEMENT_HASH", queries[1])
        self.assertIn("FK_TARGET_ELEMENT_HASH", queries[1])
        fn = P["_pilot_check_existing_scope"]
        with patch.dict(fn.__globals__, {"_pilot_count": lambda *args: 1}):
            with self.assertRaises(PilotError):
                fn(None, names, queries)


if __name__ == "__main__":
    unittest.main()
