"""Flat-artifact migration regression: frozen contracts, provenance, and graph parity.

All records are synthetic. This module never queries Snowflake or modifies fixtures.
The provenance digest was calculated from the original 147-row review JSON before
migration; it deliberately does not read that workspace-only file at test runtime.
"""
from collections import Counter
import copy
import csv
import hashlib
import json
from pathlib import Path
import runpy
import unittest

import test_metadata_driven_contract as metadata
import test_multi_model_graph as graph
from test_ssp_mapping_dispatch_contracts import EXPECTED_CIA_CONTRACTS, _mapping_row

ROOT = Path(__file__).resolve().parents[1]
# Frozen migration inputs preserve this historical release's exact 61 contracts.
# The deployed CSV/Cell One/registry path is tested in test_registry_release.py.
CSV_PATH = ROOT / "tests/fixtures/mappings_pre_registry.csv"
CATALOG_PATH = ROOT / "tests/fixtures/mapper_contract_pre_registry.json"
OLD_CATALOG_PATH = ROOT / "tests/fixtures/mapper_contract_pre_flat.json"
CONTRACT_DIGEST = "d9d3691f3e4f6781d17d79306f1cbbbf6bf01726c83f3b70e722495ac6d34bf3"
PROVENANCE_DIGEST = "dc54e527b481e35d2f438f7dbc7334bc99e73c2c9eb53ffda02767419b2b4e50"
SSP_GRAPH_DIGEST = "e483797474dab461f193225f88439fe1182f2f0f1e66eaf7968eb0f8a411a6c1"
PROVENANCE_COLUMNS = (
    "ORIGINAL_ROW_ID", "SOURCE_FIELD_NAME", "OSCAL_MODEL", "OSCAL_ELEMENT_PATH",
    "MAPPING_TYPE", "NOTES", "SOURCE_DOCUMENT", "SOURCE_LINE", "ORIGINAL_EXCEL_ROW",
)
EXECUTABLE = {"APPROVED", "BLOCKED_IF_POPULATED"}


