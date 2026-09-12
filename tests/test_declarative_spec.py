"""One executable plan drives unfamiliar fields, constraints and future models."""
import copy
import json
import unittest

import test_declarative_routing as routing
import test_metadata_driven_contract as contract


class DeclarativeSpecTests(unittest.TestCase):
    def setUp(self):
        self.ns = contract.namespace()

    def value(self, value, rules):
        compiled = self.ns["_compile_value_constraints"](rules)
        self.ns["_metadata_validate_value"](value, compiled)

    def test_unknown_constraint_is_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            self.value(7, {"requred": True})

    def test_constraints_accept_csv_json_and_do_not_mutate_input(self):
        rules = {"required": True, "cardinality": {"min": 1, "max": 1},
                 "validation": {"type": "integer", "minimum": 0, "maximum": 100}}
        original = copy.deepcopy(rules)
        self.assertEqual(rules, self.ns["_compile_value_constraints"](json.dumps(rules)))
        self.value(0, rules)
        self.assertEqual(original, rules)

    def test_invalid_constraints_are_rejected_before_runtime(self):
        invalid = [
            {"required": "true"}, {"null_policy": "invent"},
            {"cardinality": {"min": -1}}, {"cardinality": {"max": True}},
            {"cardinality": {"min": 2, "max": 1}},
            {"required": True, "cardinality": {"max": 0}},
            {"cardinality": {"count": 1}}, {"validation": {"type": "guess"}},
            {"validation": {"enum": []}}, {"validation": {"enum": [float("nan")]}},
            {"validation": {"minimum": True}}, {"validation": {"maximum": float("inf")}},
            {"validation": {"minimum": 10, "maximum": 5}},
            {"validation": {"execute": "untrusted"}},
        ]
        for rules in invalid:
            with self.subTest(rules=rules), self.assertRaises(ValueError):
                self.ns["_compile_value_constraints"](rules)

    def test_default_omits_absent_but_required_and_reject_block(self):
        absent = self.ns["SKIP_VALUE"]
        self.value(absent, {})
        self.value(absent, {"null_policy": "omit"})
        for rules in ({"required": True}, {"null_policy": "reject"}, {"cardinality": {"min": 1}}):
            with self.subTest(rules=rules), self.assertRaises(ValueError):
                self.value(absent, rules)

    def test_cardinality_counts_transformed_array_members_not_characters(self):
        self.value("abc", {"cardinality": {"min": 1, "max": 1}})
        self.value({"a": 1, "b": 2}, {"cardinality": {"max": 1}})
        self.value([1, 2], {"cardinality": {"min": 2, "max": 2}})
        with self.assertRaisesRegex(ValueError, "cardinality"):
            self.value([1, 2], {"cardinality": {"max": 1}})

    def test_zero_and_false_are_present_and_not_interchangeable(self):
        self.value(0, {"required": True, "validation": {"type": "integer", "enum": [0]}})
        self.value(False, {"required": True, "validation": {"type": "boolean", "enum": [False]}})
        for value, rule in ((False, {"type": "number"}), (True, {"enum": [1]}), (0, {"enum": [False]})):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.value(value, {"validation": rule})

    def test_bounds_apply_after_conversion_without_coercing_invalid_values(self):
        rules = {"validation": {"minimum": 0, "maximum": 10}}
        for value in (0, 10, 0.1):
            self.value(value, rules)
        for value in (-1, 11, "5", True, float("nan"), float("inf"), self.ns["Decimal"]("0.1")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.value(value, rules)

    def test_new_field_on_third_model_executes_with_only_metadata(self):
        row = contract.mapping(field="DETAILS.score", path=contract.SUMMARY + ".score", transform="direct",
                               VALUE_CONSTRAINTS={"required": True, "validation": {"type": "number", "minimum": 0}})
        ctx = contract.compile_context(self.ns, [row])
        self.assertEqual("READY", ctx["routing_report"]["STATUS"])
        nodes, edges = contract.build(self.ns, ctx, [{"SOURCE_RECORD_ID": "200", "CURATED_JSON": {"DETAILS": {"score": 0}}}])
        payloads = [json.loads(item["METADATA_JSON"]) for item in nodes.rows if item["ELEMENT_PATH"] == contract.SUMMARY]
        self.assertEqual([{"score": 0}], payloads)
        self.assertTrue(ctx["graph_report"]["OUTPUTS_PUBLISHED"])
        self.assertFalse(ctx["graph_report"]["WRITES_EXECUTED"])

    def test_failed_required_value_never_publishes_partial_graph(self):
        row = contract.mapping(VALUE_CONSTRAINTS={"required": True})
        ctx = contract.compile_context(self.ns, [row])
        with self.assertRaises(ValueError):
            contract.build(self.ns, ctx, [{"SOURCE_RECORD_ID": "200", "CURATED_JSON": {}}])
        self.assertFalse(ctx["graph_report"]["OUTPUTS_PUBLISHED"])
        self.assertFalse(ctx["graph_report"]["WRITES_EXECUTED"])

    def test_bad_constraints_block_compilation_without_source_access(self):
        ctx = contract.compile_context(self.ns, [contract.mapping(VALUE_CONSTRAINTS={"required": "yes"})])
        self.assertEqual("BLOCKED", ctx["routing_report"]["STATUS"])
        self.assertNotIn("compiled_plan", ctx)
        self.assertEqual(1, ctx["routing_report"]["BLOCKED_ROWS"])

    def test_constraints_cannot_bypass_approved_catalog(self):
        row = routing.mapping(VALUE_CONSTRAINTS={"required": True})
        models = routing.contracts()
        models["SSP"]["MAPPING_RULES"] = [{
            "RULE_ID": "approved-example", "SOURCE_FIELDS": [row["SOURCE_FIELD_NAME"]],
            "OWNER_PATH": routing.SSP, "APPROVAL_STATUS": "APPROVED", "TRANSFORM_ID": "text",
        }]
        with self.assertRaisesRegex(ValueError, "Field rules belong in the mapping artifact"):
            self.ns["compile_mapping_contexts"](
                {"source-one": [row]}, routing.registry(), [routing.profile(("SSP",))], models)

    def test_frozen_dispatchers_are_not_available_in_active_engine(self):
        for symbol in ("_legacy_prepare_model_context", "MODEL_GRAPH_POLICIES", "_mapping_handler_for_row",
                       "_score_mapping_contract", "APPROVED_TEXT_MAPPING_CONTRACTS", "COMPONENT_SOURCE_TYPES"):
            self.assertNotIn(symbol, self.ns)

    def test_skip_cannot_discard_required_constraint_failures(self):
        for rules in ({"required": True}, {"null_policy": "reject"}, {"cardinality": {"min": 1}}):
            with self.subTest(rules=rules):
                ctx = contract.compile_context(self.ns, [contract.mapping(transform="skip", VALUE_CONSTRAINTS=rules)])
                self.assertEqual("BLOCKED", ctx["routing_report"]["STATUS"])
                self.assertNotIn("compiled_plan", ctx)

    def test_runtime_never_swallows_untracked_failure(self):
        ctx = {"graph_report": {"FIELDS": {}}, "policy": {"aggregate_invalid": True}}
        row = {"SOURCE_FIELD_NAME": "UNTRACKED", "TRANSFORM_ID": "skip", "VALUE_CONSTRAINTS": {"required": True}}
        with self.assertRaisesRegex(ValueError, "cardinality"):
            self.ns["_metadata_mapped_value"](row, {}, ctx)

    def test_nested_enum_booleans_do_not_match_numbers(self):
        for value, enum in (([1], [[True]]), ({"x": 0}, [{"x": False}])):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.value(value, {"validation": {"enum": enum}})

    def test_empty_nested_json_objects_are_normalized(self):
        rules = {"cardinality": "{}", "validation": "{}"}
        self.assertEqual({"cardinality": {}, "validation": {}}, self.ns["_compile_value_constraints"](rules))
        self.value(1, rules)

    def test_numeric_type_never_turns_into_string_or_nonfinite_json(self):
        for value in (self.ns["Decimal"]("1.5"), self.ns["Decimal"]("NaN"), float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.value(value, {"validation": {"type": "number"}})


if __name__ == "__main__":
    unittest.main()
