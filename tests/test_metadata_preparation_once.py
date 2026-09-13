"""One metadata preparation boundary, including linked registry families."""
from collections import Counter
import copy
import unittest
from unittest.mock import patch

import test_metadata_driven_contract as base
import test_registry_metadata_contract as registry


class TransportRow:
    """A metadata transport row whose source representation is read once."""

    def __init__(self, values):
        self.values = {" " + key.lower() + " ": value for key, value in values.items()}
        self.reads = 0

    def as_dict(self, recursive=True):
        self.reads += 1
        if self.reads != 1:
            raise AssertionError("Raw metadata transport was read more than once")
        return dict(self.values)


class MetadataPreparationOnceTests(unittest.TestCase):
    def setUp(self):
        self.ns = base.namespace()

    def test_multi_source_compilation_normalizes_each_raw_row_once(self):
        profiles = [base.profile(), base.profile("source-two", "SECOND_SOURCE")]
        rows = [TransportRow(row) for row in registry.annotated_registry()]
        mappings = {
            profile["SOURCE_KEY"]: [TransportRow(base.mapping(
                source=profile["SOURCE_KEY"], OSCAL_MODEL="Unfamiliar display label"))]
            for profile in profiles
        }
        raw = rows + [row for source in mappings.values() for row in source]
        calls = Counter()
        normalize = self.ns["_meta_row"]

        def counted(row):
            calls[id(row)] += 1
            return normalize(row)

        with patch.dict(self.ns, {"_meta_row": counted}):
            contexts = self.ns["compile_mapping_contexts"](
                mappings, rows, profiles, {base.MODEL: registry.strict_contract()})

        self.assertEqual(Counter({id(row): 1 for row in raw}), calls)
        self.assertTrue(all(row.reads == 1 for row in raw))
        self.assertEqual(2, len(contexts))
        for context in contexts:
            self.assertEqual("READY", context["routing_report"]["STATUS"])
            self.assertEqual(base.SUMMARY, context["mapping_rows"][0]["OWNER_ELEMENT_PATH"])
            self.assertEqual("Unfamiliar display label", context["mapping_rows"][0]["ARTIFACT_MODEL"])

    def test_standalone_decoder_accepts_raw_transport_rows(self):
        rows = [TransportRow(row) for row in registry.annotated_registry()]
        mapping = TransportRow(base.mapping())
        models = {base.MODEL: registry.strict_contract()}
        original = copy.deepcopy(models)
        actual = self.ns["decode_registry_model_contracts"](
            rows, [base.profile()], models, {"source-one": [mapping]})
        expected = self.ns["decode_registry_model_contracts"](
            registry.annotated_registry(), [base.profile()], models,
            {"source-one": [base.mapping()]})
        self.assertEqual(expected, actual)
        self.assertEqual(original, models)
        self.assertTrue(all(row.reads == 1 for row in rows + [mapping]))

    def test_model_settings_cannot_supply_a_default_element(self):
        model = base.model_contract()
        model["DEFAULT_ELEMENT"] = {"operator": "object", "parameters": {"materialize_empty": True}}
        before = copy.deepcopy(model)
        with self.assertRaises(ValueError):
            self.ns["compile_mapping_contexts"](
                {"source-one": [base.mapping()]}, base.registry_rows(), [base.profile()],
                {base.MODEL: model})
        self.assertEqual(before, model)

    def test_mapping_activates_inferred_assignment_family_once(self):
        rows = registry.reference_registry()
        for row in rows:
            if row["OPERATOR"] in {"roles", "parties", "assignments"}:
                row["OPERATOR"] = None
        assignment_path = base.SUMMARY + ".assignments[]"
        mapping = base.mapping("REVIEWER", assignment_path, transform="direct",
                               ROLE_ID="reviewer", ROLE_TITLE="Reviewer")
        context = self.ns["compile_mapping_contexts"](
            {"source-one": [mapping]}, rows, [base.profile()],
            {base.MODEL: registry.strict_contract()})[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        self.assertEqual([assignment_path], [
            group["assignments_path"] for group in context["compiled_plan"]["reference_groups"]])
        for operator in ("roles", "parties", "assignments"):
            path = base.SUMMARY + "." + operator + "[]"
            self.assertEqual(operator, context["compiled_plan"]["elements"][path]["operator"])

    def decode_family(self, rows, profiles=None):
        profiles = profiles or [base.profile()]
        mappings = {profile["SOURCE_KEY"]: [base.mapping(source=profile["SOURCE_KEY"])]
                    for profile in profiles}
        return self.ns["decode_registry_model_contracts"](
            rows, profiles, {base.MODEL: registry.strict_contract()}, mappings)[base.MODEL]

    def test_inferred_family_preserves_exact_reference_paths_and_identity(self):
        rows = registry.reference_registry()
        for row in rows:
            if row["OPERATOR"] in {"roles", "parties"}:
                row["OPERATOR"] = None
        before = copy.deepcopy(rows)
        decoded = self.decode_family(rows)
        self.assertEqual([{
            "roles_path": base.SUMMARY + ".roles[]",
            "parties_path": base.SUMMARY + ".parties[]",
            "assignments_path": base.SUMMARY + ".assignments[]",
            "party_type": "person",
            "source_namespace": {
                "SOURCE_SYSTEM_NAME": "ARCHER",
                "SOURCE_TABLE_NAME": "SYNTHETIC_SOURCE",
                "MODEL_KEY": base.MODEL,
            },
        }], decoded["REFERENCE_GROUPS"])
        self.assertEqual(before, rows)
        self.assertEqual("roles", decoded["ELEMENTS"][base.SUMMARY + ".roles[]"]["operator"])
        self.assertEqual("parties", decoded["ELEMENTS"][base.SUMMARY + ".parties[]"]["operator"])

    def test_ambiguous_sibling_and_reused_family_paths_are_rejected(self):
        for operator, message in (
            ("roles", "one role and one party"),
            ("parties", "one role and one party"),
            ("assignments", "paths must be distinct"),
        ):
            rows = registry.reference_registry()
            extra = copy.deepcopy(next(row for row in rows if row["OPERATOR"] == operator))
            extra["NODE_PATH"] = base.SUMMARY + ".extra-" + operator + "[]"
            rows.append(extra)
            with self.subTest(operator=operator), self.assertRaisesRegex(ValueError, message):
                self.decode_family(rows)

    def test_family_cannot_cross_source_namespaces(self):
        with self.assertRaisesRegex(ValueError, "one source namespace"):
            self.decode_family(registry.reference_registry(), [
                base.profile(), base.profile("source-two", "SECOND_SOURCE")])

    def test_inactive_sibling_cannot_complete_family(self):
        rows = registry.reference_registry()
        next(row for row in rows if row["OPERATOR"] == "parties")["IS_ACTIVE"] = False
        with self.assertRaisesRegex(ValueError, "one role and one party"):
            self.decode_family(rows)

    def test_duplicate_normalized_headers_and_active_registry_paths_still_reject(self):
        mappings = {"source-one": [base.mapping()]}
        bad = dict(mappings["source-one"][0], ARCHER_FIELD_NAME="OTHER_FIELD")
        with self.assertRaisesRegex(ValueError, "Ambiguous metadata column aliases"):
            self.ns["compile_mapping_contexts"](
                {"source-one": [bad]}, registry.annotated_registry(), [base.profile()],
                {base.MODEL: registry.strict_contract()})
        rows = registry.annotated_registry()
        rows.append(copy.deepcopy(rows[1]))
        with self.assertRaisesRegex(ValueError, "unique active registry paths"):
            self.ns["compile_mapping_contexts"](
                mappings, rows, [base.profile()], {base.MODEL: registry.strict_contract()})


if __name__ == "__main__":
    unittest.main()
