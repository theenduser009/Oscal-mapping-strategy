"""Pure, versioned live-registry structural metadata decoding; no database access."""
import copy
from decimal import Decimal
import unittest

import test_metadata_driven_contract as base
import test_multi_model_graph as graph


def strict_contract():
    return {"MODEL_KEY": base.MODEL, "POLICY": "metadata-v1",
            "REGISTRY_METADATA_VERSION": 1, "STORAGE_CONTRACT": None}


def annotated_registry():
    result = []
    specs = {
        base.ROOT_PATH: ("object", "node", "emit", None, None),
        base.SUMMARY: ("object", "omit", "omit", None, None),
        base.RESULT: ("record", "node", "omit", "singleton", None),
        base.OBSERVATION: ("observations", "node", "omit", "source-record", "source-field-slug"),
    }
    for original in base.registry_rows():
        row = dict(original)
        operator, uuid, empty, parent, naming = specs[row["NODE_PATH"]]
        row.update(MAPPER_METADATA_VERSION=None, MAPPER_ENABLED=True,
                   OPERATOR=operator, UUID_POLICY=uuid, EMPTY_POLICY=empty,
                   LIST_INSTANCE_RULE="none", ASSEMBLY_POLICY="normal",
                   PARENT_INSTANCE_RULE=parent, PROPERTY_NAME_RULE=naming,
                   REQUIRED_MEMBERS=None, DEFAULT_SINGLETON_POLICY=None,
                   REQUIRED_RULE_IDS=None, REPORT_TARGET_PATH=None,
                   ROLES_PATH=None, PARTIES_PATH=None, PARTY_TYPE=None,
                   PARTY_UUID_PARTS=None, PARTY_UUID_SOURCE_KEY=None)
        if row["NODE_PATH"] == base.ROOT_PATH:
            row.update(MAPPER_METADATA_VERSION=Decimal("1"),
                       DEFAULT_SINGLETON_POLICY="none")
        result.append(row)
    return result


def reference_registry():
    rows = annotated_registry()
    roles, parties, assignments = [base.SUMMARY + "." + item + "[]"
                                   for item in ("roles", "parties", "assignments")]
    for row in rows:
        if row["NODE_PATH"] == base.SUMMARY:
            row["EMPTY_POLICY"] = "emit"
    for path, operator, identity, item, uuid in (
        (roles, "roles", "SOURCE_FIELD_NAME", "$", "omit"),
        (parties, "parties", "ID", "UserList[]", "instance"),
        (assignments, "assignments", "SOURCE_FIELD_NAME+ID", "UserList[]", "omit"),
    ):
        row = dict(rows[1], NODE_PATH=path, ELEMENT_TYPE=operator,
                   PARENT_NODE_PATH=base.SUMMARY, IS_COLLECTION=True,
                   OPERATOR=operator, INSTANCE_KEY_RULE=identity, ITEM_PATH=item,
                   UUID_POLICY=uuid, EMPTY_POLICY="omit")
        if operator == "assignments":
            row.update(ROLES_PATH=roles, PARTIES_PATH=parties, PARTY_TYPE="person",
                       PARTY_UUID_PARTS="$source_system|$source_record|party|$reference_id",
                       PARTY_UUID_SOURCE_KEY="source-one")
        rows.append(row)
    return rows


