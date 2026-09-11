"""Orchestrator safety tests; no Snowflake execution or target data."""
import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import unittest

CELL = Path(__file__).resolve().parents[1] / "notebooks/cells/07_mapper_orchestrator.py"


def functions():
    tree = ast.parse(CELL.read_text(encoding="utf-8"))
    ns = {"json": json}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)],
                            type_ignores=[]), str(CELL), "exec"), ns)
    return ns


class DailyOrchestrator(unittest.TestCase):
    def setUp(self):
        self.ns = functions()
        self.config = {"EXECUTE_WRITES": False, "OSCAL_MODEL": "SSP", "RUN_ID": "test-run",
                       "SOURCE_SYSTEM_NAME": "ARCHER", "SOURCE_TABLE_NAME": "SOURCE",
                       "BUILD_COVERAGE_REPORT": True}
        self.events = []
        self.ns["CANONICAL_MAPPING_ROWS"] = []
        self.ns["build_oscal_graph"] = self.graph
        self.ns["build_mapping_coverage"] = self.coverage
        self.ns["validate_and_load_oscal"] = self.loader
        self.ns["_oscal_source_count"] = lambda frame: 1

    def graph(self, **kwargs):
        self.events.append("graph")
        return "nodes", "edges"

    def coverage(self, *args):
        self.events.append("coverage")
        return "coverage"

    def loader(self, **kwargs):
        self.events.append("loader")
        self.used_config = kwargs["config"]
        return {"nodes": 4, "edges": 3, "writes_executed": kwargs["config"]["EXECUTE_WRITES"]}

    loader._oscal_loader_release = "ssp-daily-upsert-v1"

    def run_mapper(self, mode="PREVIEW"):
        with redirect_stdout(io.StringIO()):
            return self.ns["run_oscal_mapping"]("source", "mapping", "registry", self.config,
                                                load_mode=mode)

    def test_preview_default_and_order(self):
        result = self.run_mapper()
        self.assertEqual(self.events, ["graph", "coverage", "loader"])
        self.assertFalse(result[3]["writes_executed"])
        self.assertIsNot(self.config, self.used_config)
        self.assertFalse(self.config["EXECUTE_WRITES"])

    def test_commit_enables_only_copy(self):
        result = self.run_mapper("COMMIT")
        self.assertTrue(result[3]["writes_executed"])
        self.assertFalse(self.config["EXECUTE_WRITES"])

    def test_invalid_modes_fail_before_graph(self):
        for mode in ("commit", "", None, True, "ROLLBACK", "TRUNCATE"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.run_mapper(mode)
        self.assertEqual(self.events, [])

    def test_global_write_flag_cannot_bypass_mode(self):
        for value in (True, None, 0, "False"):
            self.config["EXECUTE_WRITES"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_mapper()
        self.assertEqual(self.events, [])

    def test_ar_commit_fails_before_graph(self):
        self.config["OSCAL_MODEL"] = "ASSESSMENT_RESULTS"
        with self.assertRaises(ValueError):
            self.run_mapper("COMMIT")
        self.assertEqual(self.events, [])

    def test_coverage_failure_prevents_loader(self):
        def fail(*args):
            self.events.append("coverage_failed")
            raise ValueError("invalid mapping contract")
        self.ns["build_mapping_coverage"] = fail
        with self.assertRaises(ValueError):
            self.run_mapper("COMMIT")
        self.assertEqual(self.events, ["graph", "coverage_failed"])
        self.assertFalse(self.config["EXECUTE_WRITES"])

    def test_loader_failure_does_not_change_config(self):
        def fail(**kwargs):
            raise ValueError("failed write")
        fail._oscal_loader_release = "ssp-daily-upsert-v1"
        self.ns["validate_and_load_oscal"] = fail
        with self.assertRaises(ValueError):
            self.run_mapper("COMMIT")
        self.assertFalse(self.config["EXECUTE_WRITES"])

    def test_no_coverage_path_still_loads(self):
        self.config["BUILD_COVERAGE_REPORT"] = False
        result = self.run_mapper()
        self.assertEqual(self.events, ["graph", "loader"])
        self.assertIsNone(result[2])

    def test_executable_cell_invalidates_prior_success_on_failure(self):
        from types import SimpleNamespace
        def fail(**kwargs):
            raise ValueError("graph failure")
        ns = {"CONFIG": self.config, "build_oscal_graph": fail,
              "validate_and_load_oscal": self.loader,
              "source_df": SimpleNamespace(columns=["SOURCE_RECORD_ID"], count=lambda: 1,
                  filter=lambda sql: SimpleNamespace(count=lambda: 0)),
              "canonical_mapping_df": object(),
              "element_registry_df": object(), "run_result": {"writes_executed": True},
              "final_nodes_df": "old", "final_edges_df": "old", "mapping_coverage_df": "old"}
        with redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            exec(compile(CELL.read_text(encoding="utf-8"), str(CELL), "exec"), ns)
        for key in ("run_result", "final_nodes_df", "final_edges_df", "mapping_coverage_df"):
            self.assertIsNone(ns[key])
        self.assertEqual(ns["SSP_LOAD_MODE"], "PREVIEW")
        self.assertFalse(self.config["EXECUTE_WRITES"])

    def test_old_loader_cannot_be_enabled_by_new_runner(self):
        self.ns["validate_and_load_oscal"] = lambda **kwargs: None
        for mode in ("PREVIEW", "COMMIT"):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "matching updated Cell 6"):
                self.run_mapper(mode)
        self.assertEqual(self.events, [])

    def test_missing_source_identity_is_rejected_before_stringification(self):
        from types import SimpleNamespace
        class Frame:
            columns = ["SOURCE_RECORD_ID"]
            invalid, total = 0, 1
            def filter(self, sql):
                self.last_filter = sql
                return SimpleNamespace(count=lambda: self.invalid)
            def count(self):
                return self.total
        fn = functions()["_oscal_source_count"]
        frame = Frame()
        self.assertEqual(fn(frame), 1)
        self.assertIn("IS NULL", frame.last_filter)
        for invalid, total in ((1, 1), (0, 0)):
            frame.invalid, frame.total = invalid, total
            with self.assertRaises(ValueError):
                fn(frame)


if __name__ == "__main__":
    unittest.main()
