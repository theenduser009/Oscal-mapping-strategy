"""Registry/path-first routing tests grounded in the ten posted label/path pairs."""
import copy
import json
from pathlib import Path
import unittest

import test_declarative_routing as base

ROOT = Path(__file__).resolve().parents[1]
# Fixed routing-policy fixture for explicit compiler API regressions.
CATALOG = ROOT / "tests/fixtures/mapper_contract_pre_registry.json"
# Counts/labels/paths are posted evidence; source field names below are synthetic.
POSTED_PAIRS = (
    ("Multiple - See Notes", "Multiple - See Notes", 1),
    ("N/A - Calculated", "", 37),
    ("Profile", "Multiple - See Notes", 1),
    ("Profile", "profile.imports[]", 1),
    ("Security Assessment Plan", "security-assessment-plan.tasks[]", 2),
    ("Security Assessment Plan", "security-assessment-plan.tasks[].remarks", 1),
    ("TBD", "", 413),
    ("TBD", "All Nulls", 1),
    ("TBD", "Multiple - See Notes", 1),
    ("TBD", "system-security-plan.system-characteristics.security-impact-level", 1),
)


def routing_metadata():
    return json.loads(CATALOG.read_text(encoding="utf-8-sig"))["ROUTING"]


def registry_rows():
    # Deliberately no Profile/SAP root rows: ownership of unselected models
    # is evidenced by their active registry paths, not inferred OSCAL aliases.
    return base.registry() + [
        {"OSCAL_MODEL_KEY": model, "NODE_PATH": path, "PARENT_NODE_PATH": parent,
         "IS_ACTIVE": True, "IS_COLLECTION": path.endswith("[]"), "ELEMENT_TYPE": kind}
        for model, path, parent, kind in (
            ("PROFILE", "profile.imports[]", "profile", "imports"),
            ("SECURITY_ASSESSMENT_PLAN", "security-assessment-plan.tasks[]",
             "security-assessment-plan", "tasks"),
            ("SECURITY_ASSESSMENT_PLAN", "security-assessment-plan.tasks[].remarks",
             "security-assessment-plan.tasks[]", "remarks"),
        )
    ]


def unapproved_row(field, label, path):
    return {
        "SOURCE_FIELD_NAME": field, "OSCAL_MODEL": label,
        "OSCAL_ELEMENT_PATH": path, "MAPPING_TYPE": "Direct",
    }


def posted_rows():
    return [
        unapproved_row("SYNTHETIC_POSTED_FIELD_" + str(pair) + "_" + str(index), label, path)
        for pair, (label, path, count) in enumerate(POSTED_PAIRS)
        for index in range(count)
    ]


