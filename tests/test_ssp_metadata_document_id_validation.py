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
    / "RUN_AFTER_07_ssp_metadata_document_id_validation.py"
)
TARGET_PATH = "system-security-plan.metadata.document-ids[]"
TARGET_OSCAL_PATH = TARGET_PATH + ".identifier"


class _FakeFrame:
    def __init__(self, rows):
        self.rows = list(rows)

    def select(self, *unused_columns):
        return _FakeFrame(self.rows)

    def to_local_iterator(self):
        return iter(self.rows)


def _parse_source_json(row):
    return json.loads(row["CURATED_JSON"])


def _resolve_json_path(source_obj, field_path):
    return source_obj.get(field_path)


def _has_value(value):
    return value not in (None, "", [], {})


def _transform_document_identifier(value):
    if isinstance(value, (bool, dict, list)) or value is None:
        raise ValueError("Document identifier must be a single scalar value")
    identifier = str(value).strip()
    if not identifier or identifier.lower() in {
        "nan",
        "inf",
        "+inf",
        "-inf",
    }:
        raise ValueError("Document identifier is empty or non-finite")
    return identifier


def _mapping_row(**overrides):
    row = {
        "SOURCE_FIELD_NAME": "TRACKING_ID",
        "OWNER_ELEMENT_PATH": TARGET_PATH,
        "OSCAL_ELEMENT_PATH": TARGET_OSCAL_PATH,
        "OSCAL_FIELD_NAME": "identifier",
        "MAPPING_TYPE": "Direct",
    }
    row.update(overrides)
    return row


def _node(record_id, path, payload="{}", instance_key="singleton"):
    return {
        "SOURCE_RECORD_ID": record_id,
        "ELEMENT_PATH": path,
        "INSTANCE_KEY": instance_key,
        "METADATA_JSON": payload,
    }


