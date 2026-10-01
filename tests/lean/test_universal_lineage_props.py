"""Selective source-field lineage controlled by LINEAGE_REQUIRED metadata."""
import json
import unittest

import lean_support
import test_metadata_driven_contract as base
from test_registry_release import mapping_rows


PROPS = base.SUMMARY + ".props[]"
NS = "urn:company:oscal:lineage:v1"


def registry_with_props():
    rows = base.registry_rows()
    rows.append({
        "OSCAL_MODEL_KEY": base.MODEL,
        "NODE_PATH": PROPS,
        "PARENT_NODE_PATH": base.SUMMARY,
        "ELEMENT_TYPE": "props",
        "IS_COLLECTION": True,
        "IS_ACTIVE": True,
        "INSTANCE_KEY_RULE": "SOURCE_FIELD_NAME+VALUE",
        "ITEM_PATH": "$",
        "PROCESS_ORDER": 5,
        "OPERATOR": "properties",
        "UUID_POLICY": "node",
        "REQUIRED_MEMBERS": None,
    })
    return rows


def compiled(row):
    ns = lean_support.namespace(models=("SSP",))
    context = base.compile_context(ns, [row], registry=registry_with_props())
    context["config"]["LINEAGE_PROPERTY_NS"] = NS
    return ns, context


class SelectiveLineagePropertyTests(unittest.TestCase):
    def test_lineage_required_y_emits_one_source_field_prop(self):
        row = base.mapping(
            "SOURCE_TITLE", base.SUMMARY + ".title", "text", LINEAGE_REQUIRED="Y",
        )
        ns, context = compiled(row)
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        self.assertEqual(
            {
                row["RULE_ID"]: {
                    "source_field": "SOURCE_TITLE",
                    "targets": ("title",),
                }
            },
            context["compiled_plan"]["lineage_rules"],
        )
        nodes, _ = base.build(ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"SOURCE_TITLE": "Mapped title"},
        }])
        self.assertEqual([{"title": "Mapped title"}], base.payloads(nodes, base.SUMMARY))
        lineage = base.payloads(nodes, PROPS)
        self.assertEqual(1, len(lineage))
        self.assertEqual({
            "name": "source-field",
            "ns": NS,
            "class": "title",
            "value": "SOURCE_TITLE",
        }, {key: value for key, value in lineage[0].items() if key != "uuid"})

    def test_lineage_required_n_emits_no_extra_prop(self):
        row = base.mapping(
            "SOURCE_TITLE", base.SUMMARY + ".title", "text", LINEAGE_REQUIRED="N",
        )
        ns, context = compiled(row)
        self.assertEqual({}, context["compiled_plan"]["lineage_rules"])
        nodes, _ = base.build(ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"SOURCE_TITLE": "Mapped title"},
        }])
        self.assertEqual([], base.payloads(nodes, PROPS))

    def test_missing_source_emits_no_lineage_prop(self):
        row = base.mapping(
            "SOURCE_TITLE", base.SUMMARY + ".title", "text", LINEAGE_REQUIRED="Y",
        )
        ns, context = compiled(row)
        nodes, _ = base.build(ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {},
        }])
        self.assertEqual([], base.payloads(nodes, PROPS))

    def test_business_prop_is_not_duplicated_as_lineage(self):
        row = base.mapping(
            "FISMA_REPORTABLE", PROPS, "text", LINEAGE_REQUIRED="N",
        )
        ns, context = compiled(row)
        nodes, _ = base.build(ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"FISMA_REPORTABLE": "Yes"},
        }])
        props = base.payloads(nodes, PROPS)
        self.assertEqual(1, len(props))
        self.assertEqual(
            {"name": "fisma-reportable", "value": "Yes"},
            {key: value for key, value in props[0].items() if key != "uuid"},
        )

    def test_lineage_y_rejects_business_prop_and_config_rows(self):
        cases = [
            base.mapping("FISMA_REPORTABLE", PROPS, "text", LINEAGE_REQUIRED="Y"),
            base.mapping(
                "CONFIG_TITLE", base.SUMMARY + ".title", "text",
                VALUE_SOURCE="CONFIG", VALUE_REQUIRED="true", LINEAGE_REQUIRED="Y",
            ),
        ]
        for row in cases:
            with self.subTest(field=row["SOURCE_FIELD_NAME"]):
                ns = lean_support.namespace(models=("SSP",))
                context = base.compile_context(ns, [row], registry=registry_with_props())
                self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])

    def test_invalid_lineage_required_value_rejects(self):
        ns = lean_support.namespace(models=("SSP",))
        row = base.mapping(
            "SOURCE_TITLE", base.SUMMARY + ".title", "text", LINEAGE_REQUIRED="MAYBE",
        )
        context = base.compile_context(ns, [row], registry=registry_with_props())
        self.assertEqual("BLOCKED", context["routing_report"]["STATUS"])

    def test_required_namespace_fails_closed_only_when_lineage_is_emitted(self):
        row = base.mapping(
            "SOURCE_TITLE", base.SUMMARY + ".title", "text", LINEAGE_REQUIRED="Y",
        )
        ns, context = compiled(row)
        context["config"].pop("LINEAGE_PROPERTY_NS")
        with self.assertRaisesRegex(ValueError, "LINEAGE_PROPERTY_NS must be an absolute URI"):
            base.build(ns, context, [{
                "SOURCE_RECORD_ID": "record-one",
                "CURATED_JSON": {"SOURCE_TITLE": "Mapped title"},
            }])

    def test_current_ssp_system_characteristics_lineage_flags_are_selective(self):
        actual = {
            row["SOURCE_FIELD_NAME"] for row in mapping_rows()
            if str(row.get("LINEAGE_REQUIRED") or "").upper() == "Y"
        }
        self.assertEqual({
            "OPERATIONAL_STATUS",
            "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY",
            "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE",
            "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY",
            "INTEGRITY_CONTROL_CATEGORY_OVERRIDE",
            "PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY",
            "AVAILABILITY_CONTROL_CATEGORY_OVERRIDE",
            "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY",
            "PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY",
            "CNSS_AVAILABILITY_RATING",
            "CNSS_CONFIDENTIALITY_RATING",
            "CNSS_INTEGRITY_RATING",
        }, actual)


if __name__ == "__main__":
    unittest.main()
