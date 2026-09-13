"""Graph edge cases through registered metadata, with independent frozen rules."""
import copy
import json
import unittest
from unittest.mock import Mock

from lean_support import Frame, build, business, namespace
import test_acceptance as acceptance
from test_transforms import frozen_transform_namespace
import test_metadata_driven_contract as fixtures
from test_registry_release import mapping_rows, release_registry, SUPPORT


class GraphGapTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()

    def context(self, rows, registry=None, config=None):
        profile = fixtures.profile()
        profile["BASE_CONFIG"].update(config or {})
        context = self.ns["compile_mapping_contexts"](
            {"source-one": rows}, fixtures.registry_rows() if registry is None else registry,
            [profile], {fixtures.MODEL: fixtures.model_contract()})[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"], context["routing_report"])
        context["lookups"] = {"archer_values": {}, "fips_values": {}}
        return context

    def records(self, source):
        return [{"SOURCE_RECORD_ID": "one", "CURATED_JSON": source}]

    def payload(self, nodes, path=fixtures.SUMMARY):
        return [json.loads(node["METADATA_JSON"]) for node in nodes.rows if node["ELEMENT_PATH"] == path]

    def ssp(self):
        helper = acceptance.LeanAcceptanceTests()
        helper.ns = self.ns
        return helper.ssp()

    def test_nested_mappings_do_not_change_source_or_invent_later_values(self):
        rows = [fixtures.mapping("OBJECT", fixtures.SUMMARY + ".group", transform="direct"),
                fixtures.mapping("EXTRA", fixtures.SUMMARY + ".group.added", transform="direct"),
                fixtures.mapping("OBJECT.added", fixtures.SUMMARY + ".later", transform="direct")]
        context = self.context(rows)
        frame = Frame(self.records({"OBJECT": {"original": "kept"}, "EXTRA": "mapped"}))
        before = copy.deepcopy(frame.rows)
        cfg = context["config"]
        nodes, _ = self.ns["build_oscal_graph"](frame, None, None, cfg["OSCAL_MODEL"],
                                               cfg["SOURCE_SYSTEM_NAME"], cfg["SOURCE_TABLE_NAME"], context)
        self.assertEqual(before, frame.rows)
        self.assertEqual([{"group": {"original": "kept", "added": "mapped"}}], self.payload(nodes))

    def test_distinct_json_boolean_and_number_mappings_conflict(self):
        rows = [fixtures.mapping(field, fixtures.SUMMARY + ".value", transform="direct") for field in ("A", "B")]
        for first, second in ((False, 0), (True, 1), ({"enabled": False}, {"enabled": 0})):
            with self.subTest(first=first, second=second), self.assertRaisesRegex(ValueError, "conflicting"):
                build(self.ns, self.context(rows), self.records({"A": first, "B": second}))

    def test_equal_populated_mappings_may_converge(self):
        rows = [fixtures.mapping(field, fixtures.SUMMARY + ".value", transform="direct") for field in ("A", "B")]
        nodes, _ = build(self.ns, self.context(rows), self.records({"A": {"x": 1, "y": False}, "B": {"y": False, "x": 1}}))
        self.assertEqual([{"value": {"x": 1, "y": False}}], self.payload(nodes))

    def test_scalar_object_target_collision_is_rejected(self):
        rows = [fixtures.mapping("A", fixtures.SUMMARY + ".value", transform="direct"),
                fixtures.mapping("B", fixtures.SUMMARY + ".value.member", transform="direct")]
        with self.assertRaisesRegex(ValueError, "conflicts with scalar"):
            build(self.ns, self.context(rows), self.records({"A": "scalar", "B": "nested"}))

    def value_context(self):
        path = fixtures.ROOT_PATH + ".identifiers[]"
        registry = fixtures.registry_rows() + [dict(
            OSCAL_MODEL_KEY=fixtures.MODEL, NODE_PATH=path, PARENT_NODE_PATH=fixtures.ROOT_PATH,
            IS_COLLECTION=True, IS_ACTIVE=True, INSTANCE_KEY_RULE="VALUE", ITEM_PATH="$",
            OPERATOR="values", UUID_POLICY="omit", REQUIRED_MEMBERS=None, ELEMENT_TYPE="identifier", PROCESS_ORDER=5)]
        return path, self.context([fixtures.mapping("VALUES", path + ".identity.value", transform="direct")], registry)

    def test_value_collection_normalizes_nested_identity_without_mutating_source(self):
        path, context = self.value_context()
        source = {"VALUES": [{"identity": {"value": 42}, "label": "kept"},
                             {"label": "kept", "identity": {"value": "42"}}]}
        before = copy.deepcopy(source)
        nodes, _ = build(self.ns, context, self.records(source))
        self.assertEqual(before, source)
        self.assertEqual([{"identity": {"value": "42"}, "label": "kept"}], self.payload(nodes, path))

    def test_same_collection_identity_cannot_hide_typed_payload_conflict(self):
        _, context = self.value_context()
        source = {"VALUES": [{"identity": {"value": "same"}, "enabled": False},
                             {"identity": {"value": "same"}, "enabled": 0}]}
        with self.assertRaisesRegex(ValueError, "conflicting"):
            build(self.ns, context, self.records(source))

    def test_generated_property_name_cannot_be_blank(self):
        context = self.context([fixtures.mapping("___", fixtures.OBSERVATION, transform="scalar-score")])
        with self.assertRaises(ValueError):
            build(self.ns, context, self.records({"___": 4}))

    def test_literal_source_key_precedes_nested_path_and_uppercase_fallback(self):
        rows = [fixtures.mapping("DETAIL.VALUE", fixtures.SUMMARY + ".title", transform="text"),
                fixtures.mapping("items/0/name", fixtures.SUMMARY + ".first", transform="text")]
        source = {"DETAIL.VALUE": "literal", "DETAIL": {"VALUE": "nested"}, "ITEMS": [{"NAME": "first"}]}
        nodes, _ = build(self.ns, self.context(rows), self.records(source))
        self.assertEqual([{"title": "literal", "first": "first"}], self.payload(nodes))
        frozen = frozen_transform_namespace()
        for path in ("DETAIL.VALUE", "items/0/name", "items/9/name", "missing.value"):
            self.assertEqual(frozen["resolve_json_path"](source, path), self.ns["resolve_json_path"](source, path))

    def test_failed_graph_transport_does_not_report_published_outputs(self):
        for failure_at in (1, 2):
            context = self.context([fixtures.mapping()])
            self.ns["session"].create_dataframe = Mock(side_effect=[Frame([])] * (failure_at - 1)
                                                      + [RuntimeError("simulated transport failure")])
            with self.subTest(frame=failure_at), self.assertRaisesRegex(RuntimeError, "transport failure"):
                build(self.ns, context, self.records({"NEVER_SEEN_SOURCE_FIELD": "Title"}))
            self.assertFalse(context["graph_report"]["OUTPUTS_PUBLISHED"])

    def test_failed_run_party_cache_is_cleared_before_retry(self):
        context, records = self.ssp()
        assignments = next(row for row in context["mapping_rows"] if row["REPRESENTATION"] == "assignments")
        field = assignments["SOURCE_FIELD_NAME"]
        records[0]["CURATED_JSON"][field] = {"UserList": [{"Id": "old-user"}]}
        complete = self.ns["_metadata_record_complete"]
        self.ns["_metadata_record_complete"] = Mock(side_effect=ValueError("simulated final-record failure"))
        with self.assertRaisesRegex(ValueError, "final-record failure"):
            build(self.ns, context, records)
        self.ns["_metadata_record_complete"] = complete
        records[0]["CURATED_JSON"][field] = {"UserList": [{"Id": "new-user"}]}
        nodes, _ = build(self.ns, context, records)
        cfg, record_id = context["config"], records[0]["SOURCE_RECORD_ID"]
        old_uuid = self.ns["_deterministic_uuid"](cfg["SOURCE_SYSTEM_NAME"], record_id, "party", "old-user")
        new_uuid = self.ns["_deterministic_uuid"](cfg["SOURCE_SYSTEM_NAME"], record_id, "party", "new-user")
        parties = [node["OSCAL_UUID"] for node in nodes.rows if node["ELEMENT_PATH"].endswith(".parties[]")]
        self.assertIn(new_uuid, parties)
        self.assertNotIn(old_uuid, parties)
        self.assertNotIn("_metadata_reference_cache", context)

    def test_repeated_components_keep_identity_when_source_order_changes(self):
        context, records = self.ssp()
        records[0]["CURATED_JSON"].update(SUBSYSTEMS=[{"ContentId": 9}, {"ContentId": 3}, 9])
        first = build(self.ns, context, records)
        records[0]["CURATED_JSON"]["SUBSYSTEMS"] = [3, {"ContentId": 9}]
        second = build(self.ns, context, records)
        self.assertEqual([business(frame) for frame in first], [business(frame) for frame in second])

    def test_linked_role_party_union_matches_frozen_family_and_reference_checks(self):
        context, records = self.ssp()
        source = records[0]["CURATED_JSON"]
        rows = [row for row in context["mapping_rows"] if row["REPRESENTATION"] == "assignments"]
        for row in rows:
            source.pop(row["SOURCE_FIELD_NAME"], None)
        source[rows[0]["SOURCE_FIELD_NAME"]] = {"UserList": [{"Id": "b"}, {"Id": "a"}, {"Id": "b"}]}
        source[rows[1]["SOURCE_FIELD_NAME"]] = {"UserList": [{"Id": "a"}]}
        nodes, _ = build(self.ns, context, records)
        frozen = frozen_transform_namespace()
        previous = copy.deepcopy(context)
        previous["graph_report"]["FIELDS"] = {}
        group = context["compiled_plan"]["reference_groups"][0]
        registry = self.ns["_canonical_registry_rows"](None, "SSP", context)
        for name in ("roles_path", "parties_path", "assignments_path"):
            path = group[name]
            row = next(row for row in registry if row["element_path"] == path)
            expected = frozen["_metadata_instances"](source, records[0]["SOURCE_RECORD_ID"], row, previous)
            actual = [(node["INSTANCE_KEY"], json.loads(node["METADATA_JSON"]))
                      for node in nodes.rows if node["ELEMENT_PATH"] == path]
            self.assertEqual([(item["instance_key"], item["payload"]) for item in expected], actual)
            self.assertEqual(2, len(actual))
        by_path = {row["element_path"]: [node for node in nodes.rows if node["ELEMENT_PATH"] == row["element_path"]]
                   for row in registry}
        frozen["_metadata_record_complete"](by_path, previous)

    def test_same_record_id_in_two_source_tables_has_separate_graph_identity(self):
        profiles = [fixtures.profile("source-one", "TABLE_ONE"), fixtures.profile("source-two", "TABLE_TWO")]
        contexts = self.ns["compile_mapping_contexts"](
            {profile["SOURCE_KEY"]: [fixtures.mapping(source=profile["SOURCE_KEY"])] for profile in profiles},
            fixtures.registry_rows(), profiles, {fixtures.MODEL: fixtures.model_contract()})
        graphs = []
        for context in contexts:
            self.assertEqual("READY", context["routing_report"]["STATUS"])
            context["lookups"] = {"archer_values": {}, "fips_values": {}}
            nodes, edges = build(self.ns, context, self.records({"NEVER_SEEN_SOURCE_FIELD": "Same source value"}))
            self.ns["_load_graph"](nodes, edges, context["config"])
            graphs.append((nodes, edges))
        for column, frame_index in (("NODE_KEY", 0), ("OSCAL_UUID", 0), ("EDGE_KEY", 1)):
            first = {row[column] for row in graphs[0][frame_index].rows}
            second = {row[column] for row in graphs[1][frame_index].rows}
            self.assertTrue(first)
            self.assertTrue(first.isdisjoint(second), column)

    def test_required_config_uses_config_value_and_rejects_after_conversion(self):
        row = fixtures.mapping("CONTROLLED", fixtures.SUMMARY + ".version", transform="canonical-text",
                               VALUE_SOURCE="CONFIG", VALUE_REQUIRED="true")
        context = self.context([row], config={"CONTROLLED": "1.0"})
        nodes, _ = build(self.ns, context, self.records({"CONTROLLED": "source-must-not-override"}))
        self.assertEqual([{"version": "1.0"}], self.payload(nodes))
        for value in (None, "", " 1.0 ", 1):
            context["config"]["CONTROLLED"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                build(self.ns, context, self.records({"CONTROLLED": "1.0"}))

    def test_required_field_checks_resolved_value_not_just_raw_wrapper(self):
        row = fixtures.mapping("SELECTED", fixtures.SUMMARY + ".value", transform="archer-select", VALUE_REQUIRED="true")
        context = self.context([row])
        context["lookups"]["archer_values"] = {"1": ""}
        with self.assertRaises(ValueError):
            build(self.ns, context, self.records({"SELECTED": 1}))

    def test_native_status_remarks_override_crosswalk_explanation_as_accepted(self):
        profile = copy.deepcopy(self.ns["SOURCE_PROFILES"][0])
        profile["MODEL_KEYS"] = ("SSP",)
        rows = [row for row in mapping_rows() if row["SOURCE_FIELD_NAME"] in ("OPERATIONAL_STATUS", "AUTHORIZATION_COMMENTS")
                or row["RULE_ID"] in SUPPORT]
        context = self.ns["compile_mapping_contexts"]({"source-one": rows}, release_registry(),
            [profile], self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        context["lookups"] = {"archer_values": {}, "fips_values": {}}
        source = {"AUTHORIZATION_PACKAGE_NAME": "Example", "OPERATIONAL_STATUS": "Reauthorize",
                  "AUTHORIZATION_COMMENTS": "Reviewed native remarks"}
        path = "system-security-plan.system-characteristics.status"
        nodes, _ = build(self.ns, context, self.records(source))
        actual = self.payload(nodes, path)
        self.assertEqual([{"state": "other", "remarks": "Reviewed native remarks"}], actual)
        frozen = frozen_transform_namespace()
        previous = copy.deepcopy(context)
        previous["graph_report"]["FIELDS"] = {}
        registry_row = next(row for row in self.ns["_canonical_registry_rows"](None, "SSP", context) if row["element_path"] == path)
        expected = frozen["_metadata_instances"](source, "one", registry_row, previous)
        self.assertEqual([item["payload"] for item in expected], actual)


if __name__ == "__main__":
    unittest.main()
