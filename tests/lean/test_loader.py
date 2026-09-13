"""Loader graph, generated SQL and transaction faults.

SQLite executes relational queries; the small MERGE adapter exercises their
change predicate and assignments. This is not Snowflake integration evidence.
"""
import copy
import json
import os
from pathlib import Path
import re
import runpy
import sqlite3
import unittest
from unittest.mock import patch

CELLS = Path(os.environ.get("LEAN_CELLS_DIR", Path(__file__).resolve().parents[2] / "notebooks/cells"))
P = runpy.run_path(str(CELLS / "06_validation_and_guarded_loader.py"))
G = P["validate_and_load_oscal"].__globals__
Error = P["LoadError"]


def config():
    storage = dict(VERIFIED=True, MODEL_KEY="DEMO", ROOT_PATH="demo", ROOT_ELEMENT_TYPE="demo",
                   SOURCE_SYSTEM_NAME="ARCHER", SOURCE_TABLE_NAME="SOURCE", RAW_TABLE="DEV.RAW.SOURCE",
                   IDENTITY_VERSION="v1_registry_path_instance", TARGET_DIM="DEV.DEMO.DIM",
                   TARGET_FACT="DEV.DEMO.FACT", DIM_PK_COLUMN="PK_NODE", FACT_PK_COLUMN="PK_EDGE",
                   PHYSICAL_PROFILE="BINARY16_UUID32")
    return dict(storage, OSCAL_MODEL="DEMO", STORAGE_CONTRACT=storage, EXECUTE_WRITES=False,
                EXPECTED_SOURCE_RECORDS=1)


def graph():
    nodes = []
    for number, path, parent in ((1, "demo", None), (2, "demo.section", "demo"),
                                 (3, "demo.section.items[]", "demo.section")):
        nodes.append(dict(NODE_KEY=f"{number:032x}", ELEMENT_PATH=path, PARENT_NODE_PATH=parent,
                          ELEMENT_TYPE=path.split(".")[-1].replace("[]", ""), INSTANCE_KEY=str(number),
                          PARENT_INSTANCE_KEY=None if number == 1 else str(number-1),
                          OSCAL_UUID=f"00000000-0000-5000-8000-{number:012x}", METADATA_JSON='{"value":"new"}',
                          SOURCE_SYSTEM_NAME="ARCHER", SOURCE_TABLE_NAME="SOURCE", SOURCE_RECORD_ID="record",
                          DW_PIPELINE_RUN_ID="new", DW_LOAD_TIMESTAMP="2026-09-13T00:00:00+00:00",
                          DW_LOAD_TIMESTAMP_TZ="2026-09-13T00:00:00+00:00"))
    edges = [dict(EDGE_KEY=f"{i+10:032x}", FK_SOURCE_ELEMENT_HASH=nodes[i]["NODE_KEY"],
                  FK_TARGET_ELEMENT_HASH=nodes[i+1]["NODE_KEY"], DEPENDENCY_TYPE="CONTAINS",
                  SOURCE_OSCAL_UUID=nodes[i]["OSCAL_UUID"], TARGET_OSCAL_UUID=nodes[i+1]["OSCAL_UUID"])
             for i in range(2)]
    return nodes, edges


class Frame:
    def __init__(self, session, rows, columns=None):
        self.session, self.rows, self.write = session, rows, self
        self.columns = columns or (tuple(rows[0]) if rows else ())
    def to_local_iterator(self):
        return iter(copy.deepcopy(self.rows))
    def save_as_table(self, name, **kwargs):
        columns = self.columns
        self.session.query(f"CREATE TEMPORARY TABLE {name} ({', '.join(columns)})")
        sql = self.session.translate(f"INSERT INTO {name} VALUES ({','.join('?' for _ in columns)})")
        self.session.db.executemany(sql, [tuple(row.get(column) for column in columns) for row in self.rows])


