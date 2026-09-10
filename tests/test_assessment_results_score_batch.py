import contextlib
import copy
import io
import json
from decimal import Decimal
from pathlib import Path
import runpy
import unittest

from tests.test_ssp_mapping_dispatch_contracts import _load_cell_4


CELL = Path(__file__).resolve().parents[1] / "notebooks/assessment_results/01_map_observation_scores.py"
CODE = runpy.run_path(str(CELL))
FIELDS = ("VULNERABILITY_SCORE", "ANTIVIRUS_SCORE", "PATCH_SCORE", "SECURITY_COMPLIANCE_SCORE")
NEW_FIELDS = (
    "STANDARD_OPERATING_ENVIRONMENT_SCORE", "COMPUTER_PASSWORD_AGE_SCORE",
    "VULNERABILITY_REPORTING_SCORE", "SECURITY_COMPLIANCE_REPORTING_SCORE",
    "TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE", "AVG_AUTHORIZATION_PACKAGE_RISK_SCORE",
    "RISK_SCORE_GRADE", "AVG_VULNERABILITY_SCORE", "AVG_PATCH_SCORE",
    "AVG_ANTIVIRUS_SCORE", "AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE",
    "AVG_COMPUTER_PASSWORD_AGE_SCORE", "AVG_VULNERABILITY_REPORTING_SCORE",
)
ALL_FIELDS = FIELDS + NEW_FIELDS
ROOT = "assessment-results"
RESULT = ROOT + ".results[]"
OBSERVATION = RESULT + ".observations[]"


def mappings():
    return [{
        "Archer_Field_Name": field,
        "OSCAL_Model": "Assessment Results",
        "OSCAL_Element_Path": OBSERVATION,
        "Mapping_Type": "Extension Property",
        "Notes": "Archer-specific risk scoring - map as observation",
    } for field in ALL_FIELDS]


def registry():
    contracts = [
        (ROOT, "assessment-results", None, False, None, 1),
        (RESULT, "results", ROOT, True, "SOURCE_RECORD_ID", 2),
        (OBSERVATION, "observations", RESULT, True, "SOURCE_FIELD_NAME", 3),
    ]
    return [{
        "OSCAL_MODEL_KEY": "ASSESSMENT_RESULTS", "NODE_PATH": path,
        "ELEMENT_TYPE": kind, "PARENT_NODE_PATH": parent,
        "IS_COLLECTION": collection, "INSTANCE_KEY_RULE": rule,
        "PROCESS_ORDER": order, "IS_ACTIVE": True, "ITEM_PATH": None,
    } for path, kind, parent, collection, rule, order in contracts]


def config():
    return {
        "EXECUTE_WRITES": False, "OSCAL_MODEL": "SSP", "OSCAL_VERSION": "1.2.3",
        "SOURCE_SYSTEM_NAME": "ARCHER",
        "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
        "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
        "IDENTITY_VERSION": "v1_registry_path_instance", "RUN_ID": "accepted-ssp-run",
        "TARGET_DIM": "accepted-ssp-dim", "TARGET_FACT": "accepted-ssp-fact",
    }


def source(source_id="record-a", values=None):
    return {"SOURCE_RECORD_ID": source_id, "CURATED_JSON": {} if values is None else values}


class UnreadSource:
    def __iter__(self):
        raise AssertionError("Blocked metadata must not read source records")


