"""Metadata-to-graph acceptance tests with synthetic records and no database I/O."""
import ast
import contextlib
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import unittest

import test_multi_model_graph as legacy_graph


ROOT = Path(__file__).resolve().parents[1]
CELL3 = ROOT / "notebooks/cells/03_canonical_mapping_contract.py"
STRUCTURAL_CATALOG = ROOT / "tests/fixtures/mapper_contract_pre_registry.json"
FLAT_MAPPING = ROOT / "tests/fixtures/mappings_pre_registry.csv"
MODEL = "SYNTHETIC_THIRD_MODEL"
ROOT_PATH = "synthetic-model"
RESULT = ROOT_PATH + ".results[]"
OBSERVATION = RESULT + ".observations[]"
SUMMARY = ROOT_PATH + ".summary"


def namespace():
    ns = legacy_graph.namespace()
    ns.update(copy=copy)
    tree = ast.parse(CELL3.read_text(encoding="utf-8"))
    body = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            body.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                continue
            body.append(node)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(ast.Module(body=body, type_ignores=[]), str(CELL3), "exec"), ns)
    return ns


def profile(source="source-one", table="SYNTHETIC_SOURCE"):
    return {
        "SOURCE_KEY": source, "SOURCE_SYSTEM_NAME": "ARCHER",
        "SOURCE_TABLE_NAME": table, "RAW_TABLE": "TEST_RAW.DEV." + table,
        "MAPPING_FILE": source + ".csv", "MODEL_KEYS": (MODEL,),
        "BASE_CONFIG": {"IDENTITY_VERSION": "v1_registry_path_instance",
                        "RUN_ID": "metadata-unit-test", "EXECUTE_WRITES": False},
    }


def model_contract():
    return {
        "MODEL_KEY": MODEL, "POLICY": "metadata-v1",
        "STORAGE_CONTRACT": None,
    }


def registry_rows():
    return [{
        "OSCAL_MODEL_KEY": MODEL, "NODE_PATH": path, "PARENT_NODE_PATH": parent,
        "ELEMENT_TYPE": kind, "IS_COLLECTION": path.endswith("[]"), "IS_ACTIVE": True,
        "INSTANCE_KEY_RULE": rule, "ITEM_PATH": None, "PROCESS_ORDER": index,
        "OPERATOR": {ROOT_PATH: "object", SUMMARY: "object", RESULT: "record", OBSERVATION: "observations"}[path],
        "UUID_POLICY": "omit" if path == SUMMARY else "node", "REQUIRED_MEMBERS": None,
    } for index, (path, parent, kind, rule) in enumerate((
        (ROOT_PATH, None, "synthetic-document", None),
        (SUMMARY, ROOT_PATH, "summary", None),
        (RESULT, ROOT_PATH, "result", "SOURCE_RECORD_ID"),
        (OBSERVATION, RESULT, "observation", "SOURCE_FIELD_NAME"),
    ), 1)]


def mapping(field="NEVER_SEEN_SOURCE_FIELD", path=SUMMARY + ".title",
            transform="text", source="source-one", **extra):
    row = {
        "SOURCE_KEY": source, "SOURCE_FIELD_NAME": field, "OSCAL_MODEL": MODEL,
        "OSCAL_ELEMENT_PATH": path, "MAPPING_TYPE": "Direct",
        "NOTES": "Approved mapping from a synthetic metadata fixture",
        "EXECUTION_STATUS": "APPROVED", "TRANSFORM_ID": transform,
        "RUNTIME_TARGET_PATH": path, "RULE_ID": "synthetic:" + str(field) + ":" + str(path),
    }
    row.update(extra)
    return row


def compile_context(ns, rows, source="source-one", table="SYNTHETIC_SOURCE",
                    contract=None, registry=None):
    return ns["compile_mapping_contexts"](
        {source: rows}, registry_rows() if registry is None else registry,
        [profile(source, table)],
        {MODEL: model_contract() if contract is None else contract},
    )[0]