class Session:
    def __init__(self, fail=None):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.events, self.fail, self.seen = [], fail, {}
        self.db.create_function("TO_BINARY", 2, lambda value, fmt: bytes.fromhex(value))
        self.db.create_function("PARSE_JSON", 1, lambda value: json.dumps(json.loads(value), sort_keys=True))
        self.db.create_function("IS_OBJECT", 1, lambda value: value is not None and isinstance(json.loads(value), dict))
        class CountIf:
            def __init__(self): self.n = 0
            def step(self, value): self.n += bool(value)
            def finalize(self): return self.n
        self.db.create_aggregate("COUNT_IF", 1, CountIf)
        self.schema = {}
        for table, pk, fields, kind in (("DEV.DEMO.DIM", "PK_NODE", P["_DIM_FIELDS"], "DIM"),
                                       ("DEV.DEMO.FACT", "PK_EDGE", P["_FACT_FIELDS"], "FACT")):
            self.schema[table] = [{"name": name, "type": dtype, "kind": "COLUMN", "expression": None,
                                   "null?": "N" if kind == "FACT" or name == pk else "Y"}
                                  for name, dtype in {pk: "BINARY(16)", **fields}.items()]
            self.db.execute(self.translate(f"CREATE TABLE {table} ({', '.join(row['name'] for row in self.schema[table])})"))
    def translate(self, statement):
        statement = re.sub(r"CAST\((\w+) AS TIMESTAMP_TZ\(9\)\)", r"\1", statement)
        return re.sub(r"\b[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*\b",
                      lambda match: '"' + match[0].replace(".", "__") + '"', statement)
    def table(self, name):
        return Frame(self, self.query("SELECT * FROM " + name))
    def sql(self, statement):
        owner = self
        class Query:
            def collect(self): return owner.query(statement)
        return Query()
    def query(self, statement):
        self.events.append(statement)
        kind = "DIM_MERGE" if statement.startswith("MERGE INTO DEV.DEMO.DIM") else (
            "FACT_MERGE" if statement.startswith("MERGE INTO DEV.DEMO.FACT") else statement.split()[0])
        self.seen[kind] = self.seen.get(kind, 0) + 1
        if self.fail and self.fail == (kind, self.seen[kind]):
            raise RuntimeError("private source statement")
        if statement.startswith("SELECT CURRENT_TRANSACTION()"):
            return [{"TX": "active" if self.db.in_transaction else None}]
        if statement.startswith("DESC TABLE "):
            return copy.deepcopy(self.schema[statement[11:]])
        if " MINUS " in statement:
            left, right = statement[len("SELECT COUNT(*) AS N FROM (("):-2].split(") MINUS (")
            return [{"N": len({tuple(r.values()) for r in self.query(left)} - {tuple(r.values()) for r in self.query(right)})}]
        if statement.startswith("MERGE INTO "):
            m = re.fullmatch(r"MERGE INTO (\S+) t USING (\S+) s ON t\.(\w+)=s\.\3 WHEN MATCHED AND \((.+)\) THEN UPDATE SET (.+) WHEN NOT MATCHED THEN INSERT \((.+)\) VALUES \((.+)\)", statement)
            if not m:
                raise AssertionError("Unexpected MERGE grammar")
            target, stage, pk, changed, _, columns, _ = m.groups()
            updated = self.query(f"SELECT COUNT(*) AS N FROM {target} t JOIN {stage} s ON t.{pk}=s.{pk} WHERE {changed}")[0]["N"]
            inserted = self.query(f"SELECT COUNT(*) AS N FROM {stage} s WHERE NOT EXISTS (SELECT 1 FROM {target} t WHERE t.{pk}=s.{pk})")[0]["N"]
            assignments = ",".join(f"{name}=(SELECT s.{name} FROM {stage} s WHERE s.{pk}=t.{pk})" for name in columns.split(", ") if name != pk)
            self.query(f"UPDATE {target} AS t SET {assignments} WHERE EXISTS (SELECT 1 FROM {stage} s WHERE s.{pk}=t.{pk} AND ({changed}))")
            self.query(f"INSERT INTO {target} ({columns}) SELECT {columns} FROM {stage} s WHERE NOT EXISTS (SELECT 1 FROM {target} t WHERE t.{pk}=s.{pk})")
            return [{"number of rows inserted": inserted, "number of rows updated": updated}]
        cursor = self.db.execute(self.translate(statement))
        return [dict(row) for row in cursor.fetchall()] if cursor.description else []


