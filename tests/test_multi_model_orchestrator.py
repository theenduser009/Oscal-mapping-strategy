"""Shared-pipeline orchestration boundaries, without Snowflake or target DML."""
import ast
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CELL = ROOT / "notebooks/cells/07_mapper_orchestrator.py"
RELEASE = "oscal-shared-daily-upsert-v2"


def namespace():
    tree = ast.parse(CELL.read_text(encoding="utf-8"))
    body = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            body.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                continue
            body.append(node)
    ns = {"copy": copy, "json": json}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(CELL), "exec"), ns)
    return ns


def context(source="one", model="SSP", verified=True):
    root = "system-security-plan" if model == "SSP" else "assessment-results"
    storage = {
        "VERIFIED": True, "PHYSICAL_PROFILE": "BINARY16_UUID32", "MODEL_KEY": model,
        "ROOT_PATH": root, "ROOT_ELEMENT_TYPE": root, "SOURCE_SYSTEM_NAME": "ARCHER",
        "SOURCE_TABLE_NAME": "SOURCE_" + source.upper(), "RAW_TABLE": "TEST_RAW.GRC.SOURCE_" + source.upper(),
        "TARGET_DIM": "TEST_DEV.GRC.DIM_" + source.upper() + "_" + model,
        "TARGET_FACT": "TEST_DEV.GRC.FACT_" + source.upper() + "_" + model,
        "DIM_PK_COLUMN": "PK_ELEMENT_HASH", "FACT_PK_COLUMN": "PK_DEPENDENCY_HASH",
        "IDENTITY_VERSION": "v1_registry_path_instance",
    } if verified else None
    config = {
        "EXECUTE_WRITES": False, "OSCAL_MODEL": model, "RUN_ID": "synthetic-run",
        "ROOT_PATH": root, "ROOT_ELEMENT_TYPE": root,
        "SOURCE_SYSTEM_NAME": "ARCHER", "SOURCE_TABLE_NAME": "SOURCE_" + source.upper(),
        "RAW_TABLE": "TEST_RAW.GRC.SOURCE_" + source.upper(),
        "STORAGE_CONTRACT": storage, "BUILD_COVERAGE_REPORT": True,
        "IDENTITY_VERSION": "v1_registry_path_instance",
    }
    if storage:
        config.update({key: storage[key] for key in
            ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN")})
    return {
        "source_key": source, "config": config,
        "mapping_rows": [{"SOURCE_FIELD_NAME": "SYNTHETIC_FIELD", "OSCAL_ELEMENT_PATH": root}],
        "mappings_by_path": {root: [{"SOURCE_FIELD_NAME": "SYNTHETIC_FIELD"}]},
        "model_contract": {"MODEL_KEY": model, "ROOT_PATH": root,
                           "POLICY": "ssp-approved-v1" if model == "SSP" else "observation-scores-v2",
                           "STORAGE_CONTRACT": copy.deepcopy(storage)},
        "registry_rows": [],
        "routing_report": {"STATUS": "READY", "INPUT_ROWS": 1, "SELECTED_ROWS": 1,
                           "EXCLUDED_ROWS": 0, "DEFERRED_ROWS": 0, "BLOCKED_ROWS": 0, "ISSUES": []},
    }


class Source:
    def __init__(self, source):
        self.source = source
        self.record_id = "same-id-in-every-source"


class MultiModelOrchestrator(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.events, self.seen_sources, self.seen_configs = [], [], []
        self.graph_failure = self.commit_failure = None
        self.sources = {
            key: {"source_df": Source(key), "lookups": {"scope": key}}
            for key in ("one", "two")
        }
        self.contexts = [context(), context(model="ASSESSMENT_RESULTS", verified=False)]
        self.global_config = {"EXECUTE_WRITES": False, "sentinel": "legacy-config"}
        self.ns["CONFIG"] = self.global_config
        self.ns["CANONICAL_MAPPING_ROWS"] = [{"legacy": "untouched"}]
        self.ns["run_oscal_mapping"] = self.mapping_run

        def loader(*args, **kwargs):
            config = kwargs["config"]
            route = (config["SOURCE_TABLE_NAME"], config["OSCAL_MODEL"])
            self.events.append(("COMMIT", route))
            self.seen_configs.append(config)
            if config["SOURCE_TABLE_NAME"] == self.commit_failure:
                raise RuntimeError("synthetic later-group commit failure")
            return {"status": "DAILY_MODEL_COMMITTED_AND_VERIFIED", "nodes": 2, "edges": 1,
                    "writes_executed": True, "persisted": True, "verification": {"matched": True}}

        loader._oscal_loader_release = RELEASE
        self.ns["validate_and_load_oscal"] = loader

    def mapping_run(self, source_df, canonical_mapping_df, element_registry_df, config,
                    load_mode="PREVIEW", context=None):
        route = (context["source_key"], config["OSCAL_MODEL"])
        self.events.append(("PREVIEW", route))
        self.seen_sources.append((route, source_df))
        self.seen_configs.append(config)
        self.assertEqual("PREVIEW", load_mode)
        self.assertFalse(config["EXECUTE_WRITES"])
        self.assertIsNone(canonical_mapping_df)
        self.assertIsNone(element_registry_df)
        self.assertEqual(self.sources[route[0]]["lookups"], context["lookups"])
        if route == self.graph_failure:
            raise RuntimeError("synthetic later-group graph failure")
        context["graph_report"] = {"STATUS": "MAPPED_SCOPE_BUILT", "NODES": 2, "EDGES": 1}
        status = ("MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING"
                  if not config.get("STORAGE_CONTRACT") else "DAILY_MODEL_PREVIEW_PASSED_NO_TARGET_DML")
        return ("nodes:" + ":".join(route), "edges:" + ":".join(route),
                "coverage:" + ":".join(route),
                {"status": status, "nodes": 2, "edges": 1, "writes_executed": False, "persisted": False,
                 "validation_passed": True, "source_records": 1,
                 "storage_verified": bool(config.get("STORAGE_CONTRACT"))})

    def run_pipeline(self, contexts=None, mode="PREVIEW", sources=None):
        with redirect_stdout(io.StringIO()):
            return self.ns["run_oscal_pipeline"](
                self.sources if sources is None else sources,
                self.contexts if contexts is None else contexts, load_mode=mode)

    def assert_no_work(self):
        self.assertEqual([], self.events)

    def test_preview_fans_one_source_into_ssp_and_ar_without_target_contract(self):
        graphs, report = self.run_pipeline()
        self.assertEqual({("one", "SSP"), ("one", "ASSESSMENT_RESULTS")}, set(graphs))
        self.assertEqual("PREVIEW", report["mode"])
        self.assertFalse(report["writes_executed"])
        self.assertEqual(2, len(report["groups"]))
        self.assertEqual(["PREVIEW", "PREVIEW"], [event[0] for event in self.events])
        for route, graph in graphs.items():
            self.assertEqual({"nodes", "edges", "coverage", "context"}, set(graph))
            self.assertEqual("nodes:" + ":".join(route), graph["nodes"])
        ar = next(group for group in report["groups"] if group["model"] == "ASSESSMENT_RESULTS")
        self.assertEqual("MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING", ar["load"]["status"])

    def test_same_record_ids_remain_in_the_correct_source_and_lookup_context(self):
        contexts = [context(), context("two")]
        graphs, report = self.run_pipeline(contexts)
        self.assertEqual({("one", "SSP"), ("two", "SSP")}, set(graphs))
        for route, frame in self.seen_sources:
            self.assertIs(self.sources[route[0]]["source_df"], frame)
            self.assertEqual(route[0], frame.source)
        self.assertNotEqual(graphs[("one", "SSP")]["nodes"], graphs[("two", "SSP")]["nodes"])
        self.assertEqual(2, len(report["groups"]))

    def test_original_context_configs_and_legacy_globals_remain_unchanged(self):
        originals = copy.deepcopy([item["config"] for item in self.contexts])
        self.run_pipeline()
        self.assertEqual(originals, [item["config"] for item in self.contexts])
        self.assertEqual({"EXECUTE_WRITES": False, "sentinel": "legacy-config"}, self.global_config)
        self.assertEqual([{"legacy": "untouched"}], self.ns["CANONICAL_MAPPING_ROWS"])
        for frame in self.sources.values():
            self.assertEqual("same-id-in-every-source", frame["source_df"].record_id)

    def test_all_routing_preflight_runs_before_any_group_graph(self):
        contexts = [context(), context("two")]
        contexts[1]["routing_report"].update(STATUS="BLOCKED", BLOCKED_ROWS=1, INPUT_ROWS=1)
        with self.assertRaises(ValueError):
            self.run_pipeline(contexts)
        self.assert_no_work()

    def test_missing_or_unverified_target_prevents_every_commit_and_graph(self):
        for storage in (None, {"VERIFIED": False}):
            contexts = [context(), context("two", "ASSESSMENT_RESULTS", verified=False)]
            contexts[1]["config"]["STORAGE_CONTRACT"] = storage
            with self.subTest(storage=storage), self.assertRaises(ValueError):
                self.run_pipeline(contexts, mode="COMMIT")
            self.assert_no_work()

    def test_duplicate_route_is_rejected_before_graph(self):
        with self.assertRaises(ValueError):
            self.run_pipeline([context(), context()])
        self.assert_no_work()

    def test_missing_source_binding_is_rejected_before_any_graph(self):
        with self.assertRaises(ValueError):
            self.run_pipeline([context(), context("not-bound")])
        self.assert_no_work()

    def test_invalid_modes_and_shared_write_flag_fail_before_graph(self):
        for mode in ("commit", "", None, True, "TRUNCATE"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.run_pipeline(mode=mode)
            self.assert_no_work()
        contexts = [context(), context("two")]
        contexts[1]["config"]["EXECUTE_WRITES"] = True
        with self.assertRaises(ValueError):
            self.run_pipeline(contexts)
        self.assert_no_work()

    def test_all_groups_preview_before_commit_and_graphs_are_not_rebuilt(self):
        contexts = [context(), context("two")]
        originals = copy.deepcopy([item["config"] for item in contexts])
        graphs, report = self.run_pipeline(contexts, mode="COMMIT")
        self.assertEqual(["PREVIEW", "PREVIEW", "COMMIT", "COMMIT"],
                         [event[0] for event in self.events])
        self.assertEqual(2, len(graphs))
        self.assertTrue(report["writes_executed"])
        self.assertEqual("COMMIT", report["mode"])
        self.assertEqual(2, len(report["groups"]))
        self.assertEqual(originals, [item["config"] for item in contexts])
        for config in self.seen_configs[-2:]:
            self.assertTrue(config["EXECUTE_WRITES"])

    def test_later_graph_failure_exposes_no_success_and_never_starts_commit(self):
        self.graph_failure = ("two", "SSP")
        with self.assertRaises(self.ns["PipelineError"]) as caught:
            self.run_pipeline([context(), context("two")], mode="COMMIT")
        report = caught.exception.report
        self.assertEqual("PIPELINE_FAILED_NO_TARGET_DML", report["status"])
        self.assertFalse(report["writes_executed"])
        self.assertEqual(["PREVIEW", "PREVIEW"], [event[0] for event in self.events])
        self.assertGreaterEqual(len(report["groups"]), 1)

    def test_later_commit_failure_reports_already_committed_group_without_retry(self):
        self.commit_failure = "SOURCE_TWO"
        with self.assertRaises(self.ns["PipelineError"]) as caught:
            self.run_pipeline([context(), context("two")], mode="COMMIT")
        report = caught.exception.report
        self.assertEqual("PIPELINE_COMMIT_FAILED_REVIEW_REQUIRED", report["status"])
        self.assertTrue(report["writes_executed"])
        self.assertEqual(["PREVIEW", "PREVIEW", "COMMIT", "COMMIT"],
                         [event[0] for event in self.events])
        committed = [group for group in report["groups"] if group["load"].get("persisted")]
        self.assertEqual(1, len(committed))
        self.assertEqual("one", committed[0]["source"])


if __name__ == "__main__":
    unittest.main()
