"""Pure multi-source/model planning tests; no database or notebook execution."""
import ast
import copy
import hashlib
import math
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CELL3 = ROOT / "notebooks/cells/03_canonical_mapping_contract.py"
SSP = "system-security-plan"
META = SSP + ".metadata"
AR = "assessment-results"
RESULT = AR + ".results[]"
OBS = RESULT + ".observations[]"
ACCEPTED_FIELDS = (
    "VULNERABILITY_SCORE", "ANTIVIRUS_SCORE", "PATCH_SCORE", "SECURITY_COMPLIANCE_SCORE",
    "STANDARD_OPERATING_ENVIRONMENT_SCORE", "COMPUTER_PASSWORD_AGE_SCORE",
    "VULNERABILITY_REPORTING_SCORE", "SECURITY_COMPLIANCE_REPORTING_SCORE",
    "TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE", "AVG_AUTHORIZATION_PACKAGE_RISK_SCORE",
    "RISK_SCORE_GRADE", "AVG_VULNERABILITY_SCORE", "AVG_PATCH_SCORE",
    "AVG_ANTIVIRUS_SCORE", "AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE",
    "AVG_COMPUTER_PASSWORD_AGE_SCORE", "AVG_VULNERABILITY_REPORTING_SCORE",
)
CANDIDATE_FIELDS = (
    "RISK_ACCEPTANCE_RBDS", "TOTAL_PACKAGE_RESIDUAL_RISK", "ADJUSTED_TOTAL_RISK_SCORE",
    "ADJUSTED_AVERAGE_RISK_SCORE", "CURRENT_HIGHEST_DEVICE_RISK_SCORE",
    "CURRENT_AVERAGE_DEVICE_RISK_SCORE", "CURRENT_CONTROL_RISK_SCORE",
    "PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD", "PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD",
    "BASELINE_HIGHEST_DEVICE_RISK_SCORE", "BASELINE_AVERAGE_DEVICE_RISK_SCORE",
    "BASELINE_CONTROL_RISK_SCORE", "RISK_ASSESSMENT",
    "_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD", "_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD",
    "INITIAL_RISK_ASSESSMENT", "RISK_ASSESSMENT_REPORT",
)


class NoIO:
    def __getattr__(self, name):
        raise AssertionError("The routing compiler must not perform database I/O")


def namespace():
    tree = ast.parse(CELL3.read_text(encoding="utf-8"))
    body = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            body.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                continue
            body.append(node)
    ns = {"re": re, "math": math, "copy": copy, "session": NoIO()}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(CELL3), "exec"), ns)
    helper_path = ROOT / "notebooks/cells/04_parsing_transform_payload_helpers.py"
    helper_tree = ast.parse(helper_path.read_text(encoding="utf-8"))
    ns["hashlib"] = hashlib
    exec(compile(ast.Module(body=[n for n in helper_tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "_deterministic_hash"],
        type_ignores=[]), str(helper_path), "exec"), ns)
    return ns


def contracts():
    return {
        "SSP": {"MODEL_KEY": "SSP", "ROOT_PATH": SSP, "POLICY": "ssp-approved-v1",
                "MODEL_ALIASES": ("SSP", "System Security Plan", "SSP - Metadata"),
                "ELEMENTS": {
                    SSP: {"operator": "object", "parameters": {}},
                    META: {"operator": "object", "parameters": {}},
                }},
        "ASSESSMENT_RESULTS": {
            "MODEL_KEY": "ASSESSMENT_RESULTS", "ROOT_PATH": AR,
            "POLICY": "observation-scores-v2",
            "MODEL_ALIASES": ("ASSESSMENT_RESULTS", "Assessment Results", "AR"),
            "SELECTED_FIELDS": ACCEPTED_FIELDS,
            "ELEMENT_PATHS": (AR, RESULT, OBS), "STORAGE_CONTRACT": None,
            "ELEMENTS": {
                AR: {"operator": "object", "parameters": {}},
                RESULT: {"operator": "record", "parameters": {}},
                OBS: {"operator": "observations", "parameters": {}},
            },
        },
    }