class GraphContract(unittest.TestCase):
    def test_targetless_preview_uses_no_session_and_commit_rejects(self):
        cfg = dict(config(), STORAGE_CONTRACT=None)
        nodes, edges = graph()
        result = P["validate_and_load_oscal"](nodes, edges, cfg)
        self.assertEqual((3, 2, False), (result["nodes"], result["edges"], result["writes_executed"]))
        with self.assertRaisesRegex(Error, "STORAGE_CONTRACT_NOT_VERIFIED"):
            P["validate_and_load_oscal"](nodes, edges, dict(cfg, EXECUTE_WRITES=True))
    def test_graph_corruptions_reject(self):
        cases = [lambda n,e: n.append(copy.deepcopy(n[0])), lambda n,e: e.append(copy.deepcopy(e[0])),
                 lambda n,e: n[0].update(NODE_KEY=None), lambda n,e: n[1].update(SOURCE_RECORD_ID="other"),
                 lambda n,e: n[1].update(METADATA_JSON="[]"), lambda n,e: n[1].update(OSCAL_UUID=n[0]["OSCAL_UUID"]),
                 lambda n,e: e[0].update(FK_TARGET_ELEMENT_HASH="f"*32), lambda n,e: e.pop(),
                 lambda n,e: e[0].update(TARGET_OSCAL_UUID=n[0]["OSCAL_UUID"]),
                 lambda n,e: n[2].update(PARENT_INSTANCE_KEY="wrong"), lambda n,e: n[2].pop("PARENT_NODE_PATH"),
                 lambda n,e: n[2].update(PARENT_NODE_PATH="demo"), lambda n,e: n[0].update(SOURCE_SYSTEM_NAME="OTHER")]
        for change in cases:
            with self.subTest(change=change):
                nodes, edges = graph()
                change(nodes, edges)
                with self.assertRaises(Error): P["_load_graph"](nodes, edges, config())
    def test_future_model_is_only_configuration(self):
        cfg = config()
        self.assertEqual("DEV.DEMO.DIM", P["_load_storage"](cfg)["TARGET_DIM"])
        cfg["STORAGE_CONTRACT"]["PHYSICAL_PROFILE"] = "EXOTIC"
        with self.assertRaisesRegex(Error, "UNSUPPORTED_STORAGE_PROFILE"): P["_load_storage"](cfg)
    def test_registry_controls_non_root_element_type(self):
        nodes, edges = graph()
        nodes[1]["ELEMENT_TYPE"] = "section-assembly"
        nodes[2]["ELEMENT_TYPE"] = "individual-item"
        result = P["_load_graph"](nodes, edges, config())
        self.assertEqual((3, 2), (result["nodes"], result["edges"]))
    def test_nonfinite_nested_payloads_reject_in_targetless_preview(self):
        cfg = dict(config(), STORAGE_CONTRACT=None)
        for payload in ('{"nested":[NaN]}', '{"nested":{"v":Infinity}}', '{"v":-Infinity}',
                        '{"v":1e400}', {"nested": [float("nan")]}, {"nested": {"v": float("inf")}}):
            with self.subTest(payload=payload):
                nodes, edges = graph()
                nodes[1]["METADATA_JSON"] = payload
                with self.assertRaisesRegex(Error, "INVALID_NODE_PAYLOAD"):
                    P["validate_and_load_oscal"](nodes, edges, cfg)
    def test_compact_hash_case_does_not_change_binary_identity(self):
        nodes, edges = graph()
        nodes[1]["NODE_KEY"] = "abcdef0123456789abcdef0123456789"
        edges[0]["FK_TARGET_ELEMENT_HASH"] = nodes[1]["NODE_KEY"].upper()
        edges[1]["FK_SOURCE_ELEMENT_HASH"] = nodes[1]["NODE_KEY"].upper()
        self.assertEqual(3, P["_load_graph"](nodes, edges, config())["nodes"])
        nodes.append(dict(nodes[1], NODE_KEY=nodes[1]["NODE_KEY"].upper()))
        with self.assertRaisesRegex(Error, "DUPLICATE_NODE_KEY"):
            P["_load_graph"](nodes, edges, config())


