"""Lean live-registry compiler tests; no database access."""
import copy
import unittest

import test_metadata_driven_contract as base
import test_multi_model_graph as graph


ORIGINAL_REGISTRY_COLUMNS = {
    "OSCAL_MODEL_KEY", "NODE_PATH", "ELEMENT_TYPE", "PARENT_NODE_PATH",
    "IS_COLLECTION", "INSTANCE_KEY_RULE", "PROCESS_ORDER", "IS_ACTIVE",
    "ITEM_PATH",
}
LEAN_EXECUTION_COLUMNS = {"OPERATOR", "UUID_POLICY", "REQUIRED_MEMBERS"}
RETIRED_COLUMNS = {
    "MAPPER_METADATA_VERSION", "MAPPER_ENABLED", "PARENT_INSTANCE_RULE",
    "EMPTY_POLICY", "LIST_INSTANCE_RULE", "PROPERTY_NAME_RULE",
    "ASSEMBLY_POLICY", "DEFAULT_SINGLETON_POLICY", "REQUIRED_RULE_IDS",
    "REPORT_TARGET_PATH", "ROLES_PATH", "PARTIES_PATH", "PARTY_TYPE",
    "PARTY_UUID_PARTS", "PARTY_UUID_SOURCE_KEY",
}


def strict_contract(**extra):
    contract = {
        "MODEL_KEY": base.MODEL,
        "POLICY": "metadata-v1",
        "STORAGE_CONTRACT": None,
    }
    contract.update(extra)
    return contract


def annotated_registry():
    specs = {
        base.ROOT_PATH: ("object", "node"),
        base.SUMMARY: ("object", "omit"),
        base.RESULT: ("record", "node"),
        base.OBSERVATION: ("observations", "node"),
    }
    rows = []
    for original in base.registry_rows():
        row = dict(original)
        row["OPERATOR"], row["UUID_POLICY"] = specs[row["NODE_PATH"]]
        row["REQUIRED_MEMBERS"] = None
        rows.append(row)
    return rows


def reference_registry():
    rows = annotated_registry()
    for path, operator, identity, item_path, uuid_policy in (
        (base.SUMMARY + ".roles[]", "roles", "SOURCE_FIELD_NAME", "$", "omit"),
        (base.SUMMARY + ".parties[]", "parties", "ID", "UserList[]", "instance"),
        (base.SUMMARY + ".assignments[]", "assignments", "SOURCE_FIELD_NAME+ID",
         "UserList[]", "omit"),
    ):
        rows.append({
            "OSCAL_MODEL_KEY": base.MODEL,
            "NODE_PATH": path,
            "ELEMENT_TYPE": operator,
            "PARENT_NODE_PATH": base.SUMMARY,
            "IS_COLLECTION": True,
            "INSTANCE_KEY_RULE": identity,
            "PROCESS_ORDER": len(rows) + 1,
            "IS_ACTIVE": True,
            "ITEM_PATH": item_path,
            "OPERATOR": operator,
            "UUID_POLICY": uuid_policy,
            "REQUIRED_MEMBERS": None,
        })
    return rows


