"""The compiled metadata boundary preserves validation without interpreting it twice."""
import copy
import datetime
import unittest
from unittest.mock import Mock

import test_metadata_driven_contract as contract
import test_metadata_runtime as runtime
import test_multi_model_graph as graph
from test_typed_graph_frames import StrictGraphSession, snowpark_types_stub


class UnreadSource(graph.Frame):
    """An invalid plan must fail before the first source row is read."""

    def __init__(self):
        super().__init__([{"SOURCE_RECORD_ID": "record-one", "CURATED_JSON": {}}])
        self.reads = 0

    def to_local_iterator(self):
        self.reads += 1
        raise AssertionError("Invalid metadata reached source iteration")

    def collect(self):
        self.reads += 1
        raise AssertionError("Invalid metadata reached source collection")


class CompiledMetadataBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.ns = contract.namespace()

    def assert_rejected_before_source_read(self, context, message=None):
        source = UnreadSource()
        config = context["config"]
        self.ns["session"] = StrictGraphSession()
        assertion = (self.assertRaisesRegex(ValueError, message) if message
                     else self.assertRaises(ValueError))
        with snowpark_types_stub(), assertion:
            self.ns["build_oscal_graph"](
                source, graph.Frame(context["mapping_rows"]),
                graph.Frame(context["registry_rows"]), config["OSCAL_MODEL"],
                config["SOURCE_SYSTEM_NAME"], config["SOURCE_TABLE_NAME"], context=context,
            )
        self.assertEqual(source.reads, 0)

    def test_compiled_constraints_are_not_recompiled_and_still_check_source_values(self):
        compiler = Mock(wraps=self.ns["_compile_value_constraints"])
        self.ns["_compile_value_constraints"] = compiler
        context = contract.compile_context(self.ns, [contract.mapping(
            VALUE_CONSTRAINTS={"required": True, "validation": {"enum": ["approved"]}})])
        self.assertEqual(compiler.call_count, 1)
        compiler.side_effect = AssertionError("Compiled constraints were interpreted again")

        nodes, _ = contract.build(self.ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"NEVER_SEEN_SOURCE_FIELD": "approved"},
        }])
        self.assertEqual(contract.payloads(nodes, contract.SUMMARY), [{"title": "approved"}])
        for values in ({}, {"NEVER_SEEN_SOURCE_FIELD": "unapproved"}):
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, "rejected"):
                contract.build(self.ns, copy.deepcopy(context), [{
                    "SOURCE_RECORD_ID": "record-one", "CURATED_JSON": values,
                }])
        self.assertEqual(compiler.call_count, 1)

    def test_deepcopy_preserves_compiled_execution_without_mutating_input_metadata(self):
        constraints = {"required": True, "validation": {"enum": ["stable"]}}
        row = contract.mapping(VALUE_CONSTRAINTS=constraints)
        row_before = copy.deepcopy(row)
        context = contract.compile_context(self.ns, [row])
        plan_before = copy.deepcopy(context["compiled_plan"])
        self.ns["_compile_value_constraints"] = Mock(
            side_effect=AssertionError("Copying a compiled plan must not require recompilation"))
        records = [{"SOURCE_RECORD_ID": "record-one",
                    "CURATED_JSON": {"NEVER_SEEN_SOURCE_FIELD": "stable"}}]
        copied = copy.deepcopy(context)
        first = contract.build(self.ns, context, records)
        second = contract.build(self.ns, copied, records)
        self.assertEqual(graph.business(first[0].rows), graph.business(second[0].rows))
        self.assertEqual(graph.business(first[1].rows), graph.business(second[1].rows))
        self.assertEqual(context["compiled_plan"], plan_before)
        self.assertEqual(copied["compiled_plan"], plan_before)
        self.assertEqual(row, row_before)

        copied["compiled_plan"]["mappings"][0]["VALUE_CONSTRAINTS"]["validation"]["enum"].append("new")
        self.assertEqual(context["compiled_plan"], plan_before)
        self.assertEqual(row, row_before)

    def test_approval_and_transform_changes_after_compilation_fail_before_source_read(self):
        original = contract.compile_context(self.ns, [contract.mapping()])
        for key, value in (("APPROVAL_STATUS", "PENDING"),
                           ("TRANSFORM_ID", "unregistered-transform")):
            with self.subTest(key=key):
                context = copy.deepcopy(original)
                context["compiled_plan"]["mappings"][0][key] = value
                self.assert_rejected_before_source_read(context)

    def test_boolean_constraint_changed_to_equal_integer_is_rejected(self):
        context = contract.compile_context(self.ns, [contract.mapping(
            VALUE_CONSTRAINTS={"required": True})])
        context["compiled_plan"]["mappings"][0]["VALUE_CONSTRAINTS"]["required"] = 1
        self.assert_rejected_before_source_read(context, "Required must be a boolean")

    def test_representation_parameters_and_owner_changes_are_revalidated(self):
        original = contract.compile_context(self.ns, [contract.mapping()])
        for key, value in (("REPRESENTATION", "unimplemented-representation"),
                           ("TRANSFORM_PARAMS", ["invalid"]),
                           ("REPRESENTATION_PARAMS", ["invalid"]),
                           ("OWNER_ELEMENT_PATH", contract.ROOT_PATH + ".unregistered")):
            with self.subTest(key=key):
                context = copy.deepcopy(original)
                context["compiled_plan"]["mappings"][0][key] = value
                self.assert_rejected_before_source_read(context)
        context = copy.deepcopy(original)
        context["compiled_plan"]["elements"][contract.SUMMARY]["parameters"] = ["invalid"]
        self.assert_rejected_before_source_read(context)

    def test_hand_built_contexts_retain_metadata_validation(self):
        for key, value in (("APPROVAL_STATUS", "PENDING"),
                           ("TRANSFORM_ID", "unregistered-transform"),
                           ("REPRESENTATION", "unimplemented-representation"),
                           ("REPRESENTATION_PARAMS", ["invalid"]),
                           ("VALUE_CONSTRAINTS", {"required": 1}),
                           ("OWNER_ELEMENT_PATH", runtime.ROOT_PATH + ".unregistered")):
            with self.subTest(key=key):
                row = runtime.mapping("FIRST", runtime.ROOT_PATH, "title", "text")
                row[key] = value
                context = runtime.context([row], {
                    runtime.ROOT_PATH: runtime.element(materialize_empty=True),
                })
                self.assert_rejected_before_source_read(context)

    def test_valid_new_field_edits_work_for_compiled_and_hand_built_contexts(self):
        compiled = contract.compile_context(self.ns, [contract.mapping("FIRST")])
        raw = runtime.context([runtime.mapping("FIRST", runtime.ROOT_PATH, "title", "text")], {
            runtime.ROOT_PATH: runtime.element(materialize_empty=True),
        })
        records = [{"SOURCE_RECORD_ID": "record-one",
                    "CURATED_JSON": {"FIRST": "first", "SECOND": "second"}}]
        for original, path, build, payloads in (
            (compiled, contract.SUMMARY, contract.build, contract.payloads),
            (raw, runtime.ROOT_PATH, runtime.build, runtime.payload_at),
        ):
            with self.subTest(path=path):
                context = copy.deepcopy(original)
                nodes, _ = build(self.ns, context, records)
                self.assertEqual(payloads(nodes, path), [{"title": "first"}])
                added = copy.deepcopy(context["compiled_plan"]["mappings"][0])
                added.update(SOURCE_FIELD_NAME="SECOND", FIELD_RELATIVE_PATH="description",
                             OSCAL_FIELD_NAME="description", OSCAL_ELEMENT_PATH=path + ".description")
                added.setdefault("REPRESENTATION_PARAMS", {})["target"] = "description"
                context["compiled_plan"]["mappings"].append(added)
                edited_plan = copy.deepcopy(context["compiled_plan"])
                nodes, _ = build(self.ns, context, records)
                self.assertEqual(payloads(nodes, path), [{"title": "first", "description": "second"}])
                self.assertEqual(context["compiled_plan"], edited_plan)
                compiler = self.ns["_compile_value_constraints"]
                self.ns["_compile_value_constraints"] = Mock(
                    side_effect=AssertionError("Validated edits must not be recompiled on the next build"))
                try:
                    again, _ = build(self.ns, copy.deepcopy(context), records)
                finally:
                    self.ns["_compile_value_constraints"] = compiler
                self.assertEqual(graph.business(nodes.rows), graph.business(again.rows))

    def constrained_contexts(self):
        constraints = {"validation": {"enum": ["approved"]}}
        compiled = contract.compile_context(self.ns, [contract.mapping(
            "FIRST", VALUE_CONSTRAINTS=constraints)])
        row = runtime.mapping("FIRST", runtime.ROOT_PATH, "title", "text")
        row["VALUE_CONSTRAINTS"] = copy.deepcopy(constraints)
        raw = runtime.context([row], {
            runtime.ROOT_PATH: runtime.element(materialize_empty=True),
        })
        return ((compiled, contract.build), (raw, runtime.build))

    def test_mapping_list_replaced_with_tuple_is_rejected_after_successful_build(self):
        for context, build in self.constrained_contexts():
            with self.subTest(model=context["config"]["OSCAL_MODEL"]):
                build(self.ns, context, [{"SOURCE_RECORD_ID": "record-one",
                      "CURATED_JSON": {"FIRST": "approved"}}])
                context["compiled_plan"]["mappings"] = tuple(context["compiled_plan"]["mappings"])
                self.assert_rejected_before_source_read(context)

    def test_enum_list_replaced_with_tuple_is_rejected_after_successful_build(self):
        for context, build in self.constrained_contexts():
            with self.subTest(model=context["config"]["OSCAL_MODEL"]):
                build(self.ns, context, [{"SOURCE_RECORD_ID": "record-one",
                      "CURATED_JSON": {"FIRST": "approved"}}])
                validation = context["compiled_plan"]["mappings"][0]["VALUE_CONSTRAINTS"]["validation"]
                validation["enum"] = tuple(validation["enum"])
                self.assert_rejected_before_source_read(context, "Enum must be a nonempty JSON array")

    def test_date_provenance_remains_ready_and_is_preserved(self):
        reviewed_at = datetime.date(2026, 9, 12)
        row = contract.mapping(REVIEWED_AT=reviewed_at)
        context = contract.compile_context(self.ns, [row])
        self.assertEqual(context["routing_report"]["STATUS"], "READY")
        nodes, _ = contract.build(self.ns, context, [{"SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"NEVER_SEEN_SOURCE_FIELD": "approved"}}])
        self.assertEqual(contract.payloads(nodes, contract.SUMMARY), [{"title": "approved"}])
        self.assertEqual(context["compiled_plan"]["mappings"][0]["REVIEWED_AT"], reviewed_at)
        self.assertEqual(row["REVIEWED_AT"], reviewed_at)

    def test_uncacheable_provenance_allows_repeated_builds_without_bypassing_validation(self):
        unused_provenance = lambda: self.fail("Provenance must never execute")
        context = contract.compile_context(self.ns, [contract.mapping(
            REVIEW_CALLBACK=unused_provenance)])
        self.assertEqual(context["routing_report"]["STATUS"], "READY")
        for _ in range(2):
            nodes, _ = contract.build(self.ns, context, [{"SOURCE_RECORD_ID": "record-one",
                "CURATED_JSON": {"NEVER_SEEN_SOURCE_FIELD": "approved"}}])
            self.assertEqual(contract.payloads(nodes, contract.SUMMARY), [{"title": "approved"}])
        self.assertIs(context["compiled_plan"]["mappings"][0]["REVIEW_CALLBACK"], unused_provenance)
        context["compiled_plan"]["mappings"][0]["APPROVAL_STATUS"] = "PENDING"
        self.assert_rejected_before_source_read(context)


if __name__ == "__main__":
    unittest.main()