class LoadBehavior(unittest.TestCase):
    def setUp(self):
        self.s = Session()
        self.addCleanup(self.s.db.close)
        self.patch = patch.dict(G, {"session": self.s})
        self.patch.start()
        self.addCleanup(self.patch.stop)
    def run_loader(self, commit=False, nodes=None, edges=None):
        n, e = graph()
        return P["validate_and_load_oscal"](Frame(self.s, n if nodes is None else nodes, tuple(n[0])),
                    Frame(self.s, e if edges is None else edges, tuple(e[0])), dict(config(), EXECUTE_WRITES=commit))
    def test_preview_then_insert_update_and_unchanged_repeat(self):
        self.assertEqual("PREVIEW_PASSED_NO_TARGET_DML", self.run_loader()["status"])
        self.assertFalse(any(sql.startswith("MERGE") for sql in self.s.events))
        self.assertEqual("COMMITTED_AND_VERIFIED", self.run_loader(True)["status"])
        n, e = graph()
        n[1]["METADATA_JSON"] = '{"value":"changed"}'
        n[1]["DW_PIPELINE_RUN_ID"] = "updated"
        changed = self.run_loader(True, n, e)
        self.assertEqual((0, 1), (changed["expected_changes"]["D"]["INSERTS"], changed["expected_changes"]["D"]["UPDATES"]))
        n[0]["DW_PIPELINE_RUN_ID"] = "ignored"
        repeated = self.run_loader(True, n, e)
        self.assertEqual(0, repeated["expected_changes"]["D"]["UPDATES"])
        self.assertEqual("new", self.s.query("SELECT DW_PIPELINE_RUN_ID FROM DEV.DEMO.DIM WHERE ELEMENT_TYPE='demo'")[0]["DW_PIPELINE_RUN_ID"])
        active = False
        for sql in self.s.events:
            if sql == "BEGIN TRANSACTION": active = True
            elif sql in ("COMMIT", "ROLLBACK"): active = False
            elif active: self.assertFalse(sql.startswith(("CREATE", "ALTER", "DROP")))
    def test_wrong_live_schema_blocks_before_temporary_ddl(self):
        self.s.schema["DEV.DEMO.DIM"][0]["type"] = "VARCHAR(32)"
        with self.assertRaisesRegex(Error, "TARGET_SCHEMA_MISMATCH"): self.run_loader(True)
        self.assertFalse(any(sql.startswith("CREATE") for sql in self.s.events))
    def test_existing_transaction_blocks_before_ddl(self):
        self.s.query("BEGIN TRANSACTION")
        with self.assertRaisesRegex(Error, "EXISTING_TRANSACTION"): self.run_loader(True)
        self.assertFalse(any(sql.startswith("CREATE") for sql in self.s.events))
    def test_fact_failure_rolls_back_both_tables_and_proves_baseline(self):
        self.s.fail = ("FACT_MERGE", 1)
        with self.assertRaisesRegex(Error, "TRANSACTION_ROLLED_BACK") as caught: self.run_loader(True)
        self.assertTrue(caught.exception.details["rollback_readback_verified"])
        self.assertFalse(caught.exception.details["writes_executed"])
        self.assertEqual(0, self.s.query("SELECT COUNT(*) AS N FROM DEV.DEMO.DIM")[0]["N"])
        self.assertNotIn("private", str(caught.exception.details))
    def test_commit_failure_is_unknown_and_does_not_rollback_or_retry(self):
        self.s.fail = ("COMMIT", 1)
        with self.assertRaisesRegex(Error, "COMMIT_OUTCOME_UNKNOWN_DO_NOT_RETRY") as caught: self.run_loader(True)
        self.assertEqual("UNKNOWN", caught.exception.details["persisted"])
        self.assertNotIn("ROLLBACK", self.s.events)
        self.assertEqual(1, self.s.seen["DIM_MERGE"])
    def test_postcommit_readback_failure_preserves_committed_true(self):
        verify = G["_load_verify"]
        calls = []
        def fail_after_commit(context):
            calls.append(1)
            if len(calls) == 2: raise RuntimeError("private")
            return verify(context)
        with patch.dict(G, {"_load_verify": fail_after_commit}):
            with self.assertRaisesRegex(Error, "POST_COMMIT_READBACK_FAILED") as caught: self.run_loader(True)
        self.assertTrue(caught.exception.details["committed"])
        self.assertTrue(caught.exception.details["writes_executed"])
    def test_obsolete_and_damaged_parent_rows_block(self):
        self.run_loader(True)
        n, e = graph()
        with self.assertRaisesRegex(Error, "OBSOLETE_TARGET_ROWS_BLOCKED"):
            self.run_loader(False, n[:2], e[:1])
        self.s.query("DELETE FROM DEV.DEMO.FACT")
        with self.assertRaisesRegex(Error, "TARGET_WRONG_PARENT_COUNT"): self.run_loader(False)
    def test_foreign_owned_key_cannot_hide_and_no_followup_merge_runs(self):
        self.run_loader(True)
        self.s.query("UPDATE DEV.DEMO.DIM SET SOURCE_SYSTEM_NAME='OTHER' WHERE ELEMENT_TYPE='section'")
        before = self.s.seen["DIM_MERGE"]
        with self.assertRaisesRegex(Error, "TARGET_IDENTITY_PROVENANCE_CONFLICT"): self.run_loader(True)
        self.assertEqual(before, self.s.seen["DIM_MERGE"])
    def test_absent_record_is_preserved_byte_for_byte(self):
        self.run_loader(True)
        n, e = graph()
        n[0]["SOURCE_RECORD_ID"] = "absent"
        n[0]["NODE_KEY"] = "f" * 32
        columns = tuple(row["name"] for row in self.s.schema["DEV.DEMO.DIM"])
        before = self.s.query("SELECT * FROM DEV.DEMO.DIM WHERE ELEMENT_TYPE='demo'")[0]
        before.update(PK_NODE=b"\xff" * 16, SOURCE_RECORD_ID="absent")
        self.s.db.execute(self.s.translate(f"INSERT INTO DEV.DEMO.DIM VALUES ({','.join('?' for _ in columns)})"), tuple(before[name] for name in columns))
        self.run_loader(True)
        self.assertEqual(before, self.s.query("SELECT * FROM DEV.DEMO.DIM WHERE SOURCE_RECORD_ID='absent'")[0])
    def test_cross_scope_incoming_edge_is_not_ignored(self):
        self.run_loader(True)
        self.s.query("UPDATE DEV.DEMO.FACT SET FK_SOURCE_ELEMENT_HASH=TO_BINARY('ffffffffffffffffffffffffffffffff','HEX') WHERE PK_EDGE=TO_BINARY('0000000000000000000000000000000a','HEX')")
        with self.assertRaisesRegex(Error, "TARGET_IDENTITY_PROVENANCE_CONFLICT"): self.run_loader(True)
    def test_capacity_failure_has_no_target_dml(self):
        n, e = graph()
        n[1]["DW_PIPELINE_RUN_ID"] = "x" * 65
        with self.assertRaisesRegex(Error, "TARGET_STRING_CAPACITY_EXCEEDED"): self.run_loader(True, n, e)
        self.assertFalse(any(sql.startswith("MERGE") for sql in self.s.events))
    def test_rollback_failure_is_unknown_and_does_not_retry(self):
        original = self.s.query
        def fail_both(statement):
            if statement.startswith("MERGE INTO DEV.DEMO.FACT") or statement == "ROLLBACK":
                raise RuntimeError("private")
            return original(statement)
        self.s.query = fail_both
        with self.assertRaisesRegex(Error, "ROLLBACK_OUTCOME_UNKNOWN_DO_NOT_RETRY") as caught: self.run_loader(True)
        self.assertEqual("UNKNOWN", caught.exception.details["persisted"])
        self.assertNotIn("COMMIT", self.s.events)
    def test_begin_failure_does_not_guess_a_rollback(self):
        self.s.fail = ("BEGIN", 1)
        with self.assertRaisesRegex(Error, "BEGIN_OUTCOME_UNKNOWN_DO_NOT_RETRY") as caught: self.run_loader(True)
        self.assertFalse(caught.exception.details["target_dml_attempted"])
        self.assertNotIn("ROLLBACK", self.s.events)
    def test_baseline_detects_duplicate_multiplicity_changes(self):
        self.run_loader(True)
        n, e = graph()
        context = P["_load_prepare"](Frame(self.s, n), Frame(self.s, e), config())
        self.s.query("INSERT INTO DEV.DEMO.DIM SELECT * FROM DEV.DEMO.DIM WHERE ELEMENT_TYPE='demo'")
        with self.assertRaisesRegex(Error, "TARGET_BASELINE_CHANGED"): P["_load_baseline"](context)
    def test_read_only_verification_checks_stored_values(self):
        self.run_loader(True)
        n, e = graph()
        self.assertEqual("LOAD_VERIFIED", P["verify_oscal_load"](Frame(self.s, n), Frame(self.s, e), config())["status"])
        self.s.query("UPDATE DEV.DEMO.DIM SET METADATA_JSON='{}' WHERE ELEMENT_TYPE='demo'")
        with self.assertRaisesRegex(Error, "SAVED_VALUES_OR_KEYS_DIFFER"):
            P["verify_oscal_load"](Frame(self.s, n), Frame(self.s, e), config())
    def test_root_only_graph_has_empty_fact_and_zero_change_counts(self):
        nodes, _ = graph()
        first = self.run_loader(True, nodes[:1], [])
        self.assertEqual((1, 0), (first["nodes"], first["edges"]))
        self.assertEqual({"INSERTS": 0, "UPDATES": 0, "UNCHANGED": 0}, first["verification"]["FACT"])
        self.assertEqual(0, self.run_loader(True, nodes[:1], [])["expected_changes"]["D"]["UPDATES"])
    def test_staging_uses_actual_binary_uuid_variant_and_timezone_types(self):
        # https://docs.snowflake.com/en/sql-reference/functions/to_binary
        # https://docs.snowflake.com/en/sql-reference/functions/parse_json
        self.run_loader(True)
        projected = "\n".join(sql for sql in self.s.events if sql.startswith("CREATE TEMPORARY TABLE") and " AS SELECT " in sql)
        for expression in ("TO_BINARY(NODE_KEY, 'HEX')", "TO_BINARY(EDGE_KEY, 'HEX')",
                           "TO_BINARY(FK_SOURCE_ELEMENT_HASH, 'HEX')", "TO_BINARY(FK_TARGET_ELEMENT_HASH, 'HEX')",
                           "REPLACE(OSCAL_UUID, '-', '')", "REPLACE(SOURCE_OSCAL_UUID, '-', '')",
                           "REPLACE(TARGET_OSCAL_UUID, '-', '')", "PARSE_JSON(METADATA_JSON)",
                           "CAST(DW_LOAD_TIMESTAMP AS TIMESTAMP_TZ(9))", "CAST(DW_LOAD_TIMESTAMP_TZ AS TIMESTAMP_TZ(9))"):
            self.assertIn(expression, projected)
        saved = self.s.query("SELECT * FROM DEV.DEMO.DIM WHERE ELEMENT_TYPE='demo'")[0]
        self.assertEqual(bytes.fromhex(graph()[0][0]["NODE_KEY"]), saved["PK_NODE"])
        self.assertEqual(graph()[0][0]["OSCAL_UUID"].replace("-", ""), saved["OSCAL_UUID"])
        self.assertEqual({"value": "new"}, json.loads(saved["METADATA_JSON"]))
        self.assertNotRegex(projected, r"\b(MD5|SHA2|TO_VARIANT)\s*\(")
    def test_reordered_json_object_is_unchanged_but_array_order_is_business_change(self):
        # VARIANT represents an object, rather than its serialized key order.
        # https://docs.snowflake.com/en/sql-reference/functions/parse_json
        nodes, edges = graph()
        nodes[1]["METADATA_JSON"] = '{"a":1,"b":[2,3]}'
        self.run_loader(True, nodes, edges)
        nodes[1]["METADATA_JSON"] = '{ "b": [2,3], "a": 1 }'
        nodes[1]["DW_PIPELINE_RUN_ID"] = "should-not-replace-audit"
        self.assertEqual(0, self.run_loader(True, nodes, edges)["expected_changes"]["D"]["UPDATES"])
        saved = self.s.query("SELECT DW_PIPELINE_RUN_ID FROM DEV.DEMO.DIM WHERE ELEMENT_TYPE='section'")[0]
        self.assertEqual("new", saved["DW_PIPELINE_RUN_ID"])
        nodes[1]["METADATA_JSON"] = '{"a":1,"b":[3,2]}'
        self.assertEqual(1, self.run_loader(True, nodes, edges)["expected_changes"]["D"]["UPDATES"])
    def test_snowflake_scope_does_not_use_correlated_exists_under_or(self):
        # Snowflake disallows correlated EXISTS as an OR argument.
        # https://docs.snowflake.com/en/sql-reference/operators-subquery
        self.run_loader()
        nodes, edges = graph()
        context = P["_load_prepare"](Frame(self.s, nodes), Frame(self.s, edges), config())
        for query in P["_load_scope"](context):
            self.assertNotIn("EXISTS", query.upper())
            self.assertIn("LEFT JOIN", query)
    def test_incorrect_merge_count_rolls_back_prior_successful_dml(self):
        query = self.s.query
        def wrong_count(statement):
            result = query(statement)
            if statement.startswith("MERGE INTO DEV.DEMO.FACT"):
                result[0]["number of rows inserted"] += 1
            return result
        self.s.query = wrong_count
        with self.assertRaisesRegex(Error, "TRANSACTION_ROLLED_BACK") as caught:
            self.run_loader(True)
        self.assertEqual("UNEXPECTED_MERGE_CHANGE_COUNT", caught.exception.details["cause"])
        self.assertTrue(caught.exception.details["rollback_readback_verified"])
        self.assertEqual(0, query("SELECT COUNT(*) AS N FROM DEV.DEMO.DIM")[0]["N"])
    def test_server_commit_then_lost_response_is_reported_unknown(self):
        query = self.s.query
        def lost_response(statement):
            result = query(statement)
            if statement == "COMMIT": raise ConnectionError("connection lost after server commit")
            return result
        self.s.query = lost_response
        with self.assertRaisesRegex(Error, "COMMIT_OUTCOME_UNKNOWN_DO_NOT_RETRY") as caught:
            self.run_loader(True)
        self.assertEqual("UNKNOWN", caught.exception.details["persisted"])
        self.assertTrue(caught.exception.details["target_dml_attempted"])
        self.assertEqual(3, query("SELECT COUNT(*) AS N FROM DEV.DEMO.DIM")[0]["N"])
        self.assertNotIn("ROLLBACK", self.s.events)
        self.assertEqual(1, self.s.seen["DIM_MERGE"])
    def test_rollback_readback_failure_is_unknown_and_no_automatic_retry(self):
        baseline = G["_load_baseline"]
        checks = []
        def uncertain_readback(context):
            checks.append(1)
            if len(checks) == 2: raise RuntimeError("private")
            return baseline(context)
        self.s.fail = ("FACT_MERGE", 1)
        with patch.dict(G, {"_load_baseline": uncertain_readback}):
            with self.assertRaisesRegex(Error, "ROLLBACK_READBACK_OUTCOME_UNKNOWN_DO_NOT_RETRY") as caught:
                self.run_loader(True)
        self.assertEqual("UNKNOWN", caught.exception.details["persisted"])
        self.assertNotIn("COMMIT", self.s.events)
        self.assertEqual(1, self.s.seen["DIM_MERGE"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
