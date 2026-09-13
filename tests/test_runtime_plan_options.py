"""The compiled plan owns runtime behavior without a second policy dictionary."""
import math
import unittest

import test_metadata_runtime as runtime
import test_multi_model_graph as graph


class RuntimePlanOptionsTests(unittest.TestCase):
    def context(self, transform="text", **options):
        context = runtime.context(
            [runtime.mapping("VALUE", runtime.ROOT_PATH, "title", transform)],
            {runtime.ROOT_PATH: runtime.element(materialize_empty=True)},
        )
        context["compiled_plan"]["options"] = options
        return context

    def test_aggregate_option_keeps_fail_fast_and_complete_error_report_modes(self):
        records = [{"SOURCE_RECORD_ID": "record", "CURATED_JSON": {"VALUE": {"nested": "object"}}}]
        for aggregate, message in ((False, "Mapped value must be nonblank text"),
                                   (True, "Metadata mappings rejected source values")):
            with self.subTest(aggregate=aggregate):
                context = self.context(aggregate_invalid=aggregate)
                with self.assertRaisesRegex(ValueError, message):
                    runtime.build(graph.namespace(), context, records)
                self.assertEqual(context["graph_report"]["FIELDS"]["VALUE"]["invalid"], 1)
                self.assertFalse(context["graph_report"]["OUTPUTS_PUBLISHED"])

    def test_nonfinite_serialization_still_requires_explicit_plan_option(self):
        records = [{"SOURCE_RECORD_ID": "record", "CURATED_JSON": {"VALUE": float("inf")}}]
        for options in ({}, {"allow_nan": False}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                runtime.build(graph.namespace(), self.context("direct", **options), records)
        context = self.context("direct", allow_nan=True)
        nodes, _ = runtime.build(graph.namespace(), context, records)
        self.assertTrue(math.isinf(runtime.payload_at(nodes, runtime.ROOT_PATH)[0]["title"]))
