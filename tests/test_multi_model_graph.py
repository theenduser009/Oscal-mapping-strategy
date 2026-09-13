
import ast
import contextlib
import copy
import datetime
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import unittest
import uuid

ROOT = Path(__file__).parents[1]
C3 = ROOT / "notebooks/cells/03_canonical_mapping_contract.py"
C4 = ROOT / "notebooks/cells/04_parsing_transform_payload_helpers.py"
LEGACY_C4 = ROOT / "tests/fixtures/legacy_cell4_pre_declarative.py"
LEGACY_C5 = ROOT / "tests/fixtures/legacy_cell5_pre_direct_dispatch.py"
C5 = ROOT / "notebooks/cells/05_registry_graph_builder.py"
AR = ROOT / "notebooks/assessment_results/01_map_observation_scores.py"
AUDIT = {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}


class Row(dict):
    def as_dict(self, recursive=False):
        return dict(self)


class Frame:
    def __init__(self, rows):
        self.rows = [Row(row) for row in rows]
        self.columns = list(self.rows[0]) if self.rows else []
    def collect(self):
        return list(self.rows)
    def to_local_iterator(self):
        return iter(self.rows)


class Session:
    def create_dataframe(self, rows):
        return Frame(rows)


def namespace(legacy=False):
    """Default is the active engine; legacy=True is an explicit frozen oracle."""
    ns = dict(datetime=datetime, json=json, re=re, uuid=uuid, hashlib=hashlib,
              session=Session(), CONFIG={"SOURCE_SYSTEM_NAME": "POISON"},
              ARCHER_VALUE_LOOKUP={"1": "global-poison"}, FIPS_199_VALUE_LOOKUP={},
              MAPPINGS_BY_ELEMENT_PATH={})
    with contextlib.redirect_stdout(io.StringIO()):
        if not legacy:
            # Cell3 owns executable capabilities; omit only notebook I/O statements.
            tree = ast.parse(C3.read_text(encoding="utf-8"))
            definitions = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
                    definitions.append(node)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    try:
                        ast.literal_eval(node.value)
                    except (ValueError, TypeError, SyntaxError):
                        continue
                    definitions.append(node)
            exec(compile(ast.Module(body=definitions, type_ignores=[]), str(C3), "exec"), ns)
        helper_path = LEGACY_C4 if legacy else C4
        exec(compile(helper_path.read_text(encoding="utf-8"), str(helper_path), "exec"), ns)
        graph_path = LEGACY_C5 if legacy else C5
        exec(compile(graph_path.read_text(encoding="utf-8"), str(graph_path), "exec"), ns)
    return ns


def ar_context(ns, source="ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"):
    fields = ns["_SCORE_ACCEPTED_FIELDS"]
    path = "assessment-results.results[].observations[]"
    rows = [dict(SOURCE_FIELD_NAME=f, OSCAL_MODEL="Assessment Results",
                 OSCAL_ELEMENT_PATH=path, OWNER_ELEMENT_PATH=path,
                 MAPPING_TYPE="Extension Property",
                 NOTES="Archer-specific risk scoring - map as observation")
            for f in fields]
    cfg = dict(IDENTITY_VERSION="v1_registry_path_instance", RUN_ID="test",
               OSCAL_MODEL="ASSESSMENT_RESULTS", SOURCE_SYSTEM_NAME="ARCHER",
               SOURCE_TABLE_NAME=source, EXECUTE_WRITES=False,
               RAW_TABLE="RTX_RAW_DEV.ES_ESC_GRC." + source)
    return dict(config=cfg, mapping_rows=rows, mappings_by_path={path: rows},
                lookups={"archer_values": {"1": "lookup-label"}, "fips_values": {}},
                model_contract={"MODEL_KEY": "ASSESSMENT_RESULTS",
                    "ROOT_PATH": "assessment-results", "POLICY": "observation-scores-v2",
                    "SELECTED_FIELDS": fields,
                    "ELEMENT_PATHS": ("assessment-results", "assessment-results.results[]", path)})