def profile(key="source-one", table="SOURCE_ONE", models=("SSP", "ASSESSMENT_RESULTS")):
    return {
        "SOURCE_KEY": key, "SOURCE_SYSTEM_NAME": "ARCHER",
        "SOURCE_TABLE_NAME": table, "RAW_TABLE": "TEST_RAW.GRC." + table,
        "CONTENT_ID_COLUMN": "CONTENT_ID", "CURATED_JSON_COLUMN": "CURATED_JSON",
        "MAPPING_FILE": key + ".csv", "MODEL_KEYS": models,
        "BASE_CONFIG": {
            "EXECUTE_WRITES": False, "OSCAL_MODEL": "SSP", "RUN_ID": "synthetic-run",
            "IDENTITY_VERSION": "v1_registry_path_instance", "OSCAL_VERSION": "1.2.3",
            "SOURCE_SYSTEM_NAME": "ARCHER", "SOURCE_TABLE_NAME": table,
        },
    }


def registry():
    return [
        {"OSCAL_MODEL_KEY": model, "NODE_PATH": path, "ELEMENT_TYPE": kind,
         "PARENT_NODE_PATH": parent, "IS_COLLECTION": collection,
         "INSTANCE_KEY_RULE": rule, "PROCESS_ORDER": order,
         "IS_ACTIVE": True, "ITEM_PATH": None}
        for model, path, kind, parent, collection, rule, order in (
            ("SSP", SSP, "system-security-plan", None, False, None, 1),
            ("SSP", META, "metadata", SSP, False, None, 2),
            ("ASSESSMENT_RESULTS", AR, "assessment-results", None, False, None, 1),
            ("ASSESSMENT_RESULTS", RESULT, "results", AR, True, "SOURCE_RECORD_ID", 2),
            ("ASSESSMENT_RESULTS", OBS, "observations", RESULT, True, "SOURCE_FIELD_NAME", 3),
        )
    ]


def mapping(field="AUTHORIZATION_PACKAGE_NAME", model="SSP", path=META + ".title", **extra):
    row = {"SOURCE_FIELD_NAME": field, "OSCAL_MODEL": model, "OSCAL_ELEMENT_PATH": path,
           "MAPPING_TYPE": "Direct", "TRANSFORMATION_LOGIC": "Preserve source text", "STATUS": "Mapped"}
    row.update(extra)
    return row


def ar_mappings(candidate=False):
    rows = [mapping(field, "Assessment Results", OBS, MAPPING_TYPE="Extension Property",
                    TRANSFORMATION_LOGIC="", NOTES="Archer-specific risk scoring - map as observation")
            for field in ACCEPTED_FIELDS]
    if candidate:
        rows.extend(mapping(field, "Assessment Results", OBS + " or props[]",
                            MAPPING_TYPE="Extension Property",
                            TRANSFORMATION_LOGIC="", NOTES="Archer-specific risk scoring - map as observation or property")
                    for field in CANDIDATE_FIELDS)
    return rows


