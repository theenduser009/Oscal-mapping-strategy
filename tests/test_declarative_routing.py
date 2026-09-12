"""Read-only declarative routing regressions; all metadata and records are synthetic."""
import ast
import copy
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CELL3 = ROOT / "notebooks/cells/03_canonical_mapping_contract.py"
SSP = "system-security-plan"
AR = "assessment-results"
POAM = "plan-of-action-and-milestones"
FUTURE = "future-document"


def namespace():
    tree = ast.parse(CELL3.read_text(encoding="utf-8-sig"))
    body = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            body.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            try:
                ast.literal_eval(node.value)
            except (TypeError, ValueError, SyntaxError):
                continue
            body.append(node)
    ns = {}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(CELL3), "exec"), ns)
    return ns


def contracts():
    return {
        model: {
            "MODEL_KEY": model, "ROOT_PATH": root, "POLICY": "metadata-v1",
            "STORAGE_CONTRACT": None, "UNREVIEWED_ROWS": "DEFER",
            "ELEMENTS": {root: {"operator": "object", "parameters": {"materialize_empty": True}}},
        }
        for model, root in (("SSP", SSP), ("ASSESSMENT_RESULTS", AR))
    }


def registry():
    return [
        {"OSCAL_MODEL_KEY": model, "NODE_PATH": root, "IS_COLLECTION": False,
         "PARENT_NODE_PATH": None, "IS_ACTIVE": True, "ELEMENT_TYPE": root}
        for model, root in (
            ("SSP", SSP), ("ASSESSMENT_RESULTS", AR), ("POAM", POAM),
            ("FUTURE_MODEL", FUTURE))
    ]


def profile(models=("SSP", "ASSESSMENT_RESULTS")):
    return {
        "SOURCE_KEY": "source-one", "SOURCE_SYSTEM_NAME": "ARCHER",
        "SOURCE_TABLE_NAME": "SYNTHETIC_SOURCE", "RAW_TABLE": "TEST.DEV.SYNTHETIC_SOURCE",
        "MAPPING_FILE": "synthetic.csv", "MODEL_KEYS": models,
        "BASE_CONFIG": {"EXECUTE_WRITES": False, "IDENTITY_VERSION": "test-v1"},
    }


def mapping(field="UNSEEN_APPROVED_FIELD", model="SSP", root=SSP, **changes):
    path = changes.get("OSCAL_ELEMENT_PATH", root + ".title")
    row = {
        "SOURCE_KEY": "source-one", "SOURCE_FIELD_NAME": field, "OSCAL_MODEL": model,
        "OSCAL_ELEMENT_PATH": path, "MAPPING_TYPE": "Direct",
        "TRANSFORM_ID": "text", "EXECUTION_STATUS": "APPROVED",
        "RUNTIME_TARGET_PATH": path, "RULE_ID": "routing:" + str(field) + ":" + str(path),
    }
    row.update(changes)
    return row


