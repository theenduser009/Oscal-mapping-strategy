import contextlib
import io
import json
from pathlib import Path
import runpy
import unittest


AUDIT_PATH = (
    Path(__file__).parents[1]
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_metadata_last_modified_audit.py"
)
TARGET_OWNER = "system-security-plan.metadata"
CANDIDATE_A = "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED"
CANDIDATE_B = "LAST_UPDATED"


class _FakeColumn:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return lambda row: row[self.name] == other


class _FakeFrame:
    def __init__(self, rows):
        self.rows = list(rows)

    def select(self, *unused_columns):
        return _FakeFrame(self.rows)

    def filter(self, predicate):
        return _FakeFrame(row for row in self.rows if predicate(row))

    def to_local_iterator(self):
        return iter(self.rows)

    def count(self):
        return len(self.rows)


def _parse_source_json(row):
    return json.loads(row["CURATED_JSON"])


def _resolve_json_path(source_object, field_name):
    return source_object.get(field_name)


def _target_field_name(mapping_row):
    return mapping_row["OSCAL_FIELD_NAME"]


class LastModifiedAuditTests(unittest.TestCase):
    def _run_audit(
        self,
        records,
        outputs,
        duplicate_metadata=False,
        config_overrides=None,
        metadata_instance_key="singleton",
    ):
        source_rows = [
            {
                "SOURCE_RECORD_ID": record_id,
                "CURATED_JSON": json.dumps(source_object),
            }
            for record_id, source_object in records.items()
        ]
        node_rows = [
            {
                "SOURCE_RECORD_ID": record_id,
                "ELEMENT_PATH": TARGET_OWNER,
                "INSTANCE_KEY": metadata_instance_key,
                "METADATA_JSON": json.dumps({"last-modified": output}),
            }
            for record_id, output in outputs.items()
        ]
        if duplicate_metadata:
            node_rows.append(dict(node_rows[0]))

        mappings = [
            {
                "SOURCE_FIELD_NAME": source_field,
                "OWNER_ELEMENT_PATH": TARGET_OWNER,
                "OSCAL_FIELD_NAME": "last-modified",
                "OSCAL_ELEMENT_PATH": TARGET_OWNER + ".last-modified",
                "MAPPING_TYPE": "Transform",
                "STATUS": "In Progress",
            }
            for source_field in (CANDIDATE_A, CANDIDATE_B)
        ]
        config = {
                "OSCAL_MODEL": "SSP",
                "OSCAL_VERSION": "1.2.3",
                "EXECUTE_WRITES": False,
        }
        config.update(config_overrides or {})
        notebook_globals = {
            "CONFIG": config,
            "source_df": _FakeFrame(source_rows),
            "mapping_df": _FakeFrame([None] * 608),
            "mapping_artifact_pdf": [None] * 608,
            "CANONICAL_MAPPING_ROWS": mappings,
            "final_nodes_df": _FakeFrame(node_rows),
            "run_result": {
                "validation_passed": True,
                "pre_write_validation_passed": True,
                "writes_executed": False,
            },
            "_parse_source_json": _parse_source_json,
            "resolve_json_path": _resolve_json_path,
            "_target_field_name": _target_field_name,
            "col": _FakeColumn,
            "lit": lambda value: value,
        }
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            result_globals = runpy.run_path(
                str(AUDIT_PATH), init_globals=notebook_globals
            )
        return result_globals["last_modified_audit_result"], captured.getvalue()

    def test_equivalent_aware_candidates_are_implementation_ready(self):
        records = {
            "record-1": {CANDIDATE_A: "2026-09-09T12:00:00Z"},
            "record-2": {CANDIDATE_B: "2026-09-09T08:00:00-04:00"},
            "record-3": {
                CANDIDATE_A: "2026-09-09T12:00:00Z",
                CANDIDATE_B: "2026-09-09T08:00:00-04:00",
            },
        }
        outputs = {
            "record-1": "2026-09-09T12:00:00Z",
            "record-2": "2026-09-09T08:00:00-04:00",
            "record-3": "2026-09-09T08:00:00-04:00",
        }

        result, output = self._run_audit(records, outputs)

        self.assertEqual(result["RESULT"], "TRANSFORM_IMPLEMENTATION_READY")
        self.assertEqual(result["OVERLAP"]["BOTH_POPULATED"], 1)
        self.assertEqual(result["OVERLAP"]["NORMALIZED_EQUAL"], 1)
        self.assertFalse(result["PRECEDENCE_DECISION_REQUIRED"])
        for sensitive_value in (*records, *outputs.values()):
            self.assertNotIn(sensitive_value, output)

    def test_naive_timestamp_requires_timezone_decision(self):
        records = {
            "record-naive": {CANDIDATE_A: "2026-09-09 12:00:00"},
        }
        outputs = {"record-naive": "2026-09-09 12:00:00"}

        result, _ = self._run_audit(records, outputs)

        self.assertEqual(result["RESULT"], "DECISION_REQUIRED")
        self.assertTrue(result["TIMEZONE_DECISION_REQUIRED"])
        self.assertEqual(result["CANDIDATE_A"]["PARSEABLE_NAIVE"], 1)

    def test_timezone_setting_does_not_auto_approve_naive_semantics(self):
        records = {
            "record-naive-utc": {CANDIDATE_A: "2026-09-09 12:00:00"},
        }
        outputs = {"record-naive-utc": "2026-09-09 12:00:00"}

        result, _ = self._run_audit(
            records,
            outputs,
            config_overrides={"LAST_MODIFIED_SOURCE_TIMEZONE": "UTC"},
        )

        self.assertTrue(result["SOURCE_TIMEZONE_CONFIGURED"])
        self.assertTrue(result["TIMEZONE_DECISION_REQUIRED"])
        self.assertEqual(result["RESULT"], "DECISION_REQUIRED")

    def test_partial_iso_datetime_is_not_accepted(self):
        records = {
            "record-partial": {CANDIDATE_A: "2026-09-09T12"},
        }
        outputs = {"record-partial": "2026-09-09T12"}

        result, _ = self._run_audit(records, outputs)

        self.assertEqual(result["CANDIDATE_A"]["UNRECOGNIZED"], 1)
        self.assertTrue(result["SOURCE_FORMAT_REVIEW_REQUIRED"])
        self.assertEqual(result["RESULT"], "DECISION_REQUIRED")

    def test_conflicting_aware_candidates_require_precedence(self):
        records = {
            "record-conflict": {
                CANDIDATE_A: "2026-09-09T12:00:00Z",
                CANDIDATE_B: "2026-09-09T13:00:00Z",
            },
        }
        outputs = {"record-conflict": "2026-09-09T13:00:00Z"}

        result, _ = self._run_audit(records, outputs)

        self.assertEqual(result["RESULT"], "DECISION_REQUIRED")
        self.assertTrue(result["PRECEDENCE_DECISION_REQUIRED"])
        self.assertEqual(result["OVERLAP"]["NORMALIZED_DIFFERENT"], 1)
        self.assertEqual(result["OVERLAP"]["CANDIDATE_B_LATER"], 1)

    def test_duplicate_metadata_nodes_fail_closed(self):
        records = {
            "record-duplicate": {CANDIDATE_A: "2026-09-09T12:00:00Z"},
        }
        outputs = {"record-duplicate": "2026-09-09T12:00:00Z"}

        with self.assertRaisesRegex(RuntimeError, "duplicate_nodes=1"):
            self._run_audit(records, outputs, duplicate_metadata=True)

    def test_invalid_policy_settings_do_not_suppress_decisions(self):
        records = {
            "record-policy": {
                CANDIDATE_A: "2026-09-09 12:00:00",
                CANDIDATE_B: "2026-09-09 13:00:00",
            },
        }
        outputs = {"record-policy": "2026-09-09 13:00:00"}

        result, _ = self._run_audit(
            records,
            outputs,
            config_overrides={
                "LAST_MODIFIED_SOURCE_PRECEDENCE": "Candidate B",
                "LAST_MODIFIED_SOURCE_TIMEZONE": "Definitely/Not_A_Zone",
            },
        )

        self.assertEqual(result["RESULT"], "DECISION_REQUIRED")
        self.assertTrue(result["PRECEDENCE_SETTING_INVALID"])
        self.assertTrue(result["SOURCE_TIMEZONE_SETTING_INVALID"])
        self.assertTrue(result["TIMEZONE_DECISION_REQUIRED"])

    def test_missing_source_is_reported_separately_from_code_readiness(self):
        records = {
            "record-populated": {CANDIDATE_A: "2026-09-09T12:00:00Z"},
            "record-missing": {},
        }
        outputs = {
            "record-populated": "2026-09-09T12:00:00Z",
            "record-missing": None,
        }

        result, _ = self._run_audit(records, outputs)

        self.assertEqual(
            result["RESULT"],
            "TRANSFORM_IMPLEMENTATION_READY_SOURCE_COMPLETENESS_REQUIRED",
        )
        self.assertTrue(result["SOURCE_COMPLETENESS_REQUIRED"])

    def test_high_precision_is_not_truncated_into_false_equality(self):
        records = {
            "record-precision": {
                CANDIDATE_A: "2026-09-09T12:00:00.1234567+00:00:00",
                CANDIDATE_B: "2026-09-09T12:00:00.1234568+00:00:00",
            },
        }
        outputs = {
            "record-precision": "2026-09-09T12:00:00.1234568+00:00:00",
        }

        result, _ = self._run_audit(records, outputs)

        self.assertEqual(result["RESULT"], "DECISION_REQUIRED")
        self.assertEqual(result["OVERLAP"].get("NORMALIZED_EQUAL", 0), 0)
        self.assertEqual(
            result["OVERLAP"]["NORMALIZED_COMPARISON_BLOCKED"], 1
        )
        self.assertTrue(result["SOURCE_FORMAT_REVIEW_REQUIRED"])

    def test_non_singleton_metadata_node_fails_closed(self):
        records = {
            "record-instance": {CANDIDATE_A: "2026-09-09T12:00:00Z"},
        }
        outputs = {"record-instance": "2026-09-09T12:00:00Z"}

        with self.assertRaisesRegex(RuntimeError, "instance_key_errors=1"):
            self._run_audit(
                records,
                outputs,
                metadata_instance_key="unexpected-instance",
            )


if __name__ == "__main__":
    unittest.main()
