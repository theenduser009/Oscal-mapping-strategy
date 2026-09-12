"""Flat CSV execution metadata compiles without a field-rule catalog."""
import copy
import unittest

import test_metadata_driven_contract as base
import test_multi_model_graph as graph


def mapping(field="FLAT_SOURCE", path=base.SUMMARY + ".title", **extra):
    row = {
        "SOURCE_KEY": "source-one", "SOURCE_FIELD_NAME": field,
        "OSCAL_MODEL": base.MODEL, "OSCAL_ELEMENT_PATH": path,
        "MAPPING_TYPE": "Direct", "NOTES": "Original source note.",
        "EXECUTION_STATUS": "APPROVED", "RUNTIME_TARGET_PATH": path,
        "RULE_ID": "flat:" + field, "TRANSFORM_ID": "text",
    }
    row.update(extra)
    return row


class FlatMappingColumnsTests(unittest.TestCase):
    def setUp(self):
        self.ns = base.namespace()

    def compile(self, rows, **kwargs):
        original = copy.deepcopy(rows)
        context = base.compile_context(self.ns, rows, **kwargs)
        self.assertEqual(rows, original)
        return context

    def assert_blocked(self, row, **kwargs):
        context = self.compile([row], **kwargs)
        self.assertEqual(context["routing_report"]["STATUS"], "BLOCKED")
        self.assertEqual(context["mapping_rows"], [])
        self.assertFalse(context["config"]["EXECUTE_WRITES"])

    def test_flat_row_does_not_read_catalog_matchers(self):
        for name in ("_metadata_rule_candidates", "_metadata_rule_matches", "_apply_mapping_path_rules"):
            self.assertNotIn(name, self.ns)
        context = self.compile([mapping()])
        self.assertEqual(context["routing_report"]["STATUS"], "READY")
        row = context["compiled_plan"]["mappings"][0]
        self.assertEqual(row["TRANSFORM_PARAMS"], {})
        self.assertEqual(row["REPRESENTATION_PARAMS"], {"target": "title"})
        self.assertEqual(row["CONTRACT_SOURCE"], "flat-mapping-artifact")
        nodes, _ = base.build(self.ns, context, [{
            "SOURCE_RECORD_ID": "record", "CURATED_JSON": {"FLAT_SOURCE": "Preserved"},
        }])
        self.assertEqual(base.payloads(nodes, base.SUMMARY), [{"title": "Preserved"}])

    def test_runtime_path_is_separate_from_original_path_and_notes(self):
        row = mapping(path=base.ROOT_PATH + ".original",
                      RUNTIME_TARGET_PATH=base.SUMMARY + ".description",
                      NOTES="Keep these exact Notes; they are not executable.")
        context = self.compile([row])
        compiled = context["mapping_rows"][0]
        self.assertEqual(compiled["OSCAL_ELEMENT_PATH"], row["OSCAL_ELEMENT_PATH"])
        self.assertEqual(compiled["NOTES"], row["NOTES"])
        self.assertEqual(compiled["CANONICAL_ELEMENT_PATH"], base.SUMMARY + ".description")
        self.assertEqual(compiled["OWNER_ELEMENT_PATH"], base.SUMMARY)
        self.assertEqual(compiled["REPRESENTATION_PARAMS"], {"target": "description"})

    def test_explicit_status_does_not_infer_execution_from_old_prose(self):
        row = mapping(OSCAL_ELEMENT_PATH="TBD", MAPPING_TYPE="TBD", STATUS="TBD")
        context = self.compile([row])
        self.assertEqual(context["routing_report"]["STATUS"], "READY")
        self.assertEqual(context["mapping_rows"][0]["MAPPING_TYPE"], "TBD")
        self.assertEqual(context["mapping_rows"][0]["OSCAL_ELEMENT_PATH"], "TBD")

    def test_populated_only_guard_skips_absent_and_blocks_populated(self):
        row = mapping(TRANSFORM_ID="reject-populated",
                      EXECUTION_STATUS="BLOCKED_IF_POPULATED")
        context = self.compile([row])
        self.assertEqual(context["mapping_rows"][0]["APPROVAL_STATUS"], "BLOCKED_IF_POPULATED")
        base.build(self.ns, context, [{"SOURCE_RECORD_ID": "record", "CURATED_JSON": {}}])
        self.assertTrue(context["graph_report"]["OUTPUTS_PUBLISHED"])
        context = self.compile([row])
        with self.assertRaises(ValueError) as error:
            base.build(self.ns, context, [{
                "SOURCE_RECORD_ID": "record", "CURATED_JSON": {"FLAT_SOURCE": "sensitive-value"},
            }])
        self.assertNotIn("sensitive-value", str(error.exception))
        self.assertFalse(context["graph_report"]["OUTPUTS_PUBLISHED"])
        self.assert_blocked(mapping(EXECUTION_STATUS="BLOCKED_IF_POPULATED"))

    def test_deferred_and_excluded_rows_do_not_execute(self):
        rows = [mapping(),
                mapping("WAIT", EXECUTION_STATUS="DEFERRED", RUNTIME_TARGET_PATH="unknown",
                        TRANSFORM_ID="unreviewed"),
                mapping("SKIP", EXECUTION_STATUS="EXCLUDED", OSCAL_ELEMENT_PATH="TBD",
                        RUNTIME_TARGET_PATH="", TRANSFORM_ID="")]
        context = self.compile(rows)
        report = context["routing_report"]
        self.assertEqual(report["STATUS"], "READY")
        self.assertEqual((report["SELECTED_ROWS"], report["DEFERRED_ROWS"], report["EXCLUDED_ROWS"]),
                         (1, 1, 1))
        self.assertEqual(len(context["compiled_plan"]["mappings"]), 1)

    def test_invalid_or_missing_status_transform_target_and_rule_id_block(self):
        for extra in (
            {"EXECUTION_STATUS": "PENDING"}, {"EXECUTION_STATUS": ""},
            {"EXECUTION_STATUS": True}, {"TRANSFORM_ID": "unknown"},
            {"TRANSFORM_ID": ""}, {"RUNTIME_TARGET_PATH": ""},
            {"RUNTIME_TARGET_PATH": base.SUMMARY + ".items[].title"},
            {"RUNTIME_TARGET_PATH": base.SUMMARY + ".bad["},
            {"RULE_ID": ""}, {"SOURCE_KEY": ""},
            {"SOURCE_KEY": "unknown-source"},
        ):
            with self.subTest(extra=extra):
                self.assert_blocked(mapping(**extra))

    def test_source_scoping_prevents_cross_source_execution(self):
        rows = [mapping(), mapping("SECOND", SOURCE_KEY="source-two")]
        contexts = self.ns["compile_mapping_contexts"](
            {"source-one": rows, "source-two": rows}, base.registry_rows(),
            [base.profile(), base.profile("source-two", "SECOND_SOURCE")],
            {base.MODEL: base.model_contract()})
        self.assertEqual(len(contexts), 2)
        for context, expected in zip(contexts, ("FLAT_SOURCE", "SECOND")):
            self.assertEqual(context["routing_report"]["STATUS"], "READY")
            self.assertEqual([r["SOURCE_FIELD_NAME"] for r in context["mapping_rows"]], [expected])
            self.assertEqual(context["routing_report"]["EXCLUDED_ROWS"], 1)

    def test_runtime_path_cannot_move_an_original_known_model(self):
        registry = base.registry_rows() + [{
            "OSCAL_MODEL_KEY": "OTHER_MODEL", "NODE_PATH": "other-model",
            "PARENT_NODE_PATH": None, "IS_ACTIVE": True,
            "IS_COLLECTION": False, "ELEMENT_TYPE": "other-model",
        }]
        self.assert_blocked(mapping(OSCAL_ELEMENT_PATH="other-model.title"), registry=registry)
        self.assert_blocked(mapping(RUNTIME_TARGET_PATH="other-model.title"), registry=registry)

    def test_cia_allowed_values_are_literal_reviewed_labels(self):
        context = self.compile([mapping(TRANSFORM_ID="security-objective",
            ALLOWED_VALUES="Legacy LOE A|Legacy LOE D + DFARS")])
        row = context["mapping_rows"][0]
        self.assertEqual(row["TRANSFORM_PARAMS"], {
            "approved_legacy_values": ["Legacy LOE A", "Legacy LOE D + DFARS"]})
        nodes, _ = base.build(self.ns, context, [{
            "SOURCE_RECORD_ID": "record", "CURATED_JSON": {"FLAT_SOURCE": "Legacy LOE A"},
        }])
        self.assertEqual(base.payloads(nodes, base.SUMMARY), [{"title": "Legacy LOE A"}])

    def test_status_crosswalk_and_literal_remarks_template(self):
        context = self.compile([mapping(TRANSFORM_ID="status-crosswalk",
            RUNTIME_TARGET_PATH=base.SUMMARY + ".state",
            VALUE_MAP="Operational=operational|Under Development=under-development|Reauthorize=other",
            OTHER_REMARKS_TEMPLATE="Mapped from source: {label}.")])
        params = context["mapping_rows"][0]["TRANSFORM_PARAMS"]
        self.assertEqual(params["crosswalk"]["under-development"], "under-development")
        self.assertEqual(params["other_remarks_prefix"], "Mapped from source: ")
        self.assertEqual(params["other_remarks_suffix"], ".")
        nodes, _ = base.build(self.ns, context, [{
            "SOURCE_RECORD_ID": "record", "CURATED_JSON": {"FLAT_SOURCE": "Reauthorize"},
        }])
        self.assertEqual(base.payloads(nodes, base.SUMMARY),
                         [{"state": "other", "remarks": "Mapped from source: Reauthorize."}])

    def test_crosswalk_label_normalization_matches_runtime(self):
        for label in (" Under  Development ", "UNDER_DEVELOPMENT", "under/development",
                      "under...development", "--Under-Development--"):
            with self.subTest(label=label):
                context = self.compile([mapping(TRANSFORM_ID="status-crosswalk",
                    RUNTIME_TARGET_PATH=base.SUMMARY + ".state",
                    VALUE_MAP=label + "=under-development")])
                row = context["mapping_rows"][0]
                self.assertEqual(row["TRANSFORM_PARAMS"]["crosswalk"],
                                 {self.ns["_stable_property_name"](label): "under-development"})
                nodes, _ = base.build(self.ns, context, [{
                    "SOURCE_RECORD_ID": "record", "CURATED_JSON": {"FLAT_SOURCE": label},
                }])
                self.assertEqual(base.payloads(nodes, base.SUMMARY), [{"state": "under-development"}])

    def test_collection_operators_reject_unsupported_member_targets(self):
        parameters = {
            "properties": {}, "observations": {},
            "assignments": {"ROLE_ID": "reviewer", "ROLE_TITLE": "Reviewer"},
            "references": {"REFERENCE_TYPE": "software"},
        }
        for operator, extra in parameters.items():
            with self.subTest(operator=operator), self.assertRaisesRegex(
                    ValueError, "Member target is unsupported"):
                self.ns["_compile_flat_mapping"](mapping(
                    path="x.collection[].unexpected", OWNER_ELEMENT_PATH="x.collection[]",
                    FIELD_RELATIVE_PATH="unexpected", **extra),
                    {"x.collection[]": {"operator": operator}})

    def test_malformed_and_inapplicable_parameters_block(self):
        for extra in (
            {"ALLOWED_VALUES": "A|"}, {"ALLOWED_VALUES": "A|A"},
            {"VALUE_MAP": "a=b"}, {"ROLE_ID": "some-role"},
            {"LOOKUP_KEY": "source"}, {"DESCRIPTION_REQUIRED": "yes"},
            {"TRANSFORM_ID": "security-objective", "ALLOWED_VALUES": ["A"]},
            {"TRANSFORM_ID": "security-objective", "ALLOWED_VALUES": "A|A"},
            {"TRANSFORM_ID": "status-crosswalk", "VALUE_MAP": "a=b=c"},
            {"TRANSFORM_ID": "status-crosswalk", "VALUE_MAP": "a=one|A=two"},
            {"TRANSFORM_ID": "status-crosswalk", "VALUE_MAP": "a=other"},
            {"TRANSFORM_ID": "status-crosswalk", "VALUE_MAP": "a=other",
             "OTHER_REMARKS_TEMPLATE": "bad {value}"},
            {"TRANSFORM_ID": "status-crosswalk", "VALUE_MAP": "a=other",
             "OTHER_REMARKS_TEMPLATE": "{label} {label}"},
            {"TRANSFORM_PARAMS": {"unreviewed": True}},
            {"REPRESENTATION_PARAMS": {"target": "wrong"}},
            {"APPROVAL_STATUS": "DEFERRED"}, {"REPRESENTATION": "references"},
        ):
            with self.subTest(extra=extra):
                self.assert_blocked(mapping(**extra))

    def test_role_and_reference_parameters_compile_without_source_specific_rules(self):
        def canonical(path, **extra):
            return mapping(path=path, TRANSFORM_ID="direct", OWNER_ELEMENT_PATH=path,
                           FIELD_RELATIVE_PATH="", **extra)
        role = self.ns["_compile_flat_mapping"](canonical(
            "x.assignments[]", ROLE_ID="reviewer", ROLE_TITLE="Reviewer"),
            {"x.assignments[]": {"operator": "assignments"}})
        self.assertEqual(role["REPRESENTATION_PARAMS"], {"role_id": "reviewer", "role_title": "Reviewer"})
        for flag, expected in (("true", True), ("false", False), (True, True), (False, False)):
            reference = self.ns["_compile_flat_mapping"](canonical(
                "x.references[]", REFERENCE_TYPE="software", LOOKUP_KEY="tools",
                DESCRIPTION_REQUIRED=flag), {"x.references[]": {"operator": "references"}})
            self.assertEqual(reference["REPRESENTATION_PARAMS"], {
                "reference_type": "software", "hydrate_lookup": "tools",
                "description_required": expected})
        for extra in ({}, {"REFERENCE_TYPE": "hardware", "DESCRIPTION_REQUIRED": "true"},
                      {"REFERENCE_TYPE": "software", "LOOKUP_KEY": "tools", "DESCRIPTION_REQUIRED": "yes"}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.ns["_compile_flat_mapping"](canonical("x.references[]", **extra),
                    {"x.references[]": {"operator": "references"}})

    def test_duplicate_rule_ids_are_rejected_within_a_source_model(self):
        self.assert_blocked_pair = self.compile([mapping(), mapping("ANOTHER", RULE_ID="flat:FLAT_SOURCE")])
        self.assertEqual(self.assert_blocked_pair["routing_report"]["STATUS"], "BLOCKED")
        self.assertEqual(self.assert_blocked_pair["mapping_rows"], [])


if __name__ == "__main__":
    unittest.main()
