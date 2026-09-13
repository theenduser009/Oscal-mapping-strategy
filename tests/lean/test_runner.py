"""Seven-cell runner ordering and failure reporting, without database access."""
import ast
import copy
import json
import os
from pathlib import Path
import runpy
import unittest


CELLS = Path(os.environ.get("LEAN_CELLS_DIR", Path(__file__).resolve().parents[2] / "notebooks/cells"))
LOADER = runpy.run_path(str(CELLS / "06_validation_and_guarded_loader.py"))


def runner_namespace():
    source = ast.parse((CELLS / "07_mapper_orchestrator.py").read_text(encoding="utf-8-sig"))
    definitions = [node for node in source.body if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom))]
    namespace = {"copy": copy, "json": json}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(CELLS / "07_mapper_orchestrator.py"), "exec"), namespace)
    return namespace


class SourceFrame:
    def __init__(self, name, count=2):
        self.name, self.size, self.count_calls = name, count, 0
    def count(self):
        self.count_calls += 1
        return self.size


def context(name, model="SSP", verified=True):
    return {"source_key": name, "config": {"OSCAL_MODEL": model, "SOURCE_SYSTEM_NAME": "ARCHER",
            "SOURCE_TABLE_NAME": "SOURCE_" + name.upper(), "EXECUTE_WRITES": False,
            "STORAGE_CONTRACT": {"VERIFIED": verified, "TARGET_DIM": "DEV.MAPPER.DIM_" + name.upper()}},
            "routing_report": {"STATUS": "READY"}, "mapping_rows": [{"FIELD": "reviewed"}]}


