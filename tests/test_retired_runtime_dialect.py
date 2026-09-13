"""Removed catalog-only execution settings reject before source values are read."""
import copy
import unittest

import test_metadata_runtime as runtime
import test_multi_model_graph as graph
from test_compiled_metadata_boundary import UnreadSource


class RetiredRuntimeDialectTests(unittest.TestCase):
    def context(self):
        return runtime.context(
            [runtime.mapping("TITLE", runtime.ROOT_PATH, "title", "text")],
            {runtime.ROOT_PATH: runtime.element(materialize_empty=True)},
        )

    def reject(self, context):
        source = UnreadSource()
        config = context["config"]
        with self.assertRaisesRegex(ValueError, "Retired runtime metadata|Unknown metadata mapping representation"):
            graph.namespace()["build_oscal_graph"](
                source, graph.Frame(context["mapping_rows"]), graph.Frame(context["registry_rows"]),
                config["OSCAL_MODEL"], config["SOURCE_SYSTEM_NAME"], config["SOURCE_TABLE_NAME"], context,
            )
        self.assertEqual(source.reads, 0)

    def test_removed_element_settings_reject_for_raw_and_previously_built_plans(self):
        retired = {
            "controlled_fields": [{"target": "title", "value": "injected"}],
            "type_member": "custom-type",
            "forbidden_members": ["title"],
            "nonblank_text_members": ["title"],
        }
        for prepared in (False, True):
            for key, value in retired.items():
                with self.subTest(prepared=prepared, parameter=key):
                    context = self.context()
                    if prepared:
                        nodes, _ = runtime.build(graph.namespace(), context, [
                            {"SOURCE_RECORD_ID": "record", "CURATED_JSON": {"TITLE": "Preserved"}},
                        ])
                        self.assertEqual(runtime.payload_at(nodes, runtime.ROOT_PATH), [{"title": "Preserved"}])
                    context["compiled_plan"]["elements"][runtime.ROOT_PATH]["parameters"][key] = value
                    self.reject(context)

    def test_default_element_and_arbitrary_object_merge_reject(self):
        context = self.context()
        context["compiled_plan"]["default_element"] = runtime.element(materialize_empty=True)
        self.reject(context)
        context = self.context()
        context["compiled_plan"]["mappings"][0]["REPRESENTATION"] = "merge-object"
        self.reject(context)

    def test_custom_crosswalk_and_transform_required_settings_reject(self):
        modifiers = {
            "target_member": "custom-state", "other_value": "custom-other",
            "remarks_member": "custom-remarks", "default_members": ["title"], "required": True,
        }
        for key, value in modifiers.items():
            with self.subTest(parameter=key):
                context = self.context()
                row = context["compiled_plan"]["mappings"][0]
                row["TRANSFORM_ID"] = "status-crosswalk"
                row["TRANSFORM_PARAMS"] = {
                    "crosswalk": {"legacy": "other"}, "other_remarks_prefix": "Source: ",
                    "other_remarks_suffix": ".", key: value,
                }
                self.reject(context)

    def test_property_names_and_namespaces_cannot_bypass_csv_metadata(self):
        path = runtime.ROOT_PATH + ".props[]"
        original = runtime.context(
            [runtime.mapping("FLAG", path, transform="archer-select")],
            {runtime.ROOT_PATH: runtime.element(materialize_empty=True),
             path: runtime.element("properties", property_name_rule="source-field-slug")},
        )
        nodes, _ = runtime.build(graph.namespace(), original, [
            {"SOURCE_RECORD_ID": "record", "CURATED_JSON": {"FLAG": False}},
        ])
        self.assertEqual(runtime.payload_at(nodes, path), [{"name": "flag", "value": "false"}])
        for key, value in (("namespace", "https://example.test/custom"), ("property_name", "custom-name")):
            with self.subTest(parameter=key):
                context = copy.deepcopy(original)
                context["compiled_plan"]["mappings"][0]["REPRESENTATION_PARAMS"][key] = value
                self.reject(context)

    def test_party_identity_cannot_execute_a_token_list_or_omit_namespace(self):
        for extra in (
            {"party_uuid_parts": ["$source_system", "$source_record", "party", "$reference_id"]},
            {"party_uuid_parts": ["arbitrary", "$reference_id"]},
            {"source_namespace": None},
            {"source_namespace": {"SOURCE_SYSTEM_NAME": "TEST"}},
            {"source_namespace": {"SOURCE_SYSTEM_NAME": "TEST", "SOURCE_TABLE_NAME": "TABLE_A", "MODEL_KEY": 1}},
        ):
            with self.subTest(extra=extra):
                context = self.context()
                group = {"roles_path": "roles", "parties_path": "parties", "assignments_path": "assignments",
                         "party_type": "person", "source_namespace": {
                             "SOURCE_SYSTEM_NAME": "TEST", "SOURCE_TABLE_NAME": "TABLE_A", "MODEL_KEY": "TEST_MODEL"}}
                group.update(extra)
                context["compiled_plan"]["reference_groups"] = [group]
                self.reject(context)