class MetadataDocumentIdValidationTests(unittest.TestCase):
    def _execute(
        self,
        source_values=None,
        document_nodes=None,
        graph_ids=None,
        mapping_rows=None,
        config_overrides=None,
        run_result_overrides=None,
        omit_global=None,
    ):
        if source_values is None:
            source_values = {
                "private-record-one": "  private-tracking-one  ",
                "private-record-two": 42,
                "private-record-three": None,
            }
        source_rows = [
            {
                "SOURCE_RECORD_ID": record_id,
                "CURATED_JSON": json.dumps({"TRACKING_ID": value}),
            }
            for record_id, value in source_values.items()
        ]
        if document_nodes is None:
            document_nodes = [
                _node(
                    "private-record-one",
                    TARGET_PATH,
                    json.dumps({"identifier": "private-tracking-one"}),
                ),
                _node(
                    "private-record-two",
                    TARGET_PATH,
                    json.dumps({"identifier": "42"}),
                ),
            ]
        effective_graph_ids = (
            tuple(source_values) if graph_ids is None else graph_ids
        )
        node_rows = [
            _node(record_id, "system-security-plan")
            for record_id in effective_graph_ids
        ]
        node_rows.extend(document_nodes)

        config = {"OSCAL_MODEL": "SSP", "EXECUTE_WRITES": False}
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
            "CANONICAL_MAPPING_ROWS": (
                [_mapping_row()] if mapping_rows is None else mapping_rows
            ),
            "final_nodes_df": _FakeFrame(node_rows),
            "run_result": run_result,
            "_parse_source_json": _parse_source_json,
            "resolve_json_path": _resolve_json_path,
            "_has_value": _has_value,
            "transform_document_identifier": (
                _transform_document_identifier
            ),
        }
        if omit_global:
            namespace.pop(omit_global)

        captured = io.StringIO()
        result_globals = None
        exception = None
        with contextlib.redirect_stdout(captured):
            try:
                result_globals = runpy.run_path(
                    str(VALIDATION_PATH), init_globals=namespace
                )
            except Exception as error:  # asserted by failure cases
                exception = error
        return result_globals, captured.getvalue(), exception

    def test_exact_scalar_conversion_and_absence_pass_privately(self):
        result_globals, output, exception = self._execute()

        self.assertIsNone(exception)
        result = result_globals["metadata_document_id_validation_result"]
        self.assertEqual(result["RESULT"], "PASSED")
        self.assertEqual(result["POPULATED_TRACKING_IDS"], 2)
        self.assertEqual(result["ABSENT_TRACKING_IDS"], 1)
        self.assertEqual(result["EXACT_IDENTIFIER_MATCHES"], 2)
        self.assertEqual(result["VALUE_MISMATCHES"], 0)
        self.assertFalse(result["WRITES_EXECUTED"])

        private_values = (
            "private-record-one",
            "private-record-two",
            "private-record-three",
            "private-tracking-one",
        )
        serialized = json.dumps(result, sort_keys=True)
        for private_value in private_values:
            self.assertNotIn(private_value, output)
            self.assertNotIn(private_value, serialized)

    def test_mapping_contract_drift_fails_closed(self):
        cases = (
            [],
            [_mapping_row(), _mapping_row()],
            [_mapping_row(SOURCE_FIELD_NAME="OTHER")],
            [_mapping_row(OWNER_ELEMENT_PATH="system-security-plan.metadata")],
            [_mapping_row(OSCAL_ELEMENT_PATH=TARGET_PATH + ".other")],
            [_mapping_row(OSCAL_FIELD_NAME="other")],
            [_mapping_row(MAPPING_TYPE="Transform")],
        )
        for mapping_rows in cases:
            with self.subTest(mapping_rows=mapping_rows):
                _, output, exception = self._execute(
                    mapping_rows=mapping_rows
                )
                self.assertIsInstance(exception, RuntimeError)
                self.assertIn("Mapping contract valid: False", output)

    def test_invalid_source_value_fails_without_leaking_value(self):
        source_values = {
            "private-record": {
                "private-secret-key": "private-secret-value"
            }
        }
        _, output, exception = self._execute(
            source_values=source_values,
            graph_ids=("private-record",),
            document_nodes=[],
        )

        self.assertIsInstance(exception, RuntimeError)
        self.assertIn("Invalid TRACKING_ID values: 1", output)
        self.assertNotIn("private-record", output)
        self.assertNotIn("private-secret-key", output)
        self.assertNotIn("private-secret-value", output)

    def test_missing_unexpected_and_duplicate_nodes_fail_closed(self):
        cases = (
            (
                [],
                "Missing document-id nodes: 2",
            ),
            (
                [
                    _node(
                        "private-record-three",
                        TARGET_PATH,
                        json.dumps({"identifier": "unexpected-secret"}),
                    )
                ],
                "Unexpected document-id nodes: 1",
            ),
            (
                [
                    _node(
                        "private-record-one",
                        TARGET_PATH,
                        json.dumps({"identifier": "private-tracking-one"}),
                    ),
                    _node(
                        "private-record-one",
                        TARGET_PATH,
                        json.dumps({"identifier": "private-tracking-one"}),
                    ),
                    _node(
                        "private-record-two",
                        TARGET_PATH,
                        json.dumps({"identifier": "42"}),
                    ),
                ],
                "Duplicate document-id nodes: 1",
            ),
        )
        for nodes, expected_line in cases:
            with self.subTest(expected_line=expected_line):
                _, output, exception = self._execute(
                    document_nodes=nodes
                )
                self.assertIsInstance(exception, RuntimeError)
                self.assertIn(expected_line, output)
                self.assertNotIn("unexpected-secret", output)

    def test_payload_and_value_failures_are_aggregate_only(self):
        cases = (
            (
                "not-json-secret",
                "singleton",
                "Malformed document-id payloads: 1",
            ),
            (
                json.dumps({"identifier": "private-tracking-one"}),
                "wrong-instance",
                "Non-singleton document-id nodes: 1",
            ),
            (
                json.dumps({"identifier": "private-tracking-one", "x": 1}),
                "singleton",
                "Unexpected payload shapes: 1",
            ),
            (
                json.dumps({}),
                "singleton",
                "Missing identifiers: 1",
            ),
            (
                json.dumps({"identifier": 123}),
                "singleton",
                "Non-string identifiers: 1",
            ),
            (
                json.dumps({"identifier": ""}),
                "singleton",
                "Blank identifiers: 1",
            ),
            (
                json.dumps({"identifier": "private-wrong-value"}),
                "singleton",
                "Identifier value mismatches: 1",
            ),
        )
        valid_second = _node(
            "private-record-two",
            TARGET_PATH,
            json.dumps({"identifier": "42"}),
        )
        for payload, instance_key, expected_line in cases:
            with self.subTest(expected_line=expected_line):
                nodes = [
                    _node(
                        "private-record-one",
                        TARGET_PATH,
                        payload,
                        instance_key,
                    ),
                    valid_second,
                ]
                _, output, exception = self._execute(
                    document_nodes=nodes
                )
                self.assertIsInstance(exception, RuntimeError)
                self.assertIn(expected_line, output)
                self.assertNotIn("private-wrong-value", output)
                self.assertNotIn("not-json-secret", output)

    def test_source_graph_identity_mismatch_is_private(self):
        orphan = "private-orphan-record"
        _, output, exception = self._execute(
            graph_ids=("private-record-one", "private-record-two", orphan)
        )

        self.assertIsInstance(exception, RuntimeError)
        self.assertIn("Missing graph records: 1", output)
        self.assertIn("Orphan graph records: 1", output)
        self.assertNotIn(orphan, output)
        self.assertNotIn(orphan, str(exception))

    def test_missing_state_and_safety_gates_fail_closed(self):
        required_names = (
            "CONFIG",
            "source_df",
            "CANONICAL_MAPPING_ROWS",
            "final_nodes_df",
            "run_result",
            "_parse_source_json",
            "resolve_json_path",
            "_has_value",
            "transform_document_identifier",
        )
        for name in required_names:
            with self.subTest(name=name):
                _, _, exception = self._execute(omit_global=name)
                self.assertIsInstance(exception, RuntimeError)
                self.assertIn("Missing notebook state count", str(exception))

        cases = (
            ({"EXECUTE_WRITES": True}, {}, "EXECUTE_WRITES"),
            ({"OSCAL_MODEL": "SAP"}, {}, "SSP model"),
            ({}, {"validation_passed": False}, "graph validation"),
            (
                {},
                {"pre_write_validation_passed": False},
                "pre-write validation",
            ),
            ({}, {"writes_executed": True}, "read-only"),
        )
        for config, run_result, message in cases:
            with self.subTest(message=message):
                _, _, exception = self._execute(
                    config_overrides=config,
                    run_result_overrides=run_result,
                )
                self.assertIsInstance(exception, RuntimeError)
                self.assertIn(message, str(exception))

    def test_source_contains_no_sql_or_write_calls(self):
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
        forbidden = {
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
        self.assertFalse(called_attributes & forbidden)


if __name__ == "__main__":
    unittest.main()
