"""Relational selection and transaction-fault tests, not live Snowflake proof."""
from collections import Counter
from pathlib import Path
import runpy
import sqlite3
import unittest
from unittest.mock import patch


P = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      "notebooks/persistence/PILOT_SSP_ONE_RECORD_WRITE.py"))
PilotError = P["PilotError"]
DIM_PK = P["SSP_PILOT_DIM_PK"]
FACT_PK = P["SSP_PILOT_FACT_PK"]
SOURCE = P["SSP_PILOT_SOURCE"]
MERGES = ("MERGE INTO DEV.TEST.DIM d USING S s ON d.K=s.K WHEN NOT MATCHED THEN INSERT(K) VALUES(s.K)",
          "MERGE INTO DEV.TEST.FACT d USING S s ON d.K=s.K WHEN NOT MATCHED THEN INSERT(K) VALUES(s.K)")


def hex_key(number):
    return format(number, "032x")


class Row(dict):
    def as_dict(self):
        return dict(self)


class SqliteSession:
    def __init__(self, connection):
        self.connection = connection
        self.executed = []

    def sql(self, statement):
        parent = self

        class Plan:
            def collect(self):
                parent.executed.append(statement)
                cursor = parent.connection.execute(statement)
                names = [column[0] for column in cursor.description]
                return [Row(zip(names, row)) for row in cursor.fetchall()]
        return Plan()


