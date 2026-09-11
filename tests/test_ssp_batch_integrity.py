"""Execute batch selection and per-record integrity SQL on local relational fixtures."""
import copy
from pathlib import Path
import re
import runpy
import sqlite3
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
P = runpy.run_path(str(ROOT / "notebooks/persistence/PILOT_SSP_TEN_RECORD_BATCH_WRITE.py"))
E, DK, FK = P["PilotError"], P["SSP_PILOT_DIM_PK"], P["SSP_PILOT_FACT_PK"]


class BatchGraphIntegrity(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.create_function("EQUAL_NULL", 2, lambda a, b: a == b)
        self.db.execute("CREATE TABLE IDS(SOURCE_RECORD_ID TEXT)")
        self.db.executemany("INSERT INTO IDS VALUES (?)", [("A",), ("B",)])
        for table in ("D", "DB"):
            self.db.execute(f"CREATE TABLE {table}({DK} TEXT, OSCAL_UUID TEXT, ELEMENT_TYPE TEXT,"
                            "SOURCE_SYSTEM_NAME TEXT,SOURCE_TABLE_NAME TEXT,SOURCE_RECORD_ID TEXT)")
        for table in ("F", "FB"):
            self.db.execute(f"CREATE TABLE {table}({FK} TEXT,FK_SOURCE_ELEMENT_HASH TEXT,"
                            "FK_TARGET_ELEMENT_HASH TEXT,SOURCE_OSCAL_UUID TEXT,"
                            "TARGET_OSCAL_UUID TEXT,DEPENDENCY_TYPE TEXT)")
        for record, count in (("A", 2), ("B", 4)):
            for n in range(count):
                key = record+str(n)
                self.db.execute("INSERT INTO D VALUES (?,?,?,?,?,?)",
                                (key,"uuid"+key,"system-security-plan" if n == 0 else "props",
                                 "ARCHER",P["SSP_PILOT_SOURCE"],record))
                if n:
                    self.db.execute("INSERT INTO F VALUES (?,?,?,?,?,?)",
                                    ("e"+key,record+"0",key,"uuid"+record+"0","uuid"+key,"CONTAINS"))
        self.db.execute("INSERT INTO DB SELECT * FROM D")
        self.db.execute("INSERT INTO FB SELECT * FROM F")
        self.db.execute("UPDATE FB SET DEPENDENCY_TYPE='parent_of'")
        def query(session, sql):
            return [dict(r) for r in self.db.execute(sql).fetchall()]
        ctx = patch.dict(P["_batch_integrity"].__globals__, {"_pilot_query": query})
        ctx.start()
        self.addCleanup(ctx.stop)

    def check(self, old=False):
        return P["_batch_integrity"](None, ("SELECT * FROM DB","SELECT * FROM FB") if old else
                                     ("SELECT * FROM D","SELECT * FROM F"),"IDS",2,allow_absent=old)

    def test_variable_record_sizes_valid_old_and_new(self):
        for old in (False, True):
            result = self.check(old)
            self.assertEqual((2,6,4), tuple(result[k] for k in ("SELECTED_RECORDS","NODES","EDGES")))
            self.assertEqual(0, result["DISCONNECTED_RECORDS"])

    def test_cross_record_edge_is_rejected_even_inside_selected_union(self):
        self.db.execute("UPDATE F SET FK_SOURCE_ELEMENT_HASH='B0',SOURCE_OSCAL_UUID='uuidB0' WHERE "+FK+"='eA1'")
        with self.assertRaises(E) as caught:
            self.check()
        self.assertEqual(1,caught.exception.details["KEY_CHECKS"]["CROSS_RECORD_EDGES"])

    def test_root_per_record_and_disconnected_cycle(self):
        self.db.execute("UPDATE D SET ELEMENT_TYPE='props' WHERE "+DK+"='B0'")
        with self.assertRaises(E):
            self.check()
        self.db.execute("UPDATE D SET ELEMENT_TYPE='system-security-plan' WHERE "+DK+"='B0'")
        self.db.execute("UPDATE F SET FK_SOURCE_ELEMENT_HASH='B2',SOURCE_OSCAL_UUID='uuidB2' WHERE "+FK+"='eB1'")
        self.db.execute("UPDATE F SET FK_SOURCE_ELEMENT_HASH='B1',SOURCE_OSCAL_UUID='uuidB1' WHERE "+FK+"='eB2'")
        with self.assertRaisesRegex(E,"BATCH_DISCONNECTED_RECORD_TREE"):
            self.check()

    def test_wholly_absent_old_record_allowed_but_partial_tree_rejected(self):
        self.db.execute("DELETE FROM FB WHERE FK_SOURCE_ELEMENT_HASH='A0'")
        self.db.execute("DELETE FROM DB WHERE SOURCE_RECORD_ID='A'")
        self.check(old=True)
        self.db.execute("DELETE FROM FB WHERE "+FK+"='eB1'")
        with self.assertRaises(E):
            self.check(old=True)
        self.db.execute("DELETE FROM F WHERE FK_SOURCE_ELEMENT_HASH='A0'")
        self.db.execute("DELETE FROM D WHERE SOURCE_RECORD_ID='A'")
        with self.assertRaises(E):
            self.check()

    def test_overlap_same_owner_allowed_cross_owner_or_endpoint_rejected(self):
        fn = P["_batch_overlap_ownership"]
        names = {k:k for k in ("D","F","DB","FB")}
        fn(None,names)  # parent_of -> CONTAINS is permitted for unchanged identity.
        self.db.execute("UPDATE DB SET SOURCE_RECORD_ID='B' WHERE "+DK+"='A1'")
        with self.assertRaises(E):
            fn(None,names)
        self.db.execute("UPDATE DB SET SOURCE_RECORD_ID='A' WHERE "+DK+"='A1'")
        self.db.execute("UPDATE FB SET FK_TARGET_ELEMENT_HASH='B1' WHERE "+FK+"='eA1'")
        with self.assertRaises(E):
            fn(None,names)

    def test_old_new_scope_retains_leftover_edges_and_rejects_protected_owner(self):
        self.db.execute("UPDATE DB SET SOURCE_RECORD_ID='PROTECTED' WHERE "+DK+"='A1'")
        with self.assertRaises(E) as caught:
            self.check(old=True)
        self.assertEqual(1,caught.exception.details["KEY_CHECKS"]["INVALID_NODE_OWNERSHIP_OR_UUID"])
        queries = P["_batch_retained_scope"](("SELECT * FROM D","SELECT * FROM F"),"DB","FB")
        self.assertIn("FK_SOURCE_ELEMENT_HASH IN (SELECT "+DK+" FROM DB)",queries[1])
        self.assertIn("FK_TARGET_ELEMENT_HASH IN (SELECT "+DK+" FROM DB)",queries[1])


class BatchSelection(unittest.TestCase):
    def test_selects_next_ten_ids_and_not_protected_first(self):
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        self.addCleanup(db.close)
        db.create_function("REGEXP_LIKE",2,lambda v,p: int(re.fullmatch(p,v) is not None))
        db.create_function("TRY_PARSE_JSON",1,lambda x:x)
        db.create_function("TYPEOF",1,lambda x:"OBJECT" if x == "{}" else "NULL")
        db.execute("CREATE TABLE RAW_N(NODE_KEY TEXT,SOURCE_RECORD_ID TEXT,ELEMENT_PATH TEXT,METADATA_JSON TEXT)")
        db.execute("CREATE TABLE RAW_E(EDGE_KEY TEXT,FK_SOURCE_ELEMENT_HASH TEXT,FK_TARGET_ELEMENT_HASH TEXT)")
        for record in range(13):
            for n in (0,1):
                db.execute("INSERT INTO RAW_N VALUES (?,?,?,?)",
                           (f"{record*2+n:032x}",f"{record:03}", "system-security-plan" if n==0 else
                            "system-security-plan.metadata","{}"))
            db.execute("INSERT INTO RAW_E VALUES (?,?,?)",
                       (f"{record:032x}",f"{record*2:032x}",f"{record*2+1:032x}"))
        class Frame:
            def __init__(self,table):
                self.table,self.write=table,self
            def save_as_table(self,name,mode,table_type):
                self.saved=(mode,table_type)
                db.execute(f"CREATE TEMPORARY TABLE {name} AS SELECT * FROM {self.table}")
        def query(session,sql):
            return [dict(r) for r in db.execute(sql).fetchall()]
        names={k:k for k in ("NV","EV","PROTECTED_IDS","IDS","NR","ER")}
        fn=P["_batch_freeze"]
        with patch.dict(fn.__globals__,{"_pilot_query":query,"SSP_PILOT_ACCEPTED_COUNTS":(26,13)}):
            result=fn(None,Frame("RAW_N"),Frame("RAW_E"),names)
        self.assertEqual(10,result)
        self.assertEqual(["000"],[r[0] for r in db.execute("SELECT * FROM PROTECTED_IDS")])
        self.assertEqual([f"{n:03}" for n in range(1,11)],[r[0] for r in db.execute("SELECT * FROM IDS")])
        self.assertEqual(20,db.execute("SELECT COUNT(*) FROM NR").fetchone()[0])
        self.assertEqual(10,db.execute("SELECT COUNT(*) FROM ER").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
