"""Additional release tests: in-memory execution, no Snowflake or GitHub writes.

Known-boundary tests retain their original safety assertions through corrections.
These are local runtime/source-contract tests, not live Snowflake execution.
"""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import test_metadata_driven_contract as metadata
import test_multi_model_graph as graph
import test_multi_model_inputs as inputs
import test_registry_metadata_contract as registry_contract
import test_registry_metadata_migration as migration
import test_registry_notebook_flow as flow
import test_registry_release as release
from test_typed_graph_frames import snowpark_types_stub

ROOT = Path(__file__).resolve().parents[1]
CIA = "system-security-plan.system-characteristics.security-impact-level"


class StrictTransport:
    """Match Snowpark's documented empty-data schema requirement, no SQL."""

    def create_dataframe(self, data, schema=None):
        if not data and schema is None:
            raise ValueError("Cannot infer schema from empty data")
        return graph.Frame(data)


class AdditionalReleaseTests(unittest.TestCase):
    def assert_singleton_does_not_execute(self, column):
        case = release.RegistryReleaseTests()
        case.setUp()
        rows = release.release_registry()
        next(row for row in rows if row["NODE_PATH"] == CIA)[column] = False
        context = case.compile(models=("SSP",), registry=rows)[0]
        selected = [row for row in context["mapping_rows"]
                    if row.get("CANONICAL_ELEMENT_PATH", "").startswith(CIA + ".")]
        self.assertEqual(0, len(selected),
                         "Disabled/inactive registry owner must not reroute approved children into its parent")

    def test_null_operator_derives_scalar_owner_without_rerouting(self):
        case = release.RegistryReleaseTests()
        case.setUp()
        rows = release.release_registry()
        next(row for row in rows if row["NODE_PATH"] == CIA)["OPERATOR"] = None
        context = case.compile(models=("SSP",), registry=rows)[0]
        selected = [row for row in context["mapping_rows"]
                    if row.get("CANONICAL_ELEMENT_PATH", "").startswith(CIA)]
        self.assertTrue(selected)
        self.assertTrue(all(row.get("OWNER_ELEMENT_PATH") == CIA for row in selected))

    def test_inactive_singleton_cannot_reroute_cia_mappings(self):
        self.assert_singleton_does_not_execute("IS_ACTIVE")

    def test_singleton_only_future_model_supports_typed_empty_edges(self):
        ns = metadata.namespace()
        reg = [row for row in registry_contract.annotated_registry()
               if row["NODE_PATH"] == metadata.ROOT_PATH]
        mapping = metadata.mapping(path=metadata.ROOT_PATH + ".title")
        context = ns["compile_mapping_contexts"](
            {"source-one": [mapping]}, reg, [metadata.profile()],
            {metadata.MODEL: registry_contract.strict_contract()})[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"])
        ns["session"] = StrictTransport()
        with snowpark_types_stub():
            nodes, edges = graph.build(ns, context, [
                {"SOURCE_RECORD_ID": "1", "CURATED_JSON": {"NEVER_SEEN_SOURCE_FIELD": "Example"}}
            ], graph.Frame(reg))
        self.assertEqual((1, 0), (len(nodes.rows), len(edges.rows)))

    def run_ar_pipeline(self, source_value):
        ns = flow.NotebookFlowTests().execute(("ASSESSMENT_RESULTS",))
        session = ns["session"]
        original_create = session.create_dataframe
        session.create_dataframe = lambda data, schema=None: (
            StrictTransport().create_dataframe(data, schema) if isinstance(data, list)
            else original_create(data))
        ns["SOURCE_INPUTS"]["source-one"]["source_df"].rows[0]["CURATED_JSON"] = source_value
        with patch.object(inputs.Frame, "to_local_iterator",
                          lambda frame: iter(frame.collect()), create=True), \
                contextlib.redirect_stdout(io.StringIO()):
            for filename in ("04_parsing_transform_payload_helpers.py",
                             "05_registry_graph_builder.py",
                             "06_validation_and_guarded_loader.py",
                             "07_mapper_orchestrator.py"):
                path = ROOT / "notebooks/cells" / filename
                exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), ns)
        return ns

    def test_complete_seven_cell_ar_preview_preserves_zero_and_false(self):
        ns = self.run_ar_pipeline(json.dumps({"PATCH_SCORE": 0, "ANTIVIRUS_SCORE": False}))
        self.assertEqual("PREVIEW_WITH_TARGET_CONTRACTS_PENDING", ns["PIPELINE_REPORT"]["status"])
        self.assertFalse(ns["PIPELINE_REPORT"]["writes_executed"])
        result = ns["MODEL_GRAPHS"][("source-one", "ASSESSMENT_RESULTS")]
        self.assertEqual((4, 3), (len(result["nodes"].rows), len(result["edges"].rows)))
        props = [json.loads(row["METADATA_JSON"])["props"] for row in result["nodes"].rows
                 if row["ELEMENT_PATH"].endswith(".observations[]")]
        self.assertEqual({"0", "false"}, {prop["value"] for group in props for prop in group})

    def test_ar_missing_and_null_scores_keep_valid_result_parent(self):
        for value in ("{}", '{"VULNERABILITY_SCORE":null}'):
            with self.subTest(value=value):
                ns = self.run_ar_pipeline(value)
                result = ns["MODEL_GRAPHS"][("source-one", "ASSESSMENT_RESULTS")]
                self.assertEqual((2, 1), (len(result["nodes"].rows), len(result["edges"].rows)))
                self.assertEqual(17, len(result["coverage"].rows))
                self.assertFalse(ns["PIPELINE_REPORT"]["writes_executed"])

    def test_ar_repeat_run_preserves_business_payload_and_keys(self):
        one = self.run_ar_pipeline('{"PATCH_SCORE":0,"RISK_SCORE_GRADE":"A"}')
        two = self.run_ar_pipeline('{"PATCH_SCORE":0,"RISK_SCORE_GRADE":"A"}')
        key = ("source-one", "ASSESSMENT_RESULTS")
        for kind in ("nodes", "edges"):
            self.assertEqual(graph.business(one["MODEL_GRAPHS"][key][kind].rows),
                             graph.business(two["MODEL_GRAPHS"][key][kind].rows))
        self.assertFalse(two["CONFIG"]["EXECUTE_WRITES"])

    def test_optional_cia_baseline_still_omits_partial_assembly(self):
        case = release.RegistryReleaseTests()
        case.setUp()
        (nodes, _), _ = case.ssp(mutate_record=lambda records:
            records[0]["CURATED_JSON"].pop("RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY"))
        self.assertEqual([], metadata.payloads(nodes, CIA))
        self.assertTrue(all("security-impact-level" not in payload for payload in
                           metadata.payloads(nodes, "system-security-plan.system-characteristics")))


