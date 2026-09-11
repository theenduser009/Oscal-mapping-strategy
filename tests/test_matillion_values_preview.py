"""Static contract checks: Snowflake runtime execution remains a live check."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "sql/matillion/READ_ONLY_raw_curated_values_preview.sql"
CANDIDATE = ROOT / "sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql"


class MatillionValuesPreviewTests(unittest.TestCase):
    def test_select_only_single_statement(self):
        sql = re.sub(r"--[^\n]*", "", PREVIEW.read_text(encoding="utf-8")).strip()
        self.assertTrue(sql.startswith("WITH "))
        self.assertNotRegex(sql, r"(?i)\b(UPDATE|INSERT|MERGE|DELETE|CREATE|ALTER|DROP|TRUNCATE|CALL|COPY|PUT|REMOVE)\b")
        self.assertEqual(1, sql.count(";"))

    def test_extraction_typing_and_key_precedence_match_candidate(self):
        candidate = CANDIDATE.read_text(encoding="utf-8")
        original = candidate.split("        flat AS (", 1)[1].split("        curated AS (", 1)[0]
        expected = "flat AS (" + re.sub(r"^ {8}", "", original, flags=re.MULTILINE)
        preview = PREVIEW.read_text(encoding="utf-8")
        actual = "flat AS (" + preview.split("\nflat AS (", 1)[1].split("preview_key_check AS (", 1)[0]
        self.assertEqual(expected, actual)

    def test_one_record_and_no_arbitrary_dedupe(self):
        sql = PREVIEW.read_text(encoding="utf-8")
        self.assertIn("'REPLACE_WITH_REQUESTED_OBJECT_ID' AS REQUESTED_OBJECT_ID", sql)
        self.assertIn(':"RequestedObject":"Id"::STRING =', sql)
        self.assertIn("WHERE (SELECT MATCHING_RAW_ROWS FROM preview_source_count) = 1", sql)
        self.assertIn("GROUP BY REQ_OBJ_ID, SQL_KEY\n            HAVING COUNT(*) > 1", sql)
        self.assertIn("WHERE k.INVALID_KEY_ROWS = 0\n      AND k.DUPLICATE_KEY_GROUPS = 0", sql)
        source = sql.split("preview_source AS (", 1)[1].split("preview_source_count AS (", 1)[0]
        self.assertNotIn("CURATED_JSON IS NULL", source)
        for status in ("INPUT_REQUIRED", "NO_MATCHING_RAW_RECORD",
                       "BLOCKED_MULTIPLE_RAW_ROWS_FOR_ID", "BLOCKED_DUPLICATE_FIELD_NAMES",
                       "NO_FIELDS_EXTRACTED_NOT_A_PASS"):
            self.assertIn(status, sql)

    def test_actual_values_and_preserved_identity_inputs_are_visible(self):
        sql = PREVIEW.read_text(encoding="utf-8")
        for output in ("RAW_FIELD_CONTENTS", "CURRENT_CURATED_JSON", "PROPOSED_CURATED_JSON",
                       "CURRENT_CONTENT_ID", "PROPOSED_CONTENT_ID", "CURRENT_KEY_COUNT",
                       "PROPOSED_KEY_COUNT", "CONTENT_ID_MATCHES_STORED"):
            self.assertIn(output, sql)
        self.assertIn("OBJECT_AGG(c.SQL_KEY, c.TYPED_VALUE) AS ID_SOURCE_JSON", sql)
        fallback = sql.split("preview_result AS (", 1)[1].split("FROM preview_json", 1)[0]
        previous = -1
        for key in ("ssp_uuid", "AUTH_PKG_TRACKING_ID", "HRTN_ID", "TRACKING_ID", "CONTENT_ID"):
            position = fallback.index('ID_SOURCE_JSON:"' + key + '"::string')
            self.assertGreater(position, previous)
            previous = position
        self.assertIn("REQ_OBJ_ID::string", fallback)

    def test_editable_id_occurs_once_and_ready_needs_a_candidate(self):
        sql = re.sub(r"--[^\n]*", "", PREVIEW.read_text(encoding="utf-8"))
        self.assertEqual(1, sql.count("REPLACE_WITH_REQUESTED_OBJECT_ID"))
        self.assertIn("NOT REGEXP_LIKE(i.REQUESTED_OBJECT_ID, '^[0-9]+$')", sql)
        self.assertIn("LEFT JOIN preview_result c ON sc.MATCHING_RAW_ROWS = 1", sql)
        self.assertIn("WHEN c.REQ_OBJ_ID IS NULL THEN 'NO_PROPOSED_JSON_NOT_A_PASS'", sql)


if __name__ == "__main__":
    unittest.main()
