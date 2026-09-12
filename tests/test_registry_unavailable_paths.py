"""Known registry boundaries stay closed; no Snowflake I/O."""
import unittest
import test_metadata_driven_contract as base
import test_registry_metadata_contract as reg
import test_flat_mapping_columns as flat
import test_registry_release as release

class RegistryUnavailablePaths(unittest.TestCase):
    def compile(self, rows, mappings):
        ns = base.namespace()
        context = ns["compile_mapping_contexts"](
            {"source-one": mappings}, rows, [base.profile()],
            {base.MODEL: reg.strict_contract()})[0]
        return ns, context

    def test_inactive_duplicate_does_not_disable_executable_path(self):
        rows = reg.annotated_registry()
        rows.append(dict(rows[1], IS_ACTIVE=False, MAPPER_ENABLED=False,
                         OPERATOR="irrelevant-old-value"))
        ns, ctx = self.compile(rows, [flat.mapping()])
        self.assertEqual("READY", ctx["routing_report"]["STATUS"])
        nodes, _ = base.build(ns, ctx, [{"SOURCE_RECORD_ID": "one",
            "CURATED_JSON": {"FLAT_SOURCE": "kept"}}])
        self.assertEqual([{"title": "kept"}], base.payloads(nodes, base.SUMMARY))

    def test_disabled_prefix_sibling_does_not_block_enabled_sibling(self):
        rows = reg.annotated_registry()
        sibling = base.SUMMARY + "-other"
        rows.append(dict(rows[1], NODE_PATH=sibling, PROCESS_ORDER=5))
        rows[1]["MAPPER_ENABLED"] = False
        ns, ctx = self.compile(rows, [flat.mapping(path=sibling + ".title")])
        self.assertEqual("READY", ctx["routing_report"]["STATUS"])
        nodes, _ = base.build(ns, ctx, [{"SOURCE_RECORD_ID": "one",
            "CURATED_JSON": {"FLAT_SOURCE": "kept"}}])
        self.assertEqual([{"title": "kept"}], base.payloads(nodes, sibling))
        self.assertEqual([], base.payloads(nodes, base.SUMMARY))

    def test_known_disabled_boundary_blocks_exact_and_nested_targets(self):
        for target in (base.SUMMARY, base.SUMMARY + ".title",
                       base.SUMMARY + ".nested.title"):
            with self.subTest(target=target):
                rows = reg.annotated_registry()
                rows[1]["MAPPER_ENABLED"] = False
                _, ctx = self.compile(rows, [flat.mapping(path=target)])
                self.assertEqual("BLOCKED", ctx["routing_report"]["STATUS"])
                self.assertEqual([], ctx["mapping_rows"])
                self.assertIn("REGISTRY_PATH_NOT_EXECUTABLE",
                              {i["reason"] for i in ctx["routing_report"]["ISSUES"]})

    def test_other_model_inactive_same_path_does_not_disable_selected_model(self):
        rows = reg.annotated_registry()
        rows.append(dict(rows[1], OSCAL_MODEL_KEY="OTHER_MODEL",
                         IS_ACTIVE=False, MAPPER_ENABLED=False))
        _, ctx = self.compile(rows, [flat.mapping()])
        self.assertEqual("READY", ctx["routing_report"]["STATUS"])

    def test_deferred_and_excluded_rows_skip_unavailable_boundary(self):
        rows = reg.annotated_registry()
        rows[1]["MAPPER_ENABLED"] = False
        mappings = [flat.mapping("VALID", path=base.OBSERVATION, TRANSFORM_ID="scalar-score")]
        mappings += [flat.mapping(status, EXECUTION_STATUS=status, TRANSFORM_ID="not-executable")
                     for status in ("DEFERRED", "EXCLUDED")]
        ns, ctx = self.compile(rows, mappings)
        self.assertEqual("READY", ctx["routing_report"]["STATUS"])
        self.assertEqual(["VALID"], [m["SOURCE_FIELD_NAME"] for m in ctx["mapping_rows"]])
        self.assertEqual(1, ctx["routing_report"]["DEFERRED_ROWS"])
        self.assertEqual(1, ctx["routing_report"]["EXCLUDED_ROWS"])
        nodes, _ = base.build(ns, ctx, [{"SOURCE_RECORD_ID": "one", "CURATED_JSON":
            {"VALID": 0, "DEFERRED": "not-executed", "EXCLUDED": "not-executed"}}])
        self.assertEqual([], base.payloads(nodes, base.SUMMARY))

    def test_actual_ar_disabled_observations_rejects_required_report_target(self):
        h = release.RegistryReleaseTests()
        h.setUp()
        rows = release.release_registry()
        path = "assessment-results.results[].observations[]"
        next(r for r in rows if r["NODE_PATH"] == path)["MAPPER_ENABLED"] = False
        with self.assertRaisesRegex(ValueError, "Report target must be an enabled registry path"):
            h.compile(models=("ASSESSMENT_RESULTS",), registry=rows)

    def test_approved_mapping_to_unselected_collection_blocks(self):
        rows = reg.annotated_registry()
        next(r for r in rows if r["NODE_PATH"] == base.OBSERVATION)["MAPPER_ENABLED"] = False
        _, ctx = self.compile(rows, [flat.mapping(path=base.OBSERVATION, TRANSFORM_ID="scalar-score")])
        self.assertEqual("BLOCKED", ctx["routing_report"]["STATUS"])
        self.assertEqual([], ctx["mapping_rows"])
        self.assertIn("REGISTRY_PATH_NOT_EXECUTABLE",
                      {i["reason"] for i in ctx["routing_report"]["ISSUES"]})

if __name__ == "__main__":
    unittest.main()
