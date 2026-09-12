"""Full released Cells One, Two and Three with real CSV and a fake Snowpark transport."""
import contextlib
import copy
from decimal import Decimal
import io
from pathlib import Path
import unittest

import test_multi_model_inputs as inputs
import test_registry_release as release
from test_model_selection import cell_namespace

ROOT = Path(__file__).resolve().parents[1]
CELLS = ROOT / "notebooks/cells"
METADATA_COLUMNS = (
    "MAPPER_METADATA_VERSION", "MAPPER_ENABLED", "OPERATOR", "PARENT_INSTANCE_RULE",
    "UUID_POLICY", "EMPTY_POLICY", "LIST_INSTANCE_RULE", "PROPERTY_NAME_RULE",
    "ASSEMBLY_POLICY", "REQUIRED_MEMBERS", "DEFAULT_SINGLETON_POLICY",
    "REQUIRED_RULE_IDS", "ROLES_PATH", "PARTIES_PATH", "PARTY_TYPE",
    "PARTY_UUID_PARTS", "PARTY_UUID_SOURCE_KEY", "REPORT_TARGET_PATH",
)
GUARD_RULE = "ssp:RECOMMENDED_SECURITY_CATEGORY:43"


class NotebookFlowTests(unittest.TestCase):
    def execute(self, models, version=1):
        # Cell One executes its actual visible deployment config. Only Snowpark
        # transport symbols/session are replaced for the complete next two cells.
        namespace = cell_namespace(models)
        namespace.update(inputs.namespace())
        source = namespace["SOURCE_PROFILES"][0]
        source["MAPPING_FILE"] = str(ROOT / "Mapping/ARCHER_OSCAL_MAPPINGS.csv")
        registry = release.release_registry()
        for row in registry:
            # A collected SQL row includes nullable columns even where the
            # migration left their values null; no policy value is fabricated.
            for column in METADATA_COLUMNS:
                row.setdefault(column, None)
            if row["MAPPER_METADATA_VERSION"] is not None:
                row["MAPPER_METADATA_VERSION"] = version
        before = copy.deepcopy(registry)
        tables = {
            source["RAW_TABLE"]: [inputs.raw("100", 1)],
            namespace["CONFIG"]["ARCHER_META_VALUE_TABLE"]: [
                {"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "Low"}],
            namespace["CONFIG"]["ELEMENT_REGISTRY_TABLE"]: registry,
        }
        for lookup in source["LOOKUP_CONTRACTS"].values():
            tables[lookup["source_table"]] = [inputs.raw("component-100", "component")]
        session = inputs.Session(tables)
        namespace["session"] = session
        with contextlib.redirect_stdout(io.StringIO()):
            for filename in ("02_source_mapping_registry_inputs.py",
                             "03_canonical_mapping_contract.py"):
                path = CELLS / filename
                exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
        self.assertEqual(before, registry)
        self.assertEqual(before, namespace["REGISTRY_INPUT_ROWS"])
        self.assertTrue(all(set(METADATA_COLUMNS).issubset(row)
                            for row in namespace["REGISTRY_INPUT_ROWS"]))
        self.assertEqual(list(models), [c["config"]["OSCAL_MODEL"]
                                       for c in namespace["MAPPING_CONTEXTS"]])
        self.assertTrue(all(c["routing_report"]["STATUS"] == "READY"
                            for c in namespace["MAPPING_CONTEXTS"]))
        self.assertFalse(namespace["CONFIG"]["EXECUTE_WRITES"])
        self.assertIsNone(namespace["canonical_mapping_df"])
        self.assertEqual(151, len(namespace["MAPPING_INPUTS"]["source-one"]))
        self.assertFalse(any(event[0] == "select" and
                             event[1] == namespace["CONFIG"]["ELEMENT_REGISTRY_TABLE"]
                             for event in session.events),
                         "Registry reads must not project away the new metadata columns")
        self.assertEqual(1, sum(event == ("table", source["RAW_TABLE"])
                                for event in session.events))
        return namespace

    def test_real_csv_through_complete_notebook_flow_preserves_registry_metadata(self):
        for models in (("SSP",), ("ASSESSMENT_RESULTS",),
                       ("SSP", "ASSESSMENT_RESULTS"), ("ASSESSMENT_RESULTS", "SSP")):
            for version in (1, Decimal(1)):
                with self.subTest(models=models, version_type=type(version).__name__):
                    namespace = self.execute(models, version)
                    self.assertEqual(
                        {model: {"SSP": 47, "ASSESSMENT_RESULTS": 17}[model] for model in models},
                        {context["config"]["OSCAL_MODEL"]: len(context["mapping_rows"])
                         for context in namespace["MAPPING_CONTEXTS"]})

    def test_original_blank_path_is_retained_and_does_not_break_canonical_sorting(self):
        namespace = self.execute(("SSP",))
        original = next(row for row in namespace["MAPPING_INPUTS"]["source-one"]
                        if row["RULE_ID"] == GUARD_RULE)
        self.assertTrue(inputs.pd.isna(original["OSCAL_ELEMENT_PATH"]))
        self.assertTrue(original["RUNTIME_TARGET_PATH"])
        context = namespace["MAPPING_CONTEXTS"][0]
        actual = next(row for row in context["compiled_plan"]["mappings"]
                      if row["RULE_ID"] == GUARD_RULE)
        self.assertIsNone(actual["OSCAL_ELEMENT_PATH"],
                          "Do not fabricate original Excel provenance to repair ordering")
        self.assertEqual(original["RUNTIME_TARGET_PATH"], actual["CANONICAL_ELEMENT_PATH"])
        self.assertEqual("BLOCKED_IF_POPULATED", actual["APPROVAL_STATUS"])
        self.assertEqual("reject-populated", actual["TRANSFORM_ID"])
        self.assertFalse(context["config"]["EXECUTE_WRITES"])


if __name__ == "__main__":
    unittest.main()
