"""A previous engine's cached plan cannot skip the current retirement boundary."""
import copy
import pickle
import unittest
from unittest.mock import Mock

import test_metadata_driven_contract as metadata
import test_metadata_runtime as runtime
import test_multi_model_graph as graph
import test_registry_metadata_contract as registry
from test_compiled_metadata_boundary import UnreadSource


class RetiredPlanCacheTests(unittest.TestCase):
    def reject_previous_cache(self, context):
        # Exact snapshot format emitted by Cell 3 before runtime dialect retirement.
        context["_compiled_plan_snapshot"] = pickle.dumps(context["compiled_plan"], protocol=4)
        source = UnreadSource()
        config = context["config"]
        with self.assertRaisesRegex(ValueError, "Retired runtime metadata"):
            graph.namespace()["build_oscal_graph"](
                source, graph.Frame(context["mapping_rows"]), graph.Frame(context["registry_rows"]),
                config["OSCAL_MODEL"], config["SOURCE_SYSTEM_NAME"], config["SOURCE_TABLE_NAME"], context,
            )
        self.assertEqual(source.reads, 0)

    def test_cached_controlled_fields_reject_instead_of_silently_disappearing(self):
        context = runtime.context(
            [runtime.mapping("TITLE", runtime.ROOT_PATH, "title", "text")],
            {runtime.ROOT_PATH: runtime.element(materialize_empty=True, controlled_fields=[
                {"target": "legacy-member", "value": "preserved-before-retirement", "required": False},
            ])},
        )
        self.reject_previous_cache(context)

    def test_cached_property_namespace_rejects_instead_of_changing_payload(self):
        path = runtime.ROOT_PATH + ".props[]"
        context = runtime.context(
            [runtime.mapping("FLAG", path, transform="archer-select",
                             params={"namespace": "https://example.test/approved-before-retirement"})],
            {runtime.ROOT_PATH: runtime.element(materialize_empty=True),
             path: runtime.element("properties", property_name_rule="source-field-slug")},
        )
        self.reject_previous_cache(context)

    def test_cached_uuid_token_recipe_rejects_before_reading_references(self):
        compiler = registry.RegistryMetadataContractTests()
        compiler.setUp()
        context = compiler.compile(rows=registry.reference_registry(), mappings=[metadata.mapping(
            "REVIEWER", metadata.SUMMARY + ".assignments[]", transform="direct",
            ROLE_ID="reviewer", ROLE_TITLE="Reviewer",
        )])
        group = context["compiled_plan"]["reference_groups"][0]
        group["party_uuid_parts"] = ["$source_system", "$source_record", "party", "$reference_id"]
        self.reject_previous_cache(context)

    def test_matching_cache_still_reuses_validation_and_preserves_output(self):
        namespace = graph.namespace()
        context = runtime.context(
            [runtime.mapping("TITLE", runtime.ROOT_PATH, "title", "text")],
            {runtime.ROOT_PATH: runtime.element(materialize_empty=True)},
        )
        first, _ = runtime.build(namespace, context, [
            {"SOURCE_RECORD_ID": "record", "CURATED_JSON": {"TITLE": "First"}},
        ])
        self.assertEqual(runtime.payload_at(first, runtime.ROOT_PATH), [{"title": "First"}])
        namespace["_validate_compiled_metadata"] = Mock(
            side_effect=AssertionError("An unchanged current plan was revalidated"))
        second, _ = runtime.build(namespace, copy.deepcopy(context), [
            {"SOURCE_RECORD_ID": "record", "CURATED_JSON": {"TITLE": "Second"}},
        ])
        self.assertEqual(runtime.payload_at(second, runtime.ROOT_PATH), [{"title": "Second"}])

    def test_new_cell_four_rejects_previous_cell_three_before_initializing(self):
        namespace = {
            "_validate_compiled_metadata": lambda *args, **kwargs: None,
            "_metadata_plan_snapshot": lambda plan: pickle.dumps(plan, protocol=4),
        }
        with self.assertRaisesRegex(RuntimeError, "Run the matching Cell 3 before Cell 4"):
            exec(compile(graph.C4.read_text(encoding="utf-8"), str(graph.C4), "exec"), namespace)
        self.assertNotIn("SKIP_VALUE", namespace)


if __name__ == "__main__":
    unittest.main()
