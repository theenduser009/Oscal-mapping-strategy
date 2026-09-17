"""Optional explicit property-name support without changing legacy defaults."""
import unittest

import lean_support
import test_metadata_driven_contract as base


def active_namespace():
    # Load the maintained seven-cell sources so this test exercises
    # both the Cell 3 compiler and Cell 4 property emitter together.
    return lean_support.namespace(models=("SSP",))


class PropertyNameOverrideTests(unittest.TestCase):
    def test_optional_override_compiles_and_emits_exact_name(self):
        ns = active_namespace()
        row = base.mapping(
            "NEW_SCORE", base.OBSERVATION, "scalar-score",
            PROPERTY_NAME="approved-score-label",
        )
        context = base.compile_context(ns, [row])
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        self.assertEqual(
            "approved-score-label",
            context["mapping_rows"][0]["REPRESENTATION_PARAMS"]["property_name"],
        )
        nodes, _ = base.build(ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"NEW_SCORE": 7},
        }])
        self.assertEqual(
            [{"name": "approved-score-label", "value": "7"}],
            base.payloads(nodes, base.OBSERVATION)[0]["props"],
        )

    def test_blank_override_keeps_existing_source_field_slug(self):
        ns = active_namespace()
        row = base.mapping(
            "NEW_SCORE", base.OBSERVATION, "scalar-score", PROPERTY_NAME="",
        )
        context = base.compile_context(ns, [row])
        nodes, _ = base.build(ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"NEW_SCORE": 3},
        }])
        self.assertEqual(
            [{"name": "new-score", "value": "3"}],
            base.payloads(nodes, base.OBSERVATION)[0]["props"],
        )

    def test_override_is_rejected_for_non_property_operator(self):
        ns = active_namespace()
        context = base.compile_context(ns, [base.mapping(PROPERTY_NAME="not-allowed")])
        self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])
        self.assertEqual([], context["mapping_rows"])

    def test_override_with_whitespace_is_rejected(self):
        ns = active_namespace()
        row = base.mapping(
            "NEW_SCORE", base.OBSERVATION, "scalar-score", PROPERTY_NAME="bad name",
        )
        context = base.compile_context(ns, [row])
        self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])
        self.assertEqual([], context["mapping_rows"])


if __name__ == "__main__":
    unittest.main()
