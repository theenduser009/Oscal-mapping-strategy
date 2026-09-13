"""Read-only update review: local classifications and explicit Snowpark boundaries."""
import contextlib
import copy
import io
import json
import os
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from lean_support import ROOT, namespace
import test_loader
from test_registry_release import mapping_rows, release_registry

HELPER = ROOT / "notebooks/validation/READ_ONLY_SSP_PREVIEW_UPDATE_REVIEW.py"


def helper():
    return runpy.run_path(str(HELPER), init_globals={
        **{name: test_loader.P[name] for name in ("_load_storage", "_DIM_FIELDS", "_AUDIT")},
        "_load_no_transaction": Mock()})


def accepted():
    config = test_loader.config()
    config.update(OSCAL_MODEL="SSP", RUN_ID="accepted-run")
    config["STORAGE_CONTRACT"]["MODEL_KEY"] = "SSP"
    load = dict(status="PREVIEW_PASSED_NO_TARGET_DML", pre_write_validation_passed=True,
                release="oscal-lean-daily-v3.1", validation_passed=True, persisted=False, committed=False,
                storage_verified=True, writes_executed=False, target_dml_attempted=False,
                nodes=70102, edges=67289, source_records=2813,
                expected_changes={"D": dict(INSERTS=0, UPDATES=1994, UNCHANGED=68108),
                                  "F": dict(INSERTS=0, UPDATES=0, UNCHANGED=67289)})
    report = dict(mode="PREVIEW", status="PREVIEW_COMPLETE", writes_executed=False,
                  commit_attempted=False, groups=[dict(source="source", model="SSP", load=load)])
    graphs = {("source", "SSP"): dict(nodes=object(), context=dict(config=config))}
    return graphs, report


def row(number=1, record="private-record", old='{"value":"old-private"}', new='{"value":"new-private"}'):
    return dict(REVIEW_KEY=number.to_bytes(16, "big"), ELEMENT_PATH="system-security-plan.metadata",
                REVIEW_RECORD=record, REVIEW_RUN="accepted-run", MISSING_TARGET=False,
                IDENTITY_CHANGED=False, PAYLOAD_CHANGED=True, OLD_JSON=old, NEW_JSON=new)