class AssessmentResultsScoreBatchTests(unittest.TestCase):
    def setUp(self):
        self.helper_namespace = _load_cell_4()
        self.helpers = {name: self.helper_namespace[name] for name in CODE["AR_HELPERS"]}

    def build(self, records, mapping_rows=None, registry_rows=None, run_config=None):
        return CODE["build_ar_score_batch"](
            records, mappings() if mapping_rows is None else mapping_rows,
            registry() if registry_rows is None else registry_rows,
            config() if run_config is None else run_config, self.helpers,
        )

    def assert_blocked(self, batch):
        self.assertEqual(batch["report"]["STATUS"], "BLOCKED")
        self.assertEqual(batch["nodes"], [])
        self.assertEqual(batch["edges"], [])
        self.assertEqual(batch["documents"], {})
        self.assertFalse(batch["report"]["WRITES_EXECUTED"])
        self.assertFalse(batch["report"]["FULL_MODEL_COMPLETE"])

    def observations(self, batch):
        return [n for n in batch["nodes"] if n["ELEMENT_PATH"] == OBSERVATION]

    def test_four_named_score_payloads_and_exact_parent_edges(self):
        values = dict(zip(FIELDS, [0, 2, Decimal("3.25"), " 4 "]))
        batch = self.build([source(values=values)])
        self.assertEqual(batch["report"]["STATUS"], "MAPPED_SCOPE_BUILT")
        self.assertEqual((len(batch["nodes"]), len(batch["edges"])), (6, 5))
        by_key = {n["NODE_KEY"]: n for n in batch["nodes"]}
        self.assertEqual(len(by_key), 6)
        self.assertEqual(len({e["EDGE_KEY"] for e in batch["edges"]}), 5)
        expected_values = ["0", "2", "3.25", "4"]
        for node, field, expected_value in zip(self.observations(batch), FIELDS, expected_values):
            payload = json.loads(node["METADATA_JSON"])
            self.assertEqual(payload, {
                "uuid": node["OSCAL_UUID"],
                "props": [{"name": field.lower().replace("_", "-"), "value": expected_value}],
            })
            self.assertEqual(node["INSTANCE_KEY"], field)
            self.assertEqual(node["PARENT_INSTANCE_KEY"], "record-a")
            self.assertEqual(node["NODE_KEY"], self.helpers["_deterministic_hash"](
                "v1_registry_path_instance", "ARCHER", config()["SOURCE_TABLE_NAME"],
                "record-a", "ASSESSMENT_RESULTS", OBSERVATION, field,
            ))
        for edge in batch["edges"]:
            parent = by_key[edge["FK_SOURCE_ELEMENT_HASH"]]
            child = by_key[edge["FK_TARGET_ELEMENT_HASH"]]
            self.assertEqual(parent["INSTANCE_KEY"], child["PARENT_INSTANCE_KEY"])
            self.assertEqual(parent["SOURCE_RECORD_ID"], child["SOURCE_RECORD_ID"])
            self.assertEqual(edge["SOURCE_OSCAL_UUID"], parent["OSCAL_UUID"])
            self.assertEqual(edge["TARGET_OSCAL_UUID"], child["OSCAL_UUID"])
        self.assertEqual({n["ELEMENT_PATH"] for n in batch["nodes"]}, {ROOT, RESULT, OBSERVATION})
        document = batch["documents"]["record-a"][ROOT]
        self.assertEqual(document["results"][0]["observations"],
                         [json.loads(n["METADATA_JSON"]) for n in self.observations(batch)])
        self.assertFalse(batch["report"]["SCHEMA_VALIDATED"])
        self.assertFalse(batch["report"]["FULL_MODEL_COMPLETE"])
        self.assertEqual(batch["report"]["FIELDS_WITH_POPULATED_EVIDENCE"], 4)

    def test_same_field_in_two_records_has_distinct_identity_and_correct_parent(self):
        batch = self.build([source("a", {FIELDS[0]: 5}), source("b", {FIELDS[0]: 5})])
        observations = self.observations(batch)
        self.assertEqual(len({n["NODE_KEY"] for n in observations}), 2)
        nodes = {n["NODE_KEY"]: n for n in batch["nodes"]}
        for observation in observations:
            edge = next(e for e in batch["edges"] if e["FK_TARGET_ELEMENT_HASH"] == observation["NODE_KEY"])
            parent = nodes[edge["FK_SOURCE_ELEMENT_HASH"]]
            self.assertEqual(parent["ELEMENT_PATH"], RESULT)
            self.assertEqual(parent["INSTANCE_KEY"], observation["SOURCE_RECORD_ID"])
            self.assertEqual(parent["SOURCE_RECORD_ID"], observation["SOURCE_RECORD_ID"])

    def test_reordering_inputs_and_score_changes_preserve_entity_identity(self):
        records = [source("a", {FIELDS[0]: 5}), source("b", {FIELDS[1]: 8})]
        first = self.build(records)
        reordered = self.build(list(reversed(records)), list(reversed(mappings())), list(reversed(registry())))
        signature = lambda batch: {(n["NODE_KEY"], n["OSCAL_UUID"]) for n in batch["nodes"]}
        self.assertEqual(signature(first), signature(reordered))
        self.assertEqual({e["EDGE_KEY"] for e in first["edges"]}, {e["EDGE_KEY"] for e in reordered["edges"]})
        changed = self.build([source("a", {FIELDS[0]: 9}), records[1]])
        self.assertEqual(signature(first), signature(changed))
        self.assertNotEqual(self.observations(first)[0]["METADATA_JSON"], self.observations(changed)[0]["METADATA_JSON"])

    def test_zero_is_emitted_and_null_empty_values_are_missing(self):
        batch = self.build([source(values=dict(zip(FIELDS, [0, None, "", []])))])
        self.assertEqual(len(self.observations(batch)), 1)
        self.assertEqual(json.loads(self.observations(batch)[0]["METADATA_JSON"])["props"][0]["value"], "0")
        for field in FIELDS[1:]:
            self.assertEqual(batch["report"]["FIELDS"][field], {"emitted": 0, "missing": 1, "invalid": 0})

    def test_bare_numeric_score_does_not_resolve_matching_archer_select_id(self):
        self.assertEqual(self.helper_namespace["ARCHER_VALUE_LOOKUP"]["101"], "Mission Critical")
        for value in (101, "101"):
            with self.subTest(value=value):
                batch = self.build([source(values={FIELDS[0]: value})])
                payload = json.loads(self.observations(batch)[0]["METADATA_JSON"])
                self.assertEqual(payload["props"][0]["value"], "101")

    def test_explicit_select_container_resolves_one_value(self):
        batch = self.build([source(values={FIELDS[0]: {"ValuesListIds": [101]}})])
        payload = json.loads(self.observations(batch)[0]["METADATA_JSON"])
        self.assertEqual(payload["props"][0]["value"], "Mission Critical")

    def test_json_decimal_precision_is_preserved(self):
        raw = '{"VULNERABILITY_SCORE":0.123456789012345678901}'
        batch = self.build([source(values=raw)])
        payload = json.loads(self.observations(batch)[0]["METADATA_JSON"])
        self.assertEqual(payload["props"][0]["value"], "0.123456789012345678901")

    def test_unknown_or_multiple_select_values_block_all_outputs(self):
        for value in ({"ValuesListIds": [999]}, {"ValuesListIds": [101, 102]}, [1, 2]):
            with self.subTest(value=value):
                batch = self.build([source(values={FIELDS[0]: value, FIELDS[1]: 5})])
                self.assert_blocked(batch)
                self.assertEqual(batch["report"]["FIELDS"][FIELDS[0]]["invalid"], 1)

    def test_nonfinite_and_nonscalar_scores_block(self):
        invalid = [float("nan"), float("inf"), float("-inf"), Decimal("NaN"),
                   Decimal("Infinity"), Decimal("sNaN"), "Infinity", "nan", {"unknown": 7}, [[7]], "   "]
        for value in invalid:
            with self.subTest(value=repr(value)):
                batch = self.build([source(values={FIELDS[0]: value})])
                self.assert_blocked(batch)
                self.assertEqual(batch["report"]["FIELDS"][FIELDS[0]]["invalid"], 1)

    def test_invalid_json_or_nonobject_json_blocks_all_outputs(self):
        for value in ("{", "[]", "7", "null", []):
            with self.subTest(value=value):
                batch = self.build([source("valid", {FIELDS[0]: 5}), source("invalid", value)])
                self.assert_blocked(batch)
                self.assertEqual(batch["report"]["INVALID_SOURCE_RECORDS"], 1)
        good = self.build([source(values=json.dumps({FIELDS[0]: 5}))])
        self.assertEqual(len(self.observations(good)), 1)

    def test_wrong_mapping_path_or_notes_blocks_before_source_read(self):
        mutations = [
            ("OSCAL_Element_Path", OBSERVATION + " or props[]"),
            ("OSCAL_Element_Path", OBSERVATION + ".props[]"),
            ("Notes", "Archer specific risk scoring, map as observation or property"),
            ("Mapping_Type", "Extension Properties"),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                rows = mappings()
                rows[0][key] = value
                batch = self.build(UnreadSource(), mapping_rows=rows)
                self.assert_blocked(batch)
                self.assertTrue(batch["report"]["MAPPING_CONTRACT_ERRORS"])

    def test_missing_or_duplicate_selected_mapping_blocks_before_source_read(self):
        for rows in (mappings()[1:], mappings() + [mappings()[0]]):
            batch = self.build(UnreadSource(), mapping_rows=rows)
            self.assert_blocked(batch)
            self.assertTrue(batch["report"]["MAPPING_CONTRACT_ERRORS"])

    def test_missing_duplicate_inactive_or_wrong_identity_registry_blocks_before_source_read(self):
        variants = [registry()[:-1], registry() + [registry()[-1]]]
        for column, value in (("IS_ACTIVE", False), ("INSTANCE_KEY_RULE", "VALUE"),
                              ("PARENT_NODE_PATH", ROOT), ("IS_COLLECTION", False),
                              ("ITEM_PATH", "$.scores[]"), ("ELEMENT_TYPE", "parties")):
            rows = registry()
            rows[-1][column] = value
            variants.append(rows)
        for rows in variants:
            with self.subTest(rows=rows):
                batch = self.build(UnreadSource(), registry_rows=rows)
                self.assert_blocked(batch)
                self.assertTrue(batch["report"]["REGISTRY_CONTRACT_ERRORS"])

    def test_duplicate_source_id_blocks_previously_built_candidates(self):
        batch = self.build([source("a", {FIELDS[0]: 5}), source("a", {FIELDS[0]: 6})])
        self.assert_blocked(batch)
        self.assertEqual(batch["report"]["DUPLICATE_SOURCE_RECORDS"], 1)
        self.assertGreater(batch["report"]["CANDIDATE_NODES"], 0)
        self.assertFalse(batch["report"]["OUTPUTS_PUBLISHED"])

    def test_source_and_metadata_inputs_and_config_are_not_mutated(self):
        records, rows, registry_rows, run_config = [source(values={FIELDS[0]: 5})], mappings(), registry(), config()
        before = copy.deepcopy((records, rows, registry_rows, run_config))
        self.build(records, rows, registry_rows, run_config)
        self.assertEqual((records, rows, registry_rows, run_config), before)
        self.assertEqual(self.helper_namespace["CONFIG"], {"SOURCE_SYSTEM_NAME": "unit-test"})

    def test_main_execution_retains_ssp_outputs_and_clears_old_ar_outputs(self):
        class SourceFrame:
            def to_local_iterator(self):
                return iter([source(values={FIELDS[0]: 5})])
        class MappingFrame:
            def to_dict(self, orient):
                self.assert_orient = orient
                return mappings()
        class RegistryFrame:
            def collect(self):
                return registry()
        ssp_nodes, ssp_edges, ssp_documents = object(), object(), {"accepted": "SSP"}
        run_config = config()
        before = copy.deepcopy(run_config)
        initial = dict(self.helpers, CONFIG=run_config, source_df=SourceFrame(),
                       mapping_artifact_pdf=MappingFrame(), element_registry_df=RegistryFrame(),
                       canonical_nodes_df=ssp_nodes, canonical_edges_df=ssp_edges,
                       SSP_DOCUMENTS=ssp_documents, AR_SCORE_DOCUMENTS={"stale": "AR"})
        with contextlib.redirect_stdout(io.StringIO()):
            namespace = runpy.run_path(str(CELL), init_globals=initial, run_name="__main__")
        self.assertIs(namespace["canonical_nodes_df"], ssp_nodes)
        self.assertIs(namespace["canonical_edges_df"], ssp_edges)
        self.assertIs(namespace["SSP_DOCUMENTS"], ssp_documents)
        self.assertEqual(run_config, before)
        self.assertNotIn("stale", namespace["AR_SCORE_DOCUMENTS"])
        self.assertEqual(namespace["AR_SCORE_RUN_REPORT"]["STATUS"], "MAPPED_SCOPE_BUILT")

    def test_no_source_reports_no_mapping_evidence(self):
        batch = self.build([])
        self.assert_blocked(batch)
        self.assertEqual(batch["report"]["SOURCE_RECORDS"], 0)
        self.assertFalse(batch["report"]["OUTPUTS_PUBLISHED"])
        self.assertTrue(all(counts == {"emitted": 0, "missing": 0, "invalid": 0}
                            for counts in batch["report"]["FIELDS"].values()))

    def test_main_metadata_block_does_not_start_source_query_or_print_payloads(self):
        class SourceFrame:
            def to_local_iterator(self):
                raise AssertionError("Metadata block must precede source query")
        class MappingFrame:
            def to_dict(self, orient):
                rows = mappings()
                rows[0]["OSCAL_Element_Path"] += " or props[]"
                return rows
        class RegistryFrame:
            def collect(self):
                return registry()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            state = runpy.run_path(str(CELL), run_name="__main__", init_globals=dict(
                self.helpers, CONFIG=config(), source_df=SourceFrame(),
                mapping_artifact_pdf=MappingFrame(), element_registry_df=RegistryFrame(),
                AR_SCORE_DOCUMENTS={"private-old-id": {"secret-score": 123}},
            ))
        self.assertEqual(state["AR_SCORE_RUN_REPORT"]["STATUS"], "BLOCKED")
        self.assertEqual(state["AR_SCORE_DOCUMENTS"], {})
        self.assertNotIn("private-old-id", output.getvalue())
        self.assertNotIn("secret-score", output.getvalue())

    def test_write_enabled_or_wrong_source_configuration_is_rejected(self):
        for key, value in (("EXECUTE_WRITES", True), ("SOURCE_TABLE_NAME", "OTHER")):
            changed = config()
            changed[key] = value
            with self.assertRaises(ValueError):
                self.build(UnreadSource(), run_config=changed)

    def test_all_null_source_preserves_structural_scope_without_score_evidence(self):
        batch = self.build([source(values={field: None for field in FIELDS})])
        self.assertEqual(batch["report"]["SOURCE_RECORDS"], 1)
        self.assertEqual(batch["report"]["FIELDS_WITH_POPULATED_EVIDENCE"], 0)
        self.assertEqual(self.observations(batch), [])
        self.assertTrue(all(counts == {"emitted": 0, "missing": 1, "invalid": 0}
                            for counts in batch["report"]["FIELDS"].values()))
        self.assertFalse(batch["report"]["FULL_MODEL_COMPLETE"])
        self.assertFalse(batch["report"]["SCHEMA_VALIDATED"])

    def test_expanded_release_emits_exactly_seventeen_observations_under_one_result(self):
        self.assertEqual(CODE["AR_SCORE_FIELDS"], ALL_FIELDS)
        values = {field: index for index, field in enumerate(ALL_FIELDS)}
        values["RISK_SCORE_GRADE"] = "A"
        batch = self.build([source(values=values)])
        self.assertEqual(batch["report"]["MAPPING_RELEASE"], "ar-observation-scores-v2-17-fields")
        self.assertEqual(batch["report"]["SELECTED_FIELDS"], list(ALL_FIELDS))
        self.assertEqual(batch["report"]["FIELDS_WITH_POPULATED_EVIDENCE"], 17)
        self.assertEqual((len(batch["nodes"]), len(batch["edges"])), (19, 18))
        nodes = {node["NODE_KEY"]: node for node in batch["nodes"]}
        self.assertEqual(len(nodes), 19)
        self.assertEqual(len({edge["EDGE_KEY"] for edge in batch["edges"]}), 18)
        root = next(node for node in nodes.values() if node["ELEMENT_PATH"] == ROOT)
        result = next(node for node in nodes.values() if node["ELEMENT_PATH"] == RESULT)
        self.assertEqual((root["INSTANCE_KEY"], root["PARENT_INSTANCE_KEY"]), ("singleton", None))
        self.assertEqual((result["INSTANCE_KEY"], result["PARENT_INSTANCE_KEY"]), ("record-a", "singleton"))
        observations = self.observations(batch)
        self.assertEqual([node["INSTANCE_KEY"] for node in observations], list(ALL_FIELDS))
        for node in observations:
            field = node["INSTANCE_KEY"]
            self.assertEqual(node["PARENT_INSTANCE_KEY"], result["INSTANCE_KEY"])
            payload = json.loads(node["METADATA_JSON"])
            self.assertEqual(payload, {
                "uuid": node["OSCAL_UUID"],
                "props": [{"name": field.lower().replace("_", "-"), "value": str(values[field])}],
            })
            self.assertEqual(batch["report"]["FIELDS"][field], {"emitted": 1, "missing": 0, "invalid": 0})
        self.assertEqual({(edge["FK_SOURCE_ELEMENT_HASH"], edge["FK_TARGET_ELEMENT_HASH"])
                          for edge in batch["edges"]},
                         {(root["NODE_KEY"], result["NODE_KEY"])}
                         | {(result["NODE_KEY"], node["NODE_KEY"]) for node in observations})
        self.assertEqual(batch["documents"]["record-a"][ROOT]["results"][0]["observations"],
                         [json.loads(node["METADATA_JSON"]) for node in observations])
        self.assertEqual({node["ELEMENT_PATH"] for node in nodes.values()}, {ROOT, RESULT, OBSERVATION})
        self.assertFalse(batch["report"]["WRITES_EXECUTED"])

    def test_each_new_field_requires_its_exact_approved_mapping_before_reading_source(self):
        mutations = (
            ("OSCAL_Element_Path", OBSERVATION + " or props[]", "contract_target"),
            ("Mapping_Type", "Extension Properties", "contract_mapping_type"),
            ("Notes", "Archer specific risk scoring map as observation or property", "contract_notes"),
            ("OSCAL_Model", "SSP", "contract_model"),
            ("OSCAL_FIELD_NAME", "value", "contract_target_member"),
            ("TRANSFORMATION_LOGIC", "round score", "contract_extra_transform"),
        )
        for field in NEW_FIELDS:
            for column, value, issue in mutations:
                with self.subTest(field=field, column=column):
                    rows = mappings()
                    target = next(row for row in rows if row["Archer_Field_Name"] == field)
                    target[column] = value
                    batch = self.build(UnreadSource(), mapping_rows=rows)
                    self.assert_blocked(batch)
                    self.assertIn({"field": field, "issue": issue}, batch["report"]["MAPPING_CONTRACT_ERRORS"])
            for duplicate in (False, True):
                with self.subTest(field=field, duplicate=duplicate):
                    rows = mappings()
                    target = next(row for row in rows if row["Archer_Field_Name"] == field)
                    if duplicate:
                        rows.append(dict(target))
                    else:
                        rows.remove(target)
                    batch = self.build(UnreadSource(), mapping_rows=rows)
                    self.assert_blocked(batch)
                    self.assertIn({"field": field, "issue": "expected_one_mapping_row",
                                   "rows": 2 if duplicate else 0},
                                  batch["report"]["MAPPING_CONTRACT_ERRORS"])

    def test_excluded_duplicates_conflicting_notes_and_other_groups_are_not_emitted(self):
        excluded = (
            ("AVG_SECURITY_COMPLIANCE_SCORE", OBSERVATION, "Extension Property",
             "Archer-specific risk scoring - map as observation"),
            ("AVG_SECURITY_COMPLIANCE_SCORE", OBSERVATION, "Extension Property",
             "Archer-specific risk scoring - map as observation"),
            ("TOTAL_PACKAGE_INHERENT_RISK", OBSERVATION, "Extension Property",
             "Archer specific risk scoring, map as observation or property"),
            ("UNSELECTED_OBSERVATION_SCORE", OBSERVATION, "Extension Property",
             "Archer-specific risk scoring - map as observation"),
            ("ALTERNATIVE_TARGET_SCORE", OBSERVATION + " or props[]", "Extension Property", "pending"),
            ("WORKFLOW_STATE", RESULT + ".props[]", "Extension Properties", "conditional workflow"),
            ("FINDING_REFERENCE", RESULT + ".findings[]", "Reference", "reference"),
        )
        rows = mappings() + [{
            "Archer_Field_Name": field, "OSCAL_Model": "Assessment Results",
            "OSCAL_Element_Path": path, "Mapping_Type": mapping_type, "Notes": notes,
        } for field, path, mapping_type, notes in excluded]
        values = {field: 1 for field in ALL_FIELDS}
        # Deliberately invalid values prove excluded sources never enter conversion.
        values.update({field: {"not-a-score": [1, 2]} for field, _, _, _ in excluded})
        batch = self.build([source(values=values)], mapping_rows=rows)
        self.assertEqual(batch["report"]["STATUS"], "MAPPED_SCOPE_BUILT")
        self.assertEqual(batch["report"]["OTHER_AR_MAPPING_ROWS_NOT_PROCESSED"], 7)
        self.assertEqual({node["INSTANCE_KEY"] for node in self.observations(batch)}, set(ALL_FIELDS))
        self.assertEqual(set(batch["report"]["FIELDS"]), set(ALL_FIELDS))

    def test_first_four_match_pre_expansion_identity_and_payload_snapshot(self):
        # Captured from the accepted four-field implementation before this expansion.
        expected = (
            ("VULNERABILITY_SCORE", "e80965082cf002741e05eba6949db545",
             "7fe2c052-75a4-5a85-9a50-d36394c21642", "vulnerability-score", "0"),
            ("ANTIVIRUS_SCORE", "17f4ef456ba76562cf409152a442848c",
             "14acb459-c830-59f4-b0dc-625800f23391", "antivirus-score", "2"),
            ("PATCH_SCORE", "6e1ef8db22afd7f2994746dcafb36379",
             "f8a60a78-fbea-5069-b04a-bd1909158351", "patch-score", "3.25"),
            ("SECURITY_COMPLIANCE_SCORE", "7a300afa6a012a8eaef5e533a398718a",
             "34dbfa57-8d80-5caf-a563-38a865d1eefe", "security-compliance-score", "4"),
        )
        values = dict(zip(FIELDS, [0, 2, Decimal("3.25"), "4"]))
        values.update({field: 7 for field in NEW_FIELDS})
        batch = self.build([source(values=values)])
        first_four = [node for node in self.observations(batch) if node["INSTANCE_KEY"] in FIELDS]
        self.assertEqual(len(first_four), 4)
        for node, (field, node_key, node_uuid, property_name, value) in zip(first_four, expected):
            self.assertEqual((node["INSTANCE_KEY"], node["NODE_KEY"], node["OSCAL_UUID"]),
                             (field, node_key, node_uuid))
            self.assertEqual(node["METADATA_JSON"], json.dumps({
                "props": [{"name": property_name, "value": value}], "uuid": node_uuid,
            }, sort_keys=True))
            self.assertEqual(node["PARENT_INSTANCE_KEY"], "record-a")


if __name__ == "__main__":
    unittest.main()
