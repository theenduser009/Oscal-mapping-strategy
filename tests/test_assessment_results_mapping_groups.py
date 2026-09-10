import pathlib
import runpy
import unittest


CELL = pathlib.Path(__file__).resolve().parents[1] / "notebooks/validation/READ_ONCE_assessment_results_mapping_groups.py"
CODE = runpy.run_path(str(CELL))


class Frame:
    def __init__(self, rows):
        self.rows = rows
        self.columns = list(rows[0])

    def to_dict(self, orient):
        assert orient == "records"
        return self.rows


def row(field, **changes):
    result = {
        "ARCHER_FIELD_NAME": field, "OSCAL_MODEL": "Assessment Results",
        "OSCAL_ELEMENT_PATH": "assessment-results.results[].observations[]",
        "MAPPING_TYPE": "Extension Property", "NOTES": "map as observation or property",
        "SOURCE_RECORD_ID": "not-exported", "CURATED_JSON": "not-exported",
    }
    result.update(changes)
    return result


class AssessmentMappingGroupTests(unittest.TestCase):
    def group(self, rows):
        return CODE["group_assessment_mapping_metadata"](Frame(rows))

    def test_equal_contracts_group_without_merging_values(self):
        report = self.group([row("PATCH_SCORE"), row("VULNERABILITY_SCORE")])
        self.assertEqual((report["MAPPING_ROWS"], report["GROUP_COUNT"]), (2, 1))
        self.assertEqual(report["GROUPS"][0]["SOURCE_FIELDS"], ["PATCH_SCORE", "VULNERABILITY_SCORE"])
        self.assertNotIn("not-exported", str(report))

    def test_different_notes_type_and_path_stay_separate(self):
        report = self.group([row("A"), row("B", NOTES="different"),
                             row("C", MAPPING_TYPE="Reference"),
                             row("D", OSCAL_ELEMENT_PATH="assessment-results.results[].props[]")])
        self.assertEqual(report["GROUP_COUNT"], 4)

    def test_blank_path_and_model_conflict_remain_visible(self):
        report = self.group([row("A", OSCAL_ELEMENT_PATH=""), row("B", OSCAL_MODEL="SSP"),
                             row("C", OSCAL_MODEL="SSP", OSCAL_ELEMENT_PATH="system-security-plan.metadata")])
        self.assertEqual(report["MAPPING_ROWS"], 2)
        self.assertTrue(any(not g["TARGET_PATH_MATCHES"] for g in report["GROUPS"]))
        self.assertTrue(any(not g["MODEL_LABEL_MATCHES"] for g in report["GROUPS"]))

    def test_duplicates_retained_and_input_unchanged(self):
        rows = [row("A"), row("A")]
        before = repr(rows)
        report = self.group(rows)
        self.assertEqual(report["GROUPS"][0]["SOURCE_FIELDS"], ["A", "A"])
        self.assertEqual(repr(rows), before)

    def test_alternative_paths_remain_literal_and_are_not_single_targets(self):
        paths = [
            "assessment-results.results[].observations[] or props[]",
            "assessment-results.results[].observations[] or assessment-results.results[].props[]",
            "assessment-results.results[].observations[]/props[]",
        ]
        for path in paths:
            with self.subTest(path=path):
                report = self.group([row("SCORE", OSCAL_ELEMENT_PATH=path)])
                group = report["GROUPS"][0]
                self.assertEqual(group["OSCAL_ELEMENT_PATH"], path)
                self.assertTrue(group["TARGET_PATH_MATCHES"])
                self.assertFalse(group["SYNTACTICALLY_SINGLE_TARGET_PATH"])

    def test_single_target_syntax_does_not_rewrite_raw_path(self):
        paths = [
            "assessment-results",
            "assessment-results.results[].observations[]",
            "assessment-results.results[].observations[].props[]",
            " assessment-results.results[].props[] ",
        ]
        for path in paths:
            with self.subTest(path=path):
                group = self.group([row("SCORE", OSCAL_ELEMENT_PATH=path)])["GROUPS"][0]
                self.assertEqual(group["OSCAL_ELEMENT_PATH"], path)
                self.assertTrue(group["SYNTACTICALLY_SINGLE_TARGET_PATH"])
        blank = self.group([row("SCORE", OSCAL_ELEMENT_PATH="")])["GROUPS"][0]
        self.assertFalse(blank["SYNTACTICALLY_SINGLE_TARGET_PATH"])

    def test_extension_properties_label_is_preserved_and_not_merged(self):
        report = self.group([
            row("SCORE", MAPPING_TYPE="Extension Properties"),
            row("SCORE", MAPPING_TYPE="Extension Properties"),
            row("SCORE", MAPPING_TYPE="Extension Property"),
        ])
        self.assertEqual((report["MAPPING_ROWS"], report["GROUP_COUNT"]), (3, 2))
        groups = {g["MAPPING_TYPE"]: g for g in report["GROUPS"]}
        self.assertEqual(groups["Extension Properties"]["SOURCE_FIELDS"], ["SCORE", "SCORE"])
        self.assertEqual(groups["Extension Properties"]["MAPPING_ROW_COUNT"], 2)
        self.assertEqual(groups["Extension Property"]["MAPPING_ROW_COUNT"], 1)
        workflow = self.group([row(
            "WORKFLOW_STATUS", OSCAL_MODEL="Extension Properties",
            OSCAL_ELEMENT_PATH="assessment-results.results[].props[]",
        )])["GROUPS"][0]
        self.assertEqual(workflow["OSCAL_MODEL"], "Extension Properties")
        self.assertFalse(workflow["MODEL_LABEL_MATCHES"])
        self.assertTrue(workflow["TARGET_PATH_MATCHES"])
        self.assertTrue(workflow["SYNTACTICALLY_SINGLE_TARGET_PATH"])

    def test_missing_notes_reported_and_alias_collision_rejected(self):
        missing = row("A")
        del missing["NOTES"]
        self.assertIn("NOTES", self.group([missing])["OPTIONAL_COLUMNS_ABSENT"])
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.group([row("A", SOURCE_FIELD_NAME="B")])

    def test_registry_read_only_includes_singletons_and_inactive(self):
        sql = CODE["AR_REGISTRY_READ_SQL"].upper()
        self.assertTrue(sql.lstrip().startswith("SELECT"))
        where = sql.split("WHERE", 1)[1]
        self.assertNotIn("IS_COLLECTION", where)
        self.assertNotIn("IS_ACTIVE", where)
        class RegistryRow:
            def as_dict(self, recursive):
                return {"NODE_PATH": "assessment-results", "IS_ACTIVE": False}
        class Session:
            def sql(self, query):
                self.query = query
                return self
            def collect(self):
                return [RegistryRow()]
        session = Session()
        result = CODE["read_assessment_mapping_contract"](Frame([row("A")]), session)
        self.assertFalse(result["WRITES_EXECUTED"])
        self.assertFalse(result["MAPPING_COMPLETION_CLAIM"])
        self.assertEqual(result["REGISTRY_ROW_COUNT"], 1)


if __name__ == "__main__":
    unittest.main()