class PreviewReviewTests(unittest.TestCase):
    def setUp(self):
        self.ns = helper()

    def changes(self, old, new):
        return list(self.ns["_preview_json_changes"](old, new))

    def summary(self, rows, expected=None):
        expected = expected or dict(nodes=1, source_records=1,
                                    expected_changes={"D": dict(INSERTS=0, UPDATES=1, UNCHANGED=0)})
        return self.ns["_preview_summarize"](rows, expected, "accepted-run")

    def test_missing_null_boolean_numeric_and_literal_key_paths_are_distinct(self):
        old = {"removed": None, "enabled": False, "a/b~c": {"": 0}}
        new = {"added": None, "enabled": 0, "a/b~c": {"": 1}}
        self.assertEqual([("/a~1b~0c/", "CHANGED"), ("/added", "ADDED"),
                          ("/enabled", "CHANGED"), ("/removed", "REMOVED")], self.changes(old, new))
        self.assertEqual([("", "CHANGED")], self.changes(None, {}))

    def test_array_order_and_removed_positions_are_reported(self):
        self.assertEqual([("/0/id", "CHANGED"), ("/1/id", "CHANGED"), ("/2", "REMOVED")],
                         self.changes([{"id": "a"}, {"id": "b"}, None], [{"id": "b"}, {"id": "a"}]))

    def test_number_precision_is_preserved_and_object_order_ignored(self):
        report = self.summary([row(old='{"x":0.123456789012345678901}', new='{"x":0.123456789012345678902}')])
        self.assertEqual("/x", report["BY_JSON_MEMBER"][0]["JSON_POINTER"])
        self.assertEqual([], self.changes({"a": 1, "b": False}, {"b": False, "a": 1.0}))

    def test_aggregates_count_nodes_and_distinct_records_without_private_data(self):
        rows = [row(1), row(2)]
        expected = dict(nodes=2, source_records=1, expected_changes={"D": dict(INSERTS=0, UPDATES=2, UNCHANGED=0)})
        report = self.summary(rows, expected)
        self.assertEqual("READ_ONLY_REVIEW_COMPLETE", report["STATUS"])
        self.assertEqual(2, report["BY_JSON_MEMBER"][0]["CHANGED_NODES"])
        self.assertEqual(1, report["BY_JSON_MEMBER"][0]["AFFECTED_SOURCE_RECORDS"])
        self.assertNotIn("private", json.dumps(report))
        self.assertFalse(report["HISTORICAL_TARGET_SNAPSHOT_AVAILABLE"])

    def test_missing_duplicate_identity_and_run_changes_are_reported_as_drift(self):
        for name, value, anomaly in (("MISSING_TARGET", True, None), ("REVIEW_RUN", "other", "CANDIDATE_RUN_MISMATCH"),
                                     ("IDENTITY_CHANGED", True, "IDENTITY_PROVENANCE_CHANGED")):
            with self.subTest(name=name):
                changed = row()
                changed[name] = value
                report = self.summary([changed])
                self.assertEqual("READ_ONLY_REVIEW_DRIFT_DETECTED", report["STATUS"])
                if anomaly:
                    self.assertEqual(1, report["ANOMALIES"][anomaly])
        report = self.summary([row(), row()])
        self.assertEqual(1, report["ANOMALIES"]["DUPLICATE_JOINED_KEYS"])

    def test_sql_changed_without_python_difference_is_explicit(self):
        report = self.summary([row(old='{"x":1}', new='{"x":1.0}')])
        self.assertEqual(1, report["ANOMALIES"]["SQL_CHANGED_WITHOUT_JSON_DIFFERENCE"])
        self.assertEqual("READ_ONLY_REVIEW_DRIFT_DETECTED", report["STATUS"])

    def test_identity_only_change_counts_as_update_without_payload_difference(self):
        changed = row(old=None, new=None)
        changed.update(PAYLOAD_CHANGED=False, IDENTITY_CHANGED=True)
        report = self.summary([changed])
        self.assertEqual(dict(INSERTS=0, UPDATES=1, UNCHANGED=0), report["DIM"])
        self.assertEqual("READ_ONLY_REVIEW_DRIFT_DETECTED", report["STATUS"])
        self.assertEqual(1, report["ANOMALIES"]["IDENTITY_PROVENANCE_CHANGED"])
        self.assertEqual(0, report["ANOMALIES"].get("SQL_CHANGED_WITHOUT_JSON_DIFFERENCE", 0))
        self.assertEqual([], report["BY_JSON_MEMBER"])

    def test_unchanged_rows_need_no_payload_and_record_count_drift_is_detected(self):
        unchanged = row(old=None, new=None)
        unchanged["PAYLOAD_CHANGED"] = False
        expected = dict(nodes=1, source_records=1, expected_changes={"D": dict(INSERTS=0, UPDATES=0, UNCHANGED=1)})
        report = self.summary([unchanged], expected)
        self.assertEqual("READ_ONLY_REVIEW_COMPLETE", report["STATUS"])
        self.assertEqual([], report["BY_JSON_MEMBER"])
        expected["source_records"] = 2
        self.assertEqual("READ_ONLY_REVIEW_DRIFT_DETECTED", self.summary([unchanged], expected)["STATUS"])

    def test_only_accepted_preview_and_disabled_write_config_can_query(self):
        for part, field, value in (("report", "mode", "COMMIT"), ("report", "writes_executed", True),
                                   ("load", "nodes", 19), ("load", "target_dml_attempted", True),
                                   ("load", "release", "old"), ("load", "committed", True),
                                   ("config", "EXECUTE_WRITES", True)):
            with self.subTest(part=part, field=field):
                graphs, report = accepted()
                target = {"report": report, "load": report["groups"][0]["load"],
                          "config": graphs[("source", "SSP")]["context"]["config"]}[part]
                target[field] = value
                session = Mock()
                with self.assertRaises(self.ns["PreviewReviewError"]):
                    self.ns["run_ssp_preview_update_review"](session, graphs, report)
                session.assert_not_called()
                session.table.assert_not_called()

    def test_active_transaction_blocks_before_comparison(self):
        graphs, report = accepted()
        run = self.ns["run_ssp_preview_update_review"]
        session = Mock()
        with patch.dict(run.__globals__, _load_no_transaction=Mock(side_effect=RuntimeError("active"))):
            with self.assertRaisesRegex(RuntimeError, "active"):
                run(session, graphs, report)
        session.table.assert_not_called()

    def test_query_uses_one_join_action_and_only_changed_payloads(self):
        events = []

        class Expression:
            def __eq__(self, other):
                return "join-key"

        class Frame:
            def select_expr(self, *expressions):
                events.append(("select_expr", expressions))
                return self
            def __getitem__(self, name):
                return Expression()
            def join(self, target, on, how):
                events.append(("join", on, how))
                return self
            def collect(self):
                events.append(("collect",))
                return [row()]

        graphs, report = accepted()
        graphs[("source", "SSP")]["nodes"] = Frame()
        session = SimpleNamespace(table=lambda name: Frame())
        result = self.ns["run_ssp_preview_update_review"](session, graphs, report)
        self.assertEqual(1, events.count(("collect",)))
        self.assertIn(("join", "join-key", "left"), events)
        projections = [item[1] for item in events if item[0] == "select_expr"]
        self.assertIn("TO_BINARY(NODE_KEY, 'HEX') AS REVIEW_KEY", projections[0])
        self.assertIn("REPLACE(OSCAL_UUID, '-', '') AS NEW_OSCAL_UUID", projections[0])
        self.assertIn("PARSE_JSON(METADATA_JSON) AS NEW_METADATA_JSON", projections[0])
        self.assertTrue(all(text.startswith("CASE WHEN TARGET_KEY IS NOT NULL AND ")
                            for text in projections[2] if text.endswith(("AS OLD_JSON", "AS NEW_JSON"))))
        self.assertEqual("READ_ONLY_REVIEW_DRIFT_DETECTED", result["STATUS"])

    def test_entrypoint_sanitizes_database_errors(self):
        graphs, report = accepted()
        session = SimpleNamespace(table=Mock(side_effect=RuntimeError("private-query-and-payload")))
        graphs[("source", "SSP")]["nodes"] = SimpleNamespace(select_expr=lambda *args: None)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaisesRegex(RuntimeError, "READ_ONLY_REVIEW_STOPPED"):
            runpy.run_path(str(HELPER), run_name="__main__", init_globals={
                **{name: test_loader.P[name] for name in ("_load_storage", "_DIM_FIELDS", "_AUDIT")},
                "_load_no_transaction": Mock(),
                "session": session, "MODEL_GRAPHS": graphs, "PIPELINE_REPORT": report, "SOURCE_INPUTS": {}})
        self.assertNotIn("private", output.getvalue())
        self.assertEqual("RuntimeError", json.loads(output.getvalue())["ERROR"])