def current_parent_guard(sql, row, rows):
    """Source-bound boolean simulation of current SQL, not Snowflake execution."""
    section = sql.split("-- Retained executable paths have a retained parent", 1)[1]
    predicate = section.split("WHERE ", 1)[1].split(";", 1)[0]
    predicate = " ".join(predicate.split())
    parent = (row.get("PARENT_NODE_PATH") or "").strip() or None
    root = "system-security-plan" if row["OSCAL_MODEL_KEY"] == "SSP" else "assessment-results"
    parent_row = next((other for other in rows
                       if other["OSCAL_MODEL_KEY"] == row["OSCAL_MODEL_KEY"]
                       and other["NODE_PATH"] == parent), None)
    atoms = {
        "d.x:META:OPERATOR::VARCHAR IS NOT NULL": bool(row.get("OPERATOR")),
        "r.IS_COLLECTION IS NULL": row.get("IS_COLLECTION") is None,
        "r.ELEMENT_TYPE IS NULL": row.get("ELEMENT_TYPE") is None,
        "r.PROCESS_ORDER IS NULL": row.get("PROCESS_ORDER") is None,
        "NULLIF(TRIM(r.PARENT_NODE_PATH),'') IS NOT NULL": parent is not None,
        "NULLIF(TRIM(r.PARENT_NODE_PATH),'') IS NULL": parent is None,
        "p.x:META:OPERATOR::VARCHAR IS NULL":
            not bool(parent_row and parent_row.get("OPERATOR")),
        "r.IS_COLLECTION IS DISTINCT FROM ENDSWITH(d.x:PATH::VARCHAR,'[]')":
            row.get("IS_COLLECTION") != row["NODE_PATH"].endswith("[]"),
        "COALESCE(STARTSWITH(d.x:PATH::VARCHAR, NULLIF(TRIM(r.PARENT_NODE_PATH),'') || '.'),FALSE)":
            bool(parent and row["NODE_PATH"].startswith(parent + ".")),
        "d.x:PATH::VARCHAR IS DISTINCT FROM d.root_path": row["NODE_PATH"] != root,
        "COALESCE(d.x:PATH::VARCHAR=d.root_path OR STARTSWITH(d.x:PATH::VARCHAR,d.root_path || '.'),FALSE)":
            row["NODE_PATH"] == root or row["NODE_PATH"].startswith(root + "."),
    }
    for atom, value in atoms.items():
        if atom not in predicate:
            raise AssertionError("Migration predicate changed; review simulation: " + atom)
        predicate = predicate.replace(atom, repr(bool(value)))
    for sql_word, python_word in (("AND", "and"), ("OR", "or"), ("NOT", "not")):
        predicate = re.sub(r"\b" + sql_word + r"\b", python_word, predicate)
    expression = ast.parse(" ".join(predicate.split()), mode="eval")
    allowed = (ast.Expression, ast.BoolOp, ast.UnaryOp, ast.Constant,
               ast.And, ast.Or, ast.Not)
    if any(not isinstance(node, allowed) for node in ast.walk(expression)):
        raise AssertionError("Unsupported SQL atom: review source-bound simulation")
    return eval(compile(expression, "<SQL predicate simulation>", "eval"),
                {"__builtins__": {}})


