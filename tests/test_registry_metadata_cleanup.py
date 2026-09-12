"""Static safety contract for the one-time destructive DEV registry cleanup."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "sql/registry/CLEANUP_UNUSED_OSCAL_MAPPER_METADATA_COLUMNS.sql"
TABLE = "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY"
RETAINED = {
    "OSCAL_MODEL_KEY", "NODE_PATH", "ELEMENT_TYPE", "PARENT_NODE_PATH",
    "IS_COLLECTION", "INSTANCE_KEY_RULE", "PROCESS_ORDER", "IS_ACTIVE",
    "ITEM_PATH", "OPERATOR", "UUID_POLICY", "REQUIRED_MEMBERS",
}
RETIRED = {
    "MAPPER_METADATA_VERSION", "MAPPER_ENABLED", "PARENT_INSTANCE_RULE",
    "EMPTY_POLICY", "LIST_INSTANCE_RULE", "PROPERTY_NAME_RULE",
    "ASSEMBLY_POLICY", "DEFAULT_SINGLETON_POLICY", "REQUIRED_RULE_IDS",
    "ROLES_PATH", "PARTIES_PATH", "PARTY_TYPE", "PARTY_UUID_PARTS",
    "PARTY_UUID_SOURCE_KEY", "REPORT_TARGET_PATH",
}


def declared_array(sql, variable):
    block = re.search(
        rf"{variable}\s+ARRAY\s+DEFAULT\s+PARSE_JSON\('\[(.*?)\]'\)::ARRAY",
        sql, re.S,
    )
    if not block:
        raise AssertionError(f"Missing {variable} allowlist")
    return set(re.findall(r'"([A-Z][A-Z0-9_]*)"', block.group(1)))


class RegistryMetadataCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.upper = cls.sql.upper()

    def test_allowlists_are_exact_disjoint_and_complete(self):
        self.assertEqual(declared_array(self.sql, "expected_columns"), RETAINED)
        self.assertEqual(declared_array(self.sql, "retired_columns"), RETIRED)
        self.assertFalse(RETAINED & RETIRED)
        self.assertEqual(len(RETAINED), 12)
        self.assertEqual(len(RETIRED), 15)

    def test_one_exact_restricted_drop_contains_every_retired_column(self):
        drops = re.findall(r"ALTER\s+TABLE\s+.*?\s+DROP\s+COLUMN.*?RESTRICT\s*;", self.sql, re.I | re.S)
        self.assertEqual(len(drops), 1)
        self.assertIn(TABLE, drops[0])
        self.assertIn("DROP COLUMN IF EXISTS", drops[0].upper())
        self.assertNotIn("CASCADE", drops[0].upper())
        for name in RETIRED:
            self.assertIn(f'"{name}"', drops[0])
        for name in RETAINED:
            self.assertNotIn(f'"{name}"', drops[0])

    def test_schema_and_transaction_preflight_precede_drop(self):
        drop = self.upper.index("ALTER TABLE")
        self.assertLess(self.upper.index("CURRENT_TRANSACTION()"), drop)
        self.assertLess(self.upper.index("INFORMATION_SCHEMA.TABLES"), drop)
        self.assertLess(self.upper.index("INFORMATION_SCHEMA.COLUMNS"), drop)
        self.assertIn("TABLE_TYPE = 'BASE TABLE'", self.upper[:drop])

    def test_preserved_rows_are_fingerprinted_before_and_after(self):
        drop = self.upper.index("ALTER TABLE")
        hashes = [m.start() for m in re.finditer(r"\bHASH_AGG\s*\(", self.upper)]
        self.assertEqual(len(hashes), 2)
        self.assertLess(hashes[0], drop)
        self.assertGreater(hashes[1], drop)
        for name in RETAINED:
            self.assertIn(name, self.upper[hashes[0]:drop])
            self.assertIn(name, self.upper[hashes[1]:])
        self.assertIn("BEFORE_ROWS IS DISTINCT FROM AFTER_ROWS", self.upper)
        self.assertIn("BEFORE_HASH IS DISTINCT FROM AFTER_HASH", self.upper)

    def test_postflight_requires_exact_twelve_column_schema(self):
        drop = self.upper.index("ALTER TABLE")
        post = self.upper[drop:]
        self.assertIn("ARRAY_SIZE(EXPECTED_COLUMNS)", post)
        self.assertIn("REGISTRY_UNUSED_COLUMNS_REMOVED", post)
        self.assertIn("'REMAINING_COLUMNS', ARRAY_SIZE(EXPECTED_COLUMNS)", post)

    def test_cleanup_does_not_touch_rows_or_application_tables(self):
        code = "\n".join(line for line in self.upper.splitlines()
                         if not line.lstrip().startswith("--"))
        self.assertNotRegex(code, r"\b(INSERT|UPDATE|DELETE|MERGE|TRUNCATE)\b")
        self.assertNotIn("DIM_OSCAL", code)
        self.assertNotIn("FACT_OSCAL", code)
        self.assertEqual(code.count(TABLE), 4)


if __name__ == "__main__":
    unittest.main()

