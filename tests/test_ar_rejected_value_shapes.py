import contextlib
import copy
import io
import json
from pathlib import Path
import runpy
import unittest

from tests.test_assessment_results_score_batch import (
    CODE as MAPPER, config, mappings, registry, source, UnreadSource,
)
from tests.test_ssp_mapping_dispatch_contracts import _load_cell_4


CELL = Path(__file__).resolve().parents[1] / "notebooks/validation/READ_ONCE_ar_rejected_value_shapes.py"
CODE = runpy.run_path(str(CELL))
FIELDS = ("RISK_ACCEPTANCE_RBDS", "RISK_ASSESSMENT_REPORT")


class ArRejectedValueShapesTests(unittest.TestCase):
    def setUp(self):
        namespace = _load_cell_4()
        self.helpers = {name: namespace[name] for name in MAPPER["AR_HELPERS"]}

    def records(self):
        return [source("private-record-id", {
            FIELDS[0]: {"ContentId": "private-component-id", "private-key": "private-value"},
            FIELDS[1]: [{"FileName": "private-file-name", "private-file-key": "private-file-value"}],
            "OUT_OF_SCOPE": {"private-other-key": "private-other-value"},
        })]

    def baseline(self, records):
        report = MAPPER["build_ar_score_batch"](
            records, mappings(), registry(), config(), self.helpers,
        )["report"]
        self.assertEqual(report["STATUS"], "BLOCKED")
        return report

    def inspect(self, records, baseline=None, run_config=None, helpers=None, score_value=None):
        return CODE["inspect_ar_rejected_shapes"](
            records, self.baseline(records) if baseline is None else baseline,
            config() if run_config is None else run_config,
            self.helpers if helpers is None else helpers,
            MAPPER["_ar_score_value"] if score_value is None else score_value,
        )

    def test_only_rejected_fixed_field_shapes_are_aggregated_without_private_content(self):
        records = self.records() + self.records()
        records[1]["SOURCE_RECORD_ID"] = "different-private-id"
        records[1]["CURATED_JSON"][FIELDS[0]]["ContentId"] = "different-private-component"
        result = self.inspect(records)
        self.assertEqual(result["STATUS"], "SHAPE_EVIDENCE_ONLY")
        self.assertFalse(result["WRITES_EXECUTED"])
        self.assertTrue(result["MATCHES_BLOCKED_RUN"])
        self.assertEqual(result["SOURCE_RECORDS"], 2)
        self.assertEqual(result["SOURCE_PARSE_ERRORS"], 0)
        self.assertEqual(set(result["FIELDS"]), set(FIELDS))
        for field in FIELDS:
            entry = result["FIELDS"][field]
            self.assertEqual((entry["EXPECTED_REJECTED"], entry["OBSERVED_REJECTED"]), (2, 2))
            self.assertEqual(len(entry["SHAPES"]), 1)
            self.assertEqual(entry["SHAPES"][0]["count"], 2)
            self.assertEqual(entry["SHAPES"][0]["stage"], "scalar_conversion")
            self.assertEqual(entry["SHAPES"][0]["reason"], "resolved_value_is_not_scalar")
        self.assertEqual(result["FIELDS"][FIELDS[0]]["SHAPES"][0]["source_shape"], {
            "type": "object", "key_count": 2,
            "recognized_keys": {"ContentId": "string"}, "other_key_count": 1,
        })
        self.assertEqual(result["FIELDS"][FIELDS[1]]["SHAPES"][0]["source_shape"], {
            "type": "array", "length": 1, "member_shapes": [{
                "shape": {"type": "object", "key_count": 2,
                          "recognized_keys": {"FileName": "string"}, "other_key_count": 1},
                "count": 1,
            }],
        })
        text = json.dumps(result)
        for secret in ("private", "different", "OUT_OF_SCOPE"):
            self.assertNotIn(secret, text)
        self.assertNotIn("OUTPUTS_PUBLISHED", result)
        self.assertNotIn("FULL_MODEL_COMPLETE", result)

    def test_scalar_select_zero_and_missing_values_do_not_become_rejected_shapes(self):
        records = self.records() + [
            source("scalar", {FIELDS[0]: 0, FIELDS[1]: "report label"}),
            source("missing", {FIELDS[0]: None, FIELDS[1]: ""}),
            source("empty", {FIELDS[0]: [], FIELDS[1]: None}),
            source("select", {FIELDS[0]: {"ValuesListIds": [101]}, FIELDS[1]: 101}),
        ]
        result = self.inspect(records)
        self.assertTrue(result["MATCHES_BLOCKED_RUN"])
        self.assertEqual(result["SOURCE_RECORDS"], 5)
        self.assertTrue(all(row["OBSERVED_REJECTED"] == 1 for row in result["FIELDS"].values()))
        self.assertNotIn("Mission Critical", json.dumps(result))
        self.assertNotIn("report label", json.dumps(result))

    def test_unknown_value_bearing_exception_is_replaced_with_fixed_reason(self):
        def rejected(value, helpers):
            raise ValueError("secret-source-value-and-identifier")
        records = self.records()
        result = self.inspect(records, score_value=rejected)
        self.assertTrue(result["MATCHES_BLOCKED_RUN"])
        for field in FIELDS:
            self.assertEqual(result["FIELDS"][field]["SHAPES"][0]["reason"],
                             "conversion_or_lookup_rejected")
        self.assertNotIn("secret", json.dumps(result))

    def test_parse_error_and_count_drift_do_not_match_the_blocked_run(self):
        records = self.records()
        baseline = self.baseline(records)
        for invalid_json in ('{"private":', '[]', 'null'):
            with self.subTest(invalid_json=invalid_json):
                result = self.inspect(records + [source("private-bad-id", invalid_json)], baseline)
                self.assertEqual(result["SOURCE_PARSE_ERRORS"], 1)
                self.assertFalse(result["MATCHES_BLOCKED_RUN"])
                self.assertNotIn("private", json.dumps(result))
        for location in ("source", "field"):
            changed = copy.deepcopy(baseline)
            if location == "source":
                changed["SOURCE_RECORDS"] += 1
            else:
                changed["FIELDS"][FIELDS[0]]["invalid"] += 1
            self.assertFalse(self.inspect(records, changed)["MATCHES_BLOCKED_RUN"])

    def test_wrong_baseline_or_write_flag_stops_before_source_iteration(self):
        baseline = self.baseline(self.records())
        mutations = (
            ("STATUS", "MAPPED_SCOPE_BUILT"),
            ("MAPPING_RELEASE", "ar-observation-scores-v2-17-fields"),
            ("MAPPING_CONTRACT_ERRORS", [{"private": "value"}]),
            ("REGISTRY_CONTRACT_ERRORS", [{"private": "value"}]),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                changed = copy.deepcopy(baseline)
                changed[key] = value
                with self.assertRaises(ValueError):
                    self.inspect(UnreadSource(), changed)
        for flag in (True, None, "False"):
            changed = config()
            changed["EXECUTE_WRITES"] = flag
            with self.assertRaises(ValueError):
                self.inspect(UnreadSource(), baseline, run_config=changed)
        with self.assertRaises(ValueError):
            self.inspect(UnreadSource(), baseline, helpers={})
        with self.assertRaises(ValueError):
            self.inspect(UnreadSource(), baseline, score_value="not-callable")

    def test_inspection_and_main_preserve_passed_mapper_outputs_and_inputs(self):
        records = self.records()
        baseline, run_config = self.baseline(records), config()
        before = copy.deepcopy((records, baseline, run_config))
        class SourceFrame:
            def to_local_iterator(self):
                return iter(records)
        ar_nodes, ar_edges, ar_documents = object(), object(), {"private": "accepted-ar"}
        ssp_nodes, ssp_edges, ssp_documents = object(), object(), {"private": "accepted-ssp"}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            state = runpy.run_path(str(CELL), run_name="__main__", init_globals=dict(
                self.helpers, CONFIG=run_config, source_df=SourceFrame(),
                AR_HELPERS=MAPPER["AR_HELPERS"], _ar_score_value=MAPPER["_ar_score_value"],
                AR_SCORE_RUN_REPORT=baseline, AR_SCORE_NODES=ar_nodes, AR_SCORE_EDGES=ar_edges,
                AR_SCORE_DOCUMENTS=ar_documents, canonical_nodes_df=ssp_nodes,
                canonical_edges_df=ssp_edges, SSP_DOCUMENTS=ssp_documents,
            ))
        for name, original in (
            ("AR_SCORE_RUN_REPORT", baseline), ("AR_SCORE_NODES", ar_nodes),
            ("AR_SCORE_EDGES", ar_edges), ("AR_SCORE_DOCUMENTS", ar_documents),
            ("canonical_nodes_df", ssp_nodes), ("canonical_edges_df", ssp_edges),
            ("SSP_DOCUMENTS", ssp_documents),
        ):
            self.assertIs(state[name], original)
        self.assertEqual((records, baseline, run_config), before)
        self.assertEqual(json.loads(output.getvalue()), state["AR_REJECTED_VALUE_SHAPES_REPORT"])
        self.assertNotIn("private", output.getvalue())

    def test_main_sanitizes_unexpected_source_error(self):
        class SourceFrame:
            def to_local_iterator(self):
                raise RuntimeError("private-table-and-source-value")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(RuntimeError, "^Shape inspection could not complete; no source values were printed$"):
                runpy.run_path(str(CELL), run_name="__main__", init_globals=dict(
                    self.helpers, CONFIG=config(), source_df=SourceFrame(),
                    AR_HELPERS=MAPPER["AR_HELPERS"], _ar_score_value=MAPPER["_ar_score_value"],
                    AR_SCORE_RUN_REPORT=self.baseline(self.records()),
                ))
        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