class ValueReconciliationTests(unittest.TestCase):
    def setUp(self):
        runtime = namespace()
        self.ns = runpy.run_path(str(HELPER), init_globals=runtime)
        self.context = runtime["compile_mapping_contexts"](
            {"source-one": mapping_rows()}, release_registry(), runtime["SOURCE_PROFILES"],
            runtime["MODEL_CONTRACTS"], runtime["ROUTING_METADATA"])[0]
        self.impact = "system-security-plan.system-characteristics.security-impact-level"
        self.parent = "system-security-plan.system-characteristics"
        self.sensitivity = "security-sensitivity-level"
        self.rules = [r for r in self.context["compiled_plan"]["mappings"] if r["TRANSFORM_ID"] == "security-objective"]
        self.objectives = sorted({runtime["_metadata_target"](r) for r in self.rules})
        self.fields = {objective: [r["SOURCE_FIELD_NAME"] for r in self.rules
                                  if runtime["_metadata_target"](r) == objective] for objective in self.objectives}
        self.context["lookups"] = {"archer_values": {"1": "Low", "2": "High", "3": "Legacy LOE A", "4": "private-label"},
                                   "fips_values": {"1": "Low", "2": "High"}}
        self.source = {fields[0]: {"ValuesListIds": [1]} for fields in self.fields.values()}

    def changed(self, old=None, new=None, record="private-record", path=None):
        change = row(record=record, old=json.dumps(old if old is not None else dict.fromkeys(self.objectives, "fips-199-low")),
                     new=json.dumps(new if new is not None else dict.fromkeys(self.objectives, "Low")))
        change["ELEMENT_PATH"] = path or self.impact
        return change

    def run_review(self, changes, sources):
        class SourceFrame:
            def select(self, *columns):
                self.columns = columns
                return self
            def to_local_iterator(self):
                return iter(sources)
        frame = SourceFrame()
        report = self.ns["_preview_value_reconciliation"](changes, self.context, {"source_df": frame})
        self.assertEqual(("SOURCE_RECORD_ID", "CURATED_JSON"), frame.columns)
        return report

    def records(self, source=None):
        return [{"SOURCE_RECORD_ID": "private-record", "CURATED_JSON": self.source if source is None else source}]

    def test_accepted_case_and_lowercase_context_are_compared_without_mutation(self):
        before_context, before_source = copy.deepcopy(self.context), copy.deepcopy(self.source)
        report = self.run_review([self.changed()], self.records())
        self.assertEqual({"MATCH": 1}, report["IMPACT_PAYLOAD_SOURCE_CHECKS"])
        self.assertEqual({"MATCH"}, {r["ACCEPTED_TRANSFORM"] for r in report["IMPACT_SOURCE_CHECKS"]})
        self.assertEqual({"CASE_NORMALIZATION_NEEDED"}, {r["LOWERCASE_LOOKUP_TRANSFORM"] for r in report["IMPACT_SOURCE_CHECKS"]})
        self.assertEqual(before_context, self.context)
        self.assertEqual(before_source, self.source)
        self.assertFalse(report["COMMIT_AUTHORIZED"])
        self.assertNotIn("private", json.dumps(report))

    def test_transitions_preserve_exact_case_only_and_prefix_changes(self):
        old = dict(zip(self.objectives, ("Low", "low", "fips-199-low")))
        report = self.run_review([self.changed(old=old)], self.records())
        self.assertEqual({"EXACT_MATCH", "CASE_ONLY", "OTHER_TRANSITION"},
                         {r["RELATION"] for r in report["IMPACT_VALUE_TRANSITIONS"]})

    def test_only_controlled_values_and_exact_approved_legacy_are_displayed(self):
        objective = self.objectives[0]
        self.source[self.fields[objective][0]] = {"ValuesListIds": [3]}
        candidate = dict.fromkeys(self.objectives, "Low")
        candidate[objective] = "Legacy LOE A"
        previous = {objective: "private-secret", self.objectives[1]: ["private-id"], self.objectives[2]: None}
        report = self.run_review([self.changed(previous, candidate)], self.records())
        text = json.dumps(report)
        self.assertIn("Legacy LOE A", text)
        self.assertNotIn("private", text)
        self.assertEqual({"REDACTED_STR", "REDACTED_LIST", "REDACTED_NULL"},
                         {r["OLD"] for r in report["IMPACT_VALUE_TRANSITIONS"]})
        self.assertEqual({"MATCH": 1}, report["IMPACT_PAYLOAD_SOURCE_CHECKS"])
        safe = self.ns["_preview_controlled_value"]
        self.assertEqual("REDACTED_STR", safe("legacy loe a", {"Legacy LOE A"}))

    def test_unknown_and_multiple_ids_cannot_be_reported_as_single_source_match(self):
        field = self.fields[self.objectives[0]][0]
        for ids, resolution in (([1, 999], "MULTIPLE_WITH_UNKNOWN_IDS"), ([1, 2], "MULTIPLE_VALUES"), ([999], "UNKNOWN_ID")):
            with self.subTest(resolution=resolution):
                source = dict(self.source, **{field: {"ValuesListIds": ids}})
                report = self.run_review([self.changed()], self.records(source))
                self.assertEqual({"UNRESOLVED": 1}, report["IMPACT_PAYLOAD_SOURCE_CHECKS"])
                self.assertIn(resolution, {r["RESOLUTION"] for r in report["IMPACT_SOURCE_FIELDS"] if r["FIELD"] == field})
                self.assertNotIn("999", json.dumps(report))

    def test_source_mismatch_and_conflicting_rules_are_separate(self):
        candidate = dict.fromkeys(self.objectives, "High")
        report = self.run_review([self.changed(new=candidate)], self.records())
        self.assertEqual({"MISMATCH": 1}, report["IMPACT_PAYLOAD_SOURCE_CHECKS"])
        source = dict(self.source, **{self.fields[self.objectives[0]][1]: {"ValuesListIds": [2]}})
        report = self.run_review([self.changed()], self.records(source))
        self.assertIn("CONFLICTING_RULES", {r["ACCEPTED_TRANSFORM"] for r in report["IMPACT_SOURCE_CHECKS"]})

    def test_absent_parse_failed_and_duplicate_source_records_are_explicit(self):
        for sources, expected in (([], "SOURCE_RECORD_ABSENT"), (self.records("invalid-json"), "SOURCE_PARSE_ERROR"),
                                  (self.records() * 2, "DUPLICATE_SOURCE_RECORD")):
            with self.subTest(expected=expected):
                report = self.run_review([self.changed()], sources)
                self.assertEqual({expected}, {r["ACCEPTED_TRANSFORM"] for r in report["IMPACT_SOURCE_CHECKS"]})
                self.assertEqual({"UNRESOLVED": 1}, report["IMPACT_PAYLOAD_SOURCE_CHECKS"])

    def test_sensitivity_presence_shapes_lookup_and_comparison_do_not_infer_mapping(self):
        cases = [({}, "ABSENT", "EMPTY", "UNRESOLVED"), ({"SECURITY_CATEGORY": None}, "NULL", "EMPTY", "UNRESOLVED"),
                 ({"SECURITY_CATEGORY": []}, "EMPTY", "EMPTY", "UNRESOLVED"),
                 ({"SECURITY_CATEGORY": "  "}, "EMPTY", "EMPTY", "UNRESOLVED"),
                 ({"SECURITY_CATEGORY": {"ValuesListIds": [1]}}, "POPULATED", "SINGLE_LOOKUP", "CASE_ONLY"),
                 ({"SECURITY_CATEGORY": {"ValuesListIds": [1, 999]}}, "POPULATED", "MULTIPLE_WITH_UNKNOWN_IDS", "UNRESOLVED"),
                 ({"SECURITY_CATEGORY": {"ValuesListIds": [1, 2]}}, "POPULATED", "MULTIPLE_VALUES", "UNRESOLVED"),
                 ({"SECURITY_CATEGORY": "private-label"}, "POPULATED", "DIRECT_TEXT", "OTHER_TRANSITION")]
        for source, presence, resolution, relation in cases:
            with self.subTest(presence=presence, resolution=resolution):
                change = self.changed({self.sensitivity: "low"}, {}, path=self.parent)
                report = self.run_review([change], self.records(dict(self.source, **source)))
                item = report["SENSITIVITY_SOURCE"][0]
                self.assertEqual((presence, resolution, relation),
                                 (item["PRESENCE"], item["RESOLUTION"], item["SOURCE_VS_REMOVED_VALUE"]))
                self.assertEqual(1, report["SENSITIVITY_REMOVALS"])
                self.assertNotIn("private", json.dumps(report))

    def test_all_posted_nodes_reconcile_with_one_retained_source_read(self):
        changes, sources = [], []
        for number in range(1958):
            record_id = "private-" + str(number)
            sources.append({"SOURCE_RECORD_ID": record_id,
                            "CURATED_JSON": dict(self.source, SECURITY_CATEGORY={"ValuesListIds": [1]})})
            changes.append(self.changed({self.sensitivity: "Low"}, {}, record=record_id, path=self.parent))
            if number < 36:
                changes.append(self.changed(record=record_id))
        frame = SimpleNamespace(select=Mock())
        frame.select.return_value = SimpleNamespace(to_local_iterator=Mock(return_value=iter(sources)))
        report = self.ns["_preview_value_reconciliation"](changes, self.context, {"source_df": frame})
        frame.select.assert_called_once_with("SOURCE_RECORD_ID", "CURATED_JSON")
        frame.select.return_value.to_local_iterator.assert_called_once_with()
        self.assertTrue(report["COUNTS_MATCH_POSTED_REVIEW"])
        self.assertEqual({"MATCH": 36}, report["IMPACT_PAYLOAD_SOURCE_CHECKS"])
        self.assertEqual(1958, report["SENSITIVITY_SOURCE"][0]["NODES"])
        self.assertEqual("EXACT_MATCH", report["SENSITIVITY_SOURCE"][0]["SOURCE_VS_REMOVED_VALUE"])

    def test_source_read_failure_preserves_original_summary_without_private_error_text(self):
        graphs, report = accepted()
        ns = helper()
        complete = {"STATUS": "READ_ONLY_REVIEW_COMPLETE", "DIM": {"UPDATES": 1994}}
        with patch.dict(ns["run_ssp_preview_update_review"].__globals__,
                        _preview_comparison_frame=Mock(return_value=SimpleNamespace(collect=lambda: [row()])),
                        _preview_summarize=Mock(return_value=copy.deepcopy(complete)),
                        _preview_value_reconciliation=Mock(side_effect=RuntimeError("private-source-payload"))):
            actual = ns["run_ssp_preview_update_review"](Mock(), graphs, report, source_inputs={"source": object()})
        self.assertEqual(complete["DIM"], actual["DIM"])
        self.assertEqual("VALUE_RECONCILIATION_STOPPED", actual["VALUE_RECONCILIATION"]["STATUS"])
        self.assertNotIn("private", json.dumps(actual))

    def test_existing_drift_blocks_reconciliation_before_reading_sources(self):
        graphs, report = accepted()
        ns = helper()
        ns["run_ssp_preview_update_review"].__globals__["_preview_comparison_frame"] = Mock(return_value=SimpleNamespace(collect=lambda: [row()]))
        reconcile = Mock(side_effect=AssertionError("must not read retained source on drift"))
        with patch.dict(ns["run_ssp_preview_update_review"].__globals__, _preview_value_reconciliation=reconcile):
            actual = ns["run_ssp_preview_update_review"](Mock(), graphs, report, source_inputs={"source": object()})
        reconcile.assert_not_called()
        self.assertEqual("READ_ONLY_REVIEW_DRIFT_DETECTED", actual["STATUS"])


