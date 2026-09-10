import ast
from pathlib import Path
import runpy
import unittest


REPO_ROOT = Path(__file__).parents[1]
DISCOVERY_PATH = (
    REPO_ROOT
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_component_lookup_source_discovery.py"
)


class _Row:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, name):
        return self.values[name]

    def as_dict(self, recursive=True):
        del recursive
        return dict(self.values)


def _load_helpers():
    return runpy.run_path(
        str(DISCOVERY_PATH),
        init_globals={"_LOOKUP_DISCOVERY_SKIP_EXECUTION": True},
    )


class ComponentLookupSourceDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helpers = _load_helpers()

    def test_catalog_builds_content_id_candidates_from_metadata(self):
        table_rows = [
            _Row(
                {
                    "TABLE_NAME": "COMPONENT_RAW",
                    "TABLE_TYPE": "BASE TABLE",
                    "ROW_COUNT": 20,
                }
            ),
            _Row(
                {
                    "TABLE_NAME": "DIRECT_COMPONENT",
                    "TABLE_TYPE": "VIEW",
                    "ROW_COUNT": None,
                }
            ),
            _Row(
                {
                    "TABLE_NAME": "NO_ID",
                    "TABLE_TYPE": "BASE TABLE",
                    "ROW_COUNT": 10,
                }
            ),
            _Row(
                {
                    "TABLE_NAME": "$JS_USR_TARGET_TABLE_TMP_1",
                    "TABLE_TYPE": "BASE TABLE",
                    "ROW_COUNT": 5,
                }
            ),
        ]
        column_rows = [
            _Row(
                {
                    "TABLE_NAME": "COMPONENT_RAW",
                    "COLUMN_NAME": "CONTENT_ID",
                    "DATA_TYPE": "NUMBER",
                    "ORDINAL_POSITION": 1,
                }
            ),
            _Row(
                {
                    "TABLE_NAME": "COMPONENT_RAW",
                    "COLUMN_NAME": "CURATED_JSON",
                    "DATA_TYPE": "VARIANT",
                    "ORDINAL_POSITION": 2,
                }
            ),
            _Row(
                {
                    "TABLE_NAME": "DIRECT_COMPONENT",
                    "COLUMN_NAME": "ContentId",
                    "DATA_TYPE": "VARCHAR",
                    "ORDINAL_POSITION": 1,
                }
            ),
            _Row(
                {
                    "TABLE_NAME": "DIRECT_COMPONENT",
                    "COLUMN_NAME": "TITLE",
                    "DATA_TYPE": "VARCHAR",
                    "ORDINAL_POSITION": 2,
                }
            ),
            _Row(
                {
                    "TABLE_NAME": "NO_ID",
                    "COLUMN_NAME": "CURATED_JSON",
                    "DATA_TYPE": "VARIANT",
                    "ORDINAL_POSITION": 1,
                }
            ),
            _Row(
                {
                    "TABLE_NAME": "$JS_USR_TARGET_TABLE_TMP_1",
                    "COLUMN_NAME": "CONTENT_ID",
                    "DATA_TYPE": "VARCHAR",
                    "ORDINAL_POSITION": 1,
                }
            ),
        ]
        objects = self.helpers["_lookup_catalog_objects"](
            table_rows,
            column_rows,
        )
        candidates, ambiguous = self.helpers[
            "_lookup_content_id_objects"
        ](objects)

        self.assertFalse(ambiguous)
        self.assertEqual(
            [candidate["table_name"] for candidate in candidates],
            ["COMPONENT_RAW", "DIRECT_COMPONENT"],
        )
        self.assertEqual(
            candidates[0]["key_column"]["name"],
            "CONTENT_ID",
        )

    def test_internal_and_temporary_objects_are_excluded(self):
        is_internal = self.helpers["_lookup_is_internal_object"]
        self.assertTrue(
            is_internal(
                {
                    "table_name": "_$JS_USR_TARGET_TABLE_TMP",
                    "table_type": "BASE TABLE",
                }
            )
        )
        self.assertTrue(
            is_internal(
                {
                    "table_name": "ANY_NAME",
                    "table_type": "LOCAL TEMPORARY",
                }
            )
        )
        self.assertFalse(
            is_internal(
                {
                    "table_name": "ARCHER_COMPONENT_RAW",
                    "table_type": "BASE TABLE",
                }
            )
        )

    def test_multiple_content_id_like_columns_are_ambiguous(self):
        objects = {
            "AMBIGUOUS": {
                "table_name": "AMBIGUOUS",
                "columns": [
                    {"name": "CONTENT_ID"},
                    {"name": "ContentId"},
                ],
            }
        }
        candidates, ambiguous = self.helpers[
            "_lookup_content_id_objects"
        ](objects)
        self.assertFalse(candidates)
        self.assertEqual(ambiguous, ["AMBIGUOUS"])

    def test_field_classification_excludes_technical_names(self):
        category = self.helpers["_lookup_field_category"]
        self.assertEqual(category("COMPONENT_NAME"), "title")
        self.assertEqual(category("SYSTEM_DESCRIPTION"), "description")
        self.assertEqual(category("LIFECYCLE_STATUS"), "status")
        self.assertIsNone(category("UPDATED_BY_NAME"))
        self.assertIsNone(category("DW_LOAD_STATUS"))

    def test_best_field_coverage_uses_direct_and_json_evidence(self):
        profile = {
            "direct_field_evidence": [
                {
                    "category": "title",
                    "name": "TITLE",
                    "populated_ids": 8,
                }
            ],
            "json_key_evidence": [
                {
                    "category": "title",
                    "name": "Name",
                    "nonblank_ids": 10,
                },
                {
                    "category": "status",
                    "name": "Status",
                    "nonblank_ids": 9,
                },
            ],
        }
        best = self.helpers["_lookup_best_field_coverage"]
        self.assertEqual(best(profile, "title"), 10)
        self.assertEqual(best(profile, "status"), 9)
        self.assertEqual(best(profile, "description"), 0)

    def test_runtime_state_requires_read_only_validated_ssp(self):
        validate = self.helpers["_lookup_validate_runtime_state"]
        valid_result = {
            "validation_passed": True,
            "pre_write_validation_passed": True,
            "writes_executed": False,
        }
        validate(
            {"OSCAL_MODEL": "SSP", "EXECUTE_WRITES": False},
            valid_result,
        )
        with self.assertRaisesRegex(RuntimeError, "EXECUTE_WRITES = False"):
            validate(
                {"OSCAL_MODEL": "SSP", "EXECUTE_WRITES": True},
                valid_result,
            )
        with self.assertRaisesRegex(RuntimeError, "graph validation"):
            validate(
                {"OSCAL_MODEL": "SSP", "EXECUTE_WRITES": False},
                {**valid_result, "validation_passed": False},
            )
        with self.assertRaisesRegex(RuntimeError, "read-only"):
            validate(
                {"OSCAL_MODEL": "SSP", "EXECUTE_WRITES": False},
                {**valid_result, "writes_executed": True},
            )

    def test_source_is_aggregate_only_and_contains_no_write_calls(self):
        source = DISCOVERY_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_attributes = {
            "create_dataframe",
            "create_or_replace_temp_view",
            "delete",
            "insert",
            "merge",
            "save_as_table",
            "sql",
            "update",
            "write",
        }
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(forbidden_attributes.isdisjoint(called_attributes))
        self.assertNotIn("source_df", source)
        self.assertNotIn("_parse_source_json", source)
        self.assertNotIn("component_ids_df.collect", source)
        self.assertNotIn("matched_key_rows_df.collect", source)
        self.assertIn("SOURCE-OBJECT", source)
        self.assertNotIn("SOURCE APPROVED", source)
        self.assertIn("JSUSRTARGETTABLETMP", source)
        self.assertIn("KEY_PROFILE", source)
        self.assertIn("DIRECT_FIELD_PROFILE", source)
        self.assertIn("JSON_KEY_PROFILE", source)
        self.assertIn("INCOMPLETE CATALOG SCAN", source)

    def test_identifier_and_display_helpers_are_sanitized(self):
        quote = self.helpers["_lookup_quote_identifier"]
        safe = self.helpers["_lookup_safe_name"]
        self.assertEqual(quote('A"B'), '"A""B"')
        self.assertEqual(safe("TABLE\nprivate value"), "TABLE_private_value")
        with self.assertRaisesRegex(RuntimeError, "invalid identifier"):
            quote("bad\x00name")


if __name__ == "__main__":
    unittest.main()