class RegistryMetadataContractTests(unittest.TestCase):
    def setUp(self):
        self.ns = base.namespace()

    def decode(self, rows=None, profiles=None, models=None, mappings=None):
        profiles = [base.profile()] if profiles is None else profiles
        mappings = {"source-one": [base.mapping()]} if mappings is None else mappings
        inputs = (
            annotated_registry() if rows is None else rows,
            profiles,
            {base.MODEL: strict_contract()} if models is None else models,
            mappings,
        )
        before = copy.deepcopy(inputs)
        result = self.ns["decode_registry_model_contracts"](*inputs)
        self.assertEqual(before, inputs)
        return result

    def compile(self, rows=None, mappings=None, models=None):
        source = base.profile()
        inputs = (
            {"source-one": [base.mapping()] if mappings is None else mappings},
            annotated_registry() if rows is None else rows,
            [source],
            {base.MODEL: strict_contract()} if models is None else models,
        )
        before = copy.deepcopy(inputs)
        contexts = self.ns["compile_mapping_contexts"](*inputs)
        self.assertEqual(before, inputs)
        return contexts[0]

    def test_original_nine_plus_only_three_sparse_rules(self):
        allowed = ORIGINAL_REGISTRY_COLUMNS | LEAN_EXECUTION_COLUMNS
        self.assertTrue(all(set(row) <= allowed for row in annotated_registry()))
        contract = self.decode()[base.MODEL]
        self.assertEqual(base.ROOT_PATH, contract["ROOT_PATH"])
        self.assertEqual(
            {row["NODE_PATH"] for row in annotated_registry()},
            set(contract["ELEMENTS"]),
        )
        self.assertEqual(
            "source-record",
            contract["ELEMENTS"][base.OBSERVATION]["parameters"]["parent_instance_rule"],
        )
        self.assertEqual([], contract["REFERENCE_GROUPS"])
        self.assertIsNone(contract["DEFAULT_ELEMENT"])

    def test_retired_registry_columns_are_ignored(self):
        baseline = self.decode()[base.MODEL]
        rows = annotated_registry()
        for index, row in enumerate(rows):
            for column in RETIRED_COLUMNS:
                row[column] = {"retired": index}
        self.assertEqual(baseline, self.decode(rows)[base.MODEL])

    def test_infers_mapped_owner_and_defaults_uuid_to_omit(self):
        rows = annotated_registry()
        summary = next(row for row in rows if row["NODE_PATH"] == base.SUMMARY)
        summary["OPERATOR"] = None
        summary["UUID_POLICY"] = None
        spec = self.decode(rows)[base.MODEL]["ELEMENTS"][base.SUMMARY]
        self.assertEqual("object", spec["operator"])
        self.assertNotIn("include_uuid", spec["parameters"])

        rows = annotated_registry()
        rows[1]["UUID_POLICY"] = None
        with self.assertRaises(ValueError):
            self.decode(rows)

    def test_compiled_plan_keeps_runtime_interface(self):
        plan = self.compile()["compiled_plan"]
        self.assertEqual(
            {"version", "elements", "mappings", "reference_groups",
             "options", "report", "default_element"},
            set(plan),
        )
        for element in plan["elements"].values():
            self.assertEqual({"operator", "parameters"}, set(element))
            self.assertIn("registry_contract", element["parameters"])

    def test_cell_four_consumes_cell_three_normalized_registry_rows(self):
        context = self.compile()
        config = context["config"]
        self.ns["_prepare_model_context"](
            context,
            config["OSCAL_MODEL"],
            config["SOURCE_SYSTEM_NAME"],
            config["SOURCE_TABLE_NAME"],
        )

        class NormalizedRowView:
            """Expose Cell 3's contract without raw transport iteration."""

            def __init__(self, values):
                self.values = values

            def get(self, key, default=None):
                return self.values.get(key, default)

        class UnavailableTransport:
            def collect(self):
                raise AssertionError("Cell 4 must not reread the registry transport")

        context["registry_rows"] = [
            NormalizedRowView(row) for row in context["registry_rows"]
        ]
        rows = self.ns["_canonical_registry_rows"](
            UnavailableTransport(), base.MODEL, context
        )
        self.assertEqual(
            [base.ROOT_PATH, base.SUMMARY, base.RESULT, base.OBSERVATION],
            [row["element_path"] for row in rows],
        )
        self.assertTrue(
            all(row["raw"] is source
                for row, source in zip(rows, context["registry_rows"]))
        )

    def test_explicit_programmatic_contract_stays_available(self):
        original = base.model_contract()
        decoded = self.decode(models={base.MODEL: original})[base.MODEL]
        self.assertEqual(original, decoded)

    def test_actual_builder_matches_explicit_metadata_output(self):
        mappings = [
            base.mapping(),
            base.mapping("ZERO", path=base.OBSERVATION, transform="scalar-score"),
        ]
        records = [
            {"SOURCE_RECORD_ID": "1", "CURATED_JSON": {
                "NEVER_SEEN_SOURCE_FIELD": "same", "ZERO": 0}},
            {"SOURCE_RECORD_ID": "2", "CURATED_JSON": {
                "NEVER_SEEN_SOURCE_FIELD": "other", "ZERO": 2}},
        ]
        decoded = self.compile(mappings=mappings)
        explicit = base.compile_context(self.ns, mappings)
        self.assertEqual("READY", decoded["routing_report"]["STATUS"])
        actual = base.build(self.ns, decoded, records)
        expected = base.build(self.ns, explicit, records)
        for emitted, baseline in zip(actual, expected):
            self.assertEqual(graph.business(emitted.rows), graph.business(baseline.rows))
        self.assertFalse(decoded["config"]["EXECUTE_WRITES"])

    def test_invalid_structure_fails_closed(self):
        cases = [annotated_registry() + [copy.deepcopy(annotated_registry()[1])]]
        rows = annotated_registry()
        rows[1]["PARENT_NODE_PATH"] = base.RESULT
        cases.append(rows)
        rows = annotated_registry()
        rows[0]["PARENT_NODE_PATH"] = base.SUMMARY
        cases.append(rows)
        rows = annotated_registry()
        rows[2]["IS_COLLECTION"] = False
        cases.append(rows)
        for index, rows in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.decode(rows)

    def test_only_included_collections_require_supported_identity(self):
        rows = annotated_registry()
        rows[2]["INSTANCE_KEY_RULE"] = "VALUE"
        with self.assertRaises(ValueError):
            self.decode(rows)

        future_path = base.SUMMARY + ".future-items[]"
        ignored = annotated_registry() + [{
            "OSCAL_MODEL_KEY": base.MODEL,
            "NODE_PATH": future_path,
            "ELEMENT_TYPE": "future-item",
            "PARENT_NODE_PATH": base.SUMMARY,
            "IS_COLLECTION": True,
            "INSTANCE_KEY_RULE": None,
            "PROCESS_ORDER": 99,
            "IS_ACTIVE": True,
            "ITEM_PATH": None,
            "OPERATOR": None,
            "UUID_POLICY": None,
            "REQUIRED_MEMBERS": None,
        }]
        self.assertNotIn(future_path, self.decode(ignored)[base.MODEL]["ELEMENTS"])

    def test_scalar_rows_ignore_legacy_collection_identity_metadata(self):
        rows = annotated_registry()
        scalar = next(row for row in rows if row["NODE_PATH"] == base.SUMMARY)
        scalar["INSTANCE_KEY_RULE"] = "SINGLETON"
        scalar["ITEM_PATH"] = "$"

        contract = self.decode(rows)[base.MODEL]
        registry_contract = contract["ELEMENTS"][base.SUMMARY]["parameters"][
            "registry_contract"
        ]
        self.assertEqual(
            {"parent_path": base.ROOT_PATH, "is_collection": False},
            registry_contract,
        )

        context = self.compile(rows=rows)
        config = context["config"]
        self.ns["_prepare_model_context"](
            context,
            config["OSCAL_MODEL"],
            config["SOURCE_SYSTEM_NAME"],
            config["SOURCE_TABLE_NAME"],
        )

    def test_object_list_shape_is_narrow(self):
        path = base.SUMMARY + ".identifiers[]"
        row = {
            "OSCAL_MODEL_KEY": base.MODEL,
            "NODE_PATH": path,
            "ELEMENT_TYPE": "identifier",
            "PARENT_NODE_PATH": base.SUMMARY,
            "IS_COLLECTION": True,
            "INSTANCE_KEY_RULE": "VALUE",
            "PROCESS_ORDER": 50,
            "IS_ACTIVE": True,
            "ITEM_PATH": "$",
            "OPERATOR": "object",
            "UUID_POLICY": "omit",
            "REQUIRED_MEMBERS": None,
        }
        contract = self.decode(annotated_registry() + [row])[base.MODEL]
        self.assertTrue(contract["ELEMENTS"][path]["parameters"]["allow_list_instances"])
        for key, value in (("INSTANCE_KEY_RULE", "ID"), ("ITEM_PATH", "items[]")):
            changed = annotated_registry() + [dict(row, **{key: value})]
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.decode(changed)

    def test_sparse_rule_validation_and_complete_only_assembly(self):
        rows = annotated_registry()
        rows[1]["REQUIRED_MEMBERS"] = "first|second|third"
        parameters = self.decode(rows)[base.MODEL]["ELEMENTS"][base.SUMMARY]["parameters"]
        self.assertEqual(["first", "second", "third"], parameters["required_members"])
        self.assertTrue(parameters["optional_assembly"])
        invalid = (
            ("OPERATOR", "unknown"),
            ("UUID_POLICY", "random"),
            ("REQUIRED_MEMBERS", "first||third"),
            ("REQUIRED_MEMBERS", "first|first"),
            ("REQUIRED_MEMBERS", "items[].value"),
        )
        for column, value in invalid:
            rows = annotated_registry()
            rows[1][column] = value
            with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                self.decode(rows)

    def test_report_target_is_derived_from_observations(self):
        models = {base.MODEL: strict_contract(REPORT={"MAPPING_RELEASE": "test"})}
        context = self.compile(models=models)
        self.assertEqual(
            base.OBSERVATION,
            context["compiled_plan"]["report"]["TARGET_PATH"],
        )
        with self.assertRaises(ValueError):
            self.decode(models={base.MODEL: strict_contract(
                REPORT={"TARGET_PATH": base.OBSERVATION})})

    def test_reference_family_derives_namespace_and_stable_identity(self):
        rows = reference_registry()
        group = self.decode(rows)[base.MODEL]["REFERENCE_GROUPS"][0]
        self.assertEqual(
            {"SOURCE_SYSTEM_NAME": "ARCHER",
             "SOURCE_TABLE_NAME": "SYNTHETIC_SOURCE",
             "MODEL_KEY": base.MODEL},
            group["source_namespace"],
        )
        self.assertEqual(
            ["$source_system", "$source_record", "party", "$reference_id"],
            group["party_uuid_parts"],
        )
        config = dict(
            base.profile()["BASE_CONFIG"],
            SOURCE_SYSTEM_NAME="ARCHER",
            SOURCE_TABLE_NAME="SYNTHETIC_SOURCE",
            OSCAL_MODEL=base.MODEL,
        )
        actual = self.ns["_metadata_party_uuid"](
            group, "1", "2", {"config": config})
        self.assertEqual(
            self.ns["_deterministic_uuid"]("ARCHER", "1", "party", "2"),
            actual,
        )
        other = dict(config, SOURCE_TABLE_NAME="OTHER_SOURCE")
        self.assertNotEqual(
            actual,
            self.ns["_metadata_party_uuid"](
                group, "1", "2", {"config": other}),
        )

    def test_reference_family_infers_siblings_and_fails_ambiguous_sources(self):
        rows = reference_registry()
        for operator in ("roles", "parties"):
            row = next(item for item in rows if item["OPERATOR"] == operator)
            row["OPERATOR"] = None
        group = self.decode(rows)[base.MODEL]["REFERENCE_GROUPS"][0]
        self.assertTrue(group["roles_path"].endswith(".roles[]"))
        self.assertTrue(group["parties_path"].endswith(".parties[]"))

        rows = reference_registry()
        party = next(item for item in rows if item["OPERATOR"] == "parties")
        party["UUID_POLICY"] = "omit"
        with self.assertRaises(ValueError):
            self.decode(rows)

        profiles = [base.profile(), base.profile("source-two", "OTHER_SOURCE")]
        mappings = {"source-one": [base.mapping()], "source-two": [base.mapping(source="source-two")]}
        with self.assertRaises(ValueError):
            self.decode(reference_registry(), profiles=profiles, mappings=mappings)


if __name__ == "__main__":
    unittest.main()
