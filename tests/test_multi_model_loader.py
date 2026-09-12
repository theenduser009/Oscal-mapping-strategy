"""Shared writer isolation and graph-only preview; no live Snowflake claims."""
from contextlib import redirect_stdout
import copy
import io
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
from tests.test_ssp_write_pilot_live_schema import live_description

ROOT = Path(__file__).resolve().parents[1]
P = runpy.run_path(str(ROOT / "notebooks/cells/06_validation_and_guarded_loader.py"))
G, Error = P["_load_prepare"].__globals__, P["LoadError"]


def storage(model="MODEL_A", root="alpha-document"):
    return dict(MODEL_KEY=model, ROOT_PATH=root, ROOT_ELEMENT_TYPE=root,
                SOURCE_SYSTEM_NAME="ARCHER", SOURCE_TABLE_NAME="SOURCE_" + model,
                RAW_TABLE="RAW.SOURCE.SOURCE_" + model,
                TARGET_DIM="DEV." + model + ".DIM_ELEMENTS",
                TARGET_FACT="DEV." + model + ".FACT_EDGES",
                DIM_PK_COLUMN="PK_" + model + "_NODE", FACT_PK_COLUMN="PK_" + model + "_EDGE",
                IDENTITY_VERSION="v1_registry_path_instance",
                PHYSICAL_PROFILE="BINARY16_UUID32", VERIFIED=True)


def config(contract=None):
    c = contract or dict(MODEL_KEY="ASSESSMENT_RESULTS", ROOT_PATH="assessment-results",
                         ROOT_ELEMENT_TYPE="assessment-results-document",
                         SOURCE_SYSTEM_NAME="ARCHER", SOURCE_TABLE_NAME="AUTHORIZATION_PACKAGE",
                         RAW_TABLE="RAW.SOURCE.AUTHORIZATION_PACKAGE",
                         IDENTITY_VERSION="v1_registry_path_instance")
    return dict(OSCAL_MODEL=c["MODEL_KEY"], ROOT_PATH=c["ROOT_PATH"],
                ROOT_ELEMENT_TYPE=c["ROOT_ELEMENT_TYPE"],
                SOURCE_SYSTEM_NAME=c["SOURCE_SYSTEM_NAME"], SOURCE_TABLE_NAME=c["SOURCE_TABLE_NAME"],
                RAW_TABLE=c["RAW_TABLE"], IDENTITY_VERSION=c["IDENTITY_VERSION"],
                EXECUTE_WRITES=False, STORAGE_CONTRACT=contract, EXPECTED_SOURCE_RECORDS=1)


def graph(cfg):
    root = cfg["ROOT_PATH"]
    nodes = []
    for number, path, typ, instance, parent in (
            (1, root, cfg["ROOT_ELEMENT_TYPE"], "root", None),
            (2, root + ".results", "results", "result", "root"),
            (3, root + ".results.observations", "observations", "field", "result")):
        nodes.append(dict(NODE_KEY=format(number, "032x"), SOURCE_RECORD_ID="record",
            ELEMENT_PATH=path, ELEMENT_TYPE=typ, INSTANCE_KEY=instance, PARENT_INSTANCE_KEY=parent,
            OSCAL_UUID="00000000-0000-5000-8000-" + format(number, "012x"),
            METADATA_JSON='{"props":[]}', SOURCE_SYSTEM_NAME=cfg["SOURCE_SYSTEM_NAME"],
            SOURCE_TABLE_NAME=cfg["SOURCE_TABLE_NAME"], MODEL_KEY=cfg["OSCAL_MODEL"]))
    edges = []
    for number, source, target in ((10, nodes[0], nodes[1]), (11, nodes[1], nodes[2])):
        edges.append(dict(EDGE_KEY=format(number, "032x"),
            FK_SOURCE_ELEMENT_HASH=source["NODE_KEY"], FK_TARGET_ELEMENT_HASH=target["NODE_KEY"],
            SOURCE_OSCAL_UUID=source["OSCAL_UUID"], TARGET_OSCAL_UUID=target["OSCAL_UUID"],
            DEPENDENCY_TYPE="CONTAINS"))
    return nodes, edges


class NoTargetSession:
    def sql(self, *args, **kwargs):
        raise AssertionError("Graph-only preview must not issue session/target SQL")
    def table(self, *args, **kwargs):
        raise AssertionError("Graph-only preview must not resolve targets")


