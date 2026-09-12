"""Cell One selection contracts; no Snowpark imports or database I/O."""
import ast
import copy
import csv
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CELL = ROOT / "notebooks/cells/01_initialization_and_configuration.py"
DEFAULT = object()
TARGET_KEYS = ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN")


class NoDatabaseIO:
    def __getattr__(self, name):
        raise AssertionError("Cell One must not read or write database objects")


def cell_namespace(selection=DEFAULT, storage_verified=DEFAULT):
    tree = ast.parse(CELL.read_text(encoding="utf-8"))
    body, selector_count = [], 0
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("snowflake"):
            continue
        if isinstance(node, ast.Import) and any(item.name.startswith("snowflake") for item in node.names):
            continue
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "SELECTED_MODELS" in names:
                selector_count += 1
                if selection is not DEFAULT:
                    node.value = ast.Name(id="_test_selection", ctx=ast.Load())
            if "MAPPER_CATALOG" in names and storage_verified is not DEFAULT:
                node.value = ast.Name(id="_test_catalog", ctx=ast.Load())
        body.append(node)
    if selector_count != 1:
        raise AssertionError("Cell One must expose exactly one SELECTED_MODELS assignment")
    catalog = json.loads((ROOT / "notebooks/metadata/mapper_contract.v1.json").read_text(encoding="utf-8"))
    if storage_verified is not DEFAULT:
        catalog["MODELS"]["SSP"]["STORAGE_CONTRACT"]["VERIFIED"] = storage_verified
    namespace = {"get_active_session": lambda: NoDatabaseIO(), "_test_selection": selection,
                 "_test_catalog": catalog, "__file__": str(CELL)}
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    with redirect_stdout(io.StringIO()):
        exec(compile(module, str(CELL), "exec"), namespace)
    return namespace


def selector_function():
    tree = ast.parse(CELL.read_text(encoding="utf-8"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "_selected_model_keys"]
    if len(functions) != 1:
        raise AssertionError("Expected one pure model selection helper")
    namespace = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(CELL), "exec"), namespace)
    return namespace["_selected_model_keys"]


