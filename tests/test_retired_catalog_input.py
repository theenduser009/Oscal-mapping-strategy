"""Retired catalog inputs fail closed; current flat mappings use the active engine."""
import ast
import copy
import csv
import json
from pathlib import Path
import unittest

import test_metadata_driven_contract as metadata
import test_multi_model_graph as graph
from test_flat_mapping_release import _registry_for_release

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "tests/fixtures/mapper_contract_pre_registry.json"
OLD_CATALOG = ROOT / "tests/fixtures/mapper_contract_pre_flat.json"
MAPPING = ROOT / "tests/fixtures/mappings_pre_registry.csv"
BUILDER = ROOT / "notebooks/cells/05_registry_graph_builder.py"
RETIRED_KEYS = ("MAPPING_RULES", "PATH_RULES", "EXCLUDED_FIELDS", "ELEMENTS", "DEFAULT_ELEMENT")
RETIRED_FUNCTIONS = ("_metadata_rule_candidates", "_metadata_rule_matches", "_apply_mapping_path_rules")


class RetiredCatalogInputTests(unittest.TestCase):
    def setUp(self):
        self.ns = metadata.namespace()

    def test_removed_catalog_dispatch_functions_are_unavailable_in_active_cells(self):
        definitions = {node.name for node in ast.parse(metadata.CELL3.read_text(encoding="utf-8")).body
                       if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        for name in RETIRED_FUNCTIONS:
            self.assertNotIn(name, definitions)
            self.assertNotIn(name, self.ns)

    def test_each_retired_contract_key_is_rejected_even_when_empty(self):
        for key in RETIRED_KEYS:
            for value in ([], [{"unreviewed": "must not run"}]):
                with self.subTest(key=key, value=value):
                    contract = metadata.model_contract()
                    contract[key] = value
                    row = metadata.mapping()
                    original = copy.deepcopy((row, contract))
                    with self.assertRaises(ValueError):
                        metadata.compile_context(self.ns, [row], contract=contract)
                    self.assertEqual(original, (row, contract))

    def test_old_release_catalog_is_rejected_before_any_graph_execution(self):
        catalog = json.loads(OLD_CATALOG.read_text(encoding="utf-8"))
        source = copy.deepcopy(catalog["SOURCES"][0])
        source["MODEL_KEYS"] = ("SSP", "ASSESSMENT_RESULTS")
        source["BASE_CONFIG"] = dict(catalog["CONFIG_DEFAULTS"], RUN_ID="retired-contract-test")
        with MAPPING.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        before = copy.deepcopy((rows, source, catalog))
        def forbidden(*args, **kwargs):
            self.fail("Retired input must stop before graph building or database access")
        self.ns["build_oscal_graph"] = forbidden
        self.ns["validate_and_load_oscal"] = forbidden
        with self.assertRaises(ValueError):
            self.ns["compile_mapping_contexts"](
                {source["SOURCE_KEY"]: rows}, _registry_for_release(catalog),
                [source], catalog["MODELS"], routing_metadata=catalog.get("ROUTING", {}))
        self.assertEqual(before, (rows, source, catalog))

    def test_explicit_approval_api_still_maps_new_fields_without_a_catalog_rule(self):
        row = metadata.mapping("NEW_APPROVED_SCORE", metadata.OBSERVATION, transform="scalar-score")
        context = metadata.compile_context(self.ns, [row])
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        self.assertEqual(1, len(context["mapping_rows"]))
        metadata.poison_legacy_classifier(self.ns)
        nodes, edges = metadata.build(self.ns, context, [
            {"SOURCE_RECORD_ID": "synthetic-record", "CURATED_JSON": {"NEW_APPROVED_SCORE": 0}},
        ])
        self.assertEqual(1, len(metadata.payloads(nodes, metadata.OBSERVATION)))
        self.assertEqual([{"name": "new-approved-score", "value": "0"}],
                         metadata.payloads(nodes, metadata.OBSERVATION)[0]["props"])
        self.assertEqual(len(nodes.rows) - 1, len(edges.rows))
        self.assertFalse(context["config"]["EXECUTE_WRITES"])

    def test_existing_flat_populated_value_guard_still_stops_graph_publication(self):
        from test_model_selection import cell_namespace
        from test_registry_release import release_registry
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        old = json.loads(OLD_CATALOG.read_text(encoding="utf-8"))
        with MAPPING.open(encoding="utf-8-sig", newline="") as handle:
            guard = next(row for row in csv.DictReader(handle)
                         if row["SOURCE_FIELD_NAME"] == "RECOMMENDED_SECURITY_CATEGORY")
        source = copy.deepcopy(catalog["SOURCES"][0])
        source["MODEL_KEYS"] = ("SSP",)
        source["BASE_CONFIG"] = dict(catalog["CONFIG_DEFAULTS"], RUN_ID="flat-guard-test")
        context = self.ns["compile_mapping_contexts"](
            {source["SOURCE_KEY"]: [guard]}, release_registry(_registry_for_release(old)),
            [source], cell_namespace(("SSP",))["MODEL_CONTRACTS"],
            routing_metadata=catalog.get("ROUTING", {}))[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        self.assertEqual("BLOCKED_IF_POPULATED", context["mapping_rows"][0]["APPROVAL_STATUS"])
        context["lookups"] = {}
        metadata.poison_legacy_classifier(self.ns)
        with self.assertRaisesRegex(ValueError, "Populated source has no reviewed transformation"):
            graph.build(self.ns, context, [{"SOURCE_RECORD_ID": "synthetic-record", "CURATED_JSON": {
                "AUTHORIZATION_PACKAGE_NAME": "Synthetic title",
                "RECOMMENDED_SECURITY_CATEGORY": "unreviewed",
            }}], graph.Frame(context["registry_rows"]))
        self.assertFalse(context["graph_report"]["OUTPUTS_PUBLISHED"])
        self.assertFalse(context["config"]["EXECUTE_WRITES"])

    def test_shared_builder_has_no_field_model_or_catalog_dispatch(self):
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {
            "SSP", "ASSESSMENT_RESULTS", "AUTHORIZATION_PACKAGE_NAME",
            "RECOMMENDED_SECURITY_CATEGORY", "VULNERABILITY_SCORE",
            "MAPPING_RULES", "PATH_RULES", "EXCLUDED_FIELDS",
        }
        strings = {node.value for node in ast.walk(tree)
                   if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertFalse(forbidden & strings)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertFalse(set(RETIRED_FUNCTIONS) & names)
        self.assertFalse({"_mapping_handler_for_row", "apply_mapping_transform",
                          "build_element_instances", "MODEL_GRAPH_POLICIES"} & names)
        self.assertNotIn("tests.fixtures", source)
        self.assertNotIn("legacy_cell3_catalog_input", source)
        self.assertNotIn("legacy_cell4_pre_declarative", source)


if __name__ == "__main__":
    unittest.main()
