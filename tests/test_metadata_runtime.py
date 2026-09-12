"""Metadata runtime tests: no Snowflake, writes, or field-name dispatcher."""
import copy
import json
import unittest

import test_multi_model_graph as graph
from test_typed_graph_frames import StrictGraphSession, snowpark_types_stub


ROOT_PATH = "test-model"
RESULT = ROOT_PATH + ".results[]"
OBS = RESULT + ".observations[]"


def mapping(field, owner, target="", transform="direct", params=None, transform_params=None):
    return {
        "SOURCE_FIELD_NAME": field, "OWNER_ELEMENT_PATH": owner,
        "OSCAL_ELEMENT_PATH": owner + ("." + target if target else ""),
        "FIELD_RELATIVE_PATH": target, "OSCAL_FIELD_NAME": target,
        "TRANSFORM_ID": transform, "TRANSFORM_PARAMS": transform_params or {},
        "REPRESENTATION_PARAMS": params or {}, "APPROVAL_STATUS": "APPROVED",
    }


def element(operator="object", **parameters):
    return {"operator": operator, "parameters": parameters}


def context(rows, elements=None, groups=None):
    if elements is None:
        elements = {
            ROOT_PATH: element("object", materialize_empty=True, include_uuid=True),
            RESULT: element("record", parent_instance_rule="singleton", include_uuid=True),
            OBS: element("observations", parent_instance_rule="source-record",
                         include_uuid=True, property_name_rule="source-field-slug"),
        }
    compiled = {
        "config": {
            "SOURCE_SYSTEM_NAME": "TEST", "SOURCE_TABLE_NAME": "TABLE_A",
            "OSCAL_MODEL": "TEST_MODEL", "IDENTITY_VERSION": "v1_registry_path_instance",
            "EXECUTE_WRITES": False, "RUN_ID": "test-runtime",
        },
        "model_contract": {"MODEL_KEY": "TEST_MODEL", "ROOT_PATH": ROOT_PATH,
                           "POLICY": "metadata-v1"},
        "mapping_rows": rows, "mappings_by_path": {}, "lookups": {},
        "compiled_plan": {"version": 1, "mappings": copy.deepcopy(rows),
                          "elements": elements, "reference_groups": groups or []},
    }
    compiled["registry_rows"] = registry_rows(compiled)
    return compiled


def registry_rows(ctx, rules=None):
    rules = rules or {}
    rows = []
    operator_rules = {
        "record": "SOURCE_RECORD_ID", "observations": "SOURCE_FIELD_NAME",
        "properties": "SOURCE_FIELD_NAME+VALUE", "values": "VALUE",
        "references": "CONTENT_ID",
    }
    for index, (path, spec) in enumerate(ctx["compiled_plan"]["elements"].items()):
        rows.append({
            "OSCAL_MODEL_KEY": ctx["config"]["OSCAL_MODEL"], "NODE_PATH": path,
            "PARENT_NODE_PATH": path.rsplit(".", 1)[0] if "." in path else None,
            "IS_ACTIVE": True, "IS_COLLECTION": path.endswith("[]"),
            "ELEMENT_TYPE": path.rsplit(".", 1)[-1].replace("[]", ""),
            "PROCESS_ORDER": index + 1,
            "INSTANCE_KEY_RULE": rules.get(path, operator_rules.get(spec["operator"])),
            "ITEM_PATH": None,
        })
    return rows


def registry(ctx, rules=None):
    return graph.Frame(registry_rows(ctx, rules))


def build(ns, ctx, data=None, reg=None):
    rows = data if data is not None else [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {}}]
    cfg = ctx["config"]
    # Support the real empty-data schema contract without installing Snowpark.
    ns["session"] = StrictGraphSession()
    with snowpark_types_stub():
        return ns["build_oscal_graph"](
            graph.Frame(rows), graph.Frame(ctx["mapping_rows"]), reg or registry(ctx),
            cfg["OSCAL_MODEL"], cfg["SOURCE_SYSTEM_NAME"], cfg["SOURCE_TABLE_NAME"], context=ctx,
        )


def payload_at(nodes, path):
    return [json.loads(row["METADATA_JSON"]) for row in nodes.rows if row["ELEMENT_PATH"] == path]


