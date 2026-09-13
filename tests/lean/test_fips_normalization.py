"""FIPS label normalization through actual lookup loading and approved CSV rules."""
import copy
from decimal import Decimal
import unittest

from lean_support import namespace
from test_inputs import input_namespace, Session, raw
from test_registry_release import mapping_rows, release_registry


class FipsNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.profile = copy.deepcopy(self.ns["SOURCE_PROFILES"][0])
        self.load = input_namespace()["load_source_lookups"]

    def loaded(self, values):
        config = self.ns["CONFIG"]
        session = Session({config["ARCHER_META_VALUE_TABLE"]: values,
                           **{contract["source_table"]: [raw("fixture", {})]
                              for contract in self.profile["LOOKUP_CONTRACTS"].values()}})
        return self.load(session, self.profile, self.ns["MODEL_CONTRACTS"], config)

    def approved_rows(self):
        contexts = self.ns["compile_mapping_contexts"](
            {"source-one": mapping_rows()}, release_registry(), self.ns["SOURCE_PROFILES"],
            self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])
        ssp = next(context for context in contexts if context["config"]["OSCAL_MODEL"] == "SSP")
        rows = [row for row in ssp["mapping_rows"] if row["TRANSFORM_ID"] == "security-objective"]
        self.assertEqual(11, len(rows))
        return rows

    def test_lookup_canonicalizes_only_fips_labels_and_keeps_id_identity(self):
        result = self.loaded([
            {"SELECT_VALUE_ID": Decimal("100"), "SELECT_VALUE_NAME": " LOW "},
            {"SELECT_VALUE_ID": " 101 ", "SELECT_VALUE_NAME": "mOdErAtE"},
            {"SELECT_VALUE_ID": 102, "SELECT_VALUE_NAME": "High\t"},
            {"SELECT_VALUE_ID": 103, "SELECT_VALUE_NAME": " Other Status "},
            {"SELECT_VALUE_ID": 104, "SELECT_VALUE_NAME": "Legacy LOE A"},
            {"SELECT_VALUE_ID": 105, "SELECT_VALUE_NAME": "FIPS 199 Low"},
            {"SELECT_VALUE_ID": None, "SELECT_VALUE_NAME": "Low"},
            {"SELECT_VALUE_ID": 106, "SELECT_VALUE_NAME": None},
        ])
        self.assertEqual({"100": "low", "101": "moderate", "102": "high"}, result["fips_values"])
        self.assertEqual({"100": "LOW", "101": "mOdErAtE", "102": "High", "103": "Other Status",
                          "104": "Legacy LOE A", "105": "FIPS 199 Low"}, result["archer_values"])

    def test_loaded_ids_and_direct_text_produce_identical_canonical_objectives(self):
        labels = [("31", " Low ", "low"), ("32", "MODERATE", "moderate"), ("33", "hIgH", "high")]
        lookups = self.loaded([{"SELECT_VALUE_ID": key, "SELECT_VALUE_NAME": label} for key, label, _ in labels])
        context = {"lookups": lookups}
        rows = self.approved_rows()
        for key, label, expected in labels:
            for source in (key, int(key), {"ValuesListIds": [int(key)]}, label):
                with self.subTest(source=source):
                    self.assertEqual(expected, self.ns["transform_fips_199"](source, context))
                    for row in rows:
                        self.assertEqual(expected, self.ns["_metadata_transform"](row, source, context))

    def test_all_eight_approved_legacy_labels_remain_unchanged_without_fips_equivalence(self):
        labels = ["Legacy LOE " + letter + suffix for letter in "ABCD" for suffix in ("", " + DFARS")]
        lookups = self.loaded([{"SELECT_VALUE_ID": 200 + index, "SELECT_VALUE_NAME": " " + label + " "}
                               for index, label in enumerate(labels)])
        self.assertEqual({}, lookups["fips_values"])
        context = {"lookups": lookups}
        for row in self.approved_rows():
            self.assertEqual(set(labels), set(row["TRANSFORM_PARAMS"]["approved_legacy_values"]))
            for index, label in enumerate(labels):
                for source in ({"ValuesListIds": [200 + index]}, label):
                    with self.subTest(rule=row["RULE_ID"], source=source):
                        self.assertIsNone(self.ns["transform_fips_199"](source, context))
                        self.assertEqual(label, self.ns["_metadata_transform"](row, source, context))

    def test_lookup_does_not_invent_fips_meaning_for_unknown_ids_or_labels(self):
        context = {"lookups": self.loaded([{"SELECT_VALUE_ID": 1, "SELECT_VALUE_NAME": "Not rated"}])}
        row = self.approved_rows()[0]
        for source in (1, 999, "Not rated", "FIPS 199 Low", "Legacy LOE E"):
            with self.subTest(source=source):
                self.assertIsNone(self.ns["transform_fips_199"](source, context))
                with self.assertRaisesRegex(ValueError, "unreviewed label"):
                    self.ns["_metadata_transform"](row, source, context)


if __name__ == "__main__":
    unittest.main()