class RegistryMigrationBoundaryTests(unittest.TestCase):
    """Preflight source-contract tests; the migration itself is not executed."""

    @classmethod
    def setUpClass(cls):
        cls.sql = migration.SQL_PATH.read_text(encoding="utf-8")
        cls.seed = migration.read_seed(cls.sql)
        oracle = json.loads(migration.ORACLE_PATH.read_text(encoding="utf-8"))
        cls.rows, _ = migration.simulate_guarded_update(
            migration.synthetic_registry(oracle), cls.seed)

    def setUp(self):
        self.harness = release.RegistryReleaseTests()
        self.harness.setUp()

    def test_valid_seed_fixture_still_compiles_in_active_decoder(self):
        contexts = self.harness.compile(registry=copy.deepcopy(self.rows))
        self.assertEqual({"SSP": 47, "ASSESSMENT_RESULTS": 17},
                         {ctx["config"]["OSCAL_MODEL"]: len(ctx["mapping_rows"])
                          for ctx in contexts})

    def test_null_key_simulation_exposes_inner_join_blind_spot(self):
        # One NULL is not a duplicate. OBJECT_CONSTRUCT omits SQL NULL;
        # ordinary equality joins cannot match a NULL key, including NULL=NULL.
        self.assertIn("HAVING COUNT(*)<>1 OR COUNT_IF(IS_ACTIVE IS NULL)>0", self.sql)
        self.assertIn("OBJECT_CONSTRUCT('MODEL',UPPER(TRIM(r.OSCAL_MODEL_KEY)),", self.sql)
        self.assertIn("AND TRIM(NODE_PATH)=d.path AND IS_ACTIVE", self.sql)
        self.assertIn("AND TRIM(r.NODE_PATH)=d.path AND r.IS_ACTIVE", self.sql)
        keys = [(row["OSCAL_MODEL_KEY"], row["NODE_PATH"]) for row in self.rows]
        keys.append(("SSP", None))
        self.assertEqual(len(keys), len(set(keys)))
        desired = {key: value for key, value in {"MODEL": "SSP", "PATH": None}.items()
                   if value is not None}
        self.assertNotIn("PATH", desired)
        matches = [key for key in keys if key[1] is not None
                   and desired.get("PATH") is not None
                   and key == (desired["MODEL"], desired["PATH"])]
        self.assertEqual([], matches)

    def test_preddl_guard_must_reject_null_active_path(self):
        rows = copy.deepcopy(self.rows)
        bad = copy.deepcopy(next(row for row in rows
                                 if row["NODE_PATH"] == "system-security-plan.unmapped-singleton"))
        bad.update(NODE_PATH=None, OPERATOR=None)
        rows.append(bad)
        with self.assertRaisesRegex(ValueError, "unique active registry paths"):
            self.harness.compile(registry=rows)
        preddl = self.sql.split("-- DDL PHASE:", 1)[0]
        # The seed LEFT JOIN's r.path IS NULL does not cover additional rows.
        rejection = re.search(
            r"(?i)(?:\b(?:r\.)?NODE_PATH\s+IS\s+NULL|"
            r"NULLIF\(TRIM\((?:r\.)?NODE_PATH\),\s*''\)\s+IS\s+NULL)", preddl)
        self.assertIsNotNone(rejection,
                             "Migration can verify an active NULL path the decoder rejects")

    def assert_parent_rejected_before_ddl(self, parent):
        rows = copy.deepcopy(self.rows)
        path = "system-security-plan.system-implementation"
        self.assertNotIn(("SSP", path), self.seed)
        bad = next(row for row in rows if row["NODE_PATH"] == path)
        bad["PARENT_NODE_PATH"] = parent
        self.assertTrue(bad["OPERATOR"])
        with self.assertRaisesRegex(ValueError, "path ancestor"):
            self.harness.compile(registry=rows)
        self.assertTrue(current_parent_guard(self.sql, bad, rows),
                        "Migration accepts a parent relationship rejected by the decoder")

    def test_preddl_guard_must_reject_self_parent(self):
        self.assert_parent_rejected_before_ddl("system-security-plan.system-implementation")

    def test_preddl_guard_must_reject_enabled_nonancestor_parent(self):
        self.assert_parent_rejected_before_ddl("system-security-plan.metadata")


if __name__ == "__main__":
    unittest.main()