class MultiModelContracts(unittest.TestCase):
    def test_two_immutable_contracts_have_separate_targets_and_keys(self):
        supplied = storage()
        a = P["_load_contract"](config(supplied))
        b = P["_load_contract"](config(storage("MODEL_B", "beta-document")))
        supplied["TARGET_DIM"] = "DEV.WRONG.DIM"
        self.assertEqual("DEV.MODEL_A.DIM_ELEMENTS", a["TARGET_DIM"])
        with self.assertRaises(TypeError):
            a["TARGET_DIM"] = "X"
        for c, other in ((a, b), (b, a)):
            sql = P["_build_merge_sql"](c["TARGET_DIM"], "FROZEN_DIM", c["DIM_PK_COLUMN"],
                                      [c["DIM_PK_COLUMN"], "METADATA_JSON"], c)
            self.assertIn(c["TARGET_DIM"], sql)
            self.assertIn(c["DIM_PK_COLUMN"], sql)
            self.assertNotIn(other["TARGET_DIM"], sql)
            self.assertNotIn("DIM_OSCAL_SSP_ELEMENT", sql)
            with self.assertRaises(Error):
                P["_build_merge_sql"](other["TARGET_DIM"], "STAGE", c["DIM_PK_COLUMN"],
                                     [c["DIM_PK_COLUMN"]], c)

    def test_projection_and_scope_use_only_the_explicit_contract(self):
        for c in (storage(), storage("MODEL_B", "beta-document")):
            plans = []
            for kind, pk in (("DIM", "DIM_PK_COLUMN"), ("FACT", "FACT_PK_COLUMN")):
                rows = live_description(kind)
                rows[0]["name"] = c[pk]
                plans.append(P["_load_column_plan"](rows, kind, c))
            self.assertEqual(4, sum(x["encoding"] == "HEX_TO_BINARY16" for p in plans for x in p))
            self.assertEqual(3, sum(x["encoding"] == "UUID_TO_COMPACT32" for p in plans for x in p))
            names = dict(D="FROZEN_DIM", F="FROZEN_FACT", IDS="SELECTED_IDS", DB="BASE_DIM", FB="BASE_FACT")
            dim, fact = P["_load_scope_queries"](names, c)
            self.assertIn(c["TARGET_DIM"], dim)
            self.assertIn(c["SOURCE_TABLE_NAME"], dim)
            self.assertIn(c["TARGET_FACT"], fact)
            self.assertNotIn("ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW", dim)
            integrity = P["_load_integrity_sql"]((dim, fact), "SELECTED_IDS", contract=c)
            self.assertIn(c["ROOT_ELEMENT_TYPE"], integrity)
            self.assertIn(c["DIM_PK_COLUMN"], integrity)
            self.assertNotIn("system-security-plan", integrity)

    def test_verified_contract_cannot_disagree_with_run_source_or_profile(self):
        c = storage()
        cfg = config(c)
        cfg["SOURCE_TABLE_NAME"] = "WRONG_SOURCE"
        with self.assertRaises(Error):
            P["_load_contract"](cfg)
        c["PHYSICAL_PROFILE"] = "UNREVIEWED"
        with self.assertRaises(Error):
            P["_load_contract"](config(c))

    def test_storage_contract_must_be_explicit_and_verified(self):
        for legacy_name in ("SSP_LOAD_DIM", "SSP_LOAD_FACT", "SSP_LOAD_DIM_PK",
                            "SSP_LOAD_FACT_PK", "SSP_LOAD_SOURCE", "_load_legacy_contract"):
            self.assertNotIn(legacy_name, P)
        supplied = storage("SSP", "system-security-plan")
        accepted = P["_load_contract"](config(supplied))
        self.assertEqual(supplied, accepted)
        with self.assertRaises(TypeError):
            accepted["TARGET_DIM"] = "DEV.WRONG.DIM"
        for absent in (None, dict(VERIFIED=False, TARGET_DIM="DO.NOT.QUERY_THIS")):
            cfg = config()
            cfg["STORAGE_CONTRACT"] = absent
            self.assertIsNone(P["_load_contract"](cfg))
        cfg = config()
        cfg.pop("STORAGE_CONTRACT")
        self.assertIsNone(P["_load_contract"](cfg))