class PreviewReviewSnowparkTests(unittest.TestCase):
    """Installed binary-key join/Row transport; select_expr SQL is adapted, not live-validated."""
    @classmethod
    def setUpClass(cls):
        try:
            from snowflake.snowpark import Session, DataFrame
            from snowflake.snowpark import functions, types
        except ImportError:
            if os.environ.get("REQUIRE_SNOWPARK_TESTS") == "1":
                raise
            raise unittest.SkipTest("Snowpark localtest absent; CI requires this test") from None
        cls.Session, cls.DataFrame, cls.F, cls.T = Session, DataFrame, functions, types

    def test_actual_left_join_retains_duplicate_and_missing_binary_keys(self):
        session = self.Session.builder.config("local_testing", True).create()
        self.addCleanup(session.close)
        ns, T, F = helper(), self.T, self.F
        fields = [name for name in ns["_DIM_FIELDS"] if name not in ns["_AUDIT"]]
        schema = lambda names: T.StructType([T.StructField(name, T.BinaryType() if name.endswith("KEY")
                                                       else T.StringType()) for name in names])
        nodes = session.create_dataframe([
            (f"{number:032x}", "system-security-plan", "record", "accepted-run", "root", "uuid", '{}', "S", "T")
            for number in (1, 2, 3)], schema=schema([
                "NODE_KEY_TEXT", "ELEMENT_PATH", "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID", "ELEMENT_TYPE",
                "OSCAL_UUID", "METADATA_JSON", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME"]))
        target_names = ["TARGET_KEY"] + ["OLD_" + name for name in fields]
        target = session.create_dataframe([
            tuple([number.to_bytes(16, "big")] + ["{}" if name == "METADATA_JSON" else "value" for name in fields])
            for number in (1, 1, 2)], schema=schema(target_names))
        observed = []

        def projection(frame, *expressions):
            # The emulator cannot parse SQL expression strings. Adapt just these three projections.
            if expressions[0].startswith("TO_BINARY"):
                names = ["REVIEW_KEY", "ELEMENT_PATH", "REVIEW_RECORD", "REVIEW_RUN"] + ["NEW_" + n for n in fields]
                data = [tuple([bytes.fromhex(r["NODE_KEY_TEXT"]), r["ELEMENT_PATH"], r["SOURCE_RECORD_ID"],
                               r["DW_PIPELINE_RUN_ID"]] + [r[name] for name in fields]) for r in frame.collect()]
                return session.create_dataframe(data, schema=schema(names))
            if expressions[0].endswith("AS TARGET_KEY"):
                return frame.select(*[F.col(name) for name in target_names])
            observed.extend(frame.select("REVIEW_KEY", "TARGET_KEY").collect())
            return frame.select("REVIEW_KEY", "TARGET_KEY")

        with patch.object(self.DataFrame, "select_expr", new=projection):
            actual = ns["_preview_comparison_frame"](
                SimpleNamespace(table=lambda name: target), nodes,
                dict(TARGET_DIM="DEV.DEMO.DIM", DIM_PK_COLUMN="PK_NODE")).collect()
        self.assertEqual(4, len(actual))
        self.assertEqual(1, sum(r["TARGET_KEY"] is None for r in observed))
        self.assertEqual(2, sum(bytes(r["REVIEW_KEY"]) == (1).to_bytes(16, "big") for r in observed))


if __name__ == "__main__":
    unittest.main()