class RegistryFirstRouting(unittest.TestCase):
    def setUp(self):
        self.ns = base.namespace()

    def compile(self, rows, models=None, selected=("SSP",), registry=None, routing=None):
        models = base.contracts() if models is None else models
        inputs = (
            {"source-one": rows}, registry_rows() if registry is None else registry,
            [base.profile(selected)], models, routing_metadata() if routing is None else routing,
        )
        before = copy.deepcopy(inputs)
        contexts = self.ns["compile_mapping_contexts"](*inputs)
        self.assertEqual(before, inputs, "Routing must not mutate metadata")
        self.assertEqual(list(selected), [c["config"]["OSCAL_MODEL"] for c in contexts])
        for context in contexts:
            report = context["routing_report"]
            self.assertEqual(len(rows), report["INPUT_ROWS"])
            self.assertEqual(len(rows), sum(report[k] for k in (
                "SELECTED_ROWS", "EXCLUDED_ROWS", "DEFERRED_ROWS", "BLOCKED_ROWS")))
            self.assertEqual(report["SELECTED_ROWS"], len(context["mapping_rows"]))
            self.assertFalse(context["config"]["EXECUTE_WRITES"])
        return {c["config"]["OSCAL_MODEL"]: c for c in contexts}

    def test_malformed_routing_placeholders_fail_before_any_row_can_be_approved(self):
        for metadata in (
            {"UNKNOWN_OPTION": []},
            {"DEFERRED_MODEL_LABELS": "TBD"},
            {"DEFERRED_MODEL_LABELS": [None]},
            {"DEFERRED_MODEL_LABELS": ["   "]},
            {"DEFERRED_MODEL_LABELS": ["---"]},
            {"DEFERRED_MODEL_LABELS": ["[]"]},
            {"DEFERRED_TARGET_PATHS": [False]},
            {"DEFERRED_TARGET_PATHS": [""]},
        ):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.compile([base.mapping()], routing=metadata)

    def test_placeholders_cannot_hide_registered_model_or_path(self):
        for metadata in (
            {"DEFERRED_MODEL_LABELS": ["SSP"]},
            {"DEFERRED_MODEL_LABELS": ["System Security Plan"]},
            {"DEFERRED_TARGET_PATHS": [base.SSP]},
        ):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.compile([base.mapping()], routing=metadata)

    def test_ambiguous_registry_label_cannot_override_model_alias(self):
        rows = registry_rows()
        rows.append({
            "OSCAL_MODEL_KEY": "PROFILE", "MODEL_NAME": "SSP",
            "NODE_PATH": "profile.metadata", "IS_ACTIVE": True,
            "PARENT_NODE_PATH": "profile", "IS_COLLECTION": False,
        })
        with self.assertRaises(ValueError):
            self.compile([base.mapping()], registry=rows)

    def test_registry_path_root_cannot_belong_to_multiple_models(self):
        rows = registry_rows()
        rows.append({
            "OSCAL_MODEL_KEY": "UNRELATED_MODEL", "NODE_PATH": base.SSP + ".extra",
            "IS_ACTIVE": True, "PARENT_NODE_PATH": base.SSP, "IS_COLLECTION": False,
        })
        with self.assertRaises(ValueError):
            self.compile([base.mapping()], registry=rows)

    def test_ten_posted_pairs_conserve_all_459_rows_without_approving_placeholders(self):
        rows = posted_rows()
        self.assertEqual(459, len(rows))
        self.assertEqual(416, sum(1 for row in rows if row["OSCAL_MODEL"] == "TBD"))
        context = self.compile(rows)["SSP"]
        report = context["routing_report"]
        self.assertEqual((0, 4, 455, 0), tuple(report[k] for k in (
            "SELECTED_ROWS", "EXCLUDED_ROWS", "DEFERRED_ROWS", "BLOCKED_ROWS")))
        self.assertEqual("READY", report["STATUS"])
        self.assertEqual([], context["mapping_rows"])
        self.assertEqual([], context["compiled_plan"]["mappings"])
        self.assertNotIn("UNKNOWN_MODEL_LABEL", report["REASON_COUNTS"])

    def test_608_style_fixture_preserves_existing_149_dispositions(self):
        accepted = [
            base.mapping(field="APPROVED_SSP_" + str(i),
                         OSCAL_ELEMENT_PATH=base.SSP + ".field_" + str(i))
            for i in range(43)
        ]
        other = [
            base.mapping(field="OTHER_AR_" + str(i), model="ASSESSMENT_RESULTS", root=base.AR)
            for i in range(46)
        ]
        unreviewed = [
            unapproved_row("UNREVIEWED_SSP_" + str(i), "SSP", base.SSP + ".field_" + str(i))
            for i in range(60)
        ]
        context = self.compile(accepted + other + unreviewed + posted_rows())["SSP"]
        report = context["routing_report"]
        self.assertEqual(608, report["INPUT_ROWS"])
        self.assertEqual((43, 50, 515, 0), tuple(report[k] for k in (
            "SELECTED_ROWS", "EXCLUDED_ROWS", "DEFERRED_ROWS", "BLOCKED_ROWS")))
        self.assertEqual({row["SOURCE_FIELD_NAME"] for row in accepted},
                         {row["SOURCE_FIELD_NAME"] for row in context["compiled_plan"]["mappings"]})

    def test_absent_other_model_registry_leaves_posted_rows_deferred_not_enabled(self):
        context = self.compile(posted_rows(), registry=base.registry())["SSP"]
        report = context["routing_report"]
        self.assertEqual((0, 0, 459, 0), tuple(report[k] for k in (
            "SELECTED_ROWS", "EXCLUDED_ROWS", "DEFERRED_ROWS", "BLOCKED_ROWS")))
        self.assertEqual([], context["mapping_rows"])

    def test_tbd_with_real_ssp_path_remains_deferred_even_with_transform_columns(self):
        path = POSTED_PAIRS[-1][1]
        for row in (
            unapproved_row("PENDING_IMPACT", "TBD", path),
            base.mapping(field="PENDING_IMPACT", model="TBD", OSCAL_ELEMENT_PATH=path),
        ):
            context = self.compile([row])["SSP"]
            self.assertEqual(1, context["routing_report"]["DEFERRED_ROWS"])
            self.assertEqual(0, context["routing_report"]["EXCLUDED_ROWS"])
            self.assertEqual([], context["mapping_rows"])
            self.assertEqual(path, row["OSCAL_ELEMENT_PATH"])

    def test_unrecognized_descriptive_label_routes_registered_path_with_explicit_approval(self):
        row = base.mapping(model="Unconfigured descriptive worksheet label")
        context = self.compile([row])["SSP"]
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        actual = context["compiled_plan"]["mappings"][0]
        self.assertEqual("SSP", actual["OSCAL_MODEL"])
        self.assertEqual(row["OSCAL_MODEL"], actual["ARTIFACT_MODEL"])
        self.assertEqual(row["OSCAL_ELEMENT_PATH"], actual["OSCAL_ELEMENT_PATH"])
        self.assertEqual("APPROVED", actual["APPROVAL_STATUS"])

    def test_registered_path_does_not_supply_missing_mapping_approval(self):
        row = unapproved_row("UNREVIEWED_NEW_FIELD", "Unconfigured label", base.SSP + ".title")
        context = self.compile([row])["SSP"]
        self.assertEqual(1, context["routing_report"]["DEFERRED_ROWS"])
        self.assertEqual({"MISSING_APPROVED_METADATA": 1}, context["routing_report"]["REASON_COUNTS"])
        self.assertEqual([], context["mapping_rows"])

    def test_reviewed_catalog_rule_cannot_supply_missing_artifact_approval(self):
        row = unapproved_row("REVIEWED_FIELD", "Unconfigured label", base.SSP + ".title")
        models = base.contracts()
        models["SSP"]["MAPPING_RULES"] = [{
            "RULE_ID": "approved-text", "SOURCE_FIELDS": ["REVIEWED_FIELD"],
            "OWNER_PATH": base.SSP, "TARGET_FIELDS": ["title"],
            "APPROVAL_STATUS": "APPROVED", "TRANSFORM_ID": "text",
        }]
        for path in (base.SSP + ".title", base.SSP + ".different"):
            with self.subTest(path=path):
                row["OSCAL_ELEMENT_PATH"] = path
                with self.assertRaisesRegex(ValueError, "Field rules belong in the mapping artifact"):
                    self.compile([row], models=models)

    def test_recognized_label_path_conflicts_still_block(self):
        rows = [
            base.mapping(model="SSP", root=base.AR),
            base.mapping(model="Profile", root=base.SSP),
        ]
        for row in rows:
            with self.subTest(row=row):
                context = self.compile([row])["SSP"]
                self.assertEqual({"MODEL_PATH_CONFLICT": 1}, context["routing_report"]["REASON_COUNTS"])
                self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])

    def test_unknown_real_root_is_not_a_placeholder_or_approved_route(self):
        for label in ("SSP", "Unconfigured label"):
            row = base.mapping(model=label, root="unregistered-real-model")
            context = self.compile([row])["SSP"]
            self.assertEqual(1, context["routing_report"]["BLOCKED_ROWS"])
            self.assertEqual([], context["mapping_rows"])
            self.assertEqual(0, context["routing_report"]["DEFERRED_ROWS"])

    def test_unknown_label_missing_source_on_registered_ssp_path_still_blocks(self):
        row = base.mapping(field=None, model="Unconfigured label")
        context = self.compile([row])["SSP"]
        self.assertEqual({"MISSING_SOURCE_FIELD": 1}, context["routing_report"]["REASON_COUNTS"])

    def test_registered_other_model_path_is_excluded_without_executable_model_enabling(self):
        rows = [
            base.mapping(field=None, model="Unconfigured other-model label", root=base.POAM),
            unapproved_row("PROFILE_IMPORT", "Profile", "profile.imports[]"),
            unapproved_row("SAP_TASK", "Security Assessment Plan", "security-assessment-plan.tasks[]"),
        ]
        contexts = self.compile(rows)
        self.assertEqual(["SSP"], list(contexts))
        self.assertEqual(3, contexts["SSP"]["routing_report"]["EXCLUDED_ROWS"])
        self.assertEqual(0, contexts["SSP"]["routing_report"]["BLOCKED_ROWS"])
        with self.assertRaises(ValueError):
            self.compile(rows, selected=("PROFILE",))


if __name__ == "__main__":
    unittest.main()