class NewRecordSelection(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.create_function("TO_BINARY", 2,
                                lambda value, encoding: bytes.fromhex(value)
                                if encoding.upper() == "HEX" and value is not None else None)
        self.db.create_function("EQUAL_NULL", 2, lambda left, right: left == right)
        self.db.executescript(f"""
            CREATE TABLE GRAPH_NODES (NODE_KEY TEXT, ELEMENT_PATH TEXT,
                SOURCE_SYSTEM_NAME TEXT, SOURCE_TABLE_NAME TEXT, SOURCE_RECORD_ID TEXT);
            CREATE TABLE GRAPH_EDGES (EDGE_KEY TEXT, FK_SOURCE_ELEMENT_HASH TEXT,
                FK_TARGET_ELEMENT_HASH TEXT);
            CREATE TABLE TARGET_DIM ({DIM_PK} BLOB, SOURCE_SYSTEM_NAME TEXT,
                SOURCE_TABLE_NAME TEXT, SOURCE_RECORD_ID TEXT);
            CREATE TABLE TARGET_FACT ({FACT_PK} BLOB, FK_SOURCE_ELEMENT_HASH BLOB,
                FK_TARGET_ELEMENT_HASH BLOB);
        """)
        for source_id, base in (("10", 0xA0), ("20", 0xB0), ("30", 0xC0)):
            self.db.executemany("INSERT INTO GRAPH_NODES VALUES (?,?,?,?,?)", [
                (hex_key(base + 1), "system-security-plan", "ARCHER", SOURCE, source_id),
                (hex_key(base + 2), "system-security-plan.metadata", "ARCHER", SOURCE, source_id),
            ])
            self.db.execute("INSERT INTO GRAPH_EDGES VALUES (?,?,?)",
                            (hex_key(base + 3), hex_key(base + 1), hex_key(base + 2)))

    def select(self):
        function = P["_pilot_new_record_sql"]
        with patch.dict(function.__globals__, SSP_PILOT_DIM="TARGET_DIM", SSP_PILOT_FACT="TARGET_FACT"):
            statement = function("GRAPH_NODES", "GRAPH_EDGES")
        self.assertIn("TO_BINARY", statement.upper())
        cursor = self.db.execute(statement)
        names = [column[0] for column in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]

    def assert_selected(self, source_id):
        rows = self.select()
        self.assertEqual({source_id}, {row["SOURCE_RECORD_ID"] for row in rows})
        self.assertEqual(2, len(rows))
        self.assertEqual({"system-security-plan", "system-security-plan.metadata"},
                         {row["ELEMENT_PATH"] for row in rows})

    def dim(self, key, source_id="foreign", system="ARCHER", table=SOURCE):
        self.db.execute("INSERT INTO TARGET_DIM VALUES (?,?,?,?)",
                        (bytes.fromhex(key), system, table, source_id))

    def fact(self, key, source_key, target_key):
        self.db.execute("INSERT INTO TARGET_FACT VALUES (?,?,?)",
                        tuple(bytes.fromhex(value) for value in (key, source_key, target_key)))

    def test_selects_lowest_eligible_complete_record(self):
        self.assert_selected("10")

    def test_legacy_owned_record_excluded_even_with_disjoint_physical_keys(self):
        self.dim(hex_key(999), source_id="10")
        self.assert_selected("20")

    def test_ownership_requires_same_source_system_and_table(self):
        self.dim(hex_key(991), source_id="10", system="OTHER")
        self.dim(hex_key(992), source_id="10", table="OTHER_SOURCE")
        self.assert_selected("10")

    def test_child_dim_collision_excludes_record_using_binary_key_identity(self):
        self.db.execute("UPDATE GRAPH_NODES SET NODE_KEY=UPPER(NODE_KEY) WHERE SOURCE_RECORD_ID='10'")
        self.dim(hex_key(0xA2))
        self.assert_selected("20")

    def test_either_existing_fact_endpoint_collision_excludes_record(self):
        for endpoint in ("source", "target"):
            with self.subTest(endpoint=endpoint):
                self.db.execute("DELETE FROM TARGET_FACT")
                source = hex_key(0xA2) if endpoint == "source" else hex_key(998)
                target = hex_key(0xA2) if endpoint == "target" else hex_key(997)
                self.fact(hex_key(999), source, target)
                self.assert_selected("20")

    def test_existing_edge_pk_excludes_record_even_with_unrelated_endpoints(self):
        self.fact(hex_key(0xA3), hex_key(998), hex_key(997))
        self.assert_selected("20")

    def test_incoming_incident_candidate_edge_pk_is_also_checked(self):
        self.db.execute("INSERT INTO GRAPH_EDGES VALUES (?,?,?)",
                        (hex_key(996), hex_key(995), hex_key(0xA2)))
        self.fact(hex_key(996), hex_key(994), hex_key(993))
        self.assert_selected("20")

    def test_missing_root_or_wrong_root_owner_cannot_select_record(self):
        self.db.execute("UPDATE GRAPH_NODES SET ELEMENT_PATH='system-security-plan.metadata' "
                        "WHERE SOURCE_RECORD_ID='10'")
        self.db.execute("UPDATE GRAPH_NODES SET SOURCE_SYSTEM_NAME='OTHER' "
                        "WHERE SOURCE_RECORD_ID='20'")
        self.assert_selected("30")

    def test_no_eligible_record_returns_empty_without_mutating_any_table(self):
        self.dim(hex_key(999), source_id="10")
        self.dim(hex_key(0xB2))
        self.fact(hex_key(0xC3), hex_key(998), hex_key(997))
        before = list(self.db.iterdump())
        self.assertEqual([], self.select())
        self.assertEqual(before, list(self.db.iterdump()))

    def test_require_empty_scope_checks_both_queries_and_rejects_any_existing_row(self):
        queries = ("SELECT * FROM TARGET_DIM", "SELECT * FROM TARGET_FACT")
        session = SqliteSession(self.db)
        P["_pilot_require_empty_scope"](session, queries)
        self.assertEqual(2, len(session.executed))
        for table in ("DIM", "FACT"):
            with self.subTest(table=table):
                self.db.execute("DELETE FROM TARGET_DIM")
                self.db.execute("DELETE FROM TARGET_FACT")
                if table == "DIM":
                    self.dim(hex_key(999))
                else:
                    self.fact(hex_key(999), hex_key(998), hex_key(997))
                before = list(self.db.iterdump())
                with self.assertRaises(PilotError) as caught:
                    P["_pilot_require_empty_scope"](session, queries)
                self.assertEqual("NEW_RECORD_TARGET_SCOPE_NOT_EMPTY", caught.exception.code)
                self.assertEqual(before, list(self.db.iterdump()))

    def test_merge_has_insert_only_branch_and_never_updates_or_deletes(self):
        for kind in ("DIM", "FACT"):
            target, pk = P["SSP_PILOT_" + kind], DIM_PK if kind == "DIM" else FACT_PK
            sql = P["_pilot_merge_sql"](target, "STAGE", pk,
                                         [{"name": pk}, {"name": "OSCAL_UUID"}]).upper()
            self.assertIn("WHEN NOT MATCHED THEN INSERT", sql)
            self.assertNotIn("WHEN MATCHED", sql)
            self.assertNotIn("UPDATE", sql)
            self.assertNotIn("DELETE", sql)


class InsertSession:
    def __init__(self, inserted=(2, 1, 0, 0)):
        self.inserted = list(inserted)
        self.events = []
        self.calls = Counter()
        self.transaction = None

    def sql(self, statement):
        parent = self

        class Plan:
            def collect(self):
                if statement == "SELECT CURRENT_TRANSACTION() AS TX":
                    return [Row(TX=parent.transaction)]
                if statement in MERGES:
                    kind = "DIM" if statement == MERGES[0] else "FACT"
                    parent.events.append(kind)
                    parent.calls[kind] += 1
                    value = parent.inserted.pop(0)
                    return [Row({"number of rows inserted": value})]
                kind = statement.split()[0].upper()
                if kind not in {"BEGIN", "ROLLBACK", "COMMIT"}:
                    raise AssertionError("Unexpected statement")
                parent.events.append(kind)
                parent.calls[kind] += 1
                parent.transaction = "active" if kind == "BEGIN" else None
                return [Row()]
        return Plan()


class NewRecordTransactions(unittest.TestCase):
    def test_guard_runs_once_inside_each_transaction_before_any_dml(self):
        session = InsertSession()

        def guard():
            self.assertEqual("active", session.transaction)
            self.assertEqual(0, session.calls["DIM"])
            self.assertEqual(0, session.calls["FACT"])
            session.events.append("GUARD")

        def verify(number):
            session.events.append("VERIFY" + str(number))

        result = P["_pilot_transaction"](session, MERGES, verify,
                                          before_write=guard, expected_inserts=(2, 1))
        self.assertEqual(["BEGIN", "GUARD", "DIM", "FACT", "VERIFY1", "DIM", "FACT", "VERIFY2", "ROLLBACK"],
                         session.events)
        self.assertEqual([{"PASS": 1, "DIM": 2, "FACT": 1}, {"PASS": 2, "DIM": 0, "FACT": 0}],
                         result["INSERT_COUNTS"])

    def test_scope_guard_failure_rolls_back_before_first_merge(self):
        session = InsertSession()

        def guard():
            session.events.append("GUARD")
            raise PilotError("NEW_RECORD_TARGET_SCOPE_NOT_EMPTY")

        with self.assertRaises(PilotError) as caught:
            P["_pilot_transaction"](session, MERGES, lambda _: self.fail("Must not verify"),
                                     commit=True, before_write=guard, expected_inserts=(2, 1))
        self.assertEqual("TRANSACTION_ROLLED_BACK", caught.exception.code)
        self.assertEqual("NEW_RECORD_TARGET_SCOPE_NOT_EMPTY", caught.exception.details["CAUSE"])
        self.assertEqual(["BEGIN", "GUARD", "ROLLBACK"], session.events)

    def test_mismatched_insert_count_on_either_pass_rolls_back(self):
        for counts in ((1, 1, 0, 0), (2, 0, 0, 0), (2, 1, 1, 0), (2, 1, 0, 1)):
            with self.subTest(counts=counts):
                session = InsertSession(counts)
                with self.assertRaises(PilotError) as caught:
                    P["_pilot_transaction"](session, MERGES, lambda _: None,
                                             commit=True, expected_inserts=(2, 1))
                self.assertEqual("TRANSACTION_ROLLED_BACK", caught.exception.code)
                self.assertEqual("UNEXPECTED_MERGE_INSERT_COUNT", caught.exception.details["CAUSE"])
                self.assertEqual(1, session.calls["ROLLBACK"])
                self.assertEqual(0, session.calls["COMMIT"])

    def test_exact_first_pass_and_zero_repeat_inserts_can_commit(self):
        session = InsertSession()
        result = P["_pilot_transaction"](session, MERGES, lambda _: None,
                                          commit=True, expected_inserts=(2, 1))
        self.assertEqual("COMMITTED", result["STATUS"])
        self.assertEqual(1, session.calls["COMMIT"])
        self.assertEqual(0, session.calls["ROLLBACK"])


if __name__ == "__main__":
    unittest.main()