class TargetlessGraphPreview(unittest.TestCase):
    def preview(self, cfg, nodes=None, edges=None):
        if nodes is None:
            nodes, edges = graph(cfg)
        with patch.dict(G, {"session": NoTargetSession()}), redirect_stdout(io.StringIO()):
            return P["validate_and_load_oscal"](nodes, edges, cfg)

    def test_ar_graph_preview_has_no_fabricated_storage_verification(self):
        cfg = config()
        result = self.preview(cfg)
        self.assertEqual("MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING", result["status"])
        self.assertTrue(result["validation_passed"])
        self.assertFalse(result["pre_write_validation_passed"])
        self.assertFalse(result["storage_verified"])
        self.assertFalse(result["writes_executed"])
        self.assertFalse(result["persisted"])
        self.assertFalse(result["target_dml_attempted"])
        self.assertEqual((3, 2, 1), (result["nodes"], result["edges"], result["source_records"]))
        self.assertEqual(0, result["dim_load_rows"])
        self.assertIsNone(cfg["STORAGE_CONTRACT"])

    def test_unverified_contract_is_ignored_in_preview_and_commit_is_blocked(self):
        for contract in (None, dict(VERIFIED=False, TARGET_DIM="DO.NOT.QUERY_THIS")):
            cfg = config()
            cfg["STORAGE_CONTRACT"] = contract
            self.assertFalse(self.preview(cfg)["storage_verified"])
            cfg["EXECUTE_WRITES"] = True
            with self.assertRaises(Error) as caught:
                self.preview(cfg)
            self.assertEqual("STORAGE_CONTRACT_NOT_VERIFIED", caught.exception.code)
            self.assertFalse(caught.exception.details["target_dml_attempted"])

    def test_root_is_identified_by_path_not_a_guessed_element_type(self):
        cfg = config()
        nodes, edges = graph(cfg)
        self.assertNotEqual(cfg["ROOT_PATH"], nodes[0]["ELEMENT_TYPE"])
        self.assertTrue(self.preview(cfg, nodes, edges)["validation_passed"])
        cfg.pop("ROOT_ELEMENT_TYPE")
        self.assertTrue(self.preview(cfg, nodes, edges)["validation_passed"])

    def test_key_ownership_uuid_parent_and_coverage_failures_are_not_accepted(self):
        cfg = config()
        cases = [
            lambda n, e: n.append(copy.deepcopy(n[0])),
            lambda n, e: n[1].update(SOURCE_RECORD_ID=None),
            lambda n, e: n[1].update(SOURCE_TABLE_NAME="OTHER"),
            lambda n, e: n[1].update(MODEL_KEY="SSP"),
            lambda n, e: n[1].update(ELEMENT_PATH="system-security-plan.metadata"),
            lambda n, e: e[0].update(FK_TARGET_ELEMENT_HASH="f" * 32),
            lambda n, e: e[0].update(TARGET_OSCAL_UUID=n[0]["OSCAL_UUID"]),
            lambda n, e: n[2].update(PARENT_INSTANCE_KEY="wrong"),
            lambda n, e: e.pop(),
            lambda n, e: n[0].update(ELEMENT_PATH=cfg["ROOT_PATH"] + ".unexpected"),
        ]
        for change in cases:
            nodes, edges = graph(cfg)
            change(nodes, edges)
            with self.subTest(change=change):
                with self.assertRaises(Error):
                    self.preview(cfg, nodes, edges)
        cfg["EXPECTED_SOURCE_RECORDS"] = 2
        with self.assertRaises(Error):
            self.preview(cfg)

    def test_verify_api_does_not_claim_a_database_readback_for_graph_only(self):
        cfg = config()
        nodes, edges = graph(cfg)
        with patch.dict(G, {"session": NoTargetSession()}):
            result = P["verify_oscal_load"](nodes, edges, cfg)
        self.assertFalse(result["storage_verified"])
        self.assertIsNone(result["dim_matched"])
        self.assertIsNone(result["fact_matched"])
        self.assertEqual(3, result["dim_expected"])

    def test_function_release_marker_is_bound_to_the_new_function(self):
        self.assertEqual("oscal-shared-daily-upsert-v2",
                         P["validate_and_load_oscal"]._oscal_loader_release)


if __name__ == "__main__":
    unittest.main()