class RegistryMetadataContractTests(unittest.TestCase):
    def setUp(self):
        self.ns = base.namespace()

    def decode(self, rows=None, profiles=None, models=None):
        inputs = (annotated_registry() if rows is None else rows,
                  [base.profile()] if profiles is None else profiles,
                  {base.MODEL: strict_contract()} if models is None else models)
        before = copy.deepcopy(inputs)
        result = self.ns["decode_registry_model_contracts"](*inputs)
        self.assertEqual(before, inputs)
        return result

    def compile(self, rows=None, mappings=None, models=None):
        source = base.profile()
        inputs = ({"source-one": [base.mapping()] if mappings is None else mappings},
                  annotated_registry() if rows is None else rows,
                  [source], {base.MODEL: strict_contract()} if models is None else models)
        before = copy.deepcopy(inputs)
        contexts = self.ns["compile_mapping_contexts"](*inputs)
        self.assertEqual(before, inputs)
        return contexts[0]

    def test_decodes_structure_from_existing_registry_rows_only(self):
        contract = self.decode()[base.MODEL]
        self.assertEqual(base.ROOT_PATH, contract["ROOT_PATH"])
        self.assertEqual(set(row["NODE_PATH"] for row in annotated_registry()),
                         set(contract["ELEMENTS"]))
        self.assertEqual("source-record",
                         contract["ELEMENTS"][base.OBSERVATION]["parameters"]["parent_instance_rule"])
        self.assertEqual("SOURCE_FIELD_NAME",
                         contract["ELEMENTS"][base.OBSERVATION]["parameters"]["registry_contract"]["instance_key_rule"])
        self.assertEqual([], contract["REFERENCE_GROUPS"])
        self.assertEqual(None, contract["DEFAULT_ELEMENT"])
        self.assertFalse(any("controlled_fields" in spec["parameters"]
                             for spec in contract["ELEMENTS"].values()))

    def test_actual_shared_builder_matches_explicit_metadata_output(self):
        mappings = [base.mapping(), base.mapping("ZERO", path=base.OBSERVATION,
                                                transform="scalar-score")]
        records = [{"SOURCE_RECORD_ID": "1", "CURATED_JSON": {
                    "NEVER_SEEN_SOURCE_FIELD": "same", "ZERO": 0}},
                   {"SOURCE_RECORD_ID": "2", "CURATED_JSON": {
                    "NEVER_SEEN_SOURCE_FIELD": "other", "ZERO": 2}}]
        decoded = self.compile(mappings=mappings)
        explicit = base.compile_context(self.ns, mappings)
        self.assertEqual("READY", decoded["routing_report"]["STATUS"])
        actual = base.build(self.ns, decoded, records)
        expected = base.build(self.ns, explicit, records)
        for emitted, baseline in zip(actual, expected):
            self.assertEqual(graph.business(emitted.rows), graph.business(baseline.rows))
        self.assertFalse(decoded["config"]["EXECUTE_WRITES"])

    def test_explicit_programmatic_metadata_api_stays_available(self):
        original = base.model_contract()
        self.assertEqual(original, self.decode(models={base.MODEL: original})[base.MODEL])
        self.assertEqual("READY", base.compile_context(self.ns, [base.mapping()])["routing_report"]["STATUS"])

    def test_unselected_model_metadata_does_not_block_selected_model(self):
        other = {"MODEL_KEY": "UNSELECTED", "POLICY": "metadata-v1",
                 "REGISTRY_METADATA_VERSION": "unsupported"}
        rows = annotated_registry() + [{
            "OSCAL_MODEL_KEY": "UNSELECTED", "NODE_PATH": "unselected-document",
            "PARENT_NODE_PATH": None, "IS_COLLECTION": False, "IS_ACTIVE": True,
            "MAPPER_METADATA_VERSION": 99, "MAPPER_ENABLED": "invalid",
        }]
        models = {base.MODEL: strict_contract(), "UNSELECTED": other}
        self.assertEqual(other, self.decode(rows, models=models)["UNSELECTED"])
        self.assertEqual("READY", self.compile(rows=rows, models=models)["routing_report"]["STATUS"])

    def test_missing_version_or_enabled_metadata_fails_without_fallback(self):
        for key in ("MAPPER_METADATA_VERSION", "MAPPER_ENABLED", "OPERATOR",
                    "UUID_POLICY", "EMPTY_POLICY", "LIST_INSTANCE_RULE",
                    "ASSEMBLY_POLICY", "DEFAULT_SINGLETON_POLICY"):
            rows = annotated_registry()
            rows[0][key] = None
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.decode(rows)
        with self.assertRaises(ValueError):
            self.decode([])

    def test_version_accepts_integral_snowflake_decimal_and_rejects_unknown_types(self):
        for value in (1, "1", Decimal("1"), Decimal("1.00")):
            rows = annotated_registry()
            rows[0]["MAPPER_METADATA_VERSION"] = value
            models = {base.MODEL: dict(strict_contract(), REGISTRY_METADATA_VERSION=value)}
            self.assertEqual(base.ROOT_PATH, self.decode(rows, models=models)[base.MODEL]["ROOT_PATH"])
        for value in (True, False, 1.0, 2, "v1", "1.0", Decimal("NaN"), Decimal("1.1")):
            rows = annotated_registry()
            rows[0]["MAPPER_METADATA_VERSION"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.decode(rows)

    def test_strict_models_reject_duplicated_structure_in_configuration(self):
        for key, value in (("ELEMENTS", {}), ("ROOT_PATH", base.ROOT_PATH),
                           ("REFERENCE_GROUPS", []), ("DEFAULT_ELEMENT", None),
                           ("REQUIRED_RULE_IDS", []), ("ELEMENT_PATHS", []),
                           ("MAPPING_RULES", []), ("PATH_RULES", []),
                           ("EXCLUDED_FIELDS", []), ("REPORT", {"TARGET_PATH": base.RESULT})):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.decode(models={base.MODEL: dict(strict_contract(), **{key: value})})

    def test_metadata_whitelist_excludes_disabled_paths_and_preserves_root(self):
        rows = annotated_registry()
        rows[1]["MAPPER_ENABLED"] = False
        contract = self.decode(rows)[base.MODEL]
        self.assertNotIn(base.SUMMARY, contract["ELEMENT_PATHS"])
        for index in (0, 2):
            rows = annotated_registry()
            rows[index]["MAPPER_ENABLED"] = False
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.decode(rows)

    def test_report_metadata_is_validated_before_registry_target_merge(self):
        self.assertEqual({}, self.decode(models={base.MODEL: dict(strict_contract(), REPORT=None)})
                         [base.MODEL]["REPORT"])
        for value in (42, ["not-an-object"], "{invalid"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.decode(models={base.MODEL: dict(strict_contract(), REPORT=value)})

    def test_duplicate_marker_path_or_cross_parent_is_rejected(self):
        cases = []
        rows = annotated_registry()
        rows[1]["MAPPER_METADATA_VERSION"] = 1
        cases.append(rows)
        cases.append(annotated_registry() + [annotated_registry()[1]])
        rows = annotated_registry()
        rows[1]["PARENT_NODE_PATH"] = base.RESULT
        cases.append(rows)
        rows = annotated_registry()
        rows[0]["PARENT_NODE_PATH"] = base.SUMMARY
        cases.append(rows)
        for rows in cases:
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                self.decode(rows)

    def test_invalid_or_inapplicable_policy_never_silently_changes_behavior(self):
        changes = [
            (0, "MAPPER_ENABLED", 1), (1, "OPERATOR", "unreviewed"),
            (1, "UUID_POLICY", "random"), (1, "UUID_POLICY", "instance"),
            (1, "EMPTY_POLICY", "unknown"), (1, "LIST_INSTANCE_RULE", "source-field-index"),
            (1, "ASSEMBLY_POLICY", "complete-only"), (1, "PROPERTY_NAME_RULE", "source-field-slug"),
            (2, "INSTANCE_KEY_RULE", "VALUE"), (2, "ITEM_PATH", "$"),
            (3, "PARENT_INSTANCE_RULE", None), (3, "PROPERTY_NAME_RULE", None),
            (3, "IS_COLLECTION", False), (3, "EMPTY_POLICY", "emit"),
            (1, "DEFAULT_SINGLETON_POLICY", "none"), (1, "REQUIRED_RULE_IDS", "required"),
        ]
        for index, key, value in changes:
            rows = annotated_registry()
            rows[index][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.decode(rows)

    def test_complete_only_assembly_and_default_singletons_are_explicit(self):
        rows = annotated_registry()
        rows[0]["DEFAULT_SINGLETON_POLICY"] = "emit-outside-collections"
        rows[1].update(ASSEMBLY_POLICY="complete-only", REQUIRED_MEMBERS="first|second|third")
        contract = self.decode(rows)[base.MODEL]
        parameters = contract["ELEMENTS"][base.SUMMARY]["parameters"]
        self.assertEqual(["first", "second", "third"], parameters["required_members"])
        self.assertTrue(parameters["optional_assembly"])
        self.assertEqual("singletons-without-collection-ancestors", contract["DEFAULT_ELEMENT"]["scope"])
        for members in ("first||third", "first|first", "items[].value", "nested..value"):
            rows[1]["REQUIRED_MEMBERS"] = members
            with self.subTest(members=members), self.assertRaises(ValueError):
                self.decode(rows)

    def test_root_required_rules_and_report_target_reach_compiled_plan(self):
        rows = annotated_registry()
        rows[0].update(REQUIRED_RULE_IDS="required-one", REPORT_TARGET_PATH=base.OBSERVATION)
        context = self.compile(rows, [base.mapping(RULE_ID="required-one")])
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        self.assertEqual(base.OBSERVATION, context["compiled_plan"]["report"]["TARGET_PATH"])
        self.assertEqual(["required-one"], context["model_contract"]["REQUIRED_RULE_IDS"])
        missing = self.compile(rows, [])
        self.assertEqual("BLOCKED", missing["routing_report"]["STATUS"])
        rows[0]["REPORT_TARGET_PATH"] = "unregistered"
        with self.assertRaises(ValueError):
            self.decode(rows)

    def test_reference_family_derives_exact_source_namespace_and_stable_uuid(self):
        rows = reference_registry()
        group = self.decode(rows)[base.MODEL]["REFERENCE_GROUPS"][0]
        self.assertEqual({"SOURCE_SYSTEM_NAME": "ARCHER", "SOURCE_TABLE_NAME": "SYNTHETIC_SOURCE",
                          "MODEL_KEY": base.MODEL}, group["source_namespace"])
        self.assertEqual(["$source_system", "$source_record", "party", "$reference_id"],
                         group["party_uuid_parts"])
        config = dict(base.profile()["BASE_CONFIG"], SOURCE_SYSTEM_NAME="ARCHER",
                      SOURCE_TABLE_NAME="SYNTHETIC_SOURCE", OSCAL_MODEL=base.MODEL)
        actual = self.ns["_metadata_party_uuid"](group, "1", "2", {"config": config})
        self.assertEqual(self.ns["_deterministic_uuid"]("ARCHER", "1", "party", "2"), actual)
        other = dict(config, SOURCE_TABLE_NAME="OTHER_SOURCE")
        separated = self.ns["_metadata_party_uuid"](group, "1", "2", {"config": other})
        self.assertNotEqual(actual, separated)

    def test_invalid_reference_links_or_unscoped_short_identity_are_rejected(self):
        changes = [
            ("ROLES_PATH", "missing"), ("PARTIES_PATH", base.SUMMARY + ".roles[]"),
            ("PARTY_TYPE", None), ("PARTY_UUID_SOURCE_KEY", "unconfigured"),
            ("PARTY_UUID_SOURCE_KEY", None), ("PARTY_UUID_PARTS", "$secret|$reference_id"),
            ("PARTY_UUID_PARTS", "$source_record|party"),
        ]
        for key, value in changes:
            rows = reference_registry()
            rows[-1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.decode(rows)
        rows = reference_registry()
        rows[-1].update(PARTY_UUID_SOURCE_KEY=None,
                       PARTY_UUID_PARTS="$identity_version|$source_system|$source_table|$source_record|$model|party|$reference_id")
        self.assertNotIn("source_namespace", self.decode(rows)[base.MODEL]["REFERENCE_GROUPS"][0])


if __name__ == "__main__":
    unittest.main()
