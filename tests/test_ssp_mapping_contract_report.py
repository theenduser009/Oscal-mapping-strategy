import ast
import contextlib
import io
from pathlib import Path
import runpy
import unittest

from test_ssp_mapping_dispatch_contracts import _load_cell_4, _mapping_row


REPORT = (Path(__file__).parents[1] / "notebooks" / "validation"
          / "RUN_AFTER_04_ssp_mapping_contract_report.py")
SC = "system-security-plan.system-characteristics"


class MappingContractReportTests(unittest.TestCase):
    def run_report(self, rows, config=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = runpy.run_path(str(REPORT), init_globals={
                "CANONICAL_MAPPING_ROWS": rows,
                "_mapping_handler_for_row": _load_cell_4()["_mapping_handler_for_row"],
                "CONFIG": config or {"EXECUTE_WRITES": False},
                # The report must work with no session or source dataframe.
            })
        return result["mapping_contract_report_result"], output.getvalue()

    def test_reports_all_rejections_with_notes_and_no_source_values(self):
        date = _mapping_row("ATOIATO_DATE", SC, "date-authorized", "Transform")
        date.update(NOTES="Fixture notes, not an approved date contract.",
                    TRANSFORMATION_LOGIC="Fixture rule for report preservation.",
                    CURATED_JSON="must-not-print", SOURCE_RECORD_ID="must-not-print")
        other = _mapping_row("OTHER_UNAPPROVED", SC, "other", "Transform")
        accepted = _mapping_row("ACRONYM", SC, "system-name-short", "Direct")
        result, output = self.run_report([date, accepted, other])
        self.assertEqual([row["SOURCE_FIELD_NAME"] for row in result],
                         ["ATOIATO_DATE", "OTHER_UNAPPROVED"])
        self.assertEqual(result[0]["NOTES"], date["NOTES"])
        self.assertEqual(result[0]["TRANSFORMATION_LOGIC"], date["TRANSFORMATION_LOGIC"])
        self.assertEqual(result[0]["OSCAL_FIELD_NAME"], "date-authorized")
        self.assertEqual([row["CANONICAL_ROW_NUMBER"] for row in result], [1, 3])
        self.assertNotIn("must-not-print", output)
        self.assertNotIn("CURATED_JSON", output)
        self.assertIn("regardless of source data", output)

    def test_accepted_contracts_do_not_claim_live_success(self):
        row = _mapping_row("ACRONYM", SC, "system-name-short", "Direct")
        result, output = self.run_report([row])
        self.assertEqual(result, [])
        self.assertIn("Not a graph acceptance", output)

    def test_write_setting_still_requires_disabled(self):
        row = _mapping_row("ACRONYM", SC, "system-name-short", "Direct")
        with self.assertRaisesRegex(RuntimeError, "EXECUTE_WRITES"):
            self.run_report([row], {"EXECUTE_WRITES": True})

    def test_report_has_no_database_or_dataframe_actions(self):
        tree = ast.parse(REPORT.read_text(encoding="utf-8"))
        forbidden = {"session", "source_df", "collect", "sql", "table",
                     "to_pandas", "create_dataframe", "execute", "agg"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, forbidden)
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, forbidden)


if __name__ == "__main__":
    unittest.main()