class ModelSelectionTests(unittest.TestCase):
    def assert_routes(self, namespace, expected):
        self.assertTrue(namespace["SOURCE_PROFILES"])
        for profile in namespace["SOURCE_PROFILES"]:
            self.assertEqual(profile["MODEL_KEYS"], expected)
            self.assertIsInstance(profile["MODEL_KEYS"], tuple)
            self.assertEqual(profile["BASE_CONFIG"]["OSCAL_MODEL"], expected[0])
            self.assertIs(profile["BASE_CONFIG"]["EXECUTE_WRITES"], False)
            self.assertIsNot(profile["BASE_CONFIG"], namespace["CONFIG"])
        self.assertEqual(namespace["CONFIG"]["OSCAL_MODEL"], expected[0])
        self.assertIs(namespace["CONFIG"]["EXECUTE_WRITES"], False)

    def assert_no_targets(self, namespace):
        for config in [namespace["CONFIG"]] + [p["BASE_CONFIG"] for p in namespace["SOURCE_PROFILES"]]:
            for key in TARGET_KEYS:
                self.assertNotIn(key, config)

    def test_published_default_selects_both_models_with_writes_disabled(self):
        namespace = cell_namespace()
        self.assertEqual(namespace["SELECTED_MODELS"], ("SSP", "ASSESSMENT_RESULTS"))
        self.assert_routes(namespace, ("SSP", "ASSESSMENT_RESULTS"))

    def test_ssp_only_accepts_string_tuple_and_list(self):
        for selection in ("SSP", ("SSP",), ["SSP"]):
            with self.subTest(selection=selection):
                namespace = cell_namespace(selection)
                self.assert_routes(namespace, ("SSP",))
                contract = namespace["MODEL_CONTRACTS"]["SSP"]["STORAGE_CONTRACT"]
                self.assertIs(contract["VERIFIED"], True)
                for key in TARGET_KEYS:
                    self.assertEqual(namespace["CONFIG"][key], contract[key])
                    self.assertEqual(namespace["SOURCE_PROFILES"][0]["BASE_CONFIG"][key], contract[key])

    def test_ar_only_never_inherits_ssp_destinations(self):
        for selection in ("ASSESSMENT_RESULTS", ("ASSESSMENT_RESULTS",), ["ASSESSMENT_RESULTS"]):
            with self.subTest(selection=selection):
                namespace = cell_namespace(selection)
                self.assert_routes(namespace, ("ASSESSMENT_RESULTS",))
                self.assert_no_targets(namespace)
                self.assertIsNone(namespace["MODEL_CONTRACTS"]["ASSESSMENT_RESULTS"]["STORAGE_CONTRACT"])

    def test_order_selects_compatibility_model_without_changing_routes(self):
        for selection in (("SSP", "ASSESSMENT_RESULTS"), ("ASSESSMENT_RESULTS", "SSP")):
            with self.subTest(selection=selection):
                namespace = cell_namespace(selection)
                self.assert_routes(namespace, selection)
                if selection[0] == "ASSESSMENT_RESULTS":
                    self.assert_no_targets(namespace)
                else:
                    self.assertIn("TARGET_DIM", namespace["CONFIG"])

    def test_ar_selection_preserves_ssp_contract_for_later_explicit_selection(self):
        baseline, ar_only = cell_namespace(("SSP",)), cell_namespace(("ASSESSMENT_RESULTS",))
        self.assertEqual(ar_only["MODEL_CONTRACTS"], baseline["MODEL_CONTRACTS"])
        with (ROOT / "Mapping/ARCHER_OSCAL_MAPPINGS.csv").open(
                encoding="utf-8-sig", newline="") as handle:
            rules = [row for row in csv.DictReader(handle)
                     if row["OSCAL_MODEL"].strip().upper().replace(" ", "_")
                     == "ASSESSMENT_RESULTS"
                     and row["EXECUTION_STATUS"] == "APPROVED"]
        self.assertEqual(len(rules), 17)
        self.assertTrue(all(rule["EXECUTION_STATUS"] == "APPROVED" for rule in rules))
        self.assert_no_targets(ar_only)

    def test_unverified_storage_never_enters_compatibility_configuration(self):
        for verified in (False, None, "True", 1):
            with self.subTest(verified=verified):
                namespace = cell_namespace(("SSP",), storage_verified=verified)
                self.assert_routes(namespace, ("SSP",))
                self.assert_no_targets(namespace)

    def test_list_is_copied_to_an_immutable_route_tuple(self):
        selection = ["SSP", "ASSESSMENT_RESULTS"]
        namespace = cell_namespace(selection)
        self.assertEqual(selection, ["SSP", "ASSESSMENT_RESULTS"])
        selection.clear()
        self.assert_routes(namespace, ("SSP", "ASSESSMENT_RESULTS"))

    def test_invalid_configuration_selection_fails_instead_of_using_ssp(self):
        for selection in (None, False, (), [], "", "XYZ", {"SSP"}, {"SSP": True},
                          ("SSP", "SSP"), ("SSP", "UNKNOWN"), ("SSP", None)):
            with self.subTest(selection=selection):
                with self.assertRaises((TypeError, ValueError)):
                    cell_namespace(selection)

    def test_helper_accepts_only_exact_configured_model_keys(self):
        select = selector_function()
        contracts = {"SSP": {}, "ASSESSMENT_RESULTS": {}, "XYZ": {}}
        for selection, expected in (("XYZ", ("XYZ",)), (["XYZ", "SSP"], ("XYZ", "SSP")),
                                    (("ASSESSMENT_RESULTS",), ("ASSESSMENT_RESULTS",))):
            with self.subTest(selection=selection):
                self.assertEqual(select(selection, contracts), expected)
        for selection in ("AR", "ssp", "SSP ", " SSP", "Assessment Results"):
            with self.subTest(selection=selection):
                with self.assertRaises((TypeError, ValueError)):
                    select(selection, contracts)

    def test_helper_rejects_empty_and_wrong_container_types(self):
        select = selector_function()
        for selection in (None, True, False, 1, 1.5, b"SSP", "", " ", (), [], set(),
                          {"SSP"}, {}, {"SSP": {}}, frozenset({"SSP"})):
            with self.subTest(selection=selection):
                with self.assertRaises((TypeError, ValueError)):
                    select(selection, {"SSP": {}})

    def test_helper_rejects_duplicates_unknown_and_invalid_members(self):
        select = selector_function()
        for selection in (("SSP", "SSP"), ["SSP", "SSP"], ("XYZ",), ("",), (" ",),
                          (None,), (True,), (7,), ([],), ({},), ("SSP", "AR"), ("SSP", "SSP ")):
            with self.subTest(selection=selection):
                with self.assertRaises((TypeError, ValueError)):
                    select(selection, {"SSP": {}, "ASSESSMENT_RESULTS": {}})

    def test_helper_does_not_mutate_selection_or_model_contracts(self):
        select = selector_function()
        selection = ["ASSESSMENT_RESULTS", "SSP"]
        contracts = {"SSP": {"STORAGE_CONTRACT": {"VERIFIED": True}},
                     "ASSESSMENT_RESULTS": {"STORAGE_CONTRACT": None}}
        selection_before, contracts_before = copy.deepcopy((selection, contracts))
        result = select(selection, contracts)
        self.assertEqual(result, ("ASSESSMENT_RESULTS", "SSP"))
        self.assertIsInstance(result, tuple)
        self.assertEqual(selection, selection_before)
        self.assertEqual(contracts, contracts_before)


if __name__ == "__main__":
    unittest.main()
