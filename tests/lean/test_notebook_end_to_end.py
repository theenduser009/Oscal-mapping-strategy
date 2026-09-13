"""Execute every statement in all seven cells with installed Snowpark APIs.

Source, lookup, registry and graph frames use the real local emulator. Its
unsupported SQL/target-write boundary uses the existing SQLite/MERGE adapter;
the unsupported TRIM function uses Snowflake's documented mock.patch hook.
This checks notebook wiring and full mapped flow, not live Snowflake SQL.
"""
import ast
import builtins
import contextlib
import copy
import datetime
import io
import json
import unittest
from unittest.mock import patch

from lean_support import CELLS, ROOT, namespace
from test_registry_release import mapping_rows, release_registry
import test_snowpark_local as snowpark_smoke
import test_loader as storage


def populated_source(rows):
    """One valid synthetic value for every approved FIELD row in the actual CSV."""
    source, lookups = {}, {"software": {}, "interconnection": {}}
    for index, row in enumerate(rows):
        if row["EXECUTION_STATUS"] != "APPROVED" or row["VALUE_SOURCE"] == "CONFIG":
            continue
        field, transform = row["SOURCE_FIELD_NAME"], row["TRANSFORM_ID"]
        value = "Synthetic value"
        if row["ROLE_ID"]:
            value = {"UserList": [{"Id": "synthetic-person"}]}
        elif row["REFERENCE_TYPE"]:
            identifier = str(1000 + index)
            value = [{"ContentId": identifier}]
            if row["LOOKUP_KEY"]:
                lookups[row["LOOKUP_KEY"]][identifier] = {"SOFTWARE_NAME": "Tool", "INTERCONNECTION_NAME": "Connection",
                                                         "DESCRIPTION": "Synthetic description"}
        elif transform in {"timestamp", "date"}:
            value = "2026-01-01T00:00:00+00:00"
        elif transform in {"archer-select", "security-objective"}:
            value = {"ValuesListIds": ["1"]}
        elif transform == "status-crosswalk":
            value = "operational"
        elif transform == "scalar-score":
            value = 0
        source[field] = value
    return source, lookups


class NotebookSession(storage.Session):
    """Real input/frame APIs, local relational adapter for the SQL boundary."""
    def __init__(self, actual, sources, contracts):
        super().__init__()
        self.actual, self.sources = actual, sources
        for contract in contracts:
            for table_key, pk_key, fields in (("TARGET_DIM", "DIM_PK_COLUMN", storage.P["_DIM_FIELDS"]),
                                              ("TARGET_FACT", "FACT_PK_COLUMN", storage.P["_FACT_FIELDS"])):
                table, pk = contract[table_key], contract[pk_key]
                self.schema[table] = [dict(name=name, type=dtype, kind="COLUMN", expression=None,
                                          **{"null?": "N" if table_key == "TARGET_FACT" or name == pk else "Y"})
                                      for name, dtype in {pk: "BINARY(16)", **fields}.items()]
                self.query(f"CREATE TABLE {table} ({', '.join(row['name'] for row in self.schema[table])})")

    def table(self, name):
        return self.sources[name] if name in self.sources else super().table(name)

    def create_dataframe(self, *args, **kwargs):
        return self.actual.create_dataframe(*args, **kwargs)


class NotebookEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # This gate fails in CI if the required package is missing.
        snowpark_smoke.SnowparkLocalSmokeTests.setUpClass()
        from snowflake.snowpark.mock import ColumnEmulator, patch as snowpark_patch

        @snowpark_patch(snowpark_smoke.SnowparkLocalSmokeTests.functions.trim)
        def local_trim(column, characters=None):
            # Snowflake's default TRIM removes spaces, not arbitrary whitespace.
            chars = characters if isinstance(characters, ColumnEmulator) else [characters or " "] * len(column)
            result = ColumnEmulator(data=[None if value is None or trim is None else value.strip(trim) if trim else value
                                          for value, trim in zip(column, chars)], index=column.index)
            result.sf_type = column.sf_type
            return result

    def setUp(self):
        self.smoke = snowpark_smoke.SnowparkLocalSmokeTests()
        self.smoke.setUp()
        self.addCleanup(self.smoke.doCleanups)
        self.actual, self.types = self.smoke.session, self.smoke.types
        self.defaults = namespace()
        self.profile = self.defaults["SOURCE_PROFILES"][0]
        self.contract = self.defaults["MODEL_CONTRACTS"]["SSP"]["STORAGE_CONTRACT"]
        self.source, lookups = populated_source(mapping_rows())
        rows = [{"CONTENT_ID": "synthetic-record", "CURATED_JSON": json.dumps(self.source)}]
        sources = {self.profile["RAW_TABLE"]: self.frame(rows)}
        sources[self.defaults["CONFIG"]["ARCHER_META_VALUE_TABLE"]] = self.frame([
            {"SELECT_VALUE_ID": "1", "SELECT_VALUE_NAME": "low"}])
        sources[self.defaults["CONFIG"]["ELEMENT_REGISTRY_TABLE"]] = self.frame(release_registry())
        for kind, contract in self.profile["LOOKUP_CONTRACTS"].items():
            sources[contract["source_table"]] = self.frame([
                {"CONTENT_ID": key, "CURATED_JSON": json.dumps(payload)} for key, payload in lookups[kind].items()])
        contracts = [model["STORAGE_CONTRACT"] for model in self.defaults["MODEL_CONTRACTS"].values()
                     if (model.get("STORAGE_CONTRACT") or {}).get("VERIFIED") is True]
        self.session = NotebookSession(self.actual, sources, contracts)
        self.addCleanup(self.session.db.close)

    def frame(self, rows):
        names = list(dict.fromkeys(name for row in rows for name in row))
        schema = self.types.StructType([
            self.types.StructField(name, self.types.BooleanType() if name in {"IS_ACTIVE", "IS_COLLECTION"} else
                                   self.types.LongType() if name == "PROCESS_ORDER" else self.types.StringType())
            for name in names])
        return self.actual.create_dataframe([tuple(row.get(name) for name in names) for row in rows], schema=schema)

    @contextlib.contextmanager
    def notebook_transport(self):
        original_open = builtins.open
        original_write = self.smoke.DataFrame.write
        session, schema_prefix = self.session, self.contract["TARGET_DIM"].rsplit(".", 1)[0] + ".TMP_OSCAL_"

        def mapping_open(path, *args, **kwargs):
            return original_open(ROOT / "Mapping/ARCHER_OSCAL_MAPPINGS.csv" if str(path) == "ARCHER_OSCAL_MAPPINGS.csv" else path,
                                 *args, **kwargs)

        class Writer:
            def __init__(self, frame):
                self.frame = frame
            def save_as_table(self, name, **kwargs):
                if not name.startswith(schema_prefix):
                    return original_write.fget(self.frame).save_as_table(name, **kwargs)
                rows = [row.as_dict() for row in self.frame.collect()]
                for row in rows:
                    for key, value in row.items():
                        if isinstance(value, (datetime.datetime, datetime.date)):
                            row[key] = value.isoformat()
                return storage.Frame(session, rows, self.frame.columns).save_as_table(name, **kwargs)

        with self.smoke.sql_boundaries(), patch("snowflake.snowpark.context.get_active_session", return_value=session), \
                patch("builtins.open", side_effect=mapping_open), patch.object(self.smoke.DataFrame, "write", property(Writer)):
            yield

    def run_notebook(self, models=("SSP",)):
        ns = {}
        with self.notebook_transport(), contextlib.redirect_stdout(io.StringIO()):
            for path in sorted(CELLS.glob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in tree.body:
                    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SELECTED_MODELS" for t in node.targets):
                        node.value = ast.parse(repr(models), mode="eval").body
                try:
                    exec(compile(ast.fix_missing_locations(tree), str(path), "exec"), ns)
                except Exception as error:
                    raise AssertionError(f"{path.name}: {getattr(error, 'report', str(error))}") from error.__context__
        return ns

    def test_all_seven_cells_full_csv_preview_commit_and_unchanged_retry(self):
        ns = self.run_notebook()
        self.assertEqual("PREVIEW_COMPLETE", ns["PIPELINE_REPORT"]["status"])
        self.assertFalse(ns["PIPELINE_REPORT"]["writes_executed"])
        self.assertEqual(48, len(ns["MAPPING_CONTEXTS"][0]["mapping_rows"]))
        dim = self.contract["TARGET_DIM"]
        self.assertEqual([], self.session.query("SELECT * FROM " + dim))
        graph = ns["MODEL_GRAPHS"][("source-one", "SSP")]
        payloads = [json.loads(row["METADATA_JSON"]) for row in graph["nodes"].collect()]
        self.assertTrue(any(payload.get("title") == "Tool" for payload in payloads))
        self.assertTrue(any(payload.get("state") == "operational" for payload in payloads))
        self.assertTrue(any(payload.get("security-sensitivity-level") == self.source["SECURITY_CATEGORY"] for payload in payloads))
        self.assertTrue(any(payload.get("party-uuids") for payload in payloads))
        with self.notebook_transport():
            _, first = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
            saved = self.session.query("SELECT * FROM " + dim)
            self.assertEqual("COMMITTED_AND_VERIFIED", first["status"])
            self.assertGreater(len(saved), 20)
            _, repeated = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertEqual(saved, self.session.query("SELECT * FROM " + dim))
        self.assertEqual(0, repeated["groups"][0]["load"]["expected_changes"]["D"]["UPDATES"])
        self.assertEqual(0, repeated["groups"][0]["load"]["expected_changes"]["F"]["INSERTS"])

    def test_both_models_preview_and_explicitly_targetless_ar_blocks_all_commits(self):
        ns = self.run_notebook(("SSP", "ASSESSMENT_RESULTS"))
        self.assertEqual(2, len(ns["MODEL_GRAPHS"]))
        self.assertEqual([48, 32], [len(context["mapping_rows"]) for context in ns["MAPPING_CONTEXTS"]])
        self.assertTrue(all(group["load"]["storage_verified"] for group in ns["PIPELINE_REPORT"]["groups"]))
        ns["MAPPING_CONTEXTS"][1]["config"]["STORAGE_CONTRACT"] = None
        with self.notebook_transport():
            _, preview = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "PREVIEW")
        self.assertEqual("MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING", preview["groups"][1]["load"]["status"])
        self.session.events.clear()
        with self.notebook_transport(), self.assertRaises(ns["PipelineError"]):
            ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertFalse(any(event.startswith("MERGE") for event in self.session.events))

    def test_ar_only_preview_insert_update_and_unchanged_commit(self):
        ns = self.run_notebook(("ASSESSMENT_RESULTS",))
        context = ns["MAPPING_CONTEXTS"][0]
        contract = context["config"]["STORAGE_CONTRACT"]
        dim, fact = contract["TARGET_DIM"], contract["TARGET_FACT"]
        pk = contract["DIM_PK_COLUMN"]
        self.assertEqual("PREVIEW_PASSED_NO_TARGET_DML", ns["PIPELINE_REPORT"]["groups"][0]["load"]["status"])
        self.assertEqual((34, 33), tuple(ns["PIPELINE_REPORT"]["groups"][0]["load"][key] for key in ("nodes", "edges")))
        self.assertEqual([], self.session.query("SELECT * FROM " + dim))
        with self.notebook_transport():
            _, inserted = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertEqual("COMMITTED_AND_VERIFIED", inserted["status"])
        self.assertEqual(34, inserted["groups"][0]["load"]["expected_changes"]["D"]["INSERTS"])
        self.assertEqual(33, inserted["groups"][0]["load"]["expected_changes"]["F"]["INSERTS"])
        saved = {row[pk]: row for row in self.session.query("SELECT * FROM " + dim)}
        saved_edges = self.session.query("SELECT * FROM " + fact)
        self.assertTrue(all(isinstance(key, bytes) and len(key) == 16 for key in saved))
        self.assertTrue(all(len(row["OSCAL_UUID"]) == 32 and "-" not in row["OSCAL_UUID"] for row in saved.values()))
        self.assertTrue(all(row["DW_LOAD_TIMESTAMP"] and row["DW_LOAD_TIMESTAMP_TZ"] for row in saved.values()))
        for edge in saved_edges:
            self.assertIn(edge["FK_SOURCE_ELEMENT_HASH"], saved)
            self.assertIn(edge["FK_TARGET_ELEMENT_HASH"], saved)
            self.assertEqual(saved[edge["FK_SOURCE_ELEMENT_HASH"]]["OSCAL_UUID"], edge["SOURCE_OSCAL_UUID"])
            self.assertEqual(saved[edge["FK_TARGET_ELEMENT_HASH"]]["OSCAL_UUID"], edge["TARGET_OSCAL_UUID"])
        changed_source = dict(self.source, ADJUSTED_TOTAL_RISK_SCORE=7.25)
        ns["SOURCE_INPUTS"]["source-one"]["source_df"] = self.frame([
            {"SOURCE_RECORD_ID": "synthetic-record", "CURATED_JSON": json.dumps(changed_source)}])
        context["config"]["RUN_ID"] = "ar-changed"
        with self.notebook_transport():
            _, changed = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertEqual("COMMITTED_AND_VERIFIED", changed["status"])
        self.assertEqual({"INSERTS": 0, "UPDATES": 1, "UNCHANGED": 33}, changed["groups"][0]["load"]["expected_changes"]["D"])
        saved_changed = {row[pk]: row for row in self.session.query("SELECT * FROM " + dim)}
        self.assertEqual(set(saved), set(saved_changed))
        self.assertEqual(saved_edges, self.session.query("SELECT * FROM " + fact))
        updated = [row for key, row in saved_changed.items() if row != saved[key]]
        self.assertEqual(1, len(updated))
        self.assertEqual([{"name": "adjusted-total-risk-score", "value": "7.25"}], json.loads(updated[0]["METADATA_JSON"])["props"])
        self.assertEqual("ar-changed", updated[0]["DW_PIPELINE_RUN_ID"])
        context["config"]["RUN_ID"] = "ar-unchanged"
        with self.notebook_transport():
            _, repeated = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertEqual("COMMITTED_AND_VERIFIED", repeated["status"])
        self.assertEqual({"INSERTS": 0, "UPDATES": 0, "UNCHANGED": 34}, repeated["groups"][0]["load"]["verification"]["DIM"])
        self.assertEqual(saved_changed, {row[pk]: row for row in self.session.query("SELECT * FROM " + dim)})
        self.assertEqual(saved_edges, self.session.query("SELECT * FROM " + fact))
        for table in (self.contract["TARGET_DIM"], self.contract["TARGET_FACT"]):
            self.assertEqual([], self.session.query("SELECT * FROM " + table))
            self.assertFalse(any(sql.startswith("MERGE INTO " + table + " ") for sql in self.session.events))
        self.assertFalse(ns["CONFIG"]["EXECUTE_WRITES"])

    def test_ar_schema_must_match_shared_ssp_layout_before_any_commit(self):
        ns = self.run_notebook(("ASSESSMENT_RESULTS",))
        dim = ns["MAPPING_CONTEXTS"][0]["config"]["STORAGE_CONTRACT"]["TARGET_DIM"]
        original = copy.deepcopy(self.session.schema[dim])
        for mismatch in ("ntz", "missing_tz"):
            self.session.schema[dim] = copy.deepcopy(original)
            if mismatch == "ntz":
                next(row for row in self.session.schema[dim] if row["name"] == "DW_LOAD_TIMESTAMP")["type"] = "TIMESTAMP_NTZ(9)"
            else:
                self.session.schema[dim] = [row for row in self.session.schema[dim] if row["name"] != "DW_LOAD_TIMESTAMP_TZ"]
            self.session.events.clear()
            with self.subTest(mismatch=mismatch), self.notebook_transport(), self.assertRaises(ns["PipelineError"]) as caught:
                ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
            self.assertEqual("TARGET_SCHEMA_MISMATCH", caught.exception.report["load_error"]["status"])
            self.assertFalse(caught.exception.report["commit_attempted"])
            self.assertFalse(any(sql.startswith("MERGE") for sql in self.session.events))
        self.session.schema[dim] = original

    def test_poam_only_preview_insert_unchanged_and_new_reference_isolates_models(self):
        from test_poam_references import poam_registry
        baseline = self.run_notebook(("SSP", "ASSESSMENT_RESULTS"))
        with self.notebook_transport():
            _, accepted = baseline["run_oscal_pipeline"](
                baseline["SOURCE_INPUTS"], baseline["MAPPING_CONTEXTS"], "COMMIT")
        self.assertEqual("COMMITTED_AND_VERIFIED", accepted["status"])
        unaffected = {context["config"]["STORAGE_CONTRACT"][key]: self.session.query(
            "SELECT * FROM " + context["config"]["STORAGE_CONTRACT"][key] + " ORDER BY 1")
            for context in baseline["MAPPING_CONTEXTS"] for key in ("TARGET_DIM", "TARGET_FACT")}
        self.assertTrue(all(unaffected.values()))
        self.session.sources[self.defaults["CONFIG"]["ELEMENT_REGISTRY_TABLE"]] = self.frame(
            release_registry() + poam_registry())
        source = dict(self.source, POAMS=[{"ContentId": "201", "LevelId": 9}, 202])
        self.session.sources[self.profile["RAW_TABLE"]] = self.frame([
            {"CONTENT_ID": "synthetic-record", "CURATED_JSON": json.dumps(source)}])
        self.session.events.clear()
        ns = self.run_notebook(("POAM",))
        context = ns["MAPPING_CONTEXTS"][0]
        contract = context["config"]["STORAGE_CONTRACT"]
        dim, fact = contract["TARGET_DIM"], contract["TARGET_FACT"]
        pk, edge_pk = contract["DIM_PK_COLUMN"], contract["FACT_PK_COLUMN"]
        preview = ns["PIPELINE_REPORT"]["groups"][0]["load"]
        self.assertEqual("PREVIEW_PASSED_NO_TARGET_DML", preview["status"])
        self.assertEqual((3, 2), (preview["nodes"], preview["edges"]))
        self.assertEqual([], self.session.query("SELECT * FROM " + dim))
        self.assertEqual([], self.session.query("SELECT * FROM " + fact))
        self.assertFalse(any(sql.startswith("MERGE") for sql in self.session.events))
        with self.notebook_transport():
            _, inserted = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertEqual("COMMITTED_AND_VERIFIED", inserted["status"])
        load = inserted["groups"][0]["load"]
        for kind, label, count in (("D", "DIM", 3), ("F", "FACT", 2)):
            self.assertEqual({"INSERTS": count, "UPDATES": 0, "UNCHANGED": 0}, load["expected_changes"][kind])
            self.assertEqual({"INSERTS": 0, "UPDATES": 0, "UNCHANGED": count}, load["verification"][label])
        saved = {row[pk]: row for row in self.session.query("SELECT * FROM " + dim)}
        saved_edges = {row[edge_pk]: row for row in self.session.query("SELECT * FROM " + fact)}
        for key, row in saved.items():
            self.assertIsInstance(key, bytes)
            self.assertEqual(16, len(key))
            self.assertEqual(32, len(row["OSCAL_UUID"]))
            payload = json.loads(row["METADATA_JSON"])
            self.assertEqual({"uuid"}, set(payload))
            self.assertEqual(row["OSCAL_UUID"], payload["uuid"].replace("-", ""))
            self.assertTrue(row["DW_LOAD_TIMESTAMP"] and row["DW_LOAD_TIMESTAMP_TZ"])
        for key, edge in saved_edges.items():
            self.assertIsInstance(key, bytes)
            self.assertEqual(16, len(key))
            for endpoint in ("SOURCE", "TARGET"):
                self.assertEqual(saved[edge["FK_" + endpoint + "_ELEMENT_HASH"]]["OSCAL_UUID"],
                                 edge[endpoint + "_OSCAL_UUID"])
        context["config"]["RUN_ID"] = "poam-unchanged"
        with self.notebook_transport():
            _, repeated = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertEqual("COMMITTED_AND_VERIFIED", repeated["status"])
        for kind, count in (("D", 3), ("F", 2)):
            self.assertEqual({"INSERTS": 0, "UPDATES": 0, "UNCHANGED": count},
                             repeated["groups"][0]["load"]["expected_changes"][kind])
        self.assertEqual(saved, {row[pk]: row for row in self.session.query("SELECT * FROM " + dim)})
        self.assertEqual(saved_edges, {row[edge_pk]: row for row in self.session.query("SELECT * FROM " + fact)})
        source["POAMS"].append({"ContentId": 203, "LevelId": 9})
        ns["SOURCE_INPUTS"]["source-one"]["source_df"] = self.frame([
            {"SOURCE_RECORD_ID": "synthetic-record", "CURATED_JSON": json.dumps(source)}])
        context["config"]["RUN_ID"] = "poam-new-reference"
        with self.notebook_transport():
            _, changed = ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertEqual("COMMITTED_AND_VERIFIED", changed["status"])
        load = changed["groups"][0]["load"]
        for kind, label, previous in (("D", "DIM", 3), ("F", "FACT", 2)):
            self.assertEqual({"INSERTS": 1, "UPDATES": 0, "UNCHANGED": previous}, load["expected_changes"][kind])
            self.assertEqual({"INSERTS": 0, "UPDATES": 0, "UNCHANGED": previous + 1}, load["verification"][label])
        final_nodes = {row[pk]: row for row in self.session.query("SELECT * FROM " + dim)}
        final_edges = {row[edge_pk]: row for row in self.session.query("SELECT * FROM " + fact)}
        self.assertEqual(saved, {key: final_nodes[key] for key in saved})
        self.assertEqual(saved_edges, {key: final_edges[key] for key in saved_edges})
        self.assertEqual(["poam-new-reference"], [row["DW_PIPELINE_RUN_ID"]
                         for key, row in final_nodes.items() if key not in saved])
        for table, rows in unaffected.items():
            self.assertEqual(rows, self.session.query("SELECT * FROM " + table + " ORDER BY 1"))
            self.assertFalse(any(sql.startswith("MERGE INTO " + table + " ") for sql in self.session.events))
        self.assertFalse(ns["CONFIG"]["EXECUTE_WRITES"])

    def test_many_records_keep_exact_coverage_and_record_scoped_links(self):
        rows = [{"CONTENT_ID": f"record-{index:03d}", "CURATED_JSON": json.dumps(self.source)} for index in range(32)]
        self.session.sources[self.profile["RAW_TABLE"]] = self.frame(rows)
        ns = self.run_notebook()
        graph = ns["MODEL_GRAPHS"][("source-one", "SSP")]
        nodes = {row["NODE_KEY"]: row.as_dict() for row in graph["nodes"].collect()}
        roots = [row for row in nodes.values() if row["PARENT_NODE_PATH"] is None]
        self.assertEqual(32, len(roots))
        self.assertEqual({row["CONTENT_ID"] for row in rows}, {row["SOURCE_RECORD_ID"] for row in roots})
        for edge in graph["edges"].collect():
            self.assertEqual(nodes[edge["FK_SOURCE_ELEMENT_HASH"]]["SOURCE_RECORD_ID"],
                             nodes[edge["FK_TARGET_ELEMENT_HASH"]]["SOURCE_RECORD_ID"])
        self.assertEqual(32, ns["SOURCE_INPUTS"]["source-one"]["selection"]["SELECTED_ROWS"])
        self.assertEqual("PREVIEW_COMPLETE", ns["PIPELINE_REPORT"]["status"])


if __name__ == "__main__":
    unittest.main()
