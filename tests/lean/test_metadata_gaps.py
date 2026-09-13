"""Cross-cell metadata/input boundaries using the maintained CSV and source profiles."""
import ast
import contextlib
import copy
from decimal import Decimal
import io
import unittest

from lean_support import CELLS, ROOT, namespace
from test_inputs import input_namespace
from test_multi_model_inputs import Session, raw
from test_registry_release import mapping_rows, release_registry
import test_metadata_driven_contract as synthetic


def configuration_with_sources(sources):
    """Execute actual Cell One configuration with only its source literal replaced."""
    path = CELLS / "01_initialization_and_configuration.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    body = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("snowflake"):
            continue
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "SOURCE_FILES"
                                               for target in node.targets):
            node.value = ast.Name(id="source_overrides", ctx=ast.Load())
        body.append(node)
    ns = {"source_overrides": copy.deepcopy(sources), "get_active_session": lambda: object()}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), str(path), "exec"), ns)
    return ns


class ConfigurationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.sources = copy.deepcopy(namespace()["SOURCE_FILES"])

    def test_duplicate_source_key_rejects_even_with_different_physical_tables(self):
        second = dict(self.sources[0], RAW_TABLE="SYNTHETIC.OTHER_RAW", SOURCE_TABLE_NAME="OTHER_RAW")
        with self.assertRaisesRegex(ValueError, "source key|source binding"):
            configuration_with_sources([*self.sources, second])

    def test_case_only_duplicate_physical_table_rejects(self):
        second = dict(self.sources[0], SOURCE_KEY="source-two", SOURCE_TABLE_NAME="OTHER_RAW",
                      RAW_TABLE=self.sources[0]["RAW_TABLE"].lower())
        with self.assertRaises(ValueError):
            configuration_with_sources([*self.sources, second])

    def test_case_only_duplicate_logical_source_namespace_rejects(self):
        second = dict(self.sources[0], SOURCE_KEY="source-two", RAW_TABLE="SYNTHETIC.OTHER_RAW",
                      SOURCE_TABLE_NAME=self.sources[0]["SOURCE_TABLE_NAME"].lower())
        with self.assertRaises(ValueError):
            configuration_with_sources([*self.sources, second])

    def test_distinct_source_profiles_keep_separate_model_and_base_config_copies(self):
        second = dict(self.sources[0], SOURCE_KEY="source-two", RAW_TABLE="SYNTHETIC.OTHER_RAW", SOURCE_TABLE_NAME="OTHER_RAW")
        ns = configuration_with_sources([*self.sources, second])
        first, second = ns["SOURCE_PROFILES"]
        self.assertIsNot(first["BASE_CONFIG"], second["BASE_CONFIG"])
        self.assertEqual(("SSP",), first["MODEL_KEYS"])
        self.assertFalse(first["BASE_CONFIG"]["EXECUTE_WRITES"])


class CsvRegistryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.profile = copy.deepcopy(self.ns["SOURCE_PROFILES"][0])
        self.profile["MAPPING_FILE"] = str(ROOT / "Mapping/ARCHER_OSCAL_MAPPINGS.csv")

    def compile(self, rows, registry=None):
        return self.ns["compile_mapping_contexts"](
            {self.profile["SOURCE_KEY"]: rows}, release_registry() if registry is None else registry,
            [self.profile], self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])

    def test_real_csv_optional_cells_do_not_lose_required_or_lookup_parameters(self):
        rows = self.ns["load_mapping_rows"](self.profile)
        self.assertEqual(151, len(rows))
        contexts = self.compile(rows)
        self.assertEqual({"SSP": 47, "ASSESSMENT_RESULTS": 17},
                         {context["config"]["OSCAL_MODEL"]: len(context["mapping_rows"]) for context in contexts})
        selected = {row["RULE_ID"]: row for context in contexts for row in context["mapping_rows"]}
        for rule in ("support:metadata-title", "support:oscal-version", "support:document-version"):
            self.assertTrue(selected[rule]["REPRESENTATION_PARAMS"]["required"])
        self.assertEqual("CONFIG", selected["support:oscal-version"]["REPRESENTATION_PARAMS"]["value_source"])
        self.assertEqual({"software", "interconnection"},
                         {row["REPRESENTATION_PARAMS"]["hydrate_lookup"] for row in selected.values()
                          if row["REPRESENTATION_PARAMS"].get("hydrate_lookup")})
        self.assertEqual({"APPROVED", "BLOCKED_IF_POPULATED"}, {row["APPROVAL_STATUS"] for row in selected.values()})

    def test_mistyped_mapping_source_binding_cannot_produce_an_empty_ready_plan(self):
        self.profile["MAPPING_SOURCE_VALUE"] = "source-one-typo"
        with self.assertRaisesRegex(ValueError, "No mapping rows"):
            self.ns["load_mapping_rows"](self.profile)

    def test_removed_provenance_only_columns_do_not_change_execution(self):
        columns = {"SOURCE_DOCUMENT", "SOURCE_LINE", "ORIGINAL_EXCEL_ROW", "EXECUTION_NOTE", "ORIGINAL_ROW_ID"}
        original = self.compile(mapping_rows())
        lean_rows = [{key: value for key, value in row.items() if key not in columns} for row in mapping_rows()]
        reduced = self.compile(lean_rows)
        for expected, actual in zip(original, reduced):
            for key in ("TRANSFORM_PARAMS", "REPRESENTATION_PARAMS", "RULE_ID", "OWNER_ELEMENT_PATH"):
                self.assertEqual([row[key] for row in expected["mapping_rows"]], [row[key] for row in actual["mapping_rows"]])

    def test_blank_optional_registry_item_path_is_equivalent_to_sql_null(self):
        rows = synthetic.registry_rows()
        for row in rows:
            if row["ITEM_PATH"] is None:
                row["ITEM_PATH"] = ""
        contexts = self.ns["compile_mapping_contexts"](
            {"source-one": [synthetic.mapping()]}, rows, [synthetic.profile()],
            {synthetic.MODEL: synthetic.model_contract()})
        self.assertEqual("READY", contexts[0]["routing_report"]["STATUS"])
        self.assertIsNone(contexts[0]["compiled_plan"]["elements"][synthetic.RESULT]["parameters"]["registry_contract"]["item_path"])

    def test_integral_snowflake_decimal_process_order_is_normalized_without_input_mutation(self):
        rows = release_registry()
        for row in rows:
            row["PROCESS_ORDER"] = Decimal(str(row["PROCESS_ORDER"]))
        before = copy.deepcopy(rows)
        contexts = self.compile(mapping_rows(), rows)
        self.assertEqual(before, rows)
        self.assertTrue(all(type(row["PROCESS_ORDER"]) is int for context in contexts for row in context["registry_rows"]))

    def test_nonintegral_or_boolean_registry_order_is_rejected_before_graph_build(self):
        for value in (Decimal("1.5"), True, False):
            rows = release_registry()
            rows[0]["PROCESS_ORDER"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.compile(mapping_rows(), rows)


class LookupInputBoundaryTests(unittest.TestCase):
    def setUp(self):
        deployment = namespace()
        self.profile = copy.deepcopy(deployment["SOURCE_PROFILES"][0])
        self.models, self.config = deployment["MODEL_CONTRACTS"], deployment["CONFIG"]
        self.load = input_namespace()["load_source_lookups"]

    def session(self, values):
        return Session({self.config["ARCHER_META_VALUE_TABLE"]: values,
                        **{contract["source_table"]: [raw("one", "fixture")]
                           for contract in self.profile["LOOKUP_CONTRACTS"].values()}})

    def test_actual_profile_loads_each_component_lookup_once_and_preserves_picklist_labels(self):
        session = self.session([{"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": " High "},
                                {"SELECT_VALUE_ID": 2, "SELECT_VALUE_NAME": "Custom label"}])
        lookups = self.load(session, self.profile, self.models, self.config)
        self.assertEqual({"1": "High", "2": "Custom label"}, lookups["archer_values"])
        self.assertEqual({"1": "High"}, lookups["fips_values"])
        self.assertEqual({"software", "interconnection"}, set(lookups["component_sources"]))
        self.assertTrue(all(count == 1 for count in session.cache_calls.values()))
        self.assertEqual(2, len(session.cache_calls))

    def test_conflicting_picklist_labels_reject_before_component_snapshots(self):
        session = self.session([{"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "Low"},
                                {"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "High"}])
        with self.assertRaisesRegex(ValueError, "conflicting labels"):
            self.load(session, self.profile, self.models, self.config)
        self.assertEqual({}, dict(session.cache_calls))

    def test_equal_picklist_duplicates_collapse_and_null_ids_do_not_become_keys(self):
        session = self.session([{"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "High"},
                                {"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "High"},
                                {"SELECT_VALUE_ID": None, "SELECT_VALUE_NAME": "Unbound"}])
        result = self.load(session, self.profile, self.models, self.config)
        self.assertEqual({"1": "High"}, result["archer_values"])

    def test_ar_only_input_does_not_read_ssp_component_tables(self):
        self.profile["MODEL_KEYS"] = ("ASSESSMENT_RESULTS",)
        session = self.session([{"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "High"}])
        result = self.load(session, self.profile, self.models, self.config)
        self.assertEqual({}, result["component_sources"])
        self.assertEqual({}, dict(session.cache_calls))
        queried = [event[1] for event in session.events if event[0] == "table"]
        self.assertEqual([self.config["ARCHER_META_VALUE_TABLE"]], queried)


if __name__ == "__main__":
    unittest.main()