class RunnerBehavior(unittest.TestCase):
    def setUp(self):
        self.ns = runner_namespace()
        self.events = []
        self.contexts = [context("one"), context("two")]
        self.sources = {name: {"source_df": SourceFrame(name), "lookups": {"picklist": {}},
                               "selection": {"SELECTED_ROWS": 2}} for name in ("one", "two")}
        self.fail_preview, self.fail_commit = None, None
        self.last_config = None

        def build(source_df, mapping, registry, model, system, table, context=None):
            self.events.append(("build", source_df.name))
            self.assertIsNone(mapping)
            self.assertIsNone(registry)
            self.assertEqual(context["config"]["SOURCE_TABLE_NAME"], table)
            return (source_df.name, "nodes"), (source_df.name, "edges")

        def load(nodes, edges, config):
            name = nodes[0]
            self.assertEqual(name, edges[0])
            phase = "commit" if config["EXECUTE_WRITES"] else "preview"
            self.events.append((phase, name))
            self.last_config = copy.deepcopy(config)
            operation = self.fail_commit if phase == "commit" else self.fail_preview
            if operation is not None:
                operation(name, config)
            return {"status": "COMMITTED_AND_VERIFIED" if phase == "commit" else "PREVIEW_PASSED_NO_TARGET_DML",
                    "writes_executed": phase == "commit", "persisted": phase == "commit",
                    "validation_passed": True, "storage_verified": True, "source_records": 2}

        load._oscal_loader_release = LOADER["OSCAL_LOAD_RELEASE"]
        self.ns.update(build_oscal_graph=build, validate_and_load_oscal=load)

    def run_pipeline(self, mode="PREVIEW"):
        return self.ns["run_oscal_pipeline"](self.sources, self.contexts, mode)

    def failure(self, mode="COMMIT"):
        with self.assertRaises(self.ns["PipelineError"]) as caught:
            self.run_pipeline(mode)
        return caught.exception.report

    def test_all_previews_finish_before_first_commit(self):
        graphs, report = self.run_pipeline("COMMIT")
        self.assertEqual([("build", "one"), ("preview", "one"), ("build", "two"),
                          ("preview", "two"), ("commit", "one"), ("commit", "two")], self.events)
        self.assertEqual({("one", "SSP"), ("two", "SSP")}, set(graphs))
        self.assertEqual("COMMITTED_AND_VERIFIED", report["status"])
        self.assertTrue(report["writes_executed"])
        self.assertTrue(report["commit_attempted"])

    def test_default_mode_is_preview_and_source_count_is_reused(self):
        _, report = self.run_pipeline()
        self.assertEqual("PREVIEW_COMPLETE", report["status"])
        self.assertFalse(report["writes_executed"])
        self.assertFalse(report["commit_attempted"])
        self.assertEqual(2, self.last_config["EXPECTED_SOURCE_RECORDS"])
        self.assertEqual([0, 0], [value["source_df"].count_calls for value in self.sources.values()])

    def test_late_preview_failure_prevents_every_commit(self):
        def fail(name, config):
            if name == "two": raise RuntimeError("private record and payload")
        self.fail_preview = fail
        report = self.failure()
        self.assertEqual("FAILED_BEFORE_COMMIT", report["status"])
        self.assertEqual(("two", "SSP"), report["failed_route"])
        self.assertFalse(report["commit_attempted"])
        self.assertFalse(report["writes_executed"])
        self.assertFalse(any(event[0] == "commit" for event in self.events))
        self.assertNotIn("private", json.dumps(report))

    def test_first_group_postcommit_failure_keeps_committed_fact(self):
        def fail(name, config):
            raise LOADER["LoadError"]("POST_COMMIT_READBACK_FAILED_DO_NOT_RETRY",
                {"status": "POST_COMMIT_READBACK_FAILED_DO_NOT_RETRY", "committed": True,
                 "writes_executed": True, "persisted": True})
        self.fail_commit = fail
        report = self.failure()
        self.assertEqual("COMMIT_FAILED_REVIEW_REQUIRED", report["status"])
        self.assertEqual(("one", "SSP"), report["failed_route"])
        self.assertTrue(report["writes_executed"])
        self.assertTrue(report["load_error"]["committed"])
        self.assertTrue(report["load_error"]["persisted"])
        self.assertEqual([("commit", "one")], [event for event in self.events if event[0] == "commit"])

    def test_later_group_failure_preserves_earlier_success(self):
        def fail(name, config):
            if name == "two":
                raise LOADER["LoadError"]("TRANSACTION_ROLLED_BACK", {"status": "TRANSACTION_ROLLED_BACK",
                    "writes_executed": False, "persisted": False, "rollback_readback_verified": True})
        self.fail_commit = fail
        report = self.failure()
        self.assertEqual(("two", "SSP"), report["failed_route"])
        self.assertTrue(report["writes_executed"])
        self.assertEqual("COMMITTED_AND_VERIFIED", report["groups"][0]["load"]["status"])
        self.assertTrue(report["groups"][0]["load"]["persisted"])
        self.assertFalse(report["load_error"]["persisted"])

    def test_unknown_commit_stops_without_retry(self):
        def fail(name, config):
            raise LOADER["LoadError"]("COMMIT_OUTCOME_UNKNOWN_DO_NOT_RETRY",
                {"status": "COMMIT_OUTCOME_UNKNOWN_DO_NOT_RETRY", "persisted": "UNKNOWN", "writes_executed": False})
        self.fail_commit = fail
        report = self.failure()
        self.assertEqual("UNKNOWN", report["load_error"]["persisted"])
        self.assertEqual([("commit", "one")], [event for event in self.events if event[0] == "commit"])
        self.assertTrue(report["commit_attempted"])

    def test_matching_cell_six_release_is_required_before_graph_work(self):
        for release in (None, "oscal-shared-daily-upsert-v2", LOADER["OSCAL_LOAD_RELEASE"] + "-different"):
            with self.subTest(release=release):
                self.ns["validate_and_load_oscal"]._oscal_loader_release = release
                report = self.failure("PREVIEW")
                self.assertFalse(report["commit_attempted"])
                self.assertEqual([], self.events)

    def test_unverified_later_destination_blocks_before_any_build(self):
        self.contexts[1]["config"]["STORAGE_CONTRACT"] = None
        report = self.failure()
        self.assertEqual(("two", "SSP"), report["failed_route"])
        self.assertEqual([], self.events)
        self.assertFalse(report["writes_executed"])

    def test_global_and_per_route_configuration_remain_unchanged(self):
        original = copy.deepcopy(self.contexts)
        def mutate_private_copy(name, config):
            config["STORAGE_CONTRACT"]["TARGET_DIM"] = "MUTATED_PRIVATE_COPY"
            config["EXTRA"] = True
        self.fail_commit = mutate_private_copy
        self.run_pipeline("COMMIT")
        self.assertEqual(original, self.contexts)
        self.assertTrue(all(group["config"]["EXECUTE_WRITES"] is False for group in self.contexts))

    def test_direct_mapping_copies_run_configuration_and_returns_three_outputs(self):
        ctx = self.contexts[0]
        original = copy.deepcopy(ctx["config"])
        source = self.sources["one"]["source_df"]
        nodes, edges, result = self.ns["run_oscal_mapping"](source, None, None, ctx["config"], ctx)
        self.assertEqual(("one", "nodes"), nodes)
        self.assertEqual(("one", "edges"), edges)
        self.assertFalse(result["writes_executed"])
        self.assertEqual(1, source.count_calls)
        self.assertEqual(original, ctx["config"])
        self.assertNotIn("EXPECTED_SOURCE_RECORDS", ctx["config"])

    def test_cancelled_commit_stops_later_groups_without_claiming_rollback(self):
        def cancel(name, config): raise KeyboardInterrupt()
        self.fail_commit = cancel
        report = self.failure()
        self.assertEqual("KeyboardInterrupt", report["error_type"])
        self.assertEqual("COMMIT_FAILED_REVIEW_REQUIRED", report["status"])
        self.assertEqual({}, report["load_error"])
        self.assertEqual([("commit", "one")], [event for event in self.events if event[0] == "commit"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
