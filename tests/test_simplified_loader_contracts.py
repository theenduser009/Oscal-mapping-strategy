"""Schema and graph invariants behind the reduced loader, without Snowflake."""
import copy
from itertools import combinations, permutations
import sqlite3
import unittest
from unittest.mock import patch

from tests.test_multi_model_loader import P, G, Error, config, graph, storage
from tests.test_ssp_write_pilot_live_schema import live_description


class ReviewedSchema(unittest.TestCase):
    def description(self, kind):
        rows = live_description(kind)
        rows[0]["name"] = storage()[kind + "_PK_COLUMN"]
        return rows

    def test_exact_identity_profile_rejects_other_hash_and_uuid_widths(self):
        for kind in ("DIM", "FACT"):
            original = self.description(kind)
            for index, column in enumerate(original):
                if column["type"] not in ("BINARY(16)", "VARCHAR(32)"):
                    continue
                if column["name"] == "DEPENDENCY_TYPE":
                    continue
                types = ("VARCHAR(32)", "BINARY(15)", "BINARY(17)") if column["type"] == "BINARY(16)" else (
                    "VARCHAR", "VARCHAR(31)", "VARCHAR(36)", "VARIANT")
                for dtype in types:
                    rows = copy.deepcopy(original)
                    rows[index]["type"] = dtype
                    with self.subTest(kind=kind, column=column["name"], dtype=dtype):
                        with self.assertRaises(Error):
                            P["_load_column_plan"](rows, kind, storage())

    def test_optional_audit_and_string_payload_keep_supported_projections(self):
        rows = [r for r in self.description("DIM") if not r["name"].startswith("DW_")]
        next(r for r in rows if r["name"] == "METADATA_JSON")["type"] = "TEXT( 2048 )"
        next(r for r in rows if r["name"] == "OSCAL_UUID")["type"] = "STRING( 32 )"
        rows[0]["type"] = "BINARY( 16 )"
        plan = P["_load_column_plan"](rows, "DIM", storage())
        by_name = {column["name"]: column for column in plan}
        self.assertEqual(7, len(plan))
        self.assertEqual("VARCHAR(2048)", by_name["METADATA_JSON"]["type"])
        self.assertEqual('CAST(s."METADATA_JSON" AS VARCHAR)', by_name["METADATA_JSON"]["expression"])
        self.assertEqual("UUID_TO_COMPACT32", by_name["OSCAL_UUID"]["encoding"])
        self.assertEqual("HEX_TO_BINARY16", plan[0]["encoding"])

    def test_schema_completeness_writability_and_required_extensions_still_block(self):
        original = self.description("DIM")
        changes = (
            lambda rows: rows.pop(0),
            lambda rows: rows.append(copy.deepcopy(rows[0])),
            lambda rows: rows[0].update(kind="VIRTUAL"),
            lambda rows: rows[0].update(expression="generated"),
            lambda rows: rows[0].pop("default"),
            lambda rows: rows.append(dict(name="REQUIRED_EXTENSION", type="VARCHAR", kind="COLUMN",
                                          default=None, **{"null?": "N"})),
        )
        for change in changes:
            rows = copy.deepcopy(original)
            change(rows)
            with self.subTest(change=change), self.assertRaises(Error):
                P["_load_column_plan"](rows, "DIM", storage())


class LogicalReachability(unittest.TestCase):
    def test_parent_and_path_checks_match_an_independent_tree_walk(self):
        cfg = config()
        nodes, _ = graph(cfg)
        nodes.append(dict(nodes[1], NODE_KEY="4".zfill(32),
                          OSCAL_UUID="00000000-0000-5000-8000-000000000004",
                          ELEMENT_PATH=cfg["ROOT_PATH"] + ".other", INSTANCE_KEY="other"))
        for node in nodes:
            node["PARENT_INSTANCE_KEY"] = None
        links = tuple(permutations(range(len(nodes)), 2))
        accepted = 0
        # Every possible three-edge graph includes cycles, detached branches,
        # multiple parents, reversed edges, and the valid rooted trees.
        for chosen in combinations(links, len(nodes) - 1):
            parents = [0] * len(nodes)
            reached = {0}
            for source, target in chosen:
                parents[target] += 1
            for _ in nodes:
                reached.update(target for source, target in chosen if source in reached)
            expected = parents == [0, 1, 1, 1] and len(reached) == len(nodes) and all(
                nodes[target]["ELEMENT_PATH"].startswith(nodes[source]["ELEMENT_PATH"] + ".")
                for source, target in chosen)
            edges = [dict(EDGE_KEY=format(index + 10, "032x"),
                          FK_SOURCE_ELEMENT_HASH=nodes[source]["NODE_KEY"],
                          FK_TARGET_ELEMENT_HASH=nodes[target]["NODE_KEY"],
                          SOURCE_OSCAL_UUID=nodes[source]["OSCAL_UUID"],
                          TARGET_OSCAL_UUID=nodes[target]["OSCAL_UUID"],
                          DEPENDENCY_TYPE="CONTAINS")
                     for index, (source, target) in enumerate(chosen)]
            try:
                P["_load_logical_graph"](nodes, edges, P["_load_graph_contract"](cfg), 1)
                actual = True
            except Error:
                actual = False
            self.assertEqual(expected, actual, chosen)
            accepted += actual
        self.assertEqual(2, accepted)


class BaselineMultiplicity(unittest.TestCase):
    def test_duplicate_multiplicity_changes_are_detected_without_separate_counts(self):
        database = sqlite3.connect(":memory:")
        self.addCleanup(database.close)
        for table in ("CURRENT_D", "CURRENT_F", "OLD_D", "OLD_F"):
            database.execute("CREATE TABLE " + table + " (VALUE TEXT)")
            database.executemany("INSERT INTO " + table + " VALUES (?)", [("a",), ("a",), ("b",)])

        def query(session, statement):
            # Only Snowflake set-operation spelling and GROUP BY ALL differ.
            statement = statement.replace("GROUP BY ALL", "GROUP BY VALUE")
            statement = statement.replace("FROM ((", "FROM (", 1).replace(") MINUS (", " EXCEPT ")
            cursor = database.execute(statement[:-1])
            return [{"N": cursor.fetchone()[0]}]

        names = {"DB": "OLD_D", "FB": "OLD_F"}
        queries = ("SELECT * FROM CURRENT_D", "SELECT * FROM CURRENT_F")
        with patch.dict(G, {"_load_query": query}):
            P["_load_baseline_equal"](None, names, queries)
            # Same distinct values and total rows; only multiplicities change.
            database.execute("DELETE FROM CURRENT_F WHERE rowid = 1")
            database.execute("INSERT INTO CURRENT_F VALUES ('b')")
            with self.assertRaisesRegex(Error, "TARGET_BASELINE_CHANGED"):
                P["_load_baseline_equal"](None, names, queries)


if __name__ == "__main__":
    unittest.main()
