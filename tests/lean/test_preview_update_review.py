"""Read-only update review: local classifications and explicit Snowpark boundaries."""
import contextlib
import io
import json
import os
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from lean_support import ROOT
import test_loader

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
                "session": session, "MODEL_GRAPHS": graphs, "PIPELINE_REPORT": report})
        self.assertNotIn("private", output.getvalue())
        self.assertEqual("RuntimeError", json.loads(output.getvalue())["ERROR"])


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
