"""Execute scope/key SQL locally; no claim of Snowflake runtime acceptance."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import runpy
import sqlite3
import unittest
from unittest.mock import patch

P = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      "notebooks/persistence/RECONCILE_SSP_ONE_RECORD_WRITE.py"))
DK, FK, E = P["SSP_PILOT_DIM_PK"], P["SSP_PILOT_FACT_PK"], P["PilotError"]


class RelationalChecks(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.create_function("EQUAL_NULL", 2, lambda a, b: a == b)
        self.names = {k: k for k in ("D", "F", "DB", "FB", "NR")}
        for table in ("D", "DB", "TD"):
            self.db.execute(f"CREATE TABLE {table} ({DK} TEXT, OSCAL_UUID TEXT, ELEMENT_TYPE TEXT, "
                            "SOURCE_SYSTEM_NAME TEXT, SOURCE_TABLE_NAME TEXT, SOURCE_RECORD_ID TEXT)")
        for table in ("F", "FB", "TF"):
            self.db.execute(f"CREATE TABLE {table} ({FK} TEXT, FK_SOURCE_ELEMENT_HASH TEXT, "
                            "FK_TARGET_ELEMENT_HASH TEXT, SOURCE_OSCAL_UUID TEXT, TARGET_OSCAL_UUID TEXT, "
                            "DEPENDENCY_TYPE TEXT)")
        self.db.execute("CREATE TABLE NR(SOURCE_RECORD_ID TEXT)")
        self.db.execute("INSERT INTO NR VALUES ('reviewed')")
        for dim, fact, size, prefix, rel in (("DB", "FB", 21, "old", "parent_of"),
                                             ("D", "F", 19, "new", "CONTAINS")):
            for i in range(size):
                self.db.execute(f"INSERT INTO {dim} VALUES (?,?,?,?,?,?)",
                                (prefix+str(i), prefix+"u"+str(i),
                                 "system-security-plan" if i == 0 else "props", "ARCHER",
                                 P["SSP_PILOT_SOURCE"], "reviewed"))
                if i:
                    self.db.execute(f"INSERT INTO {fact} VALUES (?,?,?,?,?,?)",
                                    (prefix+"e"+str(i), prefix+"0", prefix+str(i), prefix+"u0",
                                     prefix+"u"+str(i), rel))
        self.db.execute("INSERT INTO TD SELECT * FROM DB")
        self.db.execute("INSERT INTO TF SELECT * FROM FB")
        self.db.execute("INSERT INTO TD VALUES ('other','otheruuid','other','ARCHER','OTHER','other')")
        self.db.execute("INSERT INTO TF VALUES ('otheredge','other','outside','otheruuid','outsideuuid','other')")
        def query(session, sql):
            return [dict(r) for r in self.db.execute(sql).fetchall()]
        self.context = patch.dict(P["_reconcile_integrity"].__globals__,
                                  {"_pilot_query": query, "SSP_PILOT_DIM": "TD", "SSP_PILOT_FACT": "TF"})
        self.context.start()
        self.addCleanup(self.context.stop)

    def test_valid_old_and_new_keys_are_reported(self):
        for d, f, rel in (("DB", "FB", "parent_of"), ("D", "F", "CONTAINS")):
            report = P["_reconcile_integrity"](None, (f"SELECT * FROM {d}", f"SELECT * FROM {f}"), rel)
            self.assertEqual(1, report.pop("ROOTS"))
            self.assertTrue(all(v == 0 for v in report.values()))

    def test_corrupt_keys_uuids_relationships_and_parents_stop(self):
        cases = [
            ("DELETE FROM D WHERE " + DK + "='new1'", "DANGLING_TARGET_KEYS"),
            ("UPDATE F SET FK_SOURCE_ELEMENT_HASH='missing' WHERE " + FK + "='newe1'", "DANGLING_SOURCE_KEYS"),
            ("UPDATE F SET FK_TARGET_ELEMENT_HASH=NULL WHERE " + FK + "='newe1'", "NULL_FOREIGN_KEYS"),
            ("UPDATE F SET SOURCE_OSCAL_UUID='wrong' WHERE " + FK + "='newe1'", "UUID_LINK_MISMATCHES"),
            ("INSERT INTO F SELECT * FROM F WHERE " + FK + "='newe1'", "FACT_DUPLICATE_KEY_GROUPS"),
            ("INSERT INTO D SELECT * FROM D WHERE " + DK + "='new1'", "DIM_DUPLICATE_KEY_GROUPS"),
            ("UPDATE D SET " + DK + "=NULL WHERE " + DK + "='new1'", "DIM_NULL_KEYS"),
            ("UPDATE F SET " + FK + "=NULL WHERE " + FK + "='newe1'", "FACT_NULL_KEYS"),
            ("UPDATE F SET DEPENDENCY_TYPE='other'", "WRONG_RELATIONSHIP_TYPE"),
            ("DELETE FROM F WHERE " + FK + "='newe1'", "WRONG_PARENT_COUNTS"),
        ]
        for sql, metric in cases:
            with self.subTest(metric=metric):
                self.db.execute("SAVEPOINT case_test")
                self.db.execute(sql)
                with self.assertRaises(E) as caught:
                    P["_reconcile_integrity"](None, ("SELECT * FROM D", "SELECT * FROM F"), "CONTAINS")
                self.assertGreater(caught.exception.details["KEY_CHECKS"][metric], 0)
                self.db.execute("ROLLBACK TO case_test")
                self.db.execute("RELEASE case_test")

    def test_legacy_tree_boundary_and_reviewed_counts(self):
        fn = P["_reconcile_validate_baseline"]
        queries = P["_reconcile_live_scope_queries"](self.names)
        with patch.dict(fn.__globals__, {"_pilot_baseline_equal": lambda *a: None}):
            self.assertEqual(21, fn(None, self.names, queries)["OLD_DIM_ROWS"])
            self.db.execute("UPDATE FB SET FK_TARGET_ELEMENT_HASH='outside' WHERE " + FK + "='olde1'")
            with self.assertRaisesRegex(E, "PRIMARY_FOREIGN_KEY_OR_HIERARCHY_CHECK_FAILED"):
                fn(None, self.names, queries)

    def test_old_ownership_or_zero_overlap_changes_stop(self):
        fn = P["_reconcile_validate_baseline"]
        queries = P["_reconcile_live_scope_queries"](self.names)
        for sql, code in (("UPDATE DB SET SOURCE_RECORD_ID='other' WHERE " + DK + "='old1'", "OLD_SCOPE_CONTAINS_ANOTHER_RECORD"),
                          ("UPDATE D SET " + DK + "='old1' WHERE " + DK + "='new1'", "REVIEWED_ZERO_KEY_OVERLAP_CHANGED"),
                          ("DELETE FROM DB WHERE " + DK + "='old1'", "REVIEWED_OLD_OR_NEW_GRAPH_COUNTS_CHANGED")):
            with self.subTest(code=code):
                self.db.execute("SAVEPOINT boundary_test")
                self.db.execute(sql)
                with patch.dict(fn.__globals__, {"_pilot_baseline_equal": lambda *a: None}):
                    with self.assertRaisesRegex(E, code):
                        fn(None, self.names, queries)
                self.db.execute("ROLLBACK TO boundary_test")
                self.db.execute("RELEASE boundary_test")

    def test_scope_keeps_legacy_edges_visible_after_dim_replacement(self):
        queries = P["_reconcile_live_scope_queries"](self.names)
        self.assertEqual([21, 20], [len(self.db.execute(q).fetchall()) for q in queries])
        self.db.execute("DELETE FROM TD WHERE SOURCE_RECORD_ID='reviewed'")
        self.db.execute("DELETE FROM TF WHERE DEPENDENCY_TYPE='parent_of'")
        self.db.execute("INSERT INTO TD SELECT * FROM D")
        self.db.execute("INSERT INTO TF SELECT * FROM F")
        self.assertEqual([19, 18], [len(self.db.execute(q).fetchall()) for q in queries])
        self.db.execute("INSERT INTO TF VALUES ('leftover','old0','old1','oldu0','oldu1','parent_of')")
        self.assertEqual(19, len(self.db.execute(queries[1]).fetchall()))
        with self.assertRaises(E):
            P["_reconcile_integrity"](None, queries, "CONTAINS")
        self.assertEqual('otheruuid', self.db.execute("SELECT OSCAL_UUID FROM TD WHERE SOURCE_RECORD_ID='other'").fetchone()[0])


class BackupAndOrdering(unittest.TestCase):
    def test_backup_is_durable_non_replacing_and_verified_before_return(self):
        fn, events = P["_reconcile_create_backups"], []
        with patch.dict(fn.__globals__, {"_pilot_query": lambda s, q: events.append(q),
                         "_pilot_baseline_equal": lambda *a: events.append("VERIFIED")}):
            fn(None, {"DB": "OLD_DIM", "FB": "OLD_FACT"}, {"DIM": "BACKUP_DIM", "FACT": "BACKUP_FACT"})
        self.assertEqual('CREATE TABLE "BACKUP_DIM" AS SELECT * FROM OLD_DIM', events[0])
        self.assertEqual('CREATE TABLE "BACKUP_FACT" AS SELECT * FROM OLD_FACT', events[1])
        self.assertEqual("VERIFIED", events[2])

    def test_preview_and_failed_backup_never_begin_replacement(self):
        fn = P["run_ssp_one_record_reconciliation"]
        for mode in ("PREVIEW", "COMMIT"):
            calls, output = [], io.StringIO()
            def backup(*args):
                calls.append("BACKUP_ATTEMPT")
                raise RuntimeError("private storage failure")
            mocked = {
                "_pilot_contract": lambda *a: None, "_pilot_no_transaction": lambda *a: None,
                "_pilot_query": lambda *a: [], "_pilot_column_plan": lambda *a: [],
                "_pilot_selection_schema": lambda *a: None,
                "_pilot_freeze_graph": lambda *a: {"NODES": 19, "EDGES": 18, "SOURCE_RECORDS": 1},
                "_pilot_stage": lambda *a: None, "_pilot_scope_queries": lambda *a: ("SELECT D", "SELECT F"),
                "_reconcile_live_scope_queries": lambda *a: ("SELECT D", "SELECT F"),
                "_reconcile_validate_baseline": lambda *a: {}, "_reconcile_create_backups": backup,
                "_reconcile_transaction": lambda *a, **k: self.fail("Must not enter a transaction"),
            }
            with patch.dict(fn.__globals__, mocked), redirect_stdout(output):
                if mode == "PREVIEW":
                    report = fn(None, {}, {}, None, None, mode)
                    self.assertEqual([], calls)
                else:
                    with self.assertRaises(E):
                        fn(None, {}, {}, None, None, mode)
                    report = json.loads(output.getvalue())
                    self.assertEqual("DURABLE_BACKUP", report["PHASE"])
                    self.assertNotIn("private", output.getvalue())
                self.assertFalse(report["TARGET_DML_ATTEMPTED"])
                self.assertFalse(report["PERSISTED"])


if __name__ == "__main__":
    unittest.main()
