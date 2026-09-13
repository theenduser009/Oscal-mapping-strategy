"""Transform parity against frozen code and metadata-only graph extensibility."""
import ast
import contextlib
import copy
import datetime
import hashlib
import io
import json
import unittest

from lean_support import ROOT, build, namespace
import test_registry_release as fixtures
import test_metadata_driven_contract as metadata_fixtures


FROZEN_HASHES = {
    "03_canonical_mapping_contract.py": "bd2d965e6596af2dfa89c85eb73e91681cc4f057de89beaa2ca9e6179d2f3e25",
    "04_parsing_transform_payload_helpers.py": "ff84532e24e541bb15b170a6458299d3f1c160cc5182dc115c8b38ef56822dc1",
}


def frozen_transform_namespace():
    """Load only the immutable pre-rebuild oracle, without notebook I/O."""
    result = {}
    for filename, digest in FROZEN_HASHES.items():
        path = ROOT / "tests/fixtures/pre_lean_cells" / filename
        source = path.read_text(encoding="utf-8")
        if hashlib.sha256(source.encode()).hexdigest() != digest:
            raise AssertionError("Frozen transform oracle changed: " + filename)
        if filename.startswith("03"):
            definitions = []
            for node in ast.parse(source).body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
                    definitions.append(node)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    try:
                        ast.literal_eval(node.value)
                    except (TypeError, ValueError, SyntaxError):
                        continue
                    definitions.append(node)
            source = compile(ast.Module(body=definitions, type_ignores=[]), str(path), "exec")
        with contextlib.redirect_stdout(io.StringIO()):
            exec(source, result)
    return result