def poison_legacy_classifier(ns):
    def reject(*args, **kwargs):
        raise AssertionError("Metadata execution must not invoke source-name classification")
    ns["_mapping_handler_for_row"] = reject
    ns["_score_mapping_contract"] = reject


def build(ns, context, records):
    return legacy_graph.build(
        ns, context, records, legacy_graph.Frame(context["registry_rows"]))


def payloads(nodes, path):
    return [json.loads(row["METADATA_JSON"]) for row in nodes.rows
            if row["ELEMENT_PATH"] == path]


class MetadataDrivenContractTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()

    def assert_ready(self, context):
        self.assertEqual(context["routing_report"]["STATUS"], "READY")
        self.assertEqual(context["routing_report"]["BLOCKED_ROWS"], 0)
        self.assertFalse(context["config"]["EXECUTE_WRITES"])
        self.assertEqual(context["compiled_plan"]["version"], 1)

    def assert_blocked(self, row):
        original = copy.deepcopy(row)
        try:
            context = compile_context(self.ns, [row])
        except ValueError:
            self.assertEqual(row, original)
            return
        self.assertEqual(context["routing_report"]["STATUS"], "BLOCKED")
        self.assertGreater(context["routing_report"]["BLOCKED_ROWS"], 0)
        self.assertEqual(context["routing_report"]["SELECTED_ROWS"], 0)
        self.assertEqual(context["mapping_rows"], [])
        self.assertFalse(context["config"]["EXECUTE_WRITES"])
        self.assertEqual(row, original)

    def test_new_source_field_uses_metadata_without_source_name_classifier(self):
        context = compile_context(self.ns, [mapping()])
        self.assert_ready(context)
        poison_legacy_classifier(self.ns)
        nodes, _ = build(self.ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"NEVER_SEEN_SOURCE_FIELD": "Metadata chooses this value"},
        }])
        self.assertEqual(payloads(nodes, SUMMARY), [{"title": "Metadata chooses this value"}])

    def test_metadata_alone_changes_source_binding_target_member_and_value(self):
        records = [{"SOURCE_RECORD_ID": "record-one", "CURATED_JSON": {
            "NEVER_SEEN_SOURCE_FIELD": "first", "ANOTHER_NEW_FIELD": "second"}}]
        poison_legacy_classifier(self.ns)
        first = compile_context(self.ns, [mapping()])
        second = compile_context(self.ns, [mapping("ANOTHER_NEW_FIELD", SUMMARY + ".description")])
        first_nodes, _ = build(self.ns, first, records)
        second_nodes, _ = build(self.ns, second, records)
        self.assertEqual(payloads(first_nodes, SUMMARY), [{"title": "first"}])
        self.assertEqual(payloads(second_nodes, SUMMARY), [{"description": "second"}])
        first_key = next(n["NODE_KEY"] for n in first_nodes.rows if n["ELEMENT_PATH"] == SUMMARY)
        second_key = next(n["NODE_KEY"] for n in second_nodes.rows if n["ELEMENT_PATH"] == SUMMARY)
        self.assertEqual(first_key, second_key)

    def test_third_model_nested_collections_use_same_graph_loop(self):
        rows = [mapping(field, OBSERVATION, "scalar-score", MAPPING_TYPE="Extension Property")
                for field in ("NEW_SCORE_A", "NEW_SCORE_B")]
        context = compile_context(self.ns, rows)
        self.assert_ready(context)
        poison_legacy_classifier(self.ns)
        nodes, edges = build(self.ns, context, [
            {"SOURCE_RECORD_ID": "record-one", "CURATED_JSON": {"NEW_SCORE_A": 3, "NEW_SCORE_B": 0}},
            {"SOURCE_RECORD_ID": "record-two", "CURATED_JSON": {"NEW_SCORE_A": 8, "NEW_SCORE_B": False}},
        ])
        self.assertEqual(len(payloads(nodes, ROOT_PATH)), 2)
        self.assertEqual(len(payloads(nodes, RESULT)), 2)
        self.assertEqual(len(payloads(nodes, OBSERVATION)), 4)
        props = [value["props"][0] for value in payloads(nodes, OBSERVATION)]
        self.assertEqual({value["name"] for value in props}, {"new-score-a", "new-score-b"})
        self.assertEqual({value["value"] for value in props}, {"3", "0", "8", "false"})
        by_key = {node["NODE_KEY"]: node for node in nodes.rows}
        for edge in edges.rows:
            parent = by_key[edge["FK_SOURCE_ELEMENT_HASH"]]
            child = by_key[edge["FK_TARGET_ELEMENT_HASH"]]
            self.assertEqual(parent["SOURCE_RECORD_ID"], child["SOURCE_RECORD_ID"])
            if child["ELEMENT_PATH"] == OBSERVATION:
                self.assertEqual(parent["ELEMENT_PATH"], RESULT)
                self.assertEqual(parent["INSTANCE_KEY"], child["PARENT_INSTANCE_KEY"])

    def test_source_namespaces_remain_disjoint_with_same_record_and_field(self):
        row = mapping("NEW_SCORE", OBSERVATION, "scalar-score")
        records = [{"SOURCE_RECORD_ID": "same-record", "CURATED_JSON": {"NEW_SCORE": 5}}]
        first = compile_context(self.ns, [row], "source-one", "SOURCE_ONE")
        second = compile_context(self.ns, [dict(row, SOURCE_KEY="source-two")], "source-two", "SOURCE_TWO")
        poison_legacy_classifier(self.ns)
        an, ae = build(self.ns, first, records)
        bn, be = build(self.ns, second, records)
        for key in ("NODE_KEY", "OSCAL_UUID"):
            self.assertTrue({n[key] for n in an.rows}.isdisjoint(n[key] for n in bn.rows))
        self.assertTrue({e["EDGE_KEY"] for e in ae.rows}.isdisjoint(e["EDGE_KEY"] for e in be.rows))

    def test_repeat_build_is_deterministic_and_inputs_are_not_mutated(self):
        row = mapping()
        original = copy.deepcopy(row)
        records = [{"SOURCE_RECORD_ID": "same-record", "CURATED_JSON": {"NEVER_SEEN_SOURCE_FIELD": "stable"}}]
        records_before = copy.deepcopy(records)
        context = compile_context(self.ns, [row])
        poison_legacy_classifier(self.ns)
        first = build(self.ns, context, records)
        second = build(self.ns, compile_context(self.ns, [row]), records)
        self.assertEqual(legacy_graph.business(first[0].rows), legacy_graph.business(second[0].rows))
        self.assertEqual(legacy_graph.business(first[1].rows), legacy_graph.business(second[1].rows))
        self.assertEqual(row, original)
        self.assertEqual(records, records_before)

    def test_missing_blank_or_unapproved_status_never_becomes_executable(self):
        for approval in (None, "", " ", False, "PENDING", "TBD"):
            with self.subTest(approval=approval):
                self.assert_blocked(mapping(EXECUTION_STATUS=approval))
        row = mapping()
        del row["EXECUTION_STATUS"]
        self.assert_blocked(row)

    def test_unknown_missing_or_blank_transform_never_falls_back_to_field_name(self):
        for transform in (None, "", "unregistered-transform"):
            with self.subTest(transform=transform):
                self.assert_blocked(mapping("AUTHORIZATION_PACKAGE_NAME", transform=transform))
        row = mapping("VULNERABILITY_SCORE")
        del row["TRANSFORM_ID"]
        self.assert_blocked(row)

    def test_ambiguous_target_notes_do_not_choose_an_unapproved_destination(self):
        self.assert_blocked(mapping(
            path=OBSERVATION + " or props[]",
            NOTES="Map as observation or property", transform="scalar-score",
            MAPPING_TYPE="Extension Property"))

    def test_explicit_target_operator_and_transform_do_not_guess_from_prose(self):
        row = mapping(NOTES="Map as observation or property after owner confirms placement")
        context = compile_context(self.ns, [row])
        self.assert_ready(context)
        self.assertEqual(context["compiled_plan"]["mappings"][0]["OWNER_ELEMENT_PATH"], SUMMARY)

    def test_mismatched_representation_and_unregistered_collection_are_blocked(self):
        self.assert_blocked(mapping(REPRESENTATION="observations"))
        self.assert_blocked(mapping(path=SUMMARY + ".unregistered[].title"))

    def test_invalid_transform_parameters_fail_closed(self):
        for params in ("not JSON", "[]", [], 17):
            with self.subTest(params=params):
                self.assert_blocked(mapping(TRANSFORM_PARAMS=params))


    def test_raw_property_name_override_cannot_bypass_flat_metadata(self):
        row = mapping("NEW_SCORE", OBSERVATION, "scalar-score",
                      TRANSFORM_PARAMS="{}",
                      REPRESENTATION_PARAMS='{"property_name":"approved-score-label"}')
        self.assert_blocked(row)

    def test_flat_observation_uses_governed_source_field_naming(self):
        row = mapping("NEW_SCORE", OBSERVATION, "scalar-score")
        context = compile_context(self.ns, [row])
        self.assert_ready(context)
        poison_legacy_classifier(self.ns)
        nodes, _ = build(self.ns, context, [
            {"SOURCE_RECORD_ID": "record-one", "CURATED_JSON": {"NEW_SCORE": 0}}])
        self.assertEqual(payloads(nodes, OBSERVATION)[0]["props"],
                         [{"name": "new-score", "value": "0"}])

    def test_conflicting_values_for_one_member_do_not_publish_partial_graph(self):
        rows = [mapping("FIELD_ONE"), mapping("FIELD_TWO")]
        context = compile_context(self.ns, rows)
        self.assert_ready(context)
        poison_legacy_classifier(self.ns)
        with self.assertRaisesRegex(ValueError, "Singleton target has conflicting populated mappings"):
            build(self.ns, context, [{"SOURCE_RECORD_ID": "record-one", "CURATED_JSON": {
                "FIELD_ONE": "first", "FIELD_TWO": "second"}}])

    def test_partial_executable_metadata_cannot_silently_use_legacy_catalog_approval(self):
        from test_model_selection import cell_namespace
        from test_registry_release import release_registry
        catalog = json.loads(STRUCTURAL_CATALOG.read_text(encoding="utf-8"))
        original, _, registry, _ = legacy_graph.ssp_fixture(legacy_graph.namespace(legacy=True))
        source = copy.deepcopy(catalog["SOURCES"][0])
        source["MODEL_KEYS"] = ("SSP",)
        source["BASE_CONFIG"] = copy.deepcopy(original["config"])
        baseline = next(row for row in original["mapping_rows"]
                        if row["SOURCE_FIELD_NAME"] == "TRACKING_ID")
        registry_data = release_registry([dict(row, OSCAL_MODEL_KEY="SSP") for row in registry.collect()])
        for explicit_metadata in (
            {"TRANSFORM_ID": "identifier"},
            {"APPROVAL_STATUS": "", "TRANSFORM_ID": "unknown-transform"},
            {"REPRESENTATION": "object"},
            {"TRANSFORM_PARAMS": {"unreviewed_option": True}},
            {"REPRESENTATION_PARAMS": {"target": "unreviewed-member"}},
        ):
            with self.subTest(metadata=explicit_metadata):
                row = dict(baseline, OSCAL_MODEL="SSP", **explicit_metadata)
                with self.assertRaises(ValueError):
                    self.ns["_compile_flat_mapping"](
                        row, catalog["MODELS"]["SSP"]["ELEMENTS"])
                contexts = self.ns["compile_mapping_contexts"](
                    {source["SOURCE_KEY"]: [row]}, registry_data, [source], cell_namespace(("SSP",))["MODEL_CONTRACTS"])
                context = contexts[0]
                self.assertEqual(context["routing_report"]["STATUS"], "BLOCKED")
                self.assertEqual(context["routing_report"]["SELECTED_ROWS"], 0)
                self.assertEqual(context["mapping_rows"], [])
                self.assertFalse(context["config"]["EXECUTE_WRITES"])

    def catalog_context(self, original, registry):
        """Run current flat mappings; the frozen fixture supplies only oracle scope."""
        from test_model_selection import cell_namespace
        from test_registry_release import release_registry, mapping_rows, SUPPORT
        catalog = json.loads(STRUCTURAL_CATALOG.read_text(encoding="utf-8"))
        model = original["config"]["OSCAL_MODEL"]
        source = copy.deepcopy(catalog["SOURCES"][0])
        source["MODEL_KEYS"] = (model,)
        source["BASE_CONFIG"] = copy.deepcopy(original["config"])
        registry_data = release_registry([dict(row, OSCAL_MODEL_KEY=model) for row in registry.collect()])
        paths = [row["NODE_PATH"] for row in registry_data]
        wanted = {(row["SOURCE_FIELD_NAME"], row["OWNER_ELEMENT_PATH"])
                  for row in original["mapping_rows"]}
        with FLAT_MAPPING.open(encoding="utf-8-sig", newline="") as handle:
            artifact = list(csv.DictReader(handle))
        rows, found = [], []
        for row in artifact:
            if row["EXECUTION_STATUS"] != "APPROVED" or row["SOURCE_KEY"] != source["SOURCE_KEY"]:
                continue
            path = row["RUNTIME_TARGET_PATH"]
            owners = [owner for owner in paths if path == owner or path.startswith(owner + ".")]
            if not owners:
                continue
            pair = (row["SOURCE_FIELD_NAME"], max(owners, key=len))
            if pair in wanted:
                rows.append(row)
                found.append(pair)
        self.assertEqual(wanted, set(found), "Every oracle mapping needs its current flat row")
        self.assertEqual(len(wanted), len(found), "Do not duplicate an oracle mapping")
        # Former controlled fields now use their maintained CSV support rows.
        support = [row for row in mapping_rows() if row["RULE_ID"] in SUPPORT] if model == "SSP" else []
        rows.extend(support)
        context = self.ns["compile_mapping_contexts"](
            {source["SOURCE_KEY"]: rows}, registry_data, [source], cell_namespace((model,))["MODEL_CONTRACTS"],
            routing_metadata=catalog.get("ROUTING", {}))[0]
        context["lookups"] = copy.deepcopy(original["lookups"])
        self.assert_ready(context)
        self.assertEqual(len(wanted) + len(support), len(context["mapping_rows"]))
        self.assertTrue(all(row["CONTRACT_SOURCE"] == "flat-mapping-artifact"
                            for row in context["mapping_rows"]))
        return context

    def test_ssp_catalog_matches_independent_preconsolidation_fingerprint(self):
        original, records, registry, lookups = legacy_graph.ssp_fixture(legacy_graph.namespace(legacy=True))
        context = self.catalog_context(original, registry)
        context["lookups"]["component_sources"] = {
            "software": legacy_graph.Frame([]), "interconnection": legacy_graph.Frame([])}
        self.ns["_build_component_hydration_lookups"] = lambda *args: lookups
        poison_legacy_classifier(self.ns)
        nodes, edges = build(self.ns, context, records)
        self.assertEqual(len(nodes.rows), 20)
        self.assertEqual(len(edges.rows), 19)
        serialized = json.dumps(
            [legacy_graph.business(nodes.rows), legacy_graph.business(edges.rows)], sort_keys=True)
        self.assertEqual(hashlib.sha256(serialized.encode()).hexdigest(),
                         "e483797474dab461f193225f88439fe1182f2f0f1e66eaf7968eb0f8a411a6c1")

    def test_unmapped_singleton_below_collection_does_not_expand_accepted_ssp_graph(self):
        original, records, registry, lookups = legacy_graph.ssp_fixture(legacy_graph.namespace(legacy=True))
        parent = "system-security-plan.system-implementation.components[]"
        nested = parent + ".component"
        registry = legacy_graph.Frame(list(registry.rows) + [{
            "NODE_PATH": nested, "PARENT_NODE_PATH": parent,
            "ELEMENT_TYPE": "component", "IS_ACTIVE": True, "IS_COLLECTION": False,
            "PROCESS_ORDER": max(row["PROCESS_ORDER"] for row in registry.rows) + 1,
        }])
        oracle_ns = legacy_graph.namespace(legacy=True)
        oracle_ns["_build_component_hydration_lookups"] = lambda *args: lookups
        baseline_nodes, baseline_edges = legacy_graph.build(oracle_ns, original, records, registry)
        self.ns["_build_component_hydration_lookups"] = lambda *args: lookups
        context = self.catalog_context(original, registry)
        context["lookups"]["component_sources"] = {
            "software": legacy_graph.Frame([]), "interconnection": legacy_graph.Frame([])}
        poison_legacy_classifier(self.ns)
        nodes, edges = build(self.ns, context, records)
        self.assertEqual(payloads(nodes, nested), [])
        self.assertEqual(legacy_graph.business(nodes.rows), legacy_graph.business(baseline_nodes.rows))
        self.assertEqual(legacy_graph.business(edges.rows), legacy_graph.business(baseline_edges.rows))
        self.assertEqual(len(nodes.rows), 20)
        self.assertEqual(len(edges.rows), 19)
        serialized = json.dumps(
            [legacy_graph.business(nodes.rows), legacy_graph.business(edges.rows)], sort_keys=True)
        self.assertEqual(hashlib.sha256(serialized.encode()).hexdigest(),
                         "e483797474dab461f193225f88439fe1182f2f0f1e66eaf7968eb0f8a411a6c1")

    def test_ar17_catalog_matches_accepted_standalone_business_output(self):
        import runpy
        original = legacy_graph.ar_context(legacy_graph.namespace(legacy=True))
        context = self.catalog_context(original, legacy_graph.ar_registry())
        fields = tuple(row["SOURCE_FIELD_NAME"] for row in original["mapping_rows"])
        self.assertEqual(len(fields), 17)
        records = [
            {"SOURCE_RECORD_ID": "100", "CURATED_JSON": json.dumps(
                {field: index + 1 for index, field in enumerate(fields)})},
            {"SOURCE_RECORD_ID": "101", "CURATED_JSON":
             '{"VULNERABILITY_SCORE":1.000000000000000001,"PATCH_SCORE":0,"RISK_SCORE_GRADE":"A"}'},
        ]
        oracle = runpy.run_path(str(legacy_graph.AR), run_name="metadata_parity_oracle")
        oracle_globals = oracle["build_ar_score_batch"].__globals__
        oracle_globals["AR_SCORE_FIELDS"] = oracle_globals["AR_ACCEPTED_SCORE_FIELDS"]
        oracle_globals["AR_ALTERNATIVE_SCORE_FIELDS"] = ()
        oracle_ns = legacy_graph.namespace(legacy=True)
        helpers = {name: oracle_ns[name] for name in oracle["AR_HELPERS"]}
        helpers["resolve_archer_select_value"] = lambda value: oracle_ns["resolve_archer_select_value"](value, original)
        expected = oracle["build_ar_score_batch"](
            records, original["mapping_rows"], legacy_graph.ar_registry().collect(),
            original["config"], helpers)
        self.assertTrue(expected["report"]["OUTPUTS_PUBLISHED"])
        poison_legacy_classifier(self.ns)
        nodes, edges = build(self.ns, context, records)
        self.assertEqual(legacy_graph.business(nodes.rows), legacy_graph.business(expected["nodes"]))
        self.assertEqual(legacy_graph.business(edges.rows), legacy_graph.business(expected["edges"]))
        self.assertEqual(context["graph_report"]["FIELDS"], expected["report"]["FIELDS"])


if __name__ == "__main__":
    unittest.main()
