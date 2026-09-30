"""Universal source-field lineage props without per-field mapping metadata."""
import json
import unittest

import lean_support
import test_metadata_driven_contract as base


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


class UniversalLineagePropertyTests(unittest.TestCase):
    def test_direct_mapping_automatically_emits_source_field_lineage(self):
        row = base.mapping("SOURCE_TITLE", base.SUMMARY + ".title", "text")
        ns, context = compiled(row)
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        self.assertEqual(
            [row["RULE_ID"]],
            [item["RULE_ID"] for item in context["compiled_plan"]["lineage_by_props_path"][PROPS]],
        )
        nodes, _ = base.build(ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {"SOURCE_TITLE": "Mapped title"},
        }])
        self.assertEqual([{"title": "Mapped title"}], base.payloads(nodes, base.SUMMARY))
        self.assertEqual([{
            "name": "source-field",
            "ns": NS,
            "class": "synthetic-model.summary.title",
            "value": "SOURCE_TITLE",
        }], base.payloads(nodes, PROPS))

    def test_missing_source_emits_no_lineage_prop(self):
        row = base.mapping("SOURCE_TITLE", base.SUMMARY + ".title", "text")
        ns, context = compiled(row)
        nodes, _ = base.build(ns, context, [{
            "SOURCE_RECORD_ID": "record-one",
            "CURATED_JSON": {},
        }])
        self.assertEqual([], base.payloads(nodes, PROPS))

    def test_nearest_registered_props_collection_is_used(self):
        root_props = base.ROOT_PATH + ".props[]"
        registry = registry_with_props()
        registry.append({
            "OSCAL_MODEL_KEY": base.MODEL,
            "NODE_PATH": root_props,
            "PARENT_NODE_PATH": base.ROOT_PATH,
            "ELEMENT_TYPE": "props",
            "IS_COLLECTION": True,
            "IS_ACTIVE": True,
            "INSTANCE_KEY_RULE": "SOURCE_FIELD_NAME+VALUE",
            "ITEM_PATH": "$",
            "PROCESS_ORDER": 6,
            "OPERATOR": "properties",
            "UUID_POLICY": "node",
            "REQUIRED_MEMBERS": None,
        })
        ns = lean_support.namespace(models=("SSP",))
        row = base.mapping("SOURCE_TITLE", base.SUMMARY + ".title", "text")
        context = base.compile_context(ns, [row], registry=registry)
        context["config"]["LINEAGE_PROPERTY_NS"] = NS
        routes = context["compiled_plan"]["lineage_by_props_path"]
        self.assertIn(PROPS, routes)
        self.assertNotIn(root_props, routes)

    def test_config_mappings_are_not_source_field_lineage(self):
        ns = lean_support.namespace(models=("SSP",))
        row = base.mapping(
            "CONFIG_TITLE", base.SUMMARY + ".title", "text",
            VALUE_SOURCE="CONFIG", VALUE_REQUIRED="true",
        )
        context = base.compile_context(ns, [row], registry=registry_with_props())
        self.assertEqual({}, context["compiled_plan"]["lineage_by_props_path"])

    def test_required_lineage_namespace_fails_closed(self):
        row = base.mapping("SOURCE_TITLE", base.SUMMARY + ".title", "text")
        ns, context = compiled(row)
        context["config"].pop("LINEAGE_PROPERTY_NS")
        with self.assertRaisesRegex(ValueError, "LINEAGE_PROPERTY_NS must be an absolute URI"):
            base.build(ns, context, [{
                "SOURCE_RECORD_ID": "record-one",
                "CURATED_JSON": {"SOURCE_TITLE": "Mapped title"},
            }])


if __name__ == "__main__":
    unittest.main()