class MultiModelRouting(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.models, self.profiles, self.registry = contracts(), [profile()], registry()

    def compile(self, rows, profiles=None, models=None, registry_rows=None):
        return self.ns["compile_mapping_contexts"](
            rows, self.registry if registry_rows is None else registry_rows,
            self.profiles if profiles is None else profiles,
            self.models if models is None else models)

    def indexed(self, contexts):
        return {(ctx["source_key"], ctx["config"]["OSCAL_MODEL"]): ctx for ctx in contexts}

    def conserved(self, context, expected):
        report = context["routing_report"]
        self.assertEqual(expected, report["INPUT_ROWS"])
        self.assertEqual(expected, sum(report[key] for key in
            ("SELECTED_ROWS", "EXCLUDED_ROWS", "DEFERRED_ROWS", "BLOCKED_ROWS")))
        self.assertEqual(report["SELECTED_ROWS"], len(context["mapping_rows"]))

    def test_one_source_routes_ssp_and_ar_without_cross_model_rows(self):
        rows = {"source-one": [mapping()] + ar_mappings()}
        contexts = self.indexed(self.compile(rows))
        self.assertEqual({("source-one", "SSP"), ("source-one", "ASSESSMENT_RESULTS")}, set(contexts))
        ssp, ar = contexts[("source-one", "SSP")], contexts[("source-one", "ASSESSMENT_RESULTS")]
        self.assertEqual({"AUTHORIZATION_PACKAGE_NAME"}, {r["SOURCE_FIELD_NAME"] for r in ssp["mapping_rows"]})
        self.assertEqual(set(ACCEPTED_FIELDS), {r["SOURCE_FIELD_NAME"] for r in ar["mapping_rows"]})
        self.assertEqual({META}, set(ssp["mappings_by_path"]))
        self.assertEqual({OBS}, set(ar["mappings_by_path"]))
        for context in contexts.values():
            self.conserved(context, 18)
            self.assertEqual("READY", context["routing_report"]["STATUS"])
            self.assertFalse(context["config"]["EXECUTE_WRITES"])

    def test_two_sources_same_fields_and_record_id_have_distinct_identity_context(self):
        profiles = [profile(), profile("source-two", "SOURCE_TWO")]
        rows = {item["SOURCE_KEY"]: [mapping()] + ar_mappings() for item in profiles}
        contexts = self.compile(rows, profiles=profiles)
        self.assertEqual(4, len(contexts))
        identities = set()
        for context in contexts:
            config = context["config"]
            expected_table = "SOURCE_ONE" if context["source_key"] == "source-one" else "SOURCE_TWO"
            self.assertEqual(expected_table, config["SOURCE_TABLE_NAME"])
            self.assertEqual("TEST_RAW.GRC." + expected_table, config["RAW_TABLE"])
            # Exercise the existing identity helper using only this context's source/model.
            source = (config["IDENTITY_VERSION"], config["SOURCE_SYSTEM_NAME"],
                      config["SOURCE_TABLE_NAME"], "same-record-id", config["OSCAL_MODEL"],
                      context["model_contract"]["ROOT_PATH"], "root")
            identities.add(self.ns["_deterministic_hash"](*source))
        self.assertEqual(4, len(identities))
        ar1, ar2 = (c for c in contexts if c["config"]["OSCAL_MODEL"] == "ASSESSMENT_RESULTS")
        self.assertIsNot(ar1["mapping_rows"], ar2["mapping_rows"])
        self.assertIsNot(ar1["mapping_rows"][0], ar2["mapping_rows"][0])

    def test_unknown_source_input_key_is_rejected(self):
        with self.assertRaises(ValueError):
            self.compile({"source-one": [mapping()], "unbound-source": [mapping()]})

    def test_duplicate_source_key_raw_table_or_identity_is_rejected(self):
        for duplicate in ("SOURCE_KEY", "RAW_TABLE", "IDENTITY"):
            first, second = profile(), profile("source-two", "SOURCE_TWO")
            if duplicate == "IDENTITY":
                second["SOURCE_TABLE_NAME"] = first["SOURCE_TABLE_NAME"]
            else:
                second[duplicate] = first[duplicate]
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                self.compile({"source-one": [mapping()], "source-two": [mapping()]},
                             profiles=[first, second])

    def test_duplicate_unknown_or_aliased_enabled_model_is_rejected(self):
        for selected in (("SSP", "SSP"), ("SSP", "NOT_REGISTERED"), ("SSP", "System Security Plan")):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                self.compile({"source-one": [mapping()]}, profiles=[profile(models=selected)])

    def test_source_specific_storage_is_explicit_not_borrowed_from_another_source(self):
        profiles = [profile(models=("SSP",)), profile("source-two", "SOURCE_TWO", ("SSP",))]
        contracts_by_source = []
        for index, item in enumerate(profiles):
            value = {"VERIFIED": True, "TARGET_DIM": "DEV.S" + str(index) + ".DIM",
                     "TARGET_FACT": "DEV.S" + str(index) + ".FACT",
                     "DIM_PK_COLUMN": "PK_NODE", "FACT_PK_COLUMN": "PK_EDGE"}
            contracts_by_source.append(copy.deepcopy(value))
            item["MODEL_STORAGE_CONTRACTS"] = {"SSP": value}
        result = self.compile({p["SOURCE_KEY"]: [mapping()] for p in profiles}, profiles=profiles)
        for context, expected in zip(result, contracts_by_source):
            self.assertEqual(expected, context["config"]["STORAGE_CONTRACT"])
            self.assertEqual(expected["TARGET_DIM"], context["config"]["TARGET_DIM"])
            self.assertIsNot(context["config"]["STORAGE_CONTRACT"], expected)
        self.assertNotEqual(result[0]["config"]["TARGET_DIM"], result[1]["config"]["TARGET_DIM"])

    def test_case_only_duplicate_physical_source_is_rejected(self):
        second = profile("source-two", "SOURCE_TWO")
        second["RAW_TABLE"] = profile()["RAW_TABLE"].lower()
        with self.assertRaises(ValueError):
            self.compile({"source-one": [mapping()], "source-two": [mapping()]},
                         profiles=[profile(), second])

    def test_ambiguous_normalized_alias_cannot_choose_a_model(self):
        models = contracts()
        models["ASSESSMENT_RESULTS"]["MODEL_ALIASES"] += ("system_security_plan",)
        with self.assertRaises(ValueError):
            self.compile({"source-one": [mapping()]}, models=models)

    def test_conflicting_explicit_model_and_path_is_reported_not_reassigned(self):
        row = mapping("VULNERABILITY_SCORE", "SSP", OBS)
        for context in self.compile({"source-one": [row]}):
            self.conserved(context, 1)
            report = context["routing_report"]
            self.assertEqual("BLOCKED", report["STATUS"])
            self.assertEqual(1, report["BLOCKED_ROWS"])
            self.assertIn("MODEL_PATH_CONFLICT", {issue["reason"] for issue in report["ISSUES"]})
            self.assertEqual([], context["mapping_rows"])

    def test_unrecognized_model_label_uses_registered_path_as_authority(self):
        row = mapping(model="Unrecognized Governance Model")
        for context in self.compile({"source-one": [row]}):
            self.conserved(context, 1)
            self.assertEqual(0, context["routing_report"]["BLOCKED_ROWS"])
            self.assertEqual("READY", context["routing_report"]["STATUS"])
            if context["config"]["OSCAL_MODEL"] == "SSP":
                self.assertEqual(1, context["routing_report"]["SELECTED_ROWS"])
                self.assertEqual("SSP", context["mapping_rows"][0]["OSCAL_MODEL"])
                self.assertEqual(row["OSCAL_MODEL"], context["mapping_rows"][0]["ARTIFACT_MODEL"])
            else:
                self.assertEqual(1, context["routing_report"]["EXCLUDED_ROWS"])

    def test_unknown_root_path_is_visible_and_blocked(self):
        row = mapping(model="SSP", path="unapproved-model.branch[]")
        for context in self.compile({"source-one": [row]}):
            self.conserved(context, 1)
            self.assertEqual(1, context["routing_report"]["BLOCKED_ROWS"])
            self.assertEqual([], context["mapping_rows"])

    def test_unregistered_nested_collection_is_blocked_not_attached_as_scalar(self):
        row = mapping(path=META + ".unapproved-items[].value")
        context = self.compile({"source-one": [row]},
                               profiles=[profile(models=("SSP",))])[0]
        self.conserved(context, 1)
        self.assertEqual(1, context["routing_report"]["BLOCKED_ROWS"])
        self.assertEqual([], context["mapping_rows"])

    def test_ambiguous_mapping_column_aliases_are_rejected(self):
        row = mapping()
        row["SOURCE_FIELD"] = "DIFFERENT_FIELD"
        with self.assertRaises(ValueError):
            self.compile({"source-one": [row]})

    def test_disabled_but_known_other_model_is_excluded(self):
        contexts = self.compile({"source-one": [mapping()] + ar_mappings()},
                                profiles=[profile(models=("SSP",))])
        self.assertEqual(1, len(contexts))
        self.conserved(contexts[0], 18)
        self.assertEqual(17, contexts[0]["routing_report"]["EXCLUDED_ROWS"])
        self.assertEqual("READY", contexts[0]["routing_report"]["STATUS"])

    def test_missing_target_and_explicit_deferred_rows_are_preserved_as_deferred(self):
        for row in (mapping(path=None), mapping(STATUS="Deferred"), mapping(STATUS="TBD")):
            context = self.compile({"source-one": [row]},
                                   profiles=[profile(models=("SSP",))])[0]
            self.conserved(context, 1)
            self.assertEqual(1, context["routing_report"]["DEFERRED_ROWS"])
            self.assertEqual([], context["mapping_rows"])

    def test_missing_source_field_is_blocked_not_silently_dropped(self):
        context = self.compile({"source-one": [mapping(field=None)]},
                               profiles=[profile(models=("SSP",))])[0]
        self.conserved(context, 1)
        self.assertEqual(1, context["routing_report"]["BLOCKED_ROWS"])
        self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])

    def test_ar_accepted_seventeen_exclude_all_candidate_fields_before_graph_policy(self):
        context = self.compile({"source-one": ar_mappings(candidate=True)},
                               profiles=[profile(models=("ASSESSMENT_RESULTS",))])[0]
        self.conserved(context, 34)
        self.assertEqual(17, context["routing_report"]["SELECTED_ROWS"])
        self.assertEqual(17, context["routing_report"]["EXCLUDED_ROWS"])
        self.assertEqual(0, context["routing_report"]["BLOCKED_ROWS"])
        self.assertEqual(set(ACCEPTED_FIELDS), {r["SOURCE_FIELD_NAME"] for r in context["mapping_rows"]})
        self.assertTrue(set(CANDIDATE_FIELDS).isdisjoint(
            {r["SOURCE_FIELD_NAME"] for r in context["mapping_rows"]}))

    def test_header_aliases_and_generic_extension_label_preserve_rule(self):
        row = {"Archer_Field_Name": "VULNERABILITY_SCORE", "OSCAL_Model": "Extension Properties",
               "OSCAL_Element_Path": OBS, "Mapping_Type": "Extension Property",
               "Notes": "Archer-specific risk scoring - map as observation"}
        context = self.compile({"source-one": [row]},
                               profiles=[profile(models=("ASSESSMENT_RESULTS",))])[0]
        self.conserved(context, 1)
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        emitted = context["mapping_rows"][0]
        self.assertEqual("VULNERABILITY_SCORE", emitted["SOURCE_FIELD_NAME"])
        self.assertEqual(OBS, emitted["OSCAL_ELEMENT_PATH"])
        self.assertEqual(row["Notes"], emitted["NOTES"])
        self.assertFalse(emitted.get("TRANSFORMATION_LOGIC"))

    def test_compilation_is_read_only_and_does_not_mutate_inputs(self):
        rows = {"source-one": [mapping()] + ar_mappings(candidate=True)}
        original = copy.deepcopy((rows, self.registry, self.profiles, self.models))
        self.compile(rows)
        self.assertEqual(original, (rows, self.registry, self.profiles, self.models))
        self.assertFalse(self.profiles[0]["BASE_CONFIG"]["EXECUTE_WRITES"])

    def test_registry_column_aliases_preserve_model_and_owner(self):
        aliased = []
        for original in registry():
            row = dict(original)
            row["OSCAL_MODEL"] = row.pop("OSCAL_MODEL_KEY")
            row["ELEMENT_PATH"] = row.pop("NODE_PATH")
            aliased.append(row)
        contexts = self.indexed(self.compile({"source-one": [mapping()] + ar_mappings()},
                                            registry_rows=aliased))
        self.assertEqual({META}, set(contexts[("source-one", "SSP")]["mappings_by_path"]))
        self.assertEqual({OBS}, set(contexts[("source-one", "ASSESSMENT_RESULTS")]["mappings_by_path"]))
        for context in contexts.values():
            self.assertEqual("READY", context["routing_report"]["STATUS"])

    def test_finite_model_alias_normalization_routes_only_to_registered_model(self):
        for label in ("System Security Plan", "SSP - Metadata", "s_s_p"):
            context = self.compile({"source-one": [mapping(model=label)]},
                                   profiles=[profile(models=("SSP",))])[0]
            self.assertEqual(1, context["routing_report"]["SELECTED_ROWS"])
            self.assertEqual("SSP", context["mapping_rows"][0]["OSCAL_MODEL"])


if __name__ == "__main__":
    unittest.main()

