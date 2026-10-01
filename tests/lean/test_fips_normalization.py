"""FIPS normalization from Matillion-resolved Archer select values."""
import copy
import unittest

from lean_support import namespace
from test_registry_release import mapping_rows, release_registry


class FipsNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.context = {"lookups": {"archer_values": {}, "fips_values": {}}}

    def approved_rows(self):
        profile = copy.deepcopy(next(
            item for item in self.ns["SOURCE_PROFILES"] if item["SOURCE_KEY"] == "source-one"
        ))
        profile["MODEL_KEYS"] = ("SSP",)
        contexts = self.ns["compile_mapping_contexts"](
            {"source-one": mapping_rows()}, release_registry(), [profile],
            self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])
        ssp = contexts[0]
        rows = [row for row in ssp["mapping_rows"] if row["TRANSFORM_ID"] == "security-objective"]
        self.assertEqual(11, len(rows))
        return rows

    @staticmethod
    def enriched(value_id, label, status="MATCHED"):
        return {
            "ValuesListIds": [value_id],
            "ResolvedValues": [{
                "ValueId": str(value_id),
                "ValueName": label,
                "LookupStatus": status,
            }],
        }

    def test_runtime_no_longer_requires_archer_meta_value_table(self):
        self.assertNotIn("ARCHER_META_VALUE_TABLE", self.ns["CONFIG"])

    def test_matillion_resolved_labels_canonicalize_fips(self):
        rows = self.approved_rows()
        for value_id, label, expected in (
            (80654, "Low", "low"),
            (80655, "MODERATE", "moderate"),
            (80656, "hIgH", "high"),
        ):
            source = self.enriched(value_id, label)
            with self.subTest(source=source):
                self.assertEqual([label], self.ns["resolve_archer_select_value"](source, self.context))
                self.assertEqual(expected, self.ns["transform_fips_199"](source, self.context))
                for row in rows:
                    self.assertEqual(expected, self.ns["_metadata_transform"](row, source, self.context))

    def test_all_eight_approved_legacy_labels_remain_unchanged(self):
        labels = ["Legacy LOE " + letter + suffix for letter in "ABCD" for suffix in ("", " + DFARS")]
        for row in self.approved_rows():
            self.assertEqual(set(labels), set(self.ns["_metadata_params"](row)["approved_legacy_values"]))
            for index, label in enumerate(labels):
                source = self.enriched(162400 + index, label)
                with self.subTest(rule=row["RULE_ID"], source=source):
                    self.assertIsNone(self.ns["transform_fips_199"](source, self.context))
                    self.assertEqual(label, self.ns["_metadata_transform"](row, source, self.context))

    def test_resolved_values_fail_closed_on_status_identity_or_cardinality_errors(self):
        bad = [
            self.enriched(80654, "Low", "VALUE_NOT_FOUND"),
            {
                "ValuesListIds": [80654],
                "ResolvedValues": [{
                    "ValueId": "99999",
                    "ValueName": "Low",
                    "LookupStatus": "MATCHED",
                }],
            },
            {
                "ValuesListIds": [80654, 80655],
                "ResolvedValues": [{
                    "ValueId": "80654",
                    "ValueName": "Low",
                    "LookupStatus": "MATCHED",
                }],
            },
            {
                "ValuesListIds": [80654],
                "ResolvedValues": [],
            },
        ]
        for source in bad:
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.ns["resolve_archer_select_value"](source, self.context)

    def test_direct_text_remains_supported_for_non_container_inputs(self):
        for label, expected in (("Low", "low"), ("Moderate", "moderate"), ("High", "high")):
            with self.subTest(label=label):
                self.assertEqual(expected, self.ns["transform_fips_199"](label, self.context))


if __name__ == "__main__":
    unittest.main()