class MetadataRuntimeTests(unittest.TestCase):
    def test_third_model_and_new_score_field_use_metadata_only(self):
        ns = graph.namespace()
        ns["_mapping_handler_for_row"] = lambda *args: self.fail("Legacy field dispatcher called")
        ns["_legacy_prepare_model_context"] = lambda *args: self.fail("Legacy model selector called")
        ns["_SCORE_ACCEPTED_FIELDS"] = ()
        self.assertNotIn("MODEL_GRAPH_POLICIES", ns)
        self.assertNotIn("APPROVED_TEXT_MAPPING_CONTRACTS", ns)
        self.assertNotIn("COMPONENT_SOURCE_TYPES", ns)
        rows = [mapping("NEVER_SEEN_BEFORE_SCORE", OBS, transform="scalar-score")]
        ctx = context(rows)
        nodes, edges = build(ns, ctx, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON":
                                      {"NEVER_SEEN_BEFORE_SCORE": 0}}])
        self.assertEqual((3, 2), (len(nodes.rows), len(edges.rows)))
        self.assertEqual(payload_at(nodes, OBS)[0]["props"], [
            {"name": "never-seen-before-score", "value": "0"}])
        self.assertTrue(ctx["graph_report"]["OUTPUTS_PUBLISHED"])
        self.assertFalse(ctx["graph_report"]["WRITES_EXECUTED"])

    def test_metadata_only_new_row_reuses_engine_without_field_registration(self):
        ns = graph.namespace()
        first = context([mapping("FIRST", OBS, transform="scalar-score")])
        second = copy.deepcopy(first)
        second["compiled_plan"]["mappings"].append(mapping("SECOND", OBS, transform="scalar-score"))
        data = [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"FIRST": 1, "SECOND": 2}}]
        a, _ = build(ns, first, data)
        b, _ = build(ns, second, data)
        self.assertEqual(len(b.rows), len(a.rows) + 1)
        self.assertEqual(set(second["graph_report"]["FIELDS"]), {"FIRST", "SECOND"})

    def test_same_source_multiple_records_and_models_have_distinct_keys(self):
        ns = graph.namespace()
        ctx = context([mapping("SCORE", OBS, transform="scalar-score")])
        data = [{"SOURCE_RECORD_ID": str(i), "CURATED_JSON": {"SCORE": i}} for i in (1, 2)]
        first = build(ns, copy.deepcopy(ctx), data)
        again = build(ns, copy.deepcopy(ctx), data)
        self.assertEqual(graph.business(first[0].rows), graph.business(again[0].rows))
        other = copy.deepcopy(ctx)
        other["config"]["SOURCE_TABLE_NAME"] = "TABLE_B"
        second = build(ns, other, data)
        self.assertFalse({r["NODE_KEY"] for r in first[0].rows} & {r["NODE_KEY"] for r in second[0].rows})
        nodes_by_key = {r["NODE_KEY"]: r for r in first[0].rows}
        for edge in first[1].rows:
            parent = nodes_by_key[edge["FK_SOURCE_ELEMENT_HASH"]]
            child = nodes_by_key[edge["FK_TARGET_ELEMENT_HASH"]]
            self.assertEqual(parent["SOURCE_RECORD_ID"], child["SOURCE_RECORD_ID"])
            self.assertEqual(parent["INSTANCE_KEY"], child["PARENT_INSTANCE_KEY"])

    def test_unapproved_and_unknown_transform_metadata_fail_closed(self):
        for bad in ("approval", "transform"):
            with self.subTest(bad=bad):
                row = mapping("NEW_FIELD", OBS, transform="scalar-score")
                row["APPROVAL_STATUS" if bad == "approval" else "TRANSFORM_ID"] = "unknown"
                with self.assertRaises(ValueError):
                    build(graph.namespace(), context([row]))

    def test_blocked_if_populated_only_allows_null_omission(self):
        row = mapping("UNRESOLVED", ROOT_PATH, target="value", transform="reject-populated")
        row["APPROVAL_STATUS"] = "BLOCKED_IF_POPULATED"
        ctx = context([row], {ROOT_PATH: element("object", materialize_empty=True)})
        nodes, _ = build(graph.namespace(), copy.deepcopy(ctx))
        self.assertEqual(payload_at(nodes, ROOT_PATH), [{}])
        with self.assertRaisesRegex(ValueError, "rejected"):
            build(graph.namespace(), copy.deepcopy(ctx), [
                {"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"UNRESOLVED": "private-value"}}])
        row["TRANSFORM_ID"] = "direct"
        with self.assertRaises(ValueError):
            build(graph.namespace(), context([row], ctx["compiled_plan"]["elements"]))

    def test_new_date_and_nested_target_are_declarative(self):
        rows = [mapping("NEW_DATE", ROOT_PATH, target="details.valid-from", transform="date")]
        ctx = context(rows, {ROOT_PATH: element("object", materialize_empty=True)})
        nodes, _ = build(graph.namespace(), ctx, [
            {"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"NEW_DATE": "2026-09-11T23:50:00-07:00"}}])
        self.assertEqual(payload_at(nodes, ROOT_PATH), [{"details": {"valid-from": "2026-09-11"}}])

    def test_controlled_source_and_configuration_fields_are_metadata(self):
        ctx = context([], {ROOT_PATH: element(
            "object", controlled_fields=[
                {"target": "title", "source_field": "DISPLAY_NAME", "transform_id": "text", "required": True},
                {"target": "version", "config_key": "DOCUMENT_VERSION", "transform_id": "canonical-text"},
            ])})
        ctx["config"]["DOCUMENT_VERSION"] = "1.0"
        nodes, _ = build(graph.namespace(), copy.deepcopy(ctx), [
            {"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"DISPLAY_NAME": "Title"}}])
        self.assertEqual(payload_at(nodes, ROOT_PATH), [{"title": "Title", "version": "1.0"}])
        with self.assertRaises(ValueError):
            build(graph.namespace(), ctx)

    def test_named_properties_require_explicit_naming_policy(self):
        path = ROOT_PATH + ".props[]"
        row = mapping("FLAG", path, transform="archer-select", params={"namespace": "https://example.test/ns"})
        elements = {ROOT_PATH: element(materialize_empty=True),
                    path: element("properties", property_name_rule="source-field-slug")}
        ctx = context([row], elements)
        nodes, _ = build(graph.namespace(), ctx, [
            {"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"FLAG": False}}])
        self.assertEqual(payload_at(nodes, path), [
            {"name": "flag", "value": "false", "ns": "https://example.test/ns"}])
        del elements[path]["parameters"]["property_name_rule"]
        with self.assertRaises(ValueError):
            build(graph.namespace(), context([row], elements), [
                {"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"FLAG": False}}])

    def test_partial_optional_assembly_omits_without_inventing_values(self):
        path = ROOT_PATH + ".impact"
        elements = {ROOT_PATH: element(materialize_empty=True),
                    path: element(required_members=["a", "b"], optional_assembly=True)}
        ctx = context([mapping("A", path, "a", "text")], elements)
        nodes, _ = build(graph.namespace(), ctx, [
            {"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"A": "low"}}])
        self.assertEqual(payload_at(nodes, path), [])

    def test_crosswalk_generated_remarks_never_override_explicit_source_remarks(self):
        state = mapping("STATE", ROOT_PATH, "state", "status-crosswalk", transform_params={
            "crosswalk": {"legacy": "other"}, "other_remarks_prefix": "Source: ",
        })
        comment = mapping("COMMENT", ROOT_PATH, "remarks", "text")
        data = [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"STATE": "legacy", "COMMENT": "Reviewed comment"}}]
        for rows in ([state, comment], [comment, state]):
            ctx = context(rows, {ROOT_PATH: element(materialize_empty=True)})
            nodes, _ = build(graph.namespace(), ctx, data)
            self.assertEqual(payload_at(nodes, ROOT_PATH), [{"state": "other", "remarks": "Reviewed comment"}])

    def test_new_reference_field_uses_declared_type_and_identity(self):
        path = ROOT_PATH + ".assets[]"
        rows = [mapping("ASSET_IDS", path, params={"reference_type": "device"})]
        elements = {ROOT_PATH: element(materialize_empty=True), path: element("references", include_uuid=True)}
        ctx = context(rows, elements)
        ns = graph.namespace()
        ns["_component_mapping_type"] = lambda *args: self.fail("Legacy source/type selector called")
        self.assertNotIn("COMPONENT_SOURCE_TYPES", ns)
        nodes, _ = build(ns, ctx, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {
            "ASSET_IDS": [{"ContentId": 123}, 123]}}])
        payloads = payload_at(nodes, path)
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["type"], "device")
        self.assertIn("uuid", payloads[0])

    def test_reference_type_collision_is_not_silently_deduplicated(self):
        path = ROOT_PATH + ".assets[]"
        rows = [mapping("LEFT", path, params={"reference_type": "device"}),
                mapping("RIGHT", path, params={"reference_type": "software"})]
        elements = {ROOT_PATH: element(materialize_empty=True), path: element("references")}
        with self.assertRaisesRegex(ValueError, "contradictory types"):
            build(graph.namespace(), context(rows, elements), [{"SOURCE_RECORD_ID": "100",
                  "CURATED_JSON": {"LEFT": [123], "RIGHT": [123]}}])

    def test_hydration_routes_are_metadata_not_legacy_source_type_map(self):
        path = ROOT_PATH + ".assets[]"
        row = mapping("NEW_ASSET", path, params={
            "reference_type": "device", "hydrate_lookup": "inventory", "description_required": True})
        ctx = context([row], {ROOT_PATH: element(materialize_empty=True),
                              path: element("references", include_uuid=True)})
        ctx["lookups"] = {
            "component_contract": {"inventory": {
                "source_table": "TEST.RAW.INVENTORY", "title_field": "LABEL", "description_field": "DETAILS"}},
            "component_sources": {"inventory": object()},
        }
        ns = graph.namespace()
        self.assertNotIn("COMPONENT_SOURCE_TYPES", ns)
        captured = []
        def query_backend(source, rows, frames, supplied_context):
            spec = supplied_context["_metadata_hydration_spec"]
            captured.append(spec)
            self.assertEqual(set(frames), {"device"})
            return {"device": {"123": {"title": "Device", "description": "Details"}}}
        ns["_build_component_hydration_lookups"] = query_backend
        nodes, _ = build(ns, ctx, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"NEW_ASSET": [123]}}])
        self.assertEqual(captured[0]["routes"], {"NEW_ASSET": "device"})
        self.assertEqual(payload_at(nodes, path)[0]["description"], "Details")

    def test_report_metadata_cannot_fabricate_write_success(self):
        ctx = context([])
        ctx["compiled_plan"]["report"] = {"WRITES_EXECUTED": True}
        with self.assertRaisesRegex(ValueError, "safety evidence"):
            build(graph.namespace(), ctx)

    def test_invalid_score_aborts_all_outputs_with_aggregate_counts(self):
        ctx = context([mapping("NEW_SCORE", OBS, transform="scalar-score")])
        with self.assertRaisesRegex(ValueError, "rejected"):
            build(graph.namespace(), ctx, [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {"NEW_SCORE": [1, 2]}}])
        self.assertFalse(ctx["graph_report"]["OUTPUTS_PUBLISHED"])
        self.assertEqual(ctx["graph_report"]["FIELDS"]["NEW_SCORE"]["invalid"], 1)

    def test_unknown_mapping_representation_does_not_fall_back_to_scalar(self):
        row = mapping("VALUE", OBS, transform="scalar-score")
        row["REPRESENTATION"] = "unimplemented-representation"
        with self.assertRaisesRegex(ValueError, "Unknown metadata mapping representation"):
            build(graph.namespace(), context([row]))

    def test_linked_role_party_identity_rules_come_only_from_metadata(self):
        roles, parties, assignments = [ROOT_PATH + suffix for suffix in
                                       (".roles[]", ".parties[]", ".assignments[]")]
        elements = {
            ROOT_PATH: element(materialize_empty=True),
            roles: element("roles"), parties: element("parties", uuid_from_instance=True, include_uuid=True),
            assignments: element("assignments"),
        }
        row = mapping("NEW_USER_FIELD", assignments, params={"role_id": "reviewer", "role_title": "Reviewer"})
        group = {"roles_path": roles, "parties_path": parties, "assignments_path": assignments,
                 "party_type": "person", "party_uuid_parts": [
                     "$source_system", "$source_record", "party", "$reference_id"],
                 "source_namespace": {"SOURCE_SYSTEM_NAME": "TEST", "SOURCE_TABLE_NAME": "TABLE_A",
                                      "MODEL_KEY": "TEST_MODEL"}}
        ctx = context([row], elements, [group])
        ns = graph.namespace()
        ns["_party_uuid"] = lambda *args: self.fail("Legacy source identity selection called")
        self.assertNotIn("RESPONSIBLE_PARTY_ROLE_DEFINITIONS", ns)
        data = [{"SOURCE_RECORD_ID": "100", "CURATED_JSON": {
            "NEW_USER_FIELD": {"UserList": [{"Id": "user-1"}, {"Id": "user-1"}]}}}]
        first, _ = build(ns, copy.deepcopy(ctx), data)
        expected = ns["_deterministic_uuid"]("TEST", "100", "party", "user-1")
        self.assertEqual(payload_at(first, parties), [{"type": "person", "uuid": expected}])
        self.assertEqual(payload_at(first, roles), [{"id": "reviewer", "title": "Reviewer"}])
        self.assertEqual(payload_at(first, assignments), [{"role-id": "reviewer", "party-uuids": [expected]}])
        assignment = next(n for n in first.rows if n["ELEMENT_PATH"] == assignments)
        self.assertEqual(assignment["INSTANCE_KEY"], "NEW_USER_FIELD")
        other = copy.deepcopy(ctx)
        other["config"]["SOURCE_TABLE_NAME"] = "TABLE_B"
        second, _ = build(ns, other, data)
        self.assertNotEqual(payload_at(second, parties)[0]["uuid"], expected)

    def test_registry_identity_drift_blocks_even_when_mapping_is_approved(self):
        ctx = context([mapping("NEW_SCORE", OBS, transform="scalar-score")])
        ctx["registry_rows"] = registry_rows(ctx, {OBS: "LIST_INDEX"})
        with self.assertRaisesRegex(ValueError, "SOURCE_FIELD_NAME identity"):
            build(graph.namespace(), ctx)


if __name__ == "__main__":
    unittest.main()

