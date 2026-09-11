"""Static checks for the one-step authorization-package null-name view."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FLAT = ROOT / "sql/matillion/READ_ONLY_authorization_package_null_field_names.sql"
PREVIEW = ROOT / "sql/matillion/READ_ONLY_raw_curated_values_preview.sql"
TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"


class NullFieldNameListTests(unittest.TestCase):
    def test_one_self_contained_select(self):
        sql = re.sub(r"--[^\n]*", "", FLAT.read_text(encoding="utf-8")).strip()
        self.assertTrue(sql.startswith("WITH "))
        self.assertEqual(1, sql.count(";"))
        self.assertNotIn("${", sql)
        self.assertNotIn("RESULT_SCAN", sql)
        self.assertNotIn("LAST_QUERY_ID", sql)
        self.assertNotRegex(sql, r"(?i)\b(UPDATE|INSERT|MERGE|DELETE|CREATE|ALTER|DROP|TRUNCATE|CALL|COPY|PUT|REMOVE)\b")
        self.assertEqual(1, sql.count("REPLACE_WITH_REQUESTED_OBJECT_ID"))
        self.assertIn("FROM " + TABLE + " r", sql)

    def test_original_preview_conversion_and_report_are_preserved(self):
        original = PREVIEW.read_text(encoding="utf-8")
        original = original[original.index("WITH preview_input AS ("):].strip()
        original = original.replace("${jv_raw_table_name}", TABLE)
        ctes, report = original.split("\nSELECT\n    CASE\n", 1)
        sql = FLAT.read_text(encoding="utf-8")
        sql = sql[sql.index("WITH preview_input AS ("):]
        actual_ctes, remaining = sql.split(",\npreview_document AS (\n", 1)
        self.assertEqual(ctes, actual_ctes)
        actual_report = remaining.split("\n),\nnull_fields AS (", 1)[0]
        self.assertEqual("SELECT\n    CASE\n" + report.rstrip(";"), actual_report)

    def test_only_null_names_and_unambiguous_empty_or_blocked_states(self):
        sql = FLAT.read_text(encoding="utf-8")
        self.assertIn("f.KEY::STRING AS FIELD_NAME, f.VALUE AS MAPPED_VALUE", sql)
        self.assertIn("WHERE IS_NULL_VALUE(f.VALUE)", sql)
        self.assertIn("LEFT JOIN null_fields f ON TRUE", sql)
        self.assertIn("THEN 'NO_NULL_VALUED_FIELDS_IN_PROPOSED_JSON'", sql)
        self.assertIn("WHEN p.PREVIEW_STATUS <> 'PREVIEW_READY_NOT_WRITTEN'\n            THEN p.PREVIEW_STATUS", sql)
        self.assertIn("ELSE 'NULL_VALUED_FIELD'", sql)


if __name__ == "__main__":
    unittest.main()
