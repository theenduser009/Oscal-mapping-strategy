"""Change-boundary tests only; Snowflake SQL execution is a separate live check."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / 'docs/raw_curated_json_update_sql_checkpoint.md'
CANDIDATE = ROOT / 'sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql'
PREFLIGHT = ROOT / 'sql/matillion/READ_ONLY_raw_curated_null_preflight.sql'
REGRESSION = ROOT / 'sql/matillion/READ_ONLY_null_key_regression.sql'


class MatillionNullKeyPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = re.search(r'```sql\n([\s\S]*?)\n```', CHECKPOINT.read_text(encoding='utf-8')).group(1)
        candidate = CANDIDATE.read_text(encoding='utf-8')
        cls.candidate = candidate[candidate.index('UPDATE ${jv_raw_table_name}'):].strip()

    def test_only_aggregate_and_identity_input_are_changed(self):
        reversed_patch = self.candidate.replace(
            "OBJECT_AGG(SQL_KEY, COALESCE(TYPED_VALUE, PARSE_JSON('null'))) AS CURATED_JSON,\n"
            "                OBJECT_AGG(SQL_KEY, TYPED_VALUE) AS ID_SOURCE_JSON",
            'OBJECT_AGG(SQL_KEY, TYPED_VALUE) AS CURATED_JSON')
        for key in ('ssp_uuid', 'AUTH_PKG_TRACKING_ID', 'HRTN_ID', 'TRACKING_ID', 'CONTENT_ID'):
            self.assertEqual(1, reversed_patch.count(f'curated.ID_SOURCE_JSON:"{key}"::string'))
            reversed_patch = reversed_patch.replace(f'curated.ID_SOURCE_JSON:"{key}"::string',
                                                    f'curated.CURATED_JSON:"{key}"::string')
        reversed_patch = reversed_patch.replace('            c.CURATED_JSON,\n            c.ID_SOURCE_JSON\n',
                                                '            c.CURATED_JSON\n')
        self.assertEqual(self.original, reversed_patch)

    def test_existing_rows_not_silently_added_to_update_scope(self):
        self.assertEqual(1, self.candidate.count('r.CURATED_JSON IS NULL'))
        self.assertEqual(1, self.candidate.count('tgt.CURATED_JSON IS NULL'))
        self.assertNotRegex(self.candidate, r'(?i)SET\s+.*CURATED_JSON\s*=\s*NULL')
        self.assertNotRegex(self.candidate, r'(?i)\b(TRUNCATE|DELETE|CREATE|ALTER)\b')

    def test_internal_identity_object_is_not_persisted(self):
        assignments = self.candidate.split('SET', 1)[1].split('FROM', 1)[0]
        self.assertNotIn('ID_SOURCE_JSON', assignments)
        self.assertIn('tgt.CURATED_JSON = src.CURATED_JSON', assignments)
        self.assertIn('tgt.CONTENT_ID   = src.CONTENT_ID', assignments)
        self.assertIn('curated.REQ_OBJ_ID::string', self.candidate)

    def test_preflight_preserves_original_extraction_and_typing(self):
        original_ctes = self.original.split('        WITH norm AS (', 1)[1].split('        curated AS (', 1)[0]
        original_ctes = 'WITH norm AS (' + original_ctes
        original_ctes = re.sub(r'^ {8}', '', original_ctes, flags=re.MULTILINE).strip().rstrip(',')
        text = PREFLIGHT.read_text(encoding='utf-8')
        actual_ctes = text[text.index('WITH norm AS ('):].split(',\npreflight AS (', 1)[0].strip()
        self.assertEqual(original_ctes, actual_ctes)
        self.assertIn('GROUP BY REQ_OBJ_ID, SQL_KEY HAVING COUNT(*) > 1', text)
        self.assertIn('POPULATED_VALUES_CONVERTED_TO_SQL_NULL', text)
        self.assertIn('NO_PENDING_ROWS_NOT_A_VERIFICATION', text)

    def test_both_checks_are_select_only(self):
        for path in (PREFLIGHT, REGRESSION):
            text = re.sub(r'--[^\n]*', '', path.read_text(encoding='utf-8')).strip()
            self.assertTrue(text.startswith('WITH '))
            self.assertNotRegex(text, r'(?i)\b(UPDATE|INSERT|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|CALL)\b')
            self.assertEqual(1, text.count(';'))

    def test_synthetic_examples_cover_critical_value_shapes(self):
        text = REGRESSION.read_text(encoding='utf-8')
        for example in ('SQL_NULL', 'JSON_NULL', 'EMPTY_TEXT', 'BAD_NUMBER', 'BAD_DATE',
                        'ZERO', 'FALSE_VALUE', 'OBJECT_VALUE', 'ARRAY_VALUE'):
            self.assertIn("'" + example + "'", text)
        self.assertIn('COMPLETE_OBJECT_UNCHANGED', text)
        self.assertNotIn('${', text)


if __name__ == '__main__':
    unittest.main()
