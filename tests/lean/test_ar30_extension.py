"""Approved AR additions through CSV only, checked against the earlier mapper."""
import copy
import csv
import json
import runpy
import unittest

from lean_support import ROOT, build, business, namespace
from test_registry_release import mapping_rows, release_registry
import test_multi_model_graph as frozen

OBSERVATION_PATH = "assessment-results.results[].observations[]"
AR_ADDITIONS = (
    "TOTAL_PACKAGE_RESIDUAL_RISK", "ADJUSTED_TOTAL_RISK_SCORE",
    "ADJUSTED_AVERAGE_RISK_SCORE", "CURRENT_HIGHEST_DEVICE_RISK_SCORE",
    "CURRENT_AVERAGE_DEVICE_RISK_SCORE", "CURRENT_CONTROL_RISK_SCORE",
    "PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD", "PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD",
    "BASELINE_HIGHEST_DEVICE_RISK_SCORE", "BASELINE_AVERAGE_DEVICE_RISK_SCORE",
    "BASELINE_CONTROL_RISK_SCORE", "RISK_ASSESSMENT", "INITIAL_RISK_ASSESSMENT",
)


class AR30ExtensionTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.old_ns = frozen.namespace(legacy=True)
        self.old = frozen.ar_context(self.old_ns)
        self.registry = release_registry()
        self.rows = mapping_rows()
        self.context = self.compile(self.rows)

    def compile(self, rows):
        profile = copy.deepcopy(self.ns["SOURCE_PROFILES"][0])
        profile["MODEL_KEYS"] = ("ASSESSMENT_RESULTS",)
        profile["BASE_CONFIG"].update(self.old["config"])
        context = self.ns["compile_mapping_contexts"](
            {"source-one": rows}, self.registry, [profile],
            self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"], context["routing_report"])
        context["lookups"] = copy.deepcopy(self.old["lookups"])
        return context

    def test_exact_approved_scope_preserves_original_mapping_provenance(self):
        original_columns = ("SOURCE_FIELD_NAME", "OSCAL_MODEL", "OSCAL_ELEMENT_PATH",
                            "MAPPING_TYPE", "NOTES", "ORIGINAL_ROW_ID", "SOURCE_DOCUMENT",
                            "SOURCE_LINE", "ORIGINAL_EXCEL_ROW")
        with (ROOT / "tests/fixtures/mappings_pre_registry.csv").open(encoding="utf-8", newline="") as handle:
            original = list(csv.DictReader(handle))
        actual_by_id = {row["ORIGINAL_ROW_ID"]: row for row in self.rows}
        for row in original:
            self.assertEqual({key: row[key] for key in original_columns},
                             {key: actual_by_id[row["ORIGINAL_ROW_ID"]][key] for key in original_columns})
        accepted = {row["SOURCE_FIELD_NAME"] for row in self.old["mapping_rows"]}
        selected = {row["SOURCE_FIELD_NAME"] for row in self.context["mapping_rows"]}
        self.assertEqual(accepted | set(AR_ADDITIONS), selected)
        self.assertEqual(30, len(self.context["mapping_rows"]))
        additions = [row for row in self.context["mapping_rows"] if row["SOURCE_FIELD_NAME"] in AR_ADDITIONS]
        self.assertEqual({"scalar-score"}, {row["TRANSFORM_ID"] for row in additions})
        self.assertEqual({OBSERVATION_PATH}, {row["OWNER_ELEMENT_PATH"] for row in additions})
        self.assertEqual({"ar30:" + field for field in AR_ADDITIONS}, {row["RULE_ID"] for row in additions})
        deferred = {"RISK_ACCEPTANCE_RBDS", "RISK_ASSESSMENT_REPORT", "TOTAL_PACKAGE_INHERENT_RISK",
                    "FINDINGS", "AVG_SECURITY_COMPLIANCE_SCORE", "AVG_SECURITY_COMPLIANCE_REPORTING_SCORE",
                    "CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD", "CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD"}
        self.assertEqual(deferred, {row["SOURCE_FIELD_NAME"] for row in self.rows
                                   if row["SOURCE_FIELD_NAME"] in deferred and row["EXECUTION_STATUS"] == "DEFERRED"})

    def test_ar30_matches_original_oracle_and_preserves_existing_keys(self):
        oracle = runpy.run_path(str(frozen.AR), run_name="ar30_independent_oracle")
        scope = oracle["build_ar_score_batch"].__globals__
        scope["AR_ALTERNATIVE_SCORE_FIELDS"] = AR_ADDITIONS
        scope["AR_SCORE_FIELDS"] = scope["AR_ACCEPTED_SCORE_FIELDS"] + AR_ADDITIONS
        with (ROOT / "docs/transcribed_mapping_rows.csv").open(encoding="utf-8-sig", newline="") as handle:
            original_rows = list(csv.DictReader(handle))
        records = [
            {"SOURCE_RECORD_ID": "100", "CURATED_JSON": json.dumps(
                {field: index for index, field in enumerate(scope["AR_SCORE_FIELDS"])})},
            {"SOURCE_RECORD_ID": "101", "CURATED_JSON":
             '{"ADJUSTED_TOTAL_RISK_SCORE":1.000000000000000001,"CURRENT_CONTROL_RISK_SCORE":false,"PATCH_SCORE":0}'},
        ]
        helpers = {name: self.old_ns[name] for name in oracle["AR_HELPERS"]}
        helpers["resolve_archer_select_value"] = lambda value: self.old_ns["resolve_archer_select_value"](value, self.old)
        expected = oracle["build_ar_score_batch"](
            records, original_rows, [row for row in self.registry if row["OSCAL_MODEL_KEY"] == "ASSESSMENT_RESULTS"],
            self.old["config"], helpers)
        self.assertEqual("MAPPED_SCOPE_BUILT", expected["report"]["STATUS"], expected["report"])
        nodes, edges = build(self.ns, self.context, records)
        self.assertEqual(frozen.business(expected["nodes"]), business(nodes))
        self.assertEqual(frozen.business(expected["edges"]), business(edges))
        baseline = self.compile([row for row in self.rows if row["SOURCE_FIELD_NAME"] not in AR_ADDITIONS])
        old_nodes, old_edges = build(self.ns, baseline, records)
        old_keys = {row["NODE_KEY"] for row in old_nodes.rows}
        old_edge_keys = {row["EDGE_KEY"] for row in old_edges.rows}
        self.assertEqual(business(old_nodes), [row for row in business(nodes) if row["NODE_KEY"] in old_keys])
        self.assertEqual(business(old_edges), [row for row in business(edges) if row["EDGE_KEY"] in old_edge_keys])
        self.ns["_load_graph"](nodes, edges, dict(self.context["config"], EXPECTED_SOURCE_RECORDS=2))
        result = self.ns["validate_and_load_oscal"](nodes, edges, dict(self.context["config"], STORAGE_CONTRACT=None))
        self.assertEqual("MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING", result["status"])
        self.assertFalse(result["writes_executed"])

    def test_absent_values_and_parked_fields_do_not_create_observations(self):
        for value in (None, "", []):
            source = {field: value for field in AR_ADDITIONS}
            source.update(RISK_ACCEPTANCE_RBDS={"ContentId": 1}, RISK_ASSESSMENT_REPORT=[1, 2],
                          CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD=5, CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD=6)
            source["_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD"] = 7
            source["_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD"] = 8
            with self.subTest(value=value):
                nodes, edges = build(self.ns, self.context, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": source}])
                self.assertEqual((2, 1), (len(nodes.rows), len(edges.rows)))
                self.assertFalse(any(row["ELEMENT_PATH"] == OBSERVATION_PATH for row in nodes.rows))

    def test_populated_non_scalar_additions_fail_without_partial_graph(self):
        for field in AR_ADDITIONS:
            for value in ([1, 2], {"unexpected": 1}):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    build(self.ns, self.context, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {field: value}}])


if __name__ == "__main__":
    unittest.main()
