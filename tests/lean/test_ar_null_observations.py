"""Preserve explicit source nulls in AR warehouse properties, not missing keys."""
import copy
import json
import unittest

from lean_support import build, business, namespace
from test_registry_release import mapping_rows, release_registry


class ARNullObservationTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace(models=("ASSESSMENT_RESULTS",))
        self.context = self.compile()[0]
        self.context["lookups"] = {"archer_values": {}}

    def compile(self, models=None):
        return self.ns["compile_mapping_contexts"](
            {"source-one": mapping_rows()}, release_registry(), self.ns["SOURCE_PROFILES"],
            models or self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])

    def graph(self, source, context=None):
        return build(self.ns, context or self.context,
                     [{"SOURCE_RECORD_ID": "synthetic-null", "CURATED_JSON": source}])

    def test_explicit_null_is_preserved_for_objects_and_json_text(self):
        source = {"INITIAL_RISK_ASSESSMENT": None}
        for raw in (source, json.dumps(source)):
            with self.subTest(raw_type=type(raw).__name__):
                nodes, edges = self.graph(raw)
                self.assertEqual((3, 2), (len(nodes.rows), len(edges.rows)))
                observation = next(row for row in nodes.rows if row["ELEMENT_TYPE"] == "observations")
                self.assertEqual({"uuid": observation["OSCAL_UUID"], "props": [
                    {"name": "initial-risk-assessment", "value": None}]},
                    json.loads(observation["METADATA_JSON"]))
                self.ns["_load_graph"](nodes, edges, self.context["config"])

    def test_missing_keys_and_other_empty_values_do_not_become_nulls(self):
        for source in ({}, {"initial_risk_assessment": 1},
                       *({"INITIAL_RISK_ASSESSMENT": value} for value in ("", [], {}))):
            with self.subTest(source=source):
                nodes, edges = self.graph(source)
                self.assertEqual((2, 1), (len(nodes.rows), len(edges.rows)))

    def test_all_approved_nulls_preserve_identity_when_values_arrive(self):
        fields = [row["SOURCE_FIELD_NAME"] for row in self.context["mapping_rows"]]
        self.assertEqual(32, len(fields))
        source = dict.fromkeys(fields)
        source["TOTAL_PACKAGE_INHERENT_RISK"] = None
        null_nodes, null_edges = self.graph(source)
        self.assertEqual((34, 33), (len(null_nodes.rows), len(null_edges.rows)))
        observations = [row for row in null_nodes.rows if row["ELEMENT_TYPE"] == "observations"]
        self.assertEqual(set(fields), {row["INSTANCE_KEY"] for row in observations})
        self.assertTrue(all(json.loads(row["METADATA_JSON"])["props"][0]["value"] is None
                            for row in observations))
        score_nodes, score_edges = self.graph({field: index for index, field in enumerate(fields)})
        self.assertEqual({row["NODE_KEY"]: row["OSCAL_UUID"] for row in null_nodes.rows},
                         {row["NODE_KEY"]: row["OSCAL_UUID"] for row in score_nodes.rows})
        self.assertEqual(business(null_edges), business(score_edges))
        self.assertEqual("0", json.loads(next(row for row in score_nodes.rows
                         if row["INSTANCE_KEY"] == fields[0])["METADATA_JSON"])["props"][0]["value"])

    def test_option_defaults_to_skip_and_other_models_do_not_enable_it(self):
        context = copy.deepcopy(self.context)
        context["compiled_plan"]["options"].pop("preserve_null_observations")
        nodes, edges = self.graph({"INITIAL_RISK_ASSESSMENT": None}, context)
        self.assertEqual((2, 1), (len(nodes.rows), len(edges.rows)))
        for model in ("SSP", "POAM"):
            self.assertNotIn("preserve_null_observations", self.ns["MODEL_CONTRACTS"][model]["RUNTIME_OPTIONS"])

    def test_invalid_populated_values_still_block(self):
        for value in ([None], [1, 2], {"unexpected": 1}, " "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.graph({"INITIAL_RISK_ASSESSMENT": value})

    def test_non_boolean_option_and_previous_cached_plan_reject(self):
        models = copy.deepcopy(self.ns["MODEL_CONTRACTS"])
        models["ASSESSMENT_RESULTS"]["RUNTIME_OPTIONS"]["preserve_null_observations"] = "false"
        self.assertEqual("BLOCKED", self.compile(models)[0]["routing_report"]["STATUS"])
        context = copy.deepcopy(self.context)
        context["compiled_plan"]["release"] = "lean-csv-registry-v2"
        with self.assertRaisesRegex(ValueError, "matching lean Cell 3"):
            self.graph({"INITIAL_RISK_ASSESSMENT": None}, context)

    def test_path_resolver_distinguishes_missing_from_explicit_nested_null(self):
        resolve, missing = self.ns["resolve_json_path"], object()
        source = {"nested": {"score": None}, "items": [{"score": None}], "literal.score": None}
        for path in ("nested.score", "items.0.score", "literal.score"):
            self.assertIsNone(resolve(source, path, default=missing))
        for path in ("nested.unknown", "items.1.score", "nested.score.child"):
            self.assertIs(missing, resolve(source, path, default=missing))
            self.assertIsNone(resolve(source, path))


if __name__ == "__main__":
    unittest.main()