def ar_registry():
    root = "assessment-results"
    result = root + ".results[]"
    observation = result + ".observations[]"
    return Frame([
        dict(OSCAL_MODEL_KEY="ASSESSMENT_RESULTS", NODE_PATH=root, PARENT_NODE_PATH=None,
             IS_COLLECTION=False, IS_ACTIVE=True, ELEMENT_TYPE="assessment-results-document",
             INSTANCE_KEY_RULE=None, ITEM_PATH=None, PROCESS_ORDER=1),
        dict(OSCAL_MODEL_KEY="ASSESSMENT_RESULTS", NODE_PATH=result, PARENT_NODE_PATH=root,
             IS_COLLECTION=True, IS_ACTIVE=True, ELEMENT_TYPE="results",
             INSTANCE_KEY_RULE="SOURCE_RECORD_ID", ITEM_PATH=None, PROCESS_ORDER=2),
        dict(OSCAL_MODEL_KEY="ASSESSMENT_RESULTS", NODE_PATH=observation, PARENT_NODE_PATH=result,
             IS_COLLECTION=True, IS_ACTIVE=True, ELEMENT_TYPE="observations",
             INSTANCE_KEY_RULE="SOURCE_FIELD_NAME", ITEM_PATH=None, PROCESS_ORDER=3),
    ])


def build(ns, ctx, records, registry=None):
    cfg = ctx["config"]
    return ns["build_oscal_graph"](
        Frame(records), Frame(ctx["mapping_rows"]), registry or ar_registry(),
        cfg["OSCAL_MODEL"], cfg["SOURCE_SYSTEM_NAME"], cfg["SOURCE_TABLE_NAME"], context=ctx)


def business(rows):
    return sorted([{k: v for k, v in row.items() if k not in AUDIT} for row in rows],
                  key=lambda row: row.get("NODE_KEY", row.get("EDGE_KEY")))


