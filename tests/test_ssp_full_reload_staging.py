"""Full-graph staging regressions; local fixtures, not live Snowflake proof."""
import ast
import json
from pathlib import Path
import runpy
import sqlite3
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "notebooks/persistence/RELOAD_ALL_SSP_DEV.py"
P = runpy.run_path(str(PATH))


class FullGraphFreeze(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        def try_parse(value):
            try:
                return json.dumps(json.loads(value))
            except (ValueError, TypeError):
                return None
        self.db.create_function("TRY_PARSE_JSON", 1, try_parse)
        self.db.create_function("TYPEOF", 1, lambda x: "OBJECT" if x and x.startswith("{") else "OTHER")
        self.db.execute("CREATE TABLE RAW_N(NODE_KEY TEXT,SOURCE_RECORD_ID TEXT,ELEMENT_PATH TEXT,METADATA_JSON TEXT)")
        self.db.execute("CREATE TABLE RAW_E(EDGE_KEY TEXT)")
        for record in range(13):
            for child in (0,1):
                self.db.execute("INSERT INTO RAW_N VALUES (?,?,?,?)",
                                (str(record*2+child),str(record),
                                 "system-security-plan.metadata" if child else "system-security-plan", "{}"))
            self.db.execute("INSERT INTO RAW_E VALUES (?)", (str(record),))
        self.sql = []
        def query(session, sql):
            self.sql.append(sql)
            return [dict(r) for r in self.db.execute(sql).fetchall()]
        fn = P["_reload_freeze"]
        ctx = patch.dict(fn.__globals__, {"_pilot_query":query,
                         "SSP_PILOT_ACCEPTED_COUNTS":(26,13), "SSP_RELOAD_SOURCE_RECORDS":13})
        ctx.start()
        self.addCleanup(ctx.stop)

    def freeze(self):
        db=self.db
        class Frame:
            def __init__(self,table):
                self.table,self.write=table,self
            def save_as_table(self,name,mode,table_type):
                if (mode,table_type) != ("errorifexists","temporary"):
                    raise AssertionError("Unexpected permanent materialization or overwrite")
                db.execute(f"CREATE TEMPORARY TABLE {name} AS SELECT * FROM {self.table}")
        return P["_reload_freeze"](None,Frame("RAW_N"),Frame("RAW_E"),
                                   {k:k for k in ("NV","EV","IDS")})

    def test_all_records_preserved_including_first_eleven(self):
        self.assertEqual(13,self.freeze())
        self.assertEqual({str(n) for n in range(13)}, {r[0] for r in self.db.execute("SELECT * FROM IDS")})
        self.assertEqual(26,self.db.execute("SELECT COUNT(*) FROM NV").fetchone()[0])
        self.assertEqual(13,self.db.execute("SELECT COUNT(*) FROM EV").fetchone()[0])
        self.assertFalse(any("LIMIT" in s or "PROTECTED" in s for s in self.sql))

    def test_empty_or_incomplete_graph_refused(self):
        self.db.execute("DELETE FROM RAW_N")
        with self.assertRaisesRegex(P["PilotError"],"ACCEPTED_GRAPH_COUNTS_CHANGED"):
            self.freeze()

    def test_duplicate_root_record_refused(self):
        self.db.execute("UPDATE RAW_N SET SOURCE_RECORD_ID='0' WHERE SOURCE_RECORD_ID='1'")
        with self.assertRaisesRegex(P["PilotError"],"NULL_OR_DUPLICATE_KEYS"):
            self.freeze()

    def test_missing_expected_root_refused(self):
        self.db.execute("UPDATE RAW_N SET ELEMENT_PATH='system-security-plan.metadata' WHERE NODE_KEY='0'")
        with self.assertRaisesRegex(P["PilotError"],"FULL_RELOAD_SOURCE_RECORD_COUNT_CHANGED"):
            self.freeze()

    def test_other_model_path_refused_before_target_write(self):
        self.db.execute("UPDATE RAW_N SET ELEMENT_PATH='assessment-results.results' WHERE NODE_KEY='1'")
        with self.assertRaisesRegex(P["PilotError"],"INVALID_SSP_CANDIDATE_PATH_OR_PAYLOAD"):
            self.freeze()

    def test_null_or_nonobject_payload_refused(self):
        for value in (None,"null","[]","bad-json"):
            with self.subTest(value=value):
                self.db.execute("UPDATE RAW_N SET METADATA_JSON=? WHERE NODE_KEY='1'",(value,))
                with self.assertRaisesRegex(P["PilotError"],"INVALID_SSP_CANDIDATE_PATH_OR_PAYLOAD"):
                    self.freeze()
                for table in ("NV","EV","IDS"):
                    self.db.execute(f"DROP TABLE IF EXISTS {table}")


class FullReloadSourceContract(unittest.TestCase):
    def test_scope_mode_and_physical_defaults(self):
        self.assertEqual("PREVIEW",P["SSP_RELOAD_MODE"])
        self.assertEqual((70102,67289),P["SSP_PILOT_ACCEPTED_COUNTS"])
        self.assertEqual(2813,P["SSP_RELOAD_SOURCE_RECORDS"])
        self.assertEqual('SSP_RELOAD_MODE = "PREVIEW"  # Set COMMIT for the authorized full DEV reload.',
                         PATH.read_text(encoding="utf-8").splitlines()[9])
        self.assertNotIn("_batch_freeze",P)
        self.assertNotIn("run_ssp_ten_record_batch",P)
        self.assertNotIn("SSP_BATCH_LIMIT",P)

    def test_no_incremental_filters_or_schema_ddl_in_transaction(self):
        source=PATH.read_text(encoding="utf-8")
        tree=ast.parse(source)
        tx=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_reload_transaction")
        fragment=ast.get_source_segment(source,tx)
        for forbidden in ("CREATE ","DROP ","ALTER ","SAVE_AS_TABLE","TRUNCATE TABLE IF EXISTS"):
            self.assertNotIn(forbidden,fragment.upper())
        self.assertIn('"TRUNCATE TABLE " + target',fragment)
        self.assertIn('("FACT", SSP_PILOT_FACT), ("DIM", SSP_PILOT_DIM)',fragment)

    def test_rollback_baseline_preserves_duplicate_multiplicities(self):
        captured=[]
        fn=P["_pilot_baseline_equal"]
        def query(session,sql):
            captured.append(sql)
            return [{"N":0}]
        with patch.dict(fn.__globals__,{"_pilot_query":query}):
            fn(None,{"DB":"DB","FB":"FB"},("SELECT * FROM D","SELECT * FROM F"))
        differences=[sql for sql in captured if "MINUS" in sql]
        self.assertEqual(4,len(differences))
        self.assertTrue(all(sql.count("GROUP BY ALL")==2 for sql in differences))
        self.assertTrue(all(sql.count("COUNT(*) AS SSP_RELOAD_ROW_MULTIPLICITY")==2 for sql in differences))


if __name__=="__main__":
    unittest.main()
