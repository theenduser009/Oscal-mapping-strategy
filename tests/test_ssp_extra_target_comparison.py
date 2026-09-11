"""Read-only scope comparison SQL exercised locally; not live Snowflake execution."""
from pathlib import Path
import re
import runpy
import sqlite3
import unittest

PATH = Path(__file__).resolve().parents[1] / "notebooks/persistence/READ_ONLY_SSP_PILOT_EXTRA_TARGET_ROWS.py"
P = runpy.run_path(str(PATH))


class ExtraTargetComparison(unittest.TestCase):
    def test_invalid_and_colliding_hex_keys_stop(self):
        for keys in ([], [None], ["a" * 31], ["z" * 32], ["a" * 32, "A" * 32], ["';DROP TABLE X"]):
            with self.assertRaises(ValueError):
                P["_extra_hex_keys"](keys)

    def test_sql_only_selects_and_binds_record_id(self):
        sql = P["_extra_comparison_sql"](["a" * 32], ["b" * 32])
        self.assertEqual(1, sql.count("?"))
        self.assertTrue(sql.startswith("WITH "))
        self.assertFalse(re.search(r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|DROP|ALTER|TRUNCATE|GRANT|COMMIT|ROLLBACK)\b", sql))
        self.assertNotIn("METADATA_JSON", sql)
        self.assertIn("IN (SELECT K FROM scoped_dim)", sql)
        source = PATH.read_text(encoding="utf-8")
        self.assertNotIn("save_as_table", source)
        self.assertNotIn("create_or_replace_temp_view", source)

    def test_scope_preserves_physical_counts_and_extra_node_incident_edges(self):
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.create_function("TO_BINARY", 2, lambda s, fmt: bytes.fromhex(s))
        db.create_function("IFF", 3, lambda condition, yes, no: yes if condition else no)
        db.execute("CREATE TABLE DIM (PK_OSCAL_SSP_ELEMENT_HASH BLOB, ELEMENT_TYPE TEXT, SOURCE_SYSTEM_NAME TEXT, SOURCE_TABLE_NAME TEXT, SOURCE_RECORD_ID TEXT)")
        db.execute("CREATE TABLE FACT (PK_FACT_OSCAL_DEPENDENCY_HASH BLOB, FK_SOURCE_ELEMENT_HASH BLOB, FK_TARGET_ELEMENT_HASH BLOB, DEPENDENCY_TYPE TEXT)")
        key = lambda n: f"{n:032x}"
        binary = lambda n: bytes.fromhex(key(n))
        for n, record in ((1, "r1"), (2, "r1"), (3, "r1"), (3, "r1"), (4, "r2")):
            db.execute("INSERT INTO DIM VALUES (?, ?, 'ARCHER', 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW', ?)", (binary(n), "type" + str(n), record))
        for n, s, t, dep in ((11, 1, 2, "CONTAINS"), (12, 3, 4, "OTHER"),
                              (12, 3, 4, "OTHER"), (13, 2, 1, "RELATED"), (14, 4, 4, "UNRELATED")):
            db.execute("INSERT INTO FACT VALUES (?, ?, ?, ?)", (binary(n), binary(s), binary(t), dep))
        sql = P["_extra_comparison_sql"]([key(1), key(2)], [key(11)])
        sql = sql.replace("RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT", "DIM")
        sql = sql.replace("RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY", "FACT")
        # SQLite requires parentheses around VALUES used in a FROM clause.
        sql = re.sub(r"FROM VALUES ([^\n]+)", r"FROM (VALUES \1)", sql)
        rows = [dict(r) for r in db.execute(sql, ["r1"]).fetchall()]
        summary = {r["DETAIL"]: r["ROW_COUNT"] for r in rows if r["SECTION"] == "SUMMARY"}
        self.assertEqual(4, summary["TARGET_DIM_ROWS"])
        self.assertEqual(4, summary["TARGET_FACT_ROWS"])
        self.assertEqual((2, 1), (summary["EXTRA_DIM_ROWS"], summary["EXTRA_DIM_DISTINCT_KEYS"]))
        self.assertEqual((3, 2), (summary["EXTRA_FACT_ROWS"], summary["EXTRA_FACT_DISTINCT_KEYS"]))
        self.assertEqual(1, summary["DIM_DUPLICATE_KEY_GROUPS"])
        self.assertEqual(1, summary["FACT_DUPLICATE_KEY_GROUPS"])
        details = [r for r in rows if r["SECTION"] == "EXTRA_FACT_BY_TYPE"]
        self.assertEqual({"OTHER", "RELATED"}, {r["DETAIL"] for r in details})
        other = next(r for r in details if r["DETAIL"] == "OTHER")
        self.assertEqual((2, 0, 0), (other["ROW_COUNT"], other["SOURCE_IN_BATCH"], other["TARGET_IN_BATCH"]))
        db.close()


if __name__ == "__main__":
    unittest.main()
