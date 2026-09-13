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
    def __init__(self, actual, sources, contract):
        super().__init__()
        self.actual, self.sources = actual, sources
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
        def local_trim(column):
            # Snowflake's default TRIM removes spaces, not arbitrary whitespace.
            result = ColumnEmulator(data=[None if value is None else value.strip(" ") for value in column], index=column.index)
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
        self.session = NotebookSession(self.actual, sources, self.contract)
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
        self.assertEqual(47, len(ns["MAPPING_CONTEXTS"][0]["mapping_rows"]))
        dim = self.contract["TARGET_DIM"]
        self.assertEqual([], self.session.query("SELECT * FROM " + dim))
        graph = ns["MODEL_GRAPHS"][("source-one", "SSP")]
        payloads = [json.loads(row["METADATA_JSON"]) for row in graph["nodes"].collect()]
        self.assertTrue(any(payload.get("title") == "Tool" for payload in payloads))
        self.assertTrue(any(payload.get("state") == "operational" for payload in payloads))
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

    def test_both_models_preview_then_ar_destination_blocks_all_commits(self):
        ns = self.run_notebook(("SSP", "ASSESSMENT_RESULTS"))
        self.assertEqual(2, len(ns["MODEL_GRAPHS"]))
        self.assertEqual([47, 17], [len(context["mapping_rows"]) for context in ns["MAPPING_CONTEXTS"]])
        self.assertEqual("MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING", ns["PIPELINE_REPORT"]["groups"][1]["load"]["status"])
        self.session.events.clear()
        with self.notebook_transport(), self.assertRaises(ns["PipelineError"]):
            ns["run_oscal_pipeline"](ns["SOURCE_INPUTS"], ns["MAPPING_CONTEXTS"], "COMMIT")
        self.assertFalse(any(event.startswith("MERGE") for event in self.session.events))

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
