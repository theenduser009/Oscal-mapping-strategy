"""Production mapping CSV must contain runtime contract only."""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPPING = ROOT / "Mapping" / "ARCHER_OSCAL_MAPPINGS.csv"
EXPECTED_COLUMNS = [
    "SOURCE_FIELD_NAME",
    "OSCAL_MODEL",
    "OSCAL_ELEMENT_PATH",
    "EXECUTION_STATUS",
    "TRANSFORM_ID",
    "SOURCE_KEY",
    "NULL_POLICY",
    "LINEAGE_REQUIRED",
    "VALUE_SOURCE",
    "VALUE_REQUIRED",
    "ALLOWED_VALUES",
    "VALUE_MAP",
    "OTHER_REMARKS_TEMPLATE",
    "ROLE_ID",
    "ROLE_TITLE",
    "REFERENCE_TYPE",
    "LOOKUP_KEY",
    "DESCRIPTION_REQUIRED"
]
RETIRED_COLUMNS = {"MAPPING_TYPE","NOTES","RUNTIME_TARGET_PATH","RULE_ID","ORIGINAL_ROW_ID","SOURCE_DOCUMENT","SOURCE_LINE","ORIGINAL_EXCEL_ROW","EXECUTION_NOTE"}

class ProductionMappingContractTests(unittest.TestCase):
    def test_runtime_csv_is_minimal_and_explicit(self):
        with MAPPING.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        self.assertEqual(EXPECTED_COLUMNS, reader.fieldnames)
        self.assertTrue(RETIRED_COLUMNS.isdisjoint(reader.fieldnames))
        self.assertEqual(155, len(rows))
        self.assertTrue(all(row["SOURCE_FIELD_NAME"] and row["OSCAL_MODEL"] and row["SOURCE_KEY"] for row in rows))
        self.assertTrue(all(row["EXECUTION_STATUS"] in {"APPROVED","BLOCKED_IF_POPULATED","DEFERRED","EXCLUDED"} for row in rows))
        self.assertTrue(all(row["LINEAGE_REQUIRED"] in {"Y","N"} for row in rows))
        executable=[row for row in rows if row["EXECUTION_STATUS"] in {"APPROVED","BLOCKED_IF_POPULATED"}]
        self.assertTrue(all(row["OSCAL_ELEMENT_PATH"] for row in executable))
        self.assertEqual(12, sum(row["LINEAGE_REQUIRED"]=="Y" for row in rows))
        system_type=next(row for row in rows if row["SOURCE_FIELD_NAME"]=="INFORMATION_SYSTEM_TYPE")
        self.assertEqual("system-security-plan.system-characteristics.props[]", system_type["OSCAL_ELEMENT_PATH"])

if __name__=="__main__":
    unittest.main()