class DeclarativeRouting(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()

    def compile(self, rows, models=None, selected=("SSP", "ASSESSMENT_RESULTS")):
        mappings = {"source-one": rows}
        inputs = (mappings, registry(), [profile(selected)], models or contracts())
        original = copy.deepcopy(inputs)
        contexts = self.ns["compile_mapping_contexts"](*inputs)
        self.assertEqual(original, inputs, "Compiler must not mutate source metadata")
        for context in contexts:
            report = context["routing_report"]
            self.assertEqual(len(rows), report["INPUT_ROWS"])
            self.assertEqual(len(rows), sum(report[key] for key in (
                "SELECTED_ROWS", "EXCLUDED_ROWS", "DEFERRED_ROWS", "BLOCKED_ROWS")))
            self.assertEqual(report["SELECTED_ROWS"], len(context["mapping_rows"]))
            self.assertFalse(context["config"]["EXECUTE_WRITES"])
        return {context["config"]["OSCAL_MODEL"]: context for context in contexts}

    def test_608_mixed_rows_do_not_block_selected_models_for_other_model_field_gaps(self):
        rows = [
            mapping(field="SSP_NEW_TEXT"),
            mapping(field="AR_NEW_TEXT", model="ASSESSMENT_RESULTS", root=AR),
        ]
        for index in range(606):
            # Registry establishes ownership even without a configured POAM executor.
            rows.append(mapping(
                field=None if index % 2 else "OTHER_FIELD_" + str(index),
                model=("POAM", "", "Extension Properties")[index % 3],
                root=POAM, TRANSFORM_ID="unknown-for-another-model",
                APPROVAL_STATUS=None))
        for model, context in self.compile(rows).items():
            report = context["routing_report"]
            self.assertEqual("READY", report["STATUS"])
            self.assertEqual(1, report["SELECTED_ROWS"])
            self.assertEqual(607, report["EXCLUDED_ROWS"])
            self.assertEqual(0, report["BLOCKED_ROWS"])
            self.assertEqual([], report["ISSUES"])
            self.assertEqual({}, report["REASON_COUNTS"])
            self.assertEqual(model, context["mapping_rows"][0]["OSCAL_MODEL"])
            self.assertEqual("text", context["compiled_plan"]["mappings"][0]["TRANSFORM_ID"])

    def test_known_other_label_with_no_path_or_field_is_out_of_selected_scope(self):
        row = mapping(field=None, model="ASSESSMENT_RESULTS", root=AR, OSCAL_ELEMENT_PATH=None)
        contexts = self.compile([mapping(), row])
        self.assertEqual("READY", contexts["SSP"]["routing_report"]["STATUS"])
        self.assertEqual(1, contexts["SSP"]["routing_report"]["EXCLUDED_ROWS"])
        self.assertEqual("BLOCKED", contexts["ASSESSMENT_RESULTS"]["routing_report"]["STATUS"])
        self.assertEqual({"MISSING_SOURCE_FIELD": 1},
                         contexts["ASSESSMENT_RESULTS"]["routing_report"]["REASON_COUNTS"])

    def test_unrecognized_alias_with_registered_other_root_is_out_of_scope(self):
        for field in (None, "OTHER_FIELD"):
            with self.subTest(field=field):
                row = mapping(field=field, model="POAM - Items", root=POAM)
                for context in self.compile([mapping(), row]).values():
                    report = context["routing_report"]
                    self.assertEqual("READY", report["STATUS"])
                    self.assertEqual(0, report["BLOCKED_ROWS"])
                    self.assertGreaterEqual(report["EXCLUDED_ROWS"], 1)
                    self.assertEqual({}, report["REASON_COUNTS"])
                    self.assertEqual({}, report["SEVERITY_COUNTS"])

    def test_true_label_path_conflicts_are_not_hidden_by_missing_source(self):
        for field in (None, "CONFLICTING_FIELD"):
            row = mapping(field=field, model="SSP", root=AR)
            for context in self.compile([mapping(), row]).values():
                self.assertEqual({"MODEL_PATH_CONFLICT": 1},
                                 context["routing_report"]["REASON_COUNTS"])

    def test_unknown_root_is_not_excluded_even_with_known_other_label(self):
        row = mapping(field=None, model="POAM", root="unreviewed-root")
        for context in self.compile([mapping(), row]).values():
            self.assertEqual({"UNKNOWN_MODEL_OR_PATH": 1},
                             context["routing_report"]["REASON_COUNTS"])

    def test_missing_source_for_selected_or_unowned_row_remains_blocked(self):
        for row in (mapping(field=None), mapping(field=None, model="", OSCAL_ELEMENT_PATH=None)):
            with self.subTest(row=row):
                context = self.compile([row], selected=("SSP",))["SSP"]
                self.assertEqual({"MISSING_SOURCE_FIELD": 1},
                                 context["routing_report"]["REASON_COUNTS"])

    def test_future_model_requires_metadata_only_and_keeps_selected_field_validation(self):
        models = contracts()
        models["FUTURE_MODEL"] = {
            "MODEL_KEY": "FUTURE_MODEL", "ROOT_PATH": FUTURE, "POLICY": "metadata-v1",
            "STORAGE_CONTRACT": None,
            "ELEMENTS": {FUTURE: {"operator": "object", "parameters": {}}},
        }
        rows = [
            mapping(field="BRAND_NEW_FIELD", model="FUTURE_MODEL", root=FUTURE),
            mapping(field=None, model="POAM", root=POAM),
        ]
        context = self.compile(rows, models, ("FUTURE_MODEL",))["FUTURE_MODEL"]
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        self.assertEqual("BRAND_NEW_FIELD", context["compiled_plan"]["mappings"][0]["SOURCE_FIELD_NAME"])
        rows[0]["SOURCE_FIELD_NAME"] = None
        context = self.compile(rows, models, ("FUTURE_MODEL",))["FUTURE_MODEL"]
        self.assertEqual({"MISSING_SOURCE_FIELD": 1}, context["routing_report"]["REASON_COUNTS"])

    def test_608_issue_summary_keeps_exact_counts_and_prioritizes_blocked_samples(self):
        rows = []
        for index in range(60):
            row = mapping(field="UNREVIEWED_" + str(index))
            for key in ("EXECUTION_STATUS", "TRANSFORM_ID", "RUNTIME_TARGET_PATH", "RULE_ID"):
                row.pop(key)
            rows.append(row)
        rows.extend(mapping(field="BAD_PATH_" + str(index), model="Unknown Model",
                            root="unregistered-real-model")
                    for index in range(547))
        rows.append(mapping())
        context = self.compile(rows, selected=("SSP",))["SSP"]
        report = context["routing_report"]
        self.assertEqual((1, 0, 60, 547),
                         tuple(report[key] for key in (
                             "SELECTED_ROWS", "EXCLUDED_ROWS", "DEFERRED_ROWS", "BLOCKED_ROWS")))
        self.assertEqual({"MISSING_APPROVED_METADATA": 60, "UNKNOWN_MODEL_OR_PATH": 547},
                         report["REASON_COUNTS"])
        self.assertEqual({"DEFERRED": 60, "BLOCKED": 547}, report["SEVERITY_COUNTS"])
        self.assertEqual(607, report["ISSUE_EVENTS_TOTAL"])
        self.assertTrue(report["ISSUE_SAMPLES_TRUNCATED"])
        self.assertEqual(25, len(report["ISSUES"]))
        self.assertEqual(60, report["ISSUES"][0]["row"])
        self.assertTrue(all(issue["severity"] == "BLOCKED" for issue in report["ISSUES"]))
        self.assertNotIn("compiled_plan", context)

    def test_in_scope_unknown_transform_blocks_with_summarized_contract_reason(self):
        context = self.compile([mapping(TRANSFORM_ID="unknown")], selected=("SSP",))["SSP"]
        report = context["routing_report"]
        self.assertEqual("BLOCKED", report["STATUS"])
        self.assertEqual(1, report["BLOCKED_ROWS"])
        self.assertEqual(0, report["SELECTED_ROWS"])
        self.assertEqual({"METADATA_CONTRACT_ERROR": 1}, report["REASON_COUNTS"])
        self.assertEqual({"BLOCKED": 1}, report["SEVERITY_COUNTS"])
        self.assertEqual(1, report["ISSUE_EVENTS_TOTAL"])
        self.assertFalse(report["ISSUE_SAMPLES_TRUNCATED"])


if __name__ == "__main__":
    unittest.main()
