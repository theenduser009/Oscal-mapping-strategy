"""Focused value-source/required semantics for the registry-driven release."""
import unittest

import test_flat_mapping_columns as flat
import test_metadata_driven_contract as base
import test_registry_metadata_contract as registry
import test_registry_release as release


class RegistryValueSourceTests(unittest.TestCase):
    def setUp(self):
        self.ns = base.namespace()

    def compile(self, **changes):
        options = {"TRANSFORM_ID": "direct"}
        options.update(changes)
        row = flat.mapping(path=base.SUMMARY + ".value", **options)
        context = self.ns["compile_mapping_contexts"](
            {"source-one": [row]}, registry.annotated_registry(), [base.profile()],
            {base.MODEL: registry.strict_contract()})[0]
        self.assertFalse(context["config"]["EXECUTE_WRITES"])
        return context

    def build(self, context, source_value):
        return base.build(self.ns, context, [{"SOURCE_RECORD_ID": "1",
                           "CURATED_JSON": {"FLAT_SOURCE": source_value}}])

    def test_value_required_accepts_only_boolean_or_boolean_text(self):
        for flag, expected in ((True, True), (False, False), ("true", True),
                               ("false", False), ("TRUE", True), (" FALSE ", False)):
            with self.subTest(flag=flag):
                context = self.compile(VALUE_REQUIRED=flag)
                self.assertEqual("READY", context["routing_report"]["STATUS"])
                self.assertIs(expected, context["mapping_rows"][0]["REPRESENTATION_PARAMS"]["required"])
        for flag in (0, 1, 1.0, "yes", {}, []):
            with self.subTest(flag=flag):
                self.assertEqual("BLOCKED", self.compile(VALUE_REQUIRED=flag)["routing_report"]["STATUS"])

    def test_invalid_value_source_or_config_without_member_is_blocked(self):
        for kind in ("config", "SQL", True, {}, []):
            with self.subTest(kind=kind):
                self.assertEqual("BLOCKED", self.compile(VALUE_SOURCE=kind)["routing_report"]["STATUS"])
        context = self.compile(VALUE_SOURCE="CONFIG", RUNTIME_TARGET_PATH=base.SUMMARY)
        self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])

    def test_compiled_field_and_config_values_never_fall_back_to_each_other(self):
        for kind, expected in (("FIELD", "source value"), ("CONFIG", "config value")):
            with self.subTest(kind=kind):
                context = self.compile(VALUE_SOURCE=kind, VALUE_REQUIRED=True)
                context["config"]["FLAT_SOURCE"] = "config value"
                nodes, _ = self.build(context, "source value")
                self.assertEqual([{"value": expected}], base.payloads(nodes, base.SUMMARY))
        context = self.compile(VALUE_SOURCE="CONFIG", VALUE_REQUIRED=True)
        with self.assertRaises(ValueError):
            self.build(context, "source cannot fill a missing configuration value")
        self.assertFalse(context["graph_report"]["OUTPUTS_PUBLISHED"])

    def test_required_empty_conversion_cannot_publish_a_partial_graph(self):
        for converted in (None, "", [], {}):
            with self.subTest(converted=converted):
                context = self.compile(TRANSFORM_ID="archer-select", VALUE_REQUIRED=True)
                context["lookups"] = {"archer_values": {"777": converted}}
                with self.assertRaises(ValueError):
                    self.build(context, "777")
                report = context["graph_report"]
                self.assertFalse(report["OUTPUTS_PUBLISHED"])
                self.assertEqual(1, report["FIELDS"]["FLAT_SOURCE"]["invalid"])

    def test_optional_empty_conversion_remains_missing_without_inventing_values(self):
        context = self.compile(TRANSFORM_ID="archer-select", VALUE_REQUIRED=False)
        context["lookups"] = {"archer_values": {"777": None}}
        nodes, _ = self.build(context, "777")
        self.assertTrue(context["graph_report"]["OUTPUTS_PUBLISHED"])
        self.assertEqual([{}], base.payloads(nodes, base.SUMMARY))
        self.assertEqual({"emitted": 0, "missing": 1, "invalid": 0},
                         context["graph_report"]["FIELDS"]["FLAT_SOURCE"])

    def test_required_zero_and_false_are_preserved_not_treated_as_missing(self):
        for value in (0, False):
            with self.subTest(value=value):
                context = self.compile(VALUE_REQUIRED=True)
                nodes, _ = self.build(context, value)
                actual = base.payloads(nodes, base.SUMMARY)[0]["value"]
                self.assertEqual(value, actual)
                self.assertIs(type(value), type(actual))
                self.assertEqual(1, context["graph_report"]["FIELDS"]["FLAT_SOURCE"]["emitted"])

    def test_current_release_ignores_unselected_model_extension_values(self):
        for selected, other in (("SSP", "ASSESSMENT_RESULTS"), ("ASSESSMENT_RESULTS", "SSP")):
            with self.subTest(selected=selected):
                rows = release.release_registry()
                for row in rows:
                    if row["OSCAL_MODEL_KEY"] == other:
                        row.update(MAPPER_METADATA_VERSION=99, MAPPER_ENABLED="invalid",
                                   OPERATOR="unapproved")
                harness = release.RegistryReleaseTests()
                harness.setUp()
                context = harness.compile(models=(selected,), registry=rows)[0]
                self.assertEqual("READY", context["routing_report"]["STATUS"])
                self.assertEqual(selected, context["config"]["OSCAL_MODEL"])
                self.assertFalse(context["config"]["EXECUTE_WRITES"])


if __name__ == "__main__":
    unittest.main()