def ssp_fixture(ns):
    root = "system-security-plan"
    meta = root + ".metadata"
    sc = root + ".system-characteristics"
    comp = root + ".system-implementation.components[]"
    def mapping(field, owner, member, kind, notes=""):
        return {"SOURCE_FIELD_NAME": field, "OWNER_ELEMENT_PATH": owner,
                "OSCAL_ELEMENT_PATH": owner + ("." + member if member else ""),
                "OSCAL_FIELD_NAME": member, "MAPPING_TYPE": kind, "NOTES": notes}
    rows = [
        mapping("LAST_UPDATED", meta, "last-modified", "Transform"),
        mapping("TRACKING_ID", meta + ".document-ids[]", "identifier", "Direct"),
        mapping("AUTHORIZATION_PACKAGE_NAME", sc, "system-name", "Direct"),
        mapping("FISMA_REPORTABLE", sc + ".props[]", "value", "Extension Property"),
        mapping("SAP_ID", sc + ".system-ids[]", "id", "Direct"),
    ]
    for field in ns["RESPONSIBLE_PARTY_ROLE_IDS"]:
        rows.append(mapping(field, meta + ".responsible-parties[]", "", "Transform"))
    for field, member in (
        ("RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY", "security-objective-confidentiality"),
        ("RECOMMENDED_INTEGRITY_CONTROL_CATEGORY", "security-objective-integrity"),
        ("RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY", "security-objective-availability")):
        rows.append(mapping(field, sc + ".security-impact-level", member, "Transform"))
    for field, kind in ns["COMPONENT_SOURCE_TYPES"].items():
        rows.append(mapping(field, comp, "", "Reference", "Map component type " + kind))
    paths = [root, meta, meta + ".roles[]", meta + ".parties[]",
             meta + ".responsible-parties[]", meta + ".document-ids[]",
             sc, sc + ".props[]", sc + ".system-ids[]", sc + ".security-impact-level",
             root + ".system-implementation", comp]
    registry = []
    for i, path in enumerate(paths):
        reg = dict(NODE_PATH=path, PARENT_NODE_PATH=path.rsplit(".", 1)[0] if "." in path else None,
                   PROCESS_ORDER=i + 1, ELEMENT_TYPE=path.rsplit(".", 1)[-1].replace("[]", ""),
                   IS_ACTIVE=True, IS_COLLECTION=path.endswith("[]"))
        if path in ns["GOVERNED_COLLECTION_CONTRACTS"]:
            contract = ns["GOVERNED_COLLECTION_CONTRACTS"][path]
            reg.update(INSTANCE_KEY_RULE=contract["instance_key_rule"], ITEM_PATH=contract["item_path"])
        registry.append(reg)
    mappings = {}
    for row in rows:
        mappings.setdefault(row["OWNER_ELEMENT_PATH"], []).append(row)
    cfg = dict(IDENTITY_VERSION="v1_registry_path_instance", OSCAL_MODEL="SSP",
               OSCAL_VERSION="1.2.3", SSP_DOCUMENT_VERSION="1.0", RUN_ID="test",
               SOURCE_SYSTEM_NAME="ARCHER", SOURCE_TABLE_NAME="ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
               EXECUTE_WRITES=False)
    source = {
        "AUTHORIZATION_PACKAGE_NAME": "Example Package", "LAST_UPDATED": "2026-09-11T08:00:00",
        "TRACKING_ID": " TRACK-42 ", "SAP_ID": " SAP-42 ", "FISMA_REPORTABLE": False,
        "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY": {"ValuesListIds": [11]},
        "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY": {"ValuesListIds": [12]},
        "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY": {"ValuesListIds": [13]},
        "SOFTWARE": [{"ContentId": 1000}, {"ContentId": 1000}],
    }
    for field in ns["RESPONSIBLE_PARTY_ROLE_IDS"]:
        source[field] = {"UserList": [{"Id": "same-user"}]}
    lookups = {"software": {"1000": {"title": "Sample Tool", "description": "Reviewed tool"}}}
    ctx = dict(config=cfg, mapping_rows=rows, mappings_by_path=mappings,
               lookups={"archer_values": {"11": "low", "12": "moderate", "13": "high"},
                        "fips_values": {}, "component_sources": {}, "component_contract": ns["COMPONENT_HYDRATION_CONTRACT"]},
               model_contract={"MODEL_KEY": "SSP", "ROOT_PATH": root, "POLICY": "ssp-approved-v1"})
    return ctx, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": source}], Frame(registry), lookups

