"""Linked identities keep ordered deduplication, attribution and record isolation."""
import copy
import unittest
from unittest.mock import Mock

import test_metadata_runtime as runtime
import test_multi_model_graph as graph


ROOT = runtime.ROOT_PATH
ROLES, PARTIES, ASSIGNMENTS = [ROOT + suffix for suffix in
                              (".roles[]", ".parties[]", ".assignments[]")]


def linked_context():
    rows = [runtime.mapping(field, ASSIGNMENTS, params={"role_id": role, "role_title": title})
            for field, role, title in (("FIRST", "reviewer", "Reviewer"),
                                       ("SECOND", "reviewer", "Reviewer"),
                                       ("THIRD", "author", "Author"))]
    group = {"roles_path": ROLES, "parties_path": PARTIES, "assignments_path": ASSIGNMENTS,
             "party_type": "person", "source_namespace": {
                 "SOURCE_SYSTEM_NAME": "TEST", "SOURCE_TABLE_NAME": "TABLE_A", "MODEL_KEY": "TEST_MODEL"}}
    return runtime.context(rows, {
        ROOT: runtime.element(materialize_empty=True), ROLES: runtime.element("roles"),
        PARTIES: runtime.element("parties", uuid_from_instance=True, include_uuid=True),
        ASSIGNMENTS: runtime.element("assignments"),
    }, [group])


class LinkedIdentityIndexTests(unittest.TestCase):
    def test_role_union_reuses_parties_preserves_order_and_first_field_identity(self):
        ns, context = graph.namespace(), linked_context()
        source = {"FIRST": ["second", "first", "second"], "SECOND": ["first", "third"],
                  "THIRD": {"UserList": [{"Id": "first"}, None]}}
        before = copy.deepcopy(source)
        nodes, _ = runtime.build(ns, context, [{"SOURCE_RECORD_ID": "record", "CURATED_JSON": source}])
        uuids = {name: ns["_deterministic_uuid"]("TEST", "record", "party", name)
                 for name in ("second", "first", "third")}
        self.assertEqual(runtime.payload_at(nodes, ROLES), [
            {"id": "reviewer", "title": "Reviewer"}, {"id": "author", "title": "Author"}])
        self.assertEqual(runtime.payload_at(nodes, PARTIES), [
            {"uuid": key, "type": "person"} for key in uuids.values()])
        self.assertEqual(runtime.payload_at(nodes, ASSIGNMENTS), [
            {"role-id": "reviewer", "party-uuids": list(uuids.values())},
            {"role-id": "author", "party-uuids": [uuids["first"]]},
        ])
        self.assertEqual([row["INSTANCE_KEY"] for row in nodes.rows if row["ELEMENT_PATH"] == ASSIGNMENTS],
                         ["FIRST", "THIRD"])
        self.assertEqual(context["graph_report"]["FIELDS"], {
            field: {"emitted": 1, "missing": 0, "invalid": 0} for field in source})
        self.assertEqual(source, before)
        self.assertNotIn("_metadata_reference_cache", context)

    def test_empty_roles_do_not_leak_between_records_or_reused_contexts(self):
        ns, context = graph.namespace(), linked_context()
        records = [{"SOURCE_RECORD_ID": "one", "CURATED_JSON": {"FIRST": ["person"]}},
                   {"SOURCE_RECORD_ID": "two", "CURATED_JSON": {"FIRST": [None]}}]
        nodes, _ = runtime.build(ns, context, records)
        self.assertEqual(len(runtime.payload_at(nodes, ROLES)), 1)
        self.assertEqual(len(runtime.payload_at(nodes, PARTIES)), 1)
        self.assertEqual(len(runtime.payload_at(nodes, ASSIGNMENTS)), 1)
        again, _ = runtime.build(ns, context, records)
        self.assertEqual(graph.business(nodes.rows), graph.business(again.rows))
        self.assertNotIn("_metadata_reference_cache", context)

    def test_conflicting_titles_for_one_role_still_abort(self):
        context = linked_context()
        context["compiled_plan"]["mappings"][1]["REPRESENTATION_PARAMS"]["role_title"] = "Conflicting"
        with self.assertRaisesRegex(ValueError, "Collection identity resolves to conflicting payloads"):
            runtime.build(graph.namespace(), context, [{"SOURCE_RECORD_ID": "record", "CURATED_JSON": {
                "FIRST": ["one"], "SECOND": ["two"],
            }}])
        self.assertFalse(context["graph_report"]["OUTPUTS_PUBLISHED"])

    def test_retry_after_graph_failure_uses_fresh_source_parties(self):
        ns, context = graph.namespace(), linked_context()
        complete = ns["_metadata_record_complete"]
        ns["_metadata_record_complete"] = Mock(side_effect=ValueError("Simulated graph validation failure"))
        with self.assertRaisesRegex(ValueError, "Simulated graph validation failure"):
            runtime.build(ns, context, [{"SOURCE_RECORD_ID": "record", "CURATED_JSON": {"FIRST": ["old"]}}])
        ns["_metadata_record_complete"] = complete
        nodes, _ = runtime.build(ns, context, [
            {"SOURCE_RECORD_ID": "record", "CURATED_JSON": {"FIRST": ["new"]}},
        ])
        expected = ns["_deterministic_uuid"]("TEST", "record", "party", "new")
        self.assertEqual(runtime.payload_at(nodes, PARTIES), [{"uuid": expected, "type": "person"}])
        self.assertEqual(runtime.payload_at(nodes, ASSIGNMENTS), [
            {"role-id": "reviewer", "party-uuids": [expected]},
        ])
        self.assertEqual(context["graph_report"]["FIELDS"]["FIRST"]["emitted"], 1)


if __name__ == "__main__":
    unittest.main()
