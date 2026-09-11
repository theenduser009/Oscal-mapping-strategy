"""Actual helper SQL and physical-schema regressions; SQLite is not Snowflake."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy
import sqlite3
import unittest
from unittest.mock import patch
from tests.test_ssp_write_pilot_live_schema import live_description

ROOT = Path(__file__).resolve().parents[1]
P = runpy.run_path(str(ROOT / "notebooks/cells/06_validation_and_guarded_loader.py"))
G, Error = P["_load_prepare"].__globals__, P["LoadError"]


class DailySchema(unittest.TestCase):
    def test_proven_physical_storage_projection(self):
        plans = [P["_load_column_plan"](live_description(kind), kind) for kind in ("DIM", "FACT")]
        P["_load_selection_schema"](plans)
        self.assertEqual([10, 6], [len(p) for p in plans])
        self.assertEqual(4, sum(c["encoding"] == "HEX_TO_BINARY16" for p in plans for c in p))
        self.assertEqual(3, sum(c["encoding"] == "UUID_TO_COMPACT32" for p in plans for c in p))
        expressions = " ".join(c["expression"] for p in plans for c in p)
        self.assertIn("PARSE_JSON", expressions)
        self.assertNotIn("MD5", expressions)
        self.assertNotIn("SHA2", expressions)

    def test_missing_required_target_or_incompatible_type_fails(self):
        for missing in (True, False):
            rows = live_description("DIM")
            if missing:
                rows.pop(0)
            else:
                rows[0]["type"] = "BINARY(17)"
            with self.assertRaises(Error):
                P["_load_column_plan"](rows, "DIM")

    def test_preview_never_calls_transaction(self):
        candidate = dict(NODES=2, EDGES=1, DIM_DUPLICATE_KEYS=0, FACT_DUPLICATE_KEYS=0,
                         DANGLING_SOURCE_KEYS=0, DANGLING_TARGET_KEYS=0)
        context = dict(candidate=candidate, records=1, scope={},
                       changes=[dict(INSERTS=0, UPDATES=0, UNCHANGED=2),
                                dict(INSERTS=0, UPDATES=0, UNCHANGED=1)])
        with patch.dict(G, {"session": object(), "_load_prepare": lambda *a: context,
                            "_load_transaction": lambda *a: self.fail("PREVIEW attempted DML")}):
            with redirect_stdout(io.StringIO()):
                result = P["validate_and_load_oscal"](object(), object(),
                                                     dict(OSCAL_MODEL="SSP", EXECUTE_WRITES=False))
        self.assertEqual("DAILY_SSP_PREVIEW_PASSED_NO_TARGET_DML", result["status"])
        self.assertFalse(result["persisted"])
        self.assertFalse(result["target_dml_attempted"])

    def test_preflight_block_prints_counts_without_write_or_private_payload(self):
        def reject(*args):
            raise Error("OBSOLETE_TARGET_ROWS_BLOCKED", {"OBSOLETE_DIM_ROWS": 1,
                                                        "OBSOLETE_FACT_ROWS": 1})
        out = io.StringIO()
        with patch.dict(G, {"session": object(), "_load_prepare": reject}), redirect_stdout(out):
            with self.assertRaises(Error) as caught:
                P["validate_and_load_oscal"](object(), object(), dict(EXECUTE_WRITES=True))
        self.assertFalse(caught.exception.details["target_dml_attempted"])
        self.assertFalse(caught.exception.details["persisted"])
        self.assertIn("OBSOLETE_DIM_ROWS", out.getvalue())


class DailyScopeSQL(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.dk, self.fk = P["SSP_LOAD_DIM_PK"], P["SSP_LOAD_FACT_PK"]
        for table in ("TD", "D"):
            self.db.execute(f"CREATE TABLE {table}({self.dk} TEXT,SOURCE_SYSTEM_NAME TEXT,"
                            "SOURCE_TABLE_NAME TEXT,SOURCE_RECORD_ID TEXT)")
        for table in ("TF", "F"):
            self.db.execute(f"CREATE TABLE {table}({self.fk} TEXT,FK_SOURCE_ELEMENT_HASH TEXT,"
                            "FK_TARGET_ELEMENT_HASH TEXT)")
        self.db.execute("CREATE TABLE IDS(SOURCE_RECORD_ID TEXT)")
        self.db.execute("INSERT INTO IDS VALUES ('selected')")
        for table, key, record in (("D", "new", "selected"), ("TD", "old", "selected"),
                                   ("TD", "outside", "absent")):
            self.db.execute(f"INSERT INTO {table} VALUES (?,?,?,?)",
                            (key, "ARCHER", P["SSP_LOAD_SOURCE"], record))
        for row in (("old-edge", "old", "old"), ("outside-edge", "outside", "outside"),
                    ("incoming-edge", "outside", "old")):
            self.db.execute("INSERT INTO TF VALUES (?,?,?)", row)

    def scope(self):
        with patch.dict(G, {"SSP_LOAD_DIM": "TD", "SSP_LOAD_FACT": "TF"}):
            return P["_load_scope_queries"]({"D": "D", "F": "F", "IDS": "IDS"})

    def test_obsolete_and_incoming_edges_included_absent_records_preserved(self):
        dim, fact = self.scope()
        self.assertEqual(["old"], [r[0] for r in self.db.execute(dim)])
        self.assertEqual({"old-edge", "incoming-edge"}, {r[0] for r in self.db.execute(fact)})
        self.assertNotIn("OR EXISTS", fact.upper())
        self.assertNotIn("OR NOT EXISTS", fact.upper())

    def test_foreign_owned_key_collision_cannot_hide(self):
        self.db.execute("INSERT INTO TD VALUES ('new','FOREIGN','OTHER','foreign')")
        dim, _ = self.scope()
        self.assertEqual({"old", "new"}, {r[0] for r in self.db.execute(dim)})

    def test_physical_case_normalization_is_used_for_parent_context(self):
        source = (ROOT / "notebooks/cells/06_validation_and_guarded_loader.py").read_text()
        self.assertIn("LOWER(p.NODE_KEY)=LOWER(e.FK_SOURCE_ELEMENT_HASH)", source)
        self.assertIn("LOWER(c.NODE_KEY)=LOWER(e.FK_TARGET_ELEMENT_HASH)", source)

    def test_cell_six_and_seven_match_consolidated_source(self):
        combined = (ROOT / "notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py").read_text()
        for path, end in (("06_validation_and_guarded_loader.py", "# %% Cell 7 -"),
                          ("07_mapper_orchestrator.py", None)):
            source = (ROOT / "notebooks/cells" / path).read_text()
            marker = source.splitlines()[0]
            actual = marker + combined.split(marker, 1)[1]
            if end:
                actual = actual.split(end, 1)[0]
            self.assertEqual(source.rstrip(), actual.rstrip())


if __name__ == "__main__":
    unittest.main()