class LegacyMultiModelGraphTests(unittest.TestCase):
    def test_frozen_pre_declarative_oracle_hash(self):
        # Normalize platform line endings only; no behavioral oracle edits.
        source = LEGACY_C4.read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertEqual(
            hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "a13c16f27481159b70891aaeeed13d8d69ff4dd330ebc798d2cd43344ad2ec1b",
        )

    def test_ssp_mixed_branches_match_preconsolidation_business_fingerprint(self):
        ns = namespace(legacy=True)
        ctx, records, registry, lookups = ssp_fixture(ns)
        # Lookup acquisition is separately Snowpark-tested; this fixture fixes
        # the already approved reference payload so graph parity is independent.
        ns["_build_component_hydration_lookups"] = lambda *args: lookups
        nodes, edges = build(ns, ctx, records, registry)
        serialized = json.dumps([business(nodes.rows), business(edges.rows)], sort_keys=True)
        self.assertEqual(len(nodes.rows), 20)
        self.assertEqual(len(edges.rows), 19)
        # Produced from the preconsolidation Cells 4/5 for this exact fixture:
        # metadata + five roles/assignments + shared party + IDs + CIA + component.
        self.assertEqual(hashlib.sha256(serialized.encode()).hexdigest(),
                         "e483797474dab461f193225f88439fe1182f2f0f1e66eaf7968eb0f8a411a6c1")
        ar_nodes, _ = build(ns, ar_context(ns), [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"PATCH_SCORE": 4}}])
        second_nodes, second_edges = build(ns, ctx, records, registry)
        self.assertEqual(business(nodes.rows), business(second_nodes.rows))
        self.assertEqual(business(edges.rows), business(second_edges.rows))
        self.assertFalse({row["NODE_KEY"] for row in nodes.rows} & {row["NODE_KEY"] for row in ar_nodes.rows})

    def test_ar17_exact_business_parity_with_accepted_standalone(self):
        ns = namespace(legacy=True)
        ctx = ar_context(ns)
        records = [
            {"SOURCE_RECORD_ID": "100", "CURATED_JSON": json.dumps(
                {field: index + 1 for index, field in enumerate(ns["_SCORE_ACCEPTED_FIELDS"])})},
            {"SOURCE_RECORD_ID": "101", "CURATED_JSON":
             '{"VULNERABILITY_SCORE":1.000000000000000001,"PATCH_SCORE":0,"RISK_SCORE_GRADE":"A"}'},
        ]
        # Pin only the already accepted v2 rows in the independent historical oracle;
        # this does not change the standalone file or production globals.
        oracle = runpy.run_path(str(AR), run_name="parity_oracle")
        fn_globals = oracle["build_ar_score_batch"].__globals__
        fn_globals["AR_SCORE_FIELDS"] = fn_globals["AR_ACCEPTED_SCORE_FIELDS"]
        fn_globals["AR_ALTERNATIVE_SCORE_FIELDS"] = ()
        helpers = {name: ns[name] for name in oracle["AR_HELPERS"]}
        helpers["resolve_archer_select_value"] = lambda value: ns["resolve_archer_select_value"](value, ctx)
        expected = oracle["build_ar_score_batch"](
            records, ctx["mapping_rows"], ar_registry().collect(), ctx["config"], helpers)
        self.assertTrue(expected["report"]["OUTPUTS_PUBLISHED"])
        nodes, edges = build(ns, ctx, records)
        self.assertEqual(business(nodes.rows), business(expected["nodes"]))
        self.assertEqual(business(edges.rows), business(expected["edges"]))
        self.assertEqual(ctx["graph_report"]["FIELDS"], expected["report"]["FIELDS"])
        self.assertEqual(nodes.rows[0]["ELEMENT_TYPE"], "assessment-results-document")

    def test_context_lookup_does_not_leak_between_sources(self):
        ns = namespace(legacy=True)
        a, b = ar_context(ns, "SOURCE_A"), ar_context(ns, "SOURCE_B")
        a["lookups"]["archer_values"]["1"] = "A"
        b["lookups"]["archer_values"]["1"] = "B"
        records = [{"SOURCE_RECORD_ID": "100", "CURATED_JSON":
                    {"VULNERABILITY_SCORE": {"ValuesListIds": [1]}}}]
        an, ae = build(ns, a, records)
        bn, be = build(ns, b, records)
        self.assertFalse({r["NODE_KEY"] for r in an.rows} & {r["NODE_KEY"] for r in bn.rows})
        self.assertFalse({r["OSCAL_UUID"] for r in an.rows} & {r["OSCAL_UUID"] for r in bn.rows})
        self.assertFalse({r["EDGE_KEY"] for r in ae.rows} & {r["EDGE_KEY"] for r in be.rows})
        self.assertEqual(json.loads(an.rows[-1]["METADATA_JSON"])["props"][0]["value"], "A")
        self.assertEqual(json.loads(bn.rows[-1]["METADATA_JSON"])["props"][0]["value"], "B")
        self.assertEqual(ns["ARCHER_VALUE_LOOKUP"]["1"], "global-poison")

    def test_ar_selected_invalid_values_block_all_outputs_with_aggregate_evidence(self):
        ns = namespace(legacy=True)
        ctx = ar_context(ns)
        with self.assertRaisesRegex(ValueError, "values rejected"):
            build(ns, ctx, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"PATCH_SCORE": [1, 2]}}])
        self.assertFalse(ctx["graph_report"]["OUTPUTS_PUBLISHED"])
        self.assertEqual(ctx["graph_report"]["FIELDS"]["PATCH_SCORE"]["invalid"], 1)

    def test_ar17_excludes_later_candidate_and_counts_it(self):
        ns = namespace(legacy=True)
        ctx = ar_context(ns)
        ctx["mapping_rows"].append(dict(SOURCE_FIELD_NAME="RISK_ACCEPTANCE_RBDS",
            OSCAL_MODEL="Assessment Results", OSCAL_ELEMENT_PATH="assessment-results.results[].observations[] or props[]",
            MAPPING_TYPE="Extension Property", NOTES="Archer specific risk scoring map as observation or property"))
        nodes, edges = build(ns, ctx, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON":
            {"PATCH_SCORE": 7, "RISK_ACCEPTANCE_RBDS": {"ContentId": "unapproved"}}}])
        self.assertEqual(ctx["graph_report"]["OTHER_AR_MAPPING_ROWS_NOT_PROCESSED"], 1)
        self.assertEqual(len(nodes.rows), 3)
        self.assertEqual(len(edges.rows), 2)

    def test_parent_ids_and_model_namespaces_are_isolated(self):
        ns = namespace(legacy=True)
        ctx = ar_context(ns)
        nodes, edges = build(ns, ctx, [
            {"SOURCE_RECORD_ID": str(i), "CURATED_JSON": {"PATCH_SCORE": i}} for i in (100, 101)])
        by_key = {r["NODE_KEY"]: r for r in nodes.rows}
        for edge in edges.rows:
            parent, child = by_key[edge["FK_SOURCE_ELEMENT_HASH"]], by_key[edge["FK_TARGET_ELEMENT_HASH"]]
            self.assertEqual(parent["SOURCE_RECORD_ID"], child["SOURCE_RECORD_ID"])
            self.assertEqual(parent["INSTANCE_KEY"], child["PARENT_INSTANCE_KEY"])
        root = nodes.rows[0]
        cfg = ctx["config"]
        self.assertNotEqual(root["NODE_KEY"], ns["_deterministic_hash"](
            cfg["IDENTITY_VERSION"], cfg["SOURCE_SYSTEM_NAME"], cfg["SOURCE_TABLE_NAME"],
            root["SOURCE_RECORD_ID"], "SSP", root["ELEMENT_PATH"], root["INSTANCE_KEY"]))

    def test_duplicate_and_missing_source_ids_never_publish_partial_ar(self):
        for ids in ((None,), ("100", "100")):
            ns = namespace(legacy=True)
            ctx = ar_context(ns)
            with self.assertRaises(ValueError):
                build(ns, ctx, [{"SOURCE_RECORD_ID": i, "CURATED_JSON": {"PATCH_SCORE": 1}} for i in ids])
            self.assertFalse(ctx["graph_report"]["OUTPUTS_PUBLISHED"])

    def test_ssp_party_identity_retains_source_one_and_namespaces_other_sources(self):
        ns = namespace(legacy=True)
        ctx = ar_context(ns)
        ctx["config"]["OSCAL_MODEL"] = "SSP"
        actual = ns["_party_uuid"]("100", "user-7", ctx)
        self.assertEqual(actual, ns["_deterministic_uuid"]("ARCHER", "100", "party", "user-7"))
        ctx["config"]["SOURCE_TABLE_NAME"] = "OTHER_SOURCE"
        self.assertNotEqual(actual, ns["_party_uuid"]("100", "user-7", ctx))

    def test_same_input_rebuild_preserves_all_business_keys_and_values(self):
        ns = namespace(legacy=True)
        records = [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"PATCH_SCORE": False}}]
        first = build(ns, ar_context(ns), records)
        second = build(ns, ar_context(ns), records)
        self.assertEqual(business(first[0].rows), business(second[0].rows))
        self.assertEqual(business(first[1].rows), business(second[1].rows))


if __name__ == "__main__":
    unittest.main()
