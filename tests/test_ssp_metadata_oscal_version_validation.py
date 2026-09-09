import ast
import contextlib
import io
import json
from pathlib import Path
import runpy
import unittest


VALIDATION_PATH = (
    Path(__file__).parents[1]
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_metadata_oscal_version_validation.py"
)
METADATA_PATH = "system-security-plan.metadata"
ROOT_PATH = "system-security-plan"


class _FakeFrame:
    def __init__(self, rows):
        self.rows = list(rows)

    def select(self, *unused_columns):
        return _FakeFrame(self.rows)

    def to_local_iterator(self):
        return iter(self.rows)


def _node(record_id, path, payload, instance_key="singleton"):
    return {
        "SOURCE_RECORD_ID": record_id,
        "ELEMENT_PATH": path,
        "INSTANCE_KEY": instance_key,
        "METADATA_JSON": payload,
    }


class MetadataOscalVersionValidationTests(unittest.TestCase):
    def _execute(
        self,
        source_ids=("record-1", "record-2"),
        metadata_specs=None,
        graph_ids=None,
        config_overrides=None,
        run_result_overrides=None,
        omit_global=None,
    ):
        if metadata_specs is None:
            metadata_specs = [
                (
                    record_id,
                    json.dumps(
                        {
                            "title": "private-title-" + record_id,
                            "oscal-version": "1.2.3",
                        }
                    ),
                    "singleton",
                )
                for record_id in source_ids
            ]

        source_rows = [
            {"SOURCE_RECORD_ID": record_id} for record_id in source_ids
        ]
        effective_graph_ids = source_ids if graph_ids is None else graph_ids
        node_rows = [
            _node(record_id, ROOT_PATH, "{}")
            for record_id in effective_graph_ids
        ]
        node_rows.extend(
            _node(record_id, METADATA_PATH, payload, instance_key)
            for record_id, payload, instance_key in metadata_specs
        )

        config = {
            "OSCAL_MODEL": "SSP",
            "OSCAL_VERSION": "1.2.3",
            "EXECUTE_WRITES": False,
        }
        config.update(config_overrides or {})
        run_result = {
            "validation_passed": True,
            "pre_write_validation_passed": True,
            "writes_executed": False,
        }
        run_result.update(run_result_overrides or {})
        namespace = {
            "CONFIG": config,
            "source_df": _FakeFrame(source_rows),
            "final_nodes_df": _FakeFrame(node_rows),
            "run_result": run_result,
        }
        if omit_global:
            namespace.pop(omit_global)

        captured = io.StringIO()
        exception = None
        result_globals = None
        with contextlib.redirect_stdout(captured):
            try:
                result_globals = runpy.run_path(
                    str(VALIDATION_PATH), init_globals=namespace
                )
            except Exception as error:  # asserted by each failure test
                exception = error
        return result_globals, captured.getvalue(), exception

    def test_valid_metadata_versions_pass_with_aggregate_private_output(self):
        source_ids = (
            "sensitive-record-alpha",
            "sensitive-record-beta",
        )
        result_globals, output, exception = self._execute(
            source_ids=source_ids
        )

        self.assertIsNone(exception)
        result = result_globals[
            "metadata_oscal_version_validation_result"
        ]
        self.assertEqual(result["RESULT"], "PASSED")
        self.assertEqual(result["VALID_VERSIONS"], 2)
        self.assertEqual(result["FAILURE_COUNT"], 0)
        self.assertFalse(result["WRITES_EXECUTED"])

        serialized_result = json.dumps(result, sort_keys=True)
        for record_id in source_ids:
            self.assertNotIn(record_id, output)
            self.assertNotIn(record_id, serialized_result)
            self.assertNotIn("private-title-" + record_id, output)
            self.assertNotIn(
                "private-title-" + record_id, serialized_result
            )

    def test_missing_version_fails_closed(self):
        _, output, exception = self._execute(
            metadata_specs=[
                ("record-1", json.dumps({"title": "secret"}), "singleton"),
                (
                    "record-2",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "singleton",
                ),
            ]
        )

        self.assertIsInstance(exception, RuntimeError)
        self.assertIn("Missing oscal-version fields: 1", output)
        self.assertNotIn("secret", output)

    def test_wrong_version_fails_closed_without_printing_value(self):
        wrong_value = "private-conflicting-version"
        _, output, exception = self._execute(
            metadata_specs=[
                (
                    "record-1",
                    json.dumps({"oscal-version": wrong_value}),
                    "singleton",
                ),
                (
                    "record-2",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "singleton",
                ),
            ]
        )

        self.assertIsInstance(exception, RuntimeError)
        self.assertIn("Wrong oscal-version fields: 1", output)
        self.assertNotIn(wrong_value, output)
        self.assertNotIn(wrong_value, str(exception))

    def test_non_string_and_blank_versions_fail_closed(self):
        cases = (
            (123, "Non-string oscal-version fields: 1"),
            ("", "Blank oscal-version fields: 1"),
            ("   ", "Blank oscal-version fields: 1"),
        )
        for invalid_value, expected_line in cases:
            with self.subTest(invalid_value=invalid_value):
                _, output, exception = self._execute(
                    metadata_specs=[
                        (
                            "record-1",
                            json.dumps(
                                {"oscal-version": invalid_value}
                            ),
                            "singleton",
                        ),
                        (
                            "record-2",
                            json.dumps({"oscal-version": "1.2.3"}),
                            "singleton",
                        ),
                    ]
                )

                self.assertIsInstance(exception, RuntimeError)
                self.assertIn(expected_line, output)

    def test_malformed_or_non_object_payload_fails_closed(self):
        for invalid_payload in ("not-json", "[]"):
            with self.subTest(invalid_payload=invalid_payload):
                _, output, exception = self._execute(
                    metadata_specs=[
                        ("record-1", invalid_payload, "singleton"),
                        (
                            "record-2",
                            json.dumps({"oscal-version": "1.2.3"}),
                            "singleton",
                        ),
                    ]
                )

                self.assertIsInstance(exception, RuntimeError)
                self.assertIn("Malformed metadata payloads: 1", output)
                self.assertNotIn(invalid_payload, output)

    def test_duplicate_metadata_node_fails_closed(self):
        _, output, exception = self._execute(
            metadata_specs=[
                (
                    "record-1",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "singleton",
                ),
                (
                    "record-1",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "singleton",
                ),
                (
                    "record-2",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "singleton",
                ),
            ]
        )

        self.assertIsInstance(exception, RuntimeError)
        self.assertIn("Duplicate metadata nodes: 1", output)

    def test_non_singleton_metadata_node_fails_closed(self):
        _, output, exception = self._execute(
            metadata_specs=[
                (
                    "record-1",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "unexpected",
                ),
                (
                    "record-2",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "singleton",
                ),
            ]
        )

        self.assertIsInstance(exception, RuntimeError)
        self.assertIn("Non-singleton metadata nodes: 1", output)

    def test_missing_metadata_node_fails_closed(self):
        _, output, exception = self._execute(
            metadata_specs=[
                (
                    "record-1",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "singleton",
                )
            ]
        )

        self.assertIsInstance(exception, RuntimeError)
        self.assertIn("Missing metadata nodes: 1", output)

    def test_source_graph_identity_mismatch_fails_closed_privately(self):
        orphan_id = "private-orphan-record"
        _, output, exception = self._execute(
            graph_ids=("record-1", orphan_id),
            metadata_specs=[
                (
                    "record-1",
                    json.dumps({"oscal-version": "1.2.3"}),
                    "singleton",
                )
            ],
        )

        self.assertIsInstance(exception, RuntimeError)
        self.assertIn("Source/graph identity mismatch", str(exception))
        self.assertNotIn(orphan_id, output)
        self.assertNotIn(orphan_id, str(exception))

    def test_missing_notebook_state_fails_closed(self):
        for missing_name in (
            "CONFIG",
            "source_df",
            "final_nodes_df",
            "run_result",
        ):
            with self.subTest(missing_name=missing_name):
                _, _, exception = self._execute(
                    omit_global=missing_name
                )
                self.assertIsInstance(exception, RuntimeError)
                self.assertIn("Missing notebook state count", str(exception))

    def test_invalid_configured_version_fails_closed(self):
        invalid_versions = (None, "", "   ", 123, " 1.2.3 ")
        for invalid_version in invalid_versions:
            with self.subTest(invalid_version=invalid_version):
                _, _, exception = self._execute(
                    config_overrides={"OSCAL_VERSION": invalid_version}
                )

                self.assertIsInstance(exception, RuntimeError)
                self.assertIn("CONFIG OSCAL_VERSION", str(exception))

    def test_write_and_cell_7_safety_gates_fail_closed(self):
        cases = (
            ({"EXECUTE_WRITES": True}, {}, "EXECUTE_WRITES"),
            ({}, {"validation_passed": False}, "graph validation"),
            (
                {},
                {"pre_write_validation_passed": False},
                "pre-write validation",
            ),
            ({}, {"writes_executed": True}, "read-only"),
        )
        for config_overrides, run_overrides, message in cases:
            with self.subTest(message=message):
                _, _, exception = self._execute(
                    config_overrides=config_overrides,
                    run_result_overrides=run_overrides,
                )
                self.assertIsInstance(exception, RuntimeError)
                self.assertIn(message, str(exception))

    def test_validation_source_contains_no_sql_or_write_calls(self):
        source = VALIDATION_PATH.read_text(encoding="utf-8")
        self.assertIn("final_nodes_df", source)
        self.assertNotIn("canonical_nodes_df", source)
        tree = ast.parse(source)
        called_attributes = {
            node.func.attr.lower()
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }

        forbidden_calls = {
            "sql",
            "save_as_table",
            "merge",
            "insert",
            "insert_into",
            "update",
            "delete",
            "remove",
            "write",
        }
        self.assertFalse(called_attributes & forbidden_calls)


if __name__ == "__main__":
    unittest.main()