def outcome(runtime, row, value, context):
    try:
        result = runtime["_metadata_transform"](row, copy.deepcopy(value), context)
    except (TypeError, ValueError, ArithmeticError):
        return ("rejected",)
    if result is runtime["SKIP_VALUE"]:
        return ("absent",)
    # repr distinguishes nested boolean/number values and Decimal/string values.
    return ("value", type(result).__name__, repr(result))


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        self.contexts = self.ns["compile_mapping_contexts"](
            {"source-one": fixtures.mapping_rows()}, fixtures.release_registry(),
            self.ns["SOURCE_PROFILES"], self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])
        for context in self.contexts:
            context["lookups"] = {"archer_values": {"1": "low", "2": "high"}, "fips_values": {}}

    def test_1403_maintained_transform_cases_match_frozen_code(self):
        frozen = frozen_transform_namespace()
        values = [None, "", [], {}, False, True, 0, 1, -1, 1.25, "  example  ",
                  "Low", "Moderate", "High", "LOE 1", "2025-01-02", "2025-01-02T23:01:00-02:00",
                  [False], [1], [1, 2], {"ValuesListIds": [1]}, {"ValuesListIds": [999]},
                  {"UserList": [{"Id": "user"}]}]
        count = 0
        for context in self.contexts:
            for row in context["mapping_rows"]:
                if row["TRANSFORM_ID"] == "skip" or self.ns["_metadata_params"](row).get("required"):
                    continue
                for value in values:
                    with self.subTest(rule=row["RULE_ID"], value=value):
                        self.assertEqual(outcome(frozen, row, value, context),
                                         outcome(self.ns, row, value, context))
                    count += 1
        self.assertEqual(1403, count)

    def test_required_values_fail_after_transform_without_exposing_source_value(self):
        context = self.contexts[0]
        config = context["config"]
        self.ns["_prepare_model_context"](context, config["OSCAL_MODEL"],
                                            config["SOURCE_SYSTEM_NAME"], config["SOURCE_TABLE_NAME"])
        row = next(row for row in context["mapping_rows"] if row["RULE_ID"] == "support:metadata-title")
        for value in (None, "", " ", {"secret": "sensitive-source-value"}):
            with self.subTest(value=value), self.assertRaises(ValueError) as raised:
                self.ns["_metadata_mapped_value"](row, {row["SOURCE_FIELD_NAME"]: value}, context)
            self.assertNotIn("sensitive-source-value", str(raised.exception))
        self.assertFalse(context["graph_report"]["OUTPUTS_PUBLISHED"])

    def test_iso_date_keeps_source_calendar_day_and_rejects_invalid_shapes(self):
        convert = self.ns["transform_authorization_date"]
        for value in ("2025-01-02T23:59:59-12:00", "2025-01-02T01:00:00.123456789Z",
                      datetime.datetime(2025, 1, 2, 23, 59), datetime.date(2025, 1, 2)):
            with self.subTest(value=value):
                self.assertEqual("2025-01-02", convert(value))
        for value in ("01/02/2025", "2025-02-30", 1735776000, {"date": "2025-01-02"}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                convert(value)

    def test_select_container_never_silently_emits_unresolved_ids(self):
        context = self.contexts[0]
        resolve = self.ns["resolve_archer_select_value"]
        self.assertEqual(["low"], resolve({"ValuesListIds": [1]}, context))
        self.assertEqual("Human label", resolve("Human label", context))
        self.assertEqual(999, resolve(999, context))
        with self.assertRaises(ValueError):
            resolve({"ValuesListIds": [999]}, context)

    def test_score_precision_zero_and_boolean_preserve_scalar_text(self):
        parse, score = self.ns["_metadata_parse"], self.ns["_score_value"]
        context = next(ctx for ctx in self.contexts if ctx["config"]["OSCAL_MODEL"] == "ASSESSMENT_RESULTS")
        source = parse({"CURATED_JSON": '{"SCORE":1.000000000000000001}'}, context)
        self.assertEqual("1.000000000000000001", score(source["SCORE"], context))
        self.assertEqual("0", score(0, context))
        self.assertEqual("false", score(False, context))
        for value in (float("nan"), float("inf"), [1, 2], {"unexpected": 1}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                score(value, context)

    def test_new_field_and_third_model_build_and_validate_with_metadata_only(self):
        mappings = [metadata_fixtures.mapping(), metadata_fixtures.mapping(
            "NEW_SCORE", metadata_fixtures.OBSERVATION, transform="scalar-score")]
        context = self.ns["compile_mapping_contexts"](
            {"source-one": mappings}, metadata_fixtures.registry_rows(), [metadata_fixtures.profile()],
            {metadata_fixtures.MODEL: metadata_fixtures.model_contract()})[0]
        context["lookups"] = {"archer_values": {}, "fips_values": {}}
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        records = [{"SOURCE_RECORD_ID": str(index), "CURATED_JSON": {
            "NEVER_SEEN_SOURCE_FIELD": title, "NEW_SCORE": index}}
                   for index, title in ((0, "First"), (1, "Second"))]
        before = copy.deepcopy(records)
        nodes, edges = build(self.ns, context, records)
        self.assertEqual(records, before)
        self.assertEqual((8, 6), (len(nodes.rows), len(edges.rows)))
        summaries = [json.loads(row["METADATA_JSON"])["title"] for row in nodes.rows
                     if row["ELEMENT_PATH"] == metadata_fixtures.SUMMARY]
        self.assertEqual(["First", "Second"], summaries)
        observations = [json.loads(row["METADATA_JSON"])["props"] for row in nodes.rows
                        if row["ELEMENT_PATH"] == metadata_fixtures.OBSERVATION]
        self.assertEqual([[{"name": "new-score", "value": "0"}],
                          [{"name": "new-score", "value": "1"}]], observations)
        lookup = {row["NODE_KEY"]: row for row in nodes.rows}
        for edge in edges.rows:
            parent, child = lookup[edge["FK_SOURCE_ELEMENT_HASH"]], lookup[edge["FK_TARGET_ELEMENT_HASH"]]
            self.assertEqual(parent["SOURCE_RECORD_ID"], child["SOURCE_RECORD_ID"])
            self.assertEqual(parent["ELEMENT_PATH"], child["PARENT_NODE_PATH"])
        result = self.ns["validate_and_load_oscal"](nodes, edges, context["config"])
        self.assertEqual("MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING", result["status"])
        self.assertFalse(result["writes_executed"])


if __name__ == "__main__":
    unittest.main()
