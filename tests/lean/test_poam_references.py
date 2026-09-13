"""Package-scoped POA&M references; no full-schema or external-item claim."""
import copy
import hashlib
import json
import sys
import types
import unittest
import uuid
from unittest.mock import patch

from lean_support import build, business, namespace
from test_registry_release import mapping_rows, release_registry

ROOT_PATH = "plan-of-action-and-milestones"
ITEM_PATH = ROOT_PATH + ".poam-items[]"


def poam_registry():
    return [dict(OSCAL_MODEL_KEY="POAM", NODE_PATH=path, PARENT_NODE_PATH=parent,
                 ELEMENT_TYPE=element, IS_COLLECTION=collection, IS_ACTIVE=True,
                 INSTANCE_KEY_RULE="CONTENT_ID" if collection else None,
                 ITEM_PATH="$" if collection else None, PROCESS_ORDER=order,
                 OPERATOR=operator, UUID_POLICY="node", REQUIRED_MEMBERS=None)
            for order, (path, parent, element, collection, operator) in enumerate([
                (ROOT_PATH, None, ROOT_PATH, False, "object"),
                (ITEM_PATH, ROOT_PATH, "poam-items", True, "references"),
            ], 1)]


class PoamReferenceTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace(models=("POAM",))
        self.rows = mapping_rows()
        self.registry = release_registry() + poam_registry()
        self.context = self.compile()
        # Unhydrated references import Snowpark but must never query a lookup.
        functions = types.ModuleType("snowflake.snowpark.functions")
        snowpark = types.ModuleType("snowflake.snowpark")
        snowpark.functions = functions
        self.modules = {"snowflake": types.ModuleType("snowflake"),
                        "snowflake.snowpark": snowpark,
                        "snowflake.snowpark.functions": functions}

    def compile(self, rows=None, registry=None, profiles=None, contracts=None):
        context = self.ns["compile_mapping_contexts"](
            {"source-one": self.rows if rows is None else rows},
            self.registry if registry is None else registry,
            self.ns["SOURCE_PROFILES"] if profiles is None else profiles,
            self.ns["MODEL_CONTRACTS"] if contracts is None else contracts,
            self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"], context["routing_report"])
        context["lookups"] = {}
        return context

    def graph(self, records, context=None):
        with patch.dict(sys.modules, self.modules):
            return build(self.ns, context or self.context, records)

    def test_actual_csv_maps_only_approved_uuid_references(self):
        rows = self.context["mapping_rows"]
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual(("POAMS", ITEM_PATH, "direct", "APPROVED", "poam:POAMS:references"),
                         tuple(row[key] for key in ("SOURCE_FIELD_NAME", "OWNER_ELEMENT_PATH",
                               "TRANSFORM_ID", "APPROVAL_STATUS", "RULE_ID")))
        self.assertIsNone(row["REPRESENTATION_PARAMS"]["reference_type"])
        self.assertNotIn("hydrate_lookup", row["REPRESENTATION_PARAMS"])
        contract = self.context["config"]["STORAGE_CONTRACT"]
        prefix = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED."
        self.assertEqual((prefix + "DIM_OSCAL_POAM_ELEMENT", prefix + "FACT_OSCAL_POAM_DEPENDENCY",
                          "PK_DIM_OSCAL_POAM_ELEMENT_HASH", "PK_FACT_OSCAL_POAM_DEPENDENCY_HASH"),
                         tuple(contract[key] for key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN")))
        differing = {"MODEL_KEY", "ROOT_PATH", "ROOT_ELEMENT_TYPE", "TARGET_DIM", "TARGET_FACT",
                     "DIM_PK_COLUMN", "FACT_PK_COLUMN"}
        for model in ("SSP", "ASSESSMENT_RESULTS"):
            shared = self.ns["MODEL_CONTRACTS"][model]["STORAGE_CONTRACT"]
            self.assertEqual({key: value for key, value in shared.items() if key not in differing},
                             {key: value for key, value in contract.items() if key not in differing})
        self.assertEqual(("POAM", ROOT_PATH, ROOT_PATH),
                         tuple(contract[key] for key in ("MODEL_KEY", "ROOT_PATH", "ROOT_ELEMENT_TYPE")))

    def test_content_ids_build_standard_identities_and_matching_root_edges(self):
        records = [{"SOURCE_RECORD_ID": "package-a", "CURATED_JSON": {
            "POAMS": [101, "102", {"ContentId": "103", "LevelId": 99}]}},
                   {"SOURCE_RECORD_ID": "package-b", "CURATED_JSON": {"POAMS": [101]}}]
        nodes, edges = self.graph(records)
        config = self.context["config"]
        roots = {node["SOURCE_RECORD_ID"]: node for node in nodes.rows if node["ELEMENT_PATH"] == ROOT_PATH}
        items = [node for node in nodes.rows if node["ELEMENT_PATH"] == ITEM_PATH]
        self.assertEqual((6, 4), (len(nodes.rows), len(edges.rows)))
        for item in items:
            seed = "|".join((config["IDENTITY_VERSION"], config["SOURCE_SYSTEM_NAME"],
                             config["SOURCE_TABLE_NAME"], item["SOURCE_RECORD_ID"], "POAM",
                             ITEM_PATH, item["INSTANCE_KEY"]))
            self.assertEqual(hashlib.md5(seed.encode()).hexdigest(), item["NODE_KEY"])
            self.assertEqual(str(uuid.uuid5(uuid.NAMESPACE_URL, seed)), item["OSCAL_UUID"])
            self.assertEqual({"uuid": item["OSCAL_UUID"]}, json.loads(item["METADATA_JSON"]))
            edge = next(edge for edge in edges.rows if edge["FK_TARGET_ELEMENT_HASH"] == item["NODE_KEY"])
            parent = roots[item["SOURCE_RECORD_ID"]]
            self.assertEqual((parent["NODE_KEY"], parent["OSCAL_UUID"], item["OSCAL_UUID"], "CONTAINS"),
                             tuple(edge[key] for key in ("FK_SOURCE_ELEMENT_HASH", "SOURCE_OSCAL_UUID",
                                                        "TARGET_OSCAL_UUID", "DEPENDENCY_TYPE")))
        shared = [node["OSCAL_UUID"] for node in items if node["INSTANCE_KEY"] == "101"]
        self.assertEqual(2, len(set(shared)))
        self.assertEqual({"nodes": 6, "edges": 4, "source_records": 2},
                         self.ns["_load_graph"](nodes, edges, config))

    def test_duplicate_and_reordered_references_preserve_graph(self):
        first = [{"SOURCE_RECORD_ID": "package-a", "CURATED_JSON": {
            "POAMS": [101, {"ContentId": "101", "LevelId": 9}, "102"]}}]
        second = [{"SOURCE_RECORD_ID": "package-a", "CURATED_JSON": {
            "POAMS": ["102", {"ContentId": 101, "LevelId": 10}, 101]}}]
        before, after = self.graph(first), self.graph(second)
        self.assertEqual((3, 2), tuple(len(frame.rows) for frame in before))
        self.assertEqual(tuple(map(business, before)), tuple(map(business, after)))

    def test_missing_null_and_empty_references_emit_roots_only(self):
        records = [{"SOURCE_RECORD_ID": str(index), "CURATED_JSON": source}
                   for index, source in enumerate(({}, {"POAMS": None}, {"POAMS": []}))]
        nodes, edges = self.graph(records)
        self.assertEqual((3, 0), (len(nodes.rows), len(edges.rows)))
        for node in nodes.rows:
            self.assertEqual(ROOT_PATH, node["ELEMENT_PATH"])
            self.assertEqual({"uuid": node["OSCAL_UUID"]}, json.loads(node["METADATA_JSON"]))

    def test_malformed_reference_items_fail(self):
        for value in ([{}], [None], [True], [[101]], [{"LevelId": 9}],
                      [{"ContentId": []}], [{"ContentId": " "}], {"ContentIds": [101]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.graph([{"SOURCE_RECORD_ID": "package-a", "CURATED_JSON": {"POAMS": value}}])

    def test_targetless_preview_validates_and_commit_cannot_write(self):
        nodes, edges = self.graph([{"SOURCE_RECORD_ID": "package-a", "CURATED_JSON": {"POAMS": [101]}}])
        config = dict(self.context["config"], STORAGE_CONTRACT=None)
        with patch.dict(self.ns, _load_query=lambda *args: self.fail("Unexpected database query")):
            result = self.ns["validate_and_load_oscal"](nodes, edges, config)
            self.assertEqual("MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING", result["status"])
            self.assertTrue(result["validation_passed"])
            self.assertFalse(result["writes_executed"])
            self.assertFalse(result["storage_verified"])
            with self.assertRaisesRegex(self.ns["LoadError"], "STORAGE_CONTRACT_NOT_VERIFIED"):
                self.ns["validate_and_load_oscal"](nodes, edges, dict(config, EXECUTE_WRITES=True))

    def test_hydrated_reference_still_requires_type(self):
        rows = copy.deepcopy(self.rows)
        next(row for row in rows if row["SOURCE_FIELD_NAME"] == "POAMS")["LOOKUP_KEY"] = "untyped-lookup"
        context = self.ns["compile_mapping_contexts"](
            {"source-one": rows}, self.registry, self.ns["SOURCE_PROFILES"],
            self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])

    def test_old_compiled_plan_rejected_before_source_iteration(self):
        context = copy.deepcopy(self.context)
        context["compiled_plan"]["release"] = "lean-csv-registry-v1"
        class UnreadableSource:
            def to_local_iterator(self):
                raise AssertionError("Stale plan read source rows")
        config = context["config"]
        with self.assertRaisesRegex(ValueError, "matching lean Cell 3"):
            self.ns["build_oscal_graph"](UnreadableSource(), None, None, "POAM",
                config["SOURCE_SYSTEM_NAME"], config["SOURCE_TABLE_NAME"], context=context)

    def test_other_field_and_model_use_same_operator_through_metadata(self):
        model, root = "FUTURE_MODEL", "future-document"
        registry = [{**row, "OSCAL_MODEL_KEY": model,
                     "NODE_PATH": row["NODE_PATH"].replace(ROOT_PATH, root).replace("poam-items", "items"),
                     "PARENT_NODE_PATH": root if row["PARENT_NODE_PATH"] else None,
                     "ELEMENT_TYPE": "items" if row["IS_COLLECTION"] else root}
                    for row in poam_registry()]
        mapping = dict(next(row for row in self.rows if row["SOURCE_FIELD_NAME"] == "POAMS"),
                       SOURCE_FIELD_NAME="UNRELATED_REFERENCES", OSCAL_MODEL=model,
                       OSCAL_ELEMENT_PATH=root + ".items[]", RUNTIME_TARGET_PATH=root + ".items[]",
                       RULE_ID="synthetic:unrelated-references")
        profiles = [dict(self.ns["SOURCE_PROFILES"][0], MODEL_KEYS=(model,))]
        contracts = {model: dict(MODEL_KEY=model, POLICY="metadata-v1", STORAGE_CONTRACT=None)}
        context = self.compile([mapping], registry, profiles, contracts)
        nodes, edges = self.graph([{"SOURCE_RECORD_ID": "package-a", "CURATED_JSON": {
            "UNRELATED_REFERENCES": [{"ContentId": 101}]}}], context)
        self.assertEqual((2, 1), (len(nodes.rows), len(edges.rows)))
        item = next(node for node in nodes.rows if node["INSTANCE_KEY"] == "101")
        self.assertEqual(root + ".items[]", item["ELEMENT_PATH"])
        self.assertEqual({"uuid": item["OSCAL_UUID"]}, json.loads(item["METADATA_JSON"]))

    def test_unselected_poam_without_registry_does_not_block_ssp_or_ar(self):
        deployed = namespace(models=("SSP", "ASSESSMENT_RESULTS"))
        contexts = deployed["compile_mapping_contexts"](
            {"source-one": self.rows}, release_registry(), deployed["SOURCE_PROFILES"],
            deployed["MODEL_CONTRACTS"], deployed["ROUTING_METADATA"])
        self.assertEqual({"SSP": 48, "ASSESSMENT_RESULTS": 30},
                         {ctx["config"]["OSCAL_MODEL"]: len(ctx["mapping_rows"]) for ctx in contexts})
        for context in contexts:
            self.assertEqual("READY", context["routing_report"]["STATUS"], context["routing_report"])

    def test_selected_missing_collection_and_known_owner_conflict_still_block(self):
        context = self.ns["compile_mapping_contexts"](
            {"source-one": self.rows}, release_registry() + poam_registry()[:1],
            self.ns["SOURCE_PROFILES"], self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])
        self.assertIn("UNREGISTERED_COLLECTION", context["routing_report"]["REASON_COUNTS"])
        rows = copy.deepcopy(self.rows)
        row = next(row for row in rows if row["SOURCE_FIELD_NAME"] == "POAMS")
        row["RUNTIME_TARGET_PATH"] = "system-security-plan.metadata"
        context = self.ns["compile_mapping_contexts"](
            {"source-one": rows}, self.registry, self.ns["SOURCE_PROFILES"],
            self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])
        self.assertIn("MODEL_PATH_CONFLICT", context["routing_report"]["REASON_COUNTS"])


if __name__ == "__main__":
    unittest.main()
