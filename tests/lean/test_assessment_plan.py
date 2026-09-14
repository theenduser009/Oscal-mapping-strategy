"""SAP mappings with synthetic data; relational tests do not prove live Snowflake acceptance."""
import copy
import datetime
import json
import unittest
from unittest.mock import patch

from lean_support import build, business, namespace
from test_registry_release import mapping_rows, release_registry
import test_loader as storage

MODEL = "SECURITY_ASSESSMENT_PLAN"
ROOT_PATH = "assessment-plan"
TASK_PATH = ROOT_PATH + ".tasks[]"
PROP_PATH = TASK_PATH + ".props[]"
REQUEST = "REQUEST_TO_BEGIN_ASSESSMENT"
APPROVAL = "APPROVAL_TO_BEGIN_ASSESSMENT"
COMMENTS = "PREASSESSMENT_REVIEW_COMMENTS"


def sap_registry():
    """Independent expectation for the three-element hierarchy."""
    return [dict(OSCAL_MODEL_KEY=MODEL, NODE_PATH=path, PARENT_NODE_PATH=parent,
                 ELEMENT_TYPE=element, IS_COLLECTION=collection, IS_ACTIVE=True,
                 INSTANCE_KEY_RULE=identity, ITEM_PATH=item_path, PROCESS_ORDER=order,
                 OPERATOR=operator, UUID_POLICY=uuid_policy, REQUIRED_MEMBERS=None)
            for order, (path, parent, element, collection, operator, identity, item_path, uuid_policy)
            in enumerate([
                (ROOT_PATH, None, ROOT_PATH, False, "object", None, None, "node"),
                (TASK_PATH, ROOT_PATH, "tasks", True, "record", "SOURCE_RECORD_ID", None, "node"),
                (PROP_PATH, TASK_PATH, "props", True, "properties", "SOURCE_FIELD_NAME", "$", "omit"),
            ], 1)]


class AssessmentPlanTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace(models=(MODEL,))
        self.rows = mapping_rows()
        self.context = self.compile()

    def compile(self, rows=None, registry=None):
        context = self.ns["compile_mapping_contexts"](
            {"source-one": self.rows if rows is None else rows},
            release_registry() + sap_registry() if registry is None else registry,
            self.ns["SOURCE_PROFILES"], self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"], context["routing_report"])
        context["lookups"] = {"archer_values": {"101": "Requested", "102": "Approved", "103": "Pending"}}
        return context

    def graph(self, source, record_id="synthetic-package", context=None):
        return build(self.ns, context or self.context,
                     [{"SOURCE_RECORD_ID": record_id, "CURATED_JSON": source}])

    def payloads(self, nodes, path):
        return [json.loads(row["METADATA_JSON"]) for row in nodes.rows if row["ELEMENT_PATH"] == path]

    def test_actual_csv_selects_three_source_fields_and_two_config_supports(self):
        rows = self.context["mapping_rows"]
        self.assertEqual(5, len(rows))
        fields = {row["SOURCE_FIELD_NAME"]: row for row in rows
                  if row["REPRESENTATION_PARAMS"].get("value_source") != "CONFIG"}
        self.assertEqual({REQUEST, APPROVAL, COMMENTS}, set(fields))
        for field in (REQUEST, APPROVAL):
            self.assertEqual((PROP_PATH, "archer-select", "APPROVED"), tuple(fields[field][key]
                for key in ("OWNER_ELEMENT_PATH", "TRANSFORM_ID", "APPROVAL_STATUS")))
        self.assertEqual((TASK_PATH, "remarks", "text"), tuple(fields[COMMENTS][key]
            for key in ("OWNER_ELEMENT_PATH", "FIELD_RELATIVE_PATH", "TRANSFORM_ID")))
        self.assertTrue(all(row["REPRESENTATION_PARAMS"]["preserve_null"] for row in fields.values()))
        support = {row["SOURCE_FIELD_NAME"]: row for row in rows
                   if row["REPRESENTATION_PARAMS"].get("value_source") == "CONFIG"}
        self.assertEqual({"ASSESSMENT_TASK_TITLE", "ASSESSMENT_TASK_TYPE"}, set(support))
        self.assertTrue(all(row["REPRESENTATION_PARAMS"]["required"] for row in support.values()))
        selected_csv = [row for row in self.rows if row["SOURCE_FIELD_NAME"] in fields]
        self.assertEqual({"61", "62", "63"}, {row["ORIGINAL_EXCEL_ROW"] for row in selected_csv})
        self.assertTrue(all(row["OSCAL_ELEMENT_PATH"] == row["RUNTIME_TARGET_PATH"] for row in selected_csv))
        self.assertFalse(self.context["config"]["EXECUTE_WRITES"])

    def test_picklists_and_remarks_belong_to_one_source_scoped_task(self):
        source = {REQUEST: {"ValuesListIds": [101]}, APPROVAL: {"ValuesListIds": [102]},
                  COMMENTS: "  Review completed.\nFollow-up retained.  ",
                  "ASSESSMENT_TASK_TITLE": "Source cannot override CONFIG",
                  "UNMAPPED_PRIVATE_FIELD": "Must not appear"}
        records = [{"SOURCE_RECORD_ID": record, "CURATED_JSON": source} for record in ("package-a", "package-b")]
        nodes, edges = build(self.ns, self.context, records)
        self.assertEqual((8, 6), (len(nodes.rows), len(edges.rows)))
        for record in ("package-a", "package-b"):
            owned = [row for row in nodes.rows if row["SOURCE_RECORD_ID"] == record]
            task = next(row for row in owned if row["ELEMENT_PATH"] == TASK_PATH)
            self.assertEqual({"uuid": task["OSCAL_UUID"], "title": "Preassessment review", "type": "action",
                              "remarks": source[COMMENTS]}, json.loads(task["METADATA_JSON"]))
            properties = [row for row in owned if row["ELEMENT_PATH"] == PROP_PATH]
            self.assertEqual({"request-to-begin-assessment": "Requested", "approval-to-begin-assessment": "Approved"},
                {json.loads(row["METADATA_JSON"])["name"]: json.loads(row["METADATA_JSON"])["value"] for row in properties})
            for row in properties:
                self.assertNotIn("uuid", json.loads(row["METADATA_JSON"]))
                edge = next(edge for edge in edges.rows if edge["FK_TARGET_ELEMENT_HASH"] == row["NODE_KEY"])
                self.assertEqual(task["NODE_KEY"], edge["FK_SOURCE_ELEMENT_HASH"])
        self.assertEqual(8, len({row["NODE_KEY"] for row in nodes.rows}))
        self.assertEqual(8, len({row["OSCAL_UUID"] for row in nodes.rows}))
        self.assertNotIn("Must not appear", json.dumps(business(nodes), default=str))
        self.assertEqual({"nodes": 8, "edges": 6, "source_records": 2},
                         self.ns["_load_graph"](nodes, edges, self.context["config"]))

    def test_explicit_nulls_preserved_but_missing_fields_are_absent(self):
        source = {REQUEST: None, APPROVAL: None, COMMENTS: None}
        for raw in (source, json.dumps(source)):
            with self.subTest(source_type=type(raw).__name__):
                nodes, edges = self.graph(raw)
                self.assertEqual((4, 3), (len(nodes.rows), len(edges.rows)))
                self.assertEqual([None, None], [payload["value"] for payload in self.payloads(nodes, PROP_PATH)])
                self.assertIsNone(self.payloads(nodes, TASK_PATH)[0]["remarks"])
        for source in ({}, {REQUEST: "", APPROVAL: [], COMMENTS: ""}):
            nodes, edges = self.graph(source)
            self.assertEqual((2, 1), (len(nodes.rows), len(edges.rows)))
            self.assertNotIn("remarks", self.payloads(nodes, TASK_PATH)[0])
            self.assertEqual([], self.payloads(nodes, PROP_PATH))

    def test_null_changes_and_source_order_preserve_every_identity(self):
        null_graph = self.graph({REQUEST: None, APPROVAL: None, COMMENTS: None})
        source = {COMMENTS: "Updated remarks", APPROVAL: {"ValuesListIds": [102]}, REQUEST: {"ValuesListIds": [101]}}
        value_graph = self.graph(source)
        self.assertEqual({row["NODE_KEY"]: row["OSCAL_UUID"] for row in null_graph[0].rows},
                         {row["NODE_KEY"]: row["OSCAL_UUID"] for row in value_graph[0].rows})
        self.assertEqual(business(null_graph[1]), business(value_graph[1]))
        reordered = self.graph(dict(reversed(list(source.items()))))
        self.assertEqual(tuple(map(business, value_graph)), tuple(map(business, reordered)))

    def test_unknown_picklists_multiselect_and_bad_remarks_fail_without_source_values(self):
        cases = ({REQUEST: {"ValuesListIds": [999999]}}, {APPROVAL: {"ValuesListIds": [101, 102]}},
                 {COMMENTS: {"unexpected": "do-not-echo-private-data"}})
        for source in cases:
            with self.subTest(field=next(iter(source))), self.assertRaises(ValueError) as caught:
                self.graph(source)
            self.assertNotIn("999999", str(caught.exception))
            self.assertNotIn("do-not-echo-private-data", str(caught.exception))

    def test_required_config_and_invalid_null_policy_block(self):
        context = copy.deepcopy(self.context)
        context["config"].pop("ASSESSMENT_TASK_TITLE")
        with self.assertRaises(ValueError):
            self.graph({"ASSESSMENT_TASK_TITLE": "Not an approved fallback"}, context=context)
        rows = copy.deepcopy(self.rows)
        next(row for row in rows if row["SOURCE_FIELD_NAME"] == REQUEST)["NULL_POLICY"] = "invent"
        contexts = self.ns["compile_mapping_contexts"]({"source-one": rows}, release_registry() + sap_registry(),
            self.ns["SOURCE_PROFILES"], self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])
        self.assertEqual("BLOCKED", contexts[0]["routing_report"]["STATUS"])

    def test_storage_keeps_shared_layout_with_distinct_plan_names(self):
        contract = self.context["config"]["STORAGE_CONTRACT"]
        prefix = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED."
        self.assertEqual((prefix + "DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT", prefix + "FACT_OSCAL_ASSESSMENT_PLAN_DEPENDENCY",
                          "PK_DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT_HASH", "PK_FACT_OSCAL_ASSESSMENT_PLAN_DEPENDENCY_HASH"),
                         tuple(contract[key] for key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN")))
        differences = {"MODEL_KEY", "ROOT_PATH", "ROOT_ELEMENT_TYPE", "TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"}
        for model in ("SSP", "ASSESSMENT_RESULTS", "POAM"):
            other = self.ns["MODEL_CONTRACTS"][model]["STORAGE_CONTRACT"]
            self.assertEqual({key: value for key, value in other.items() if key not in differences},
                             {key: value for key, value in contract.items() if key not in differences})

    def test_unselected_plan_does_not_change_existing_scopes(self):
        from test_poam_references import poam_registry
        deployed = namespace(models=("SSP", "ASSESSMENT_RESULTS", "POAM"))
        contexts = deployed["compile_mapping_contexts"]({"source-one": self.rows}, release_registry() + poam_registry(),
            deployed["SOURCE_PROFILES"], deployed["MODEL_CONTRACTS"], deployed["ROUTING_METADATA"])
        self.assertEqual({"SSP": 48, "ASSESSMENT_RESULTS": 32, "POAM": 1},
                         {context["config"]["OSCAL_MODEL"]: len(context["mapping_rows"]) for context in contexts})
        self.assertTrue(all(context["routing_report"]["STATUS"] == "READY" for context in contexts))

    def test_renamed_model_and_field_reuse_the_same_metadata_behavior(self):
        model, root = "FUTURE_REVIEW", "future-review"
        chosen = [copy.deepcopy(row) for row in self.rows if row["SOURCE_FIELD_NAME"] == REQUEST
                  or row["RULE_ID"] in {"support:sap-task-title", "support:sap-task-type"}]
        for row in chosen:
            row["OSCAL_MODEL"] = model
            for column in ("OSCAL_ELEMENT_PATH", "RUNTIME_TARGET_PATH"):
                row[column] = row[column].replace(ROOT_PATH, root)
            if row["SOURCE_FIELD_NAME"] == REQUEST:
                row["SOURCE_FIELD_NAME"], row["RULE_ID"] = "UNRELATED_REVIEW_CHOICE", "future:choice"
        registry = [{**row, "OSCAL_MODEL_KEY": model,
                     "NODE_PATH": row["NODE_PATH"].replace(ROOT_PATH, root),
                     "PARENT_NODE_PATH": row["PARENT_NODE_PATH"].replace(ROOT_PATH, root) if row["PARENT_NODE_PATH"] else None}
                    for row in sap_registry()]
        profiles = [dict(self.ns["SOURCE_PROFILES"][0], MODEL_KEYS=(model,))]
        contract = {model: dict(MODEL_KEY=model, POLICY="metadata-v1", STORAGE_CONTRACT=None)}
        context = self.ns["compile_mapping_contexts"]({"source-one": chosen}, registry, profiles, contract,
            self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("READY", context["routing_report"]["STATUS"], context["routing_report"])
        context["lookups"] = {"archer_values": {"101": "Selected"}}
        before = self.graph({"UNRELATED_REVIEW_CHOICE": None}, context=context)
        after = self.graph({"UNRELATED_REVIEW_CHOICE": {"ValuesListIds": [101]}}, context=context)
        self.assertEqual((3, 2), tuple(len(frame.rows) for frame in before))
        self.assertEqual({row["NODE_KEY"] for row in before[0].rows}, {row["NODE_KEY"] for row in after[0].rows})
        self.assertEqual(business(before[1]), business(after[1]))
        self.assertEqual([{"name": "unrelated-review-choice", "value": "Selected"}],
                         self.payloads(after[0], root + ".tasks[].props[]"))

    def test_preview_null_insert_populated_update_and_unchanged_readback(self):
        session = storage.Session()
        self.addCleanup(session.db.close)
        config = dict(self.context["config"])
        contract = config["STORAGE_CONTRACT"]
        for table_key, pk_key, fields in (("TARGET_DIM", "DIM_PK_COLUMN", storage.P["_DIM_FIELDS"]),
                                          ("TARGET_FACT", "FACT_PK_COLUMN", storage.P["_FACT_FIELDS"])):
            table, pk = contract[table_key], contract[pk_key]
            session.schema[table] = [dict(name=name, type=dtype, kind="COLUMN", expression=None,
                **{"null?": "N" if table_key == "TARGET_FACT" or name == pk else "Y"})
                for name, dtype in {pk: "BINARY(16)", **fields}.items()]
            session.query(f"CREATE TABLE {table} ({', '.join(row['name'] for row in session.schema[table])})")
        def load(source, writes):
            transported = []
            for frame in self.graph(source):
                rows = [{key: value.isoformat() if isinstance(value, (datetime.datetime, datetime.date)) else value
                         for key, value in row.items()} for row in frame.rows]
                transported.append(storage.Frame(session, rows, frame.columns))
            with patch.dict(self.ns, session=session):
                return self.ns["validate_and_load_oscal"](*transported, dict(config, EXECUTE_WRITES=writes))
        nulls = {REQUEST: None, APPROVAL: None, COMMENTS: None}
        preview = load(nulls, False)
        self.assertEqual("PREVIEW_PASSED_NO_TARGET_DML", preview["status"])
        self.assertEqual([], session.query("SELECT * FROM " + contract["TARGET_DIM"]))
        inserted = load(nulls, True)
        self.assertEqual("COMMITTED_AND_VERIFIED", inserted["status"])
        self.assertEqual({"INSERTS": 4, "UPDATES": 0, "UNCHANGED": 0}, inserted["expected_changes"]["D"])
        dim, pk = contract["TARGET_DIM"], contract["DIM_PK_COLUMN"]
        saved = {row[pk]: row for row in session.query("SELECT * FROM " + dim)}
        facts = session.query("SELECT * FROM " + contract["TARGET_FACT"])
        self.assertTrue(all(isinstance(key, bytes) and len(key) == 16 for key in saved))
        populated = {REQUEST: {"ValuesListIds": [101]}, APPROVAL: {"ValuesListIds": [102]}, COMMENTS: "Reviewed"}
        changed = load(populated, True)
        self.assertEqual("COMMITTED_AND_VERIFIED", changed["status"])
        self.assertEqual({"INSERTS": 0, "UPDATES": 3, "UNCHANGED": 1}, changed["expected_changes"]["D"])
        changed_rows = {row[pk]: row for row in session.query("SELECT * FROM " + dim)}
        self.assertEqual(set(saved), set(changed_rows))
        self.assertEqual(facts, session.query("SELECT * FROM " + contract["TARGET_FACT"]))
        repeated = load(populated, True)
        self.assertEqual({"D": {"INSERTS": 0, "UPDATES": 0, "UNCHANGED": 4},
                          "F": {"INSERTS": 0, "UPDATES": 0, "UNCHANGED": 3}}, repeated["expected_changes"])
        restored = load(nulls, True)
        self.assertEqual({"INSERTS": 0, "UPDATES": 3, "UNCHANGED": 1}, restored["expected_changes"]["D"])
        payloads = [json.loads(row["METADATA_JSON"]) for row in session.query("SELECT * FROM " + dim)]
        self.assertEqual(2, sum("value" in payload and payload["value"] is None for payload in payloads))
        self.assertTrue(any("remarks" in payload and payload["remarks"] is None for payload in payloads))


if __name__ == "__main__":
    unittest.main()