def _digest(value, *, semantic=True):
    encoded = json.dumps(value, sort_keys=semantic, ensure_ascii=semantic,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _frozen_semantics(catalog):
    rows = []
    for model, contract in catalog["MODELS"].items():
        for rule in contract["MAPPING_RULES"]:
            owner = rule["OWNER_PATH"]
            operator = contract["ELEMENTS"].get(owner, contract.get("DEFAULT_ELEMENT", {}))["operator"]
            for field in rule["SOURCE_FIELDS"]:
                rows.append([
                    model, field, owner, operator, rule["TRANSFORM_ID"],
                    rule.get("TRANSFORM_PARAMS", {}), rule.get("REPRESENTATION_PARAMS", {}),
                    rule["APPROVAL_STATUS"], rule.get("VALUE_CONSTRAINTS", {}),
                ])
    return sorted(rows, key=lambda row: tuple(row[:3]))


def _compiled_semantics(contexts):
    return sorted([
        [ctx["config"]["OSCAL_MODEL"], row["SOURCE_FIELD_NAME"], row["OWNER_ELEMENT_PATH"],
         row["REPRESENTATION"], row["TRANSFORM_ID"], row["TRANSFORM_PARAMS"],
         row["REPRESENTATION_PARAMS"], row["APPROVAL_STATUS"], row["VALUE_CONSTRAINTS"]]
        for ctx in contexts for row in ctx["compiled_plan"]["mappings"]
    ], key=lambda row: tuple(row[:3]))


def _registry_for_release(old_catalog):
    """Synthetic hierarchy from the frozen contract, not the migrated CSV."""
    rows = []
    for model, contract in old_catalog["MODELS"].items():
        paths = set(contract["ELEMENTS"])
        paths.update(rule["OWNER_PATH"] for rule in contract["MAPPING_RULES"])
        for path in tuple(paths):
            while "." in path:
                path = path.rsplit(".", 1)[0]
                paths.add(path)
        for path in sorted(paths, key=lambda value: (value.count("."), value)):
            expected = contract["ELEMENTS"].get(path, {}).get("parameters", {}).get("registry_contract", {})
            rows.append({
                "OSCAL_MODEL_KEY": model, "NODE_PATH": path,
                "PARENT_NODE_PATH": expected.get(
                    "parent_path", path.rsplit(".", 1)[0] if "." in path else None),
                "IS_COLLECTION": expected.get("is_collection", path.endswith("[]")),
                "INSTANCE_KEY_RULE": expected.get("instance_key_rule"),
                "ITEM_PATH": expected.get("item_path"), "IS_ACTIVE": True,
                "ELEMENT_TYPE": path.rsplit(".", 1)[-1].replace("[]", ""),
                "PROCESS_ORDER": len(rows) + 1,
            })
    return rows


class FlatMappingReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            cls.header = reader.fieldnames
            cls.rows = list(reader)
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.old_catalog = json.loads(OLD_CATALOG_PATH.read_text(encoding="utf-8"))

    def setUp(self):
        self.ns = metadata.namespace()

    def compile(self, rows=None, models=("SSP", "ASSESSMENT_RESULTS"), registry=None,
                base_config=None):
        from test_model_selection import cell_namespace
        from test_registry_release import release_registry, mapping_rows, SUPPORT
        source = copy.deepcopy(self.catalog["SOURCES"][0])
        source["MODEL_KEYS"] = models
        source["BASE_CONFIG"] = copy.deepcopy(
            self.catalog["CONFIG_DEFAULTS"] if base_config is None else base_config)
        source["BASE_CONFIG"]["RUN_ID"] = "flat-migration-regression"
        artifact = copy.deepcopy(self.rows if rows is None else rows)
        registry = release_registry(_registry_for_release(self.old_catalog)
                                    if registry is None else registry)
        if base_config is not None and "SSP" in models:
            # Graph parity includes the same required values, now explicit CSV rows.
            artifact.extend(row for row in mapping_rows() if row["RULE_ID"] in SUPPORT)
        arguments = (
            {source["SOURCE_KEY"]: artifact}, registry, [source],
            copy.deepcopy(cell_namespace(models)["MODEL_CONTRACTS"]),
        )
        before = copy.deepcopy(arguments)
        result = self.ns["compile_mapping_contexts"](
            *arguments, routing_metadata=copy.deepcopy(self.catalog.get("ROUTING", {})))
        self.assertEqual(before, arguments, "Compiling must not mutate flat source metadata")
        for context in result:
            report = context["routing_report"]
            self.assertEqual("READY", report["STATUS"], report)
            self.assertEqual(0, report["BLOCKED_ROWS"], report)
            self.assertEqual(len(artifact), report["INPUT_ROWS"])
            self.assertEqual(len(artifact), sum(report[key] for key in (
                "SELECTED_ROWS", "EXCLUDED_ROWS", "DEFERRED_ROWS", "BLOCKED_ROWS")))
            self.assertEqual(report["SELECTED_ROWS"], len(context["mapping_rows"]))
            self.assertFalse(context["config"]["EXECUTE_WRITES"])
        return result

    def test_original_147_occurrences_paths_notes_and_provenance_are_unchanged(self):
        self.assertEqual(len(self.header), len(set(self.header)))
        self.assertEqual(148, len(self.rows))
        self.assertEqual([str(i) for i in range(1, 149)],
                         [row["ORIGINAL_ROW_ID"] for row in self.rows])
        original = [[row[column] for column in PROVENANCE_COLUMNS] for row in self.rows[:147]]
        self.assertEqual(PROVENANCE_DIGEST, _digest(original, semantic=False))
        self.assertEqual(146, len({row["SOURCE_FIELD_NAME"] for row in self.rows[:147]}))
        helpers = [row for row in self.rows[:147] if row["SOURCE_FIELD_NAME"] == "HELPER_ALLOCATED_CONTROLS"]
        self.assertEqual(2, len(helpers))
        self.assertNotEqual(helpers[0]["ORIGINAL_ROW_ID"], helpers[1]["ORIGINAL_ROW_ID"])
        guard = self.rows[-1]
        self.assertEqual("RECOMMENDED_SECURITY_CATEGORY", guard["SOURCE_FIELD_NAME"])
        self.assertEqual("BLOCKED_IF_POPULATED", guard["EXECUTION_STATUS"])

    def test_release_keeps_60_approved_one_guard_and_every_other_occurrence_unapproved(self):
        self.assertEqual(Counter({"APPROVED": 60, "BLOCKED_IF_POPULATED": 1,
                                  "DEFERRED": 85, "EXCLUDED": 2}),
                         Counter(row["EXECUTION_STATUS"] for row in self.rows))
        self.assertEqual({"source-one"}, {row["SOURCE_KEY"] for row in self.rows})
        for row in self.rows:
            if row["EXECUTION_STATUS"] not in EXECUTABLE:
                self.assertEqual("", row["TRANSFORM_ID"], row["SOURCE_FIELD_NAME"])
                self.assertEqual("", row["RUNTIME_TARGET_PATH"], row["SOURCE_FIELD_NAME"])

    def test_structural_catalog_has_no_duplicate_field_rule_tables_or_new_models(self):
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse({"MAPPING_RULES", "PATH_RULES", "EXCLUDED_FIELDS"} & value.keys())
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)
        inspect(self.catalog)
        self.assertEqual({"SSP", "ASSESSMENT_RESULTS"}, set(self.catalog["MODELS"]))
        self.assertEqual(["SSP", "ASSESSMENT_RESULTS"], self.catalog["SOURCES"][0]["MODEL_BINDINGS"])
        self.assertFalse(self.catalog["CONFIG_DEFAULTS"]["EXECUTE_WRITES"])
        self.assertEqual("ARCHER_OSCAL_MAPPINGS.csv", self.catalog["SOURCES"][0]["MAPPING_FILE"])
        self.assertIsNone(self.catalog["MODELS"]["ASSESSMENT_RESULTS"].get("STORAGE_CONTRACT"))

    def test_exact_61_frozen_semantic_contracts_come_from_flat_rows(self):
        frozen = _frozen_semantics(self.old_catalog)
        self.assertEqual(61, len(frozen))
        self.assertEqual(CONTRACT_DIGEST, _digest(frozen))
        contexts = self.compile()
        actual = _compiled_semantics(contexts)
        self.assertEqual(frozen, actual)
        self.assertEqual(CONTRACT_DIGEST, _digest(actual))
        self.assertEqual({"SSP": 44, "ASSESSMENT_RESULTS": 17},
                         {ctx["config"]["OSCAL_MODEL"]: len(ctx["mapping_rows"]) for ctx in contexts})
        self.assertTrue(all(row["CONTRACT_SOURCE"] != "reviewed-catalog"
                            for ctx in contexts for row in ctx["mapping_rows"]))

    def test_deferred_rows_and_ambiguous_ar_alternatives_do_not_become_executable(self):
        contexts = self.compile()
        selected = {row["ORIGINAL_ROW_ID"] for ctx in contexts for row in ctx["mapping_rows"]}
        expected = {row["ORIGINAL_ROW_ID"] for row in self.rows
                    if row["EXECUTION_STATUS"] in EXECUTABLE}
        self.assertEqual(expected, selected)
        alternatives = [row for row in self.rows if " or " in row["OSCAL_ELEMENT_PATH"]]
        self.assertEqual(18, len(alternatives))
        for row in alternatives:
            self.assertEqual("DEFERRED", row["EXECUTION_STATUS"])
            self.assertNotIn(row["ORIGINAL_ROW_ID"], selected)
        for field in ("RISK_ACCEPTANCE_RBDS", "RISK_ASSESSMENT_REPORT", "AVG_SECURITY_COMPLIANCE_SCORE",
                      "FINDINGS", "PTA_HELPER"):
            for row in self.rows:
                if row["SOURCE_FIELD_NAME"] == field:
                    self.assertNotIn(row["ORIGINAL_ROW_ID"], selected, field)

    def test_all_eleven_cia_transforms_match_frozen_behavior(self):
        contexts = self.compile()
        ssp = next(ctx for ctx in contexts if ctx["config"]["OSCAL_MODEL"] == "SSP")
        actual = {row["SOURCE_FIELD_NAME"]: row for row in ssp["mapping_rows"]
                  if row["TRANSFORM_ID"] == "security-objective"}
        self.assertEqual(set(EXPECTED_CIA_CONTRACTS), set(actual))
        self.assertEqual(11, len(actual))
        oracle = graph.namespace(legacy=True)
        lookups = {"archer_values": {"101": "Low", "102": "Moderate", "103": "High"},
                   "fips_values": {"101": "low", "102": "moderate", "103": "high"}}
        ssp["lookups"] = lookups
        values = ["Low", "Moderate", "High", {"ValuesListIds": [101]}, {"ValuesListIds": [102]},
                  {"ValuesListIds": [103]}] + sorted(oracle["REVIEWED_LEGACY_SECURITY_VALUES"])
        for field, member in EXPECTED_CIA_CONTRACTS.items():
            row = actual[field]
            self.assertEqual(member, row["REPRESENTATION_PARAMS"]["target"])
            previous = _mapping_row(field, row["OWNER_ELEMENT_PATH"], member, "Transform")
            for value in values:
                with self.subTest(field=field, value=value):
                    expected = oracle["apply_mapping_transform"](
                        previous, value, "synthetic-record", ssp)
                    self.assertEqual(expected, self.ns["_metadata_transform"](row, value, ssp))
            for value in ("unapproved-level", ["Low", "High"]):
                with self.subTest(field=field, invalid=value):
                    with self.assertRaises(ValueError):
                        self.ns["_metadata_transform"](row, value, ssp)

    def test_existing_reject_populated_guard_remains_guard_not_new_mapping(self):
        ssp = next(ctx for ctx in self.compile() if ctx["config"]["OSCAL_MODEL"] == "SSP")
        row = next(row for row in ssp["mapping_rows"]
                   if row["SOURCE_FIELD_NAME"] == "RECOMMENDED_SECURITY_CATEGORY")
        self.assertEqual("BLOCKED_IF_POPULATED", row["APPROVAL_STATUS"])
        self.assertEqual("reject-populated", row["TRANSFORM_ID"])
        self.assertIs(self.ns["SKIP_VALUE"], self.ns["_metadata_transform"](row, None, ssp))
        with self.assertRaises(ValueError):
            self.ns["_metadata_transform"](row, "new-populated-value", ssp)

    def test_flat_ssp_rows_match_independent_accepted_graph_fingerprint(self):
        old, records, registry, lookups = graph.ssp_fixture(graph.namespace(legacy=True))
        fields = {row["SOURCE_FIELD_NAME"] for row in old["mapping_rows"]}
        rows = [row for row in self.rows if row["SOURCE_FIELD_NAME"] in fields
                and row["EXECUTION_STATUS"] == "APPROVED"]
        context = self.compile(rows, ("SSP",),
                               [dict(row, OSCAL_MODEL_KEY="SSP") for row in registry.rows],
                               old["config"])[0]
        context["lookups"] = copy.deepcopy(old["lookups"])
        context["lookups"]["component_sources"] = {
            "software": graph.Frame([]), "interconnection": graph.Frame([])}
        self.ns["_build_component_hydration_lookups"] = lambda *args: lookups
        metadata.poison_legacy_classifier(self.ns)
        nodes, edges = graph.build(self.ns, context, records, registry)
        self.assertEqual((20, 19), (len(nodes.rows), len(edges.rows)))
        serialized = json.dumps([graph.business(nodes.rows), graph.business(edges.rows)], sort_keys=True)
        self.assertEqual(SSP_GRAPH_DIGEST, hashlib.sha256(serialized.encode()).hexdigest())

    def test_flat_ar17_rows_match_independent_accepted_standalone_output(self):
        oracle_ns = graph.namespace(legacy=True)
        old = graph.ar_context(oracle_ns)
        fields = tuple(row["SOURCE_FIELD_NAME"] for row in old["mapping_rows"])
        self.assertEqual(17, len(fields))
        rows = [row for row in self.rows if row["SOURCE_FIELD_NAME"] in fields
                and row["EXECUTION_STATUS"] == "APPROVED"]
        registry = graph.ar_registry()
        context = self.compile(rows, ("ASSESSMENT_RESULTS",), list(registry.rows), old["config"])[0]
        context["lookups"] = copy.deepcopy(old["lookups"])
        records = [
            {"SOURCE_RECORD_ID": "100", "CURATED_JSON": json.dumps(
                {field: index + 1 for index, field in enumerate(fields)})},
            {"SOURCE_RECORD_ID": "101", "CURATED_JSON":
             '{"VULNERABILITY_SCORE":1.000000000000000001,"PATCH_SCORE":0,"RISK_SCORE_GRADE":"A"}'},
        ]
        oracle = runpy.run_path(str(graph.AR), run_name="flat_migration_oracle")
        oracle_globals = oracle["build_ar_score_batch"].__globals__
        oracle_globals["AR_SCORE_FIELDS"] = oracle_globals["AR_ACCEPTED_SCORE_FIELDS"]
        oracle_globals["AR_ALTERNATIVE_SCORE_FIELDS"] = ()
        helpers = {name: oracle_ns[name] for name in oracle["AR_HELPERS"]}
        helpers["resolve_archer_select_value"] = lambda value: oracle_ns["resolve_archer_select_value"](value, old)
        expected = oracle["build_ar_score_batch"](
            records, old["mapping_rows"], registry.collect(), old["config"], helpers)
        self.assertTrue(expected["report"]["OUTPUTS_PUBLISHED"])
        metadata.poison_legacy_classifier(self.ns)
        nodes, edges = graph.build(self.ns, context, records, registry)
        self.assertEqual(graph.business(expected["nodes"]), graph.business(nodes.rows))
        self.assertEqual(graph.business(expected["edges"]), graph.business(edges.rows))
        self.assertEqual(expected["report"]["FIELDS"], context["graph_report"]["FIELDS"])


if __name__ == "__main__":
    unittest.main()
