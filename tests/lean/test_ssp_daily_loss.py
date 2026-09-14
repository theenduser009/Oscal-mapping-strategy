"""Owner-enabled SSP property; synthetic values and a local relational adapter."""
import datetime
import json
import unittest
from unittest.mock import patch

from lean_support import build, business, namespace
from test_registry_release import mapping_rows, release_registry
import test_loader as storage

FIELD = "DAILY_LOSS_AMOUNT_FROM_OUTAGE"
PATH = "system-security-plan.system-characteristics.props[]"
NAME = "daily-loss-amount-from-outage"


class SSPDailyLossTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace(models=("SSP",))
        # No component references occur in these records; transport is tested separately.
        self.ns["_build_component_hydration_lookups"] = lambda *args: {}
        self.context = self.ns["compile_mapping_contexts"](
            {"source-one": mapping_rows()}, release_registry(), self.ns["SOURCE_PROFILES"],
            self.ns["MODEL_CONTRACTS"], self.ns["ROUTING_METADATA"])[0]
        self.assertEqual("READY", self.context["routing_report"]["STATUS"])
        self.context["lookups"] = {"archer_values": {}, "fips_values": {}}

    def graph(self, fields):
        source = {"AUTHORIZATION_PACKAGE_NAME": "Synthetic package", **fields}
        return build(self.ns, self.context,
                     [{"SOURCE_RECORD_ID": "synthetic-daily-loss", "CURATED_JSON": source}])

    def property(self, nodes):
        return [row for row in nodes.rows if row["ELEMENT_PATH"] == PATH
                and json.loads(row["METADATA_JSON"])["name"] == NAME]

    def test_exact_mapping_and_existing_registry_identity(self):
        rows = [row for row in mapping_rows() if row["SOURCE_FIELD_NAME"] == FIELD]
        self.assertEqual(1, len(rows))
        self.assertEqual(("96", "APPROVED", "direct", PATH, PATH,
                          "ssp:" + FIELD, "preserve"), tuple(rows[0][key] for key in (
            "ORIGINAL_ROW_ID", "EXECUTION_STATUS", "TRANSFORM_ID", "OSCAL_ELEMENT_PATH",
            "RUNTIME_TARGET_PATH", "RULE_ID", "NULL_POLICY")))
        self.assertIn("All Nulls", rows[0]["NOTES"])
        self.assertEqual("Extension Property", rows[0]["MAPPING_TYPE"])
        self.assertIn("Original mapping type: TBD.", rows[0]["EXECUTION_NOTE"])
        spec = self.context["compiled_plan"]["elements"][PATH]
        self.assertEqual("properties", spec["operator"])
        self.assertEqual("SOURCE_FIELD_NAME+VALUE", spec["parameters"]["registry_contract"]["instance_key_rule"])

    def test_missing_and_empty_values_omit_but_explicit_null_zero_and_scalars_map(self):
        baseline = self.graph({})
        for value in ("", [], {}):
            self.assertEqual(tuple(map(business, baseline)), tuple(map(business, self.graph({FIELD: value}))))
        for value, expected in ((None, None), (0, "0"), (1250.5, "1250.5"), ("1250.50", "1250.50")):
            with self.subTest(value=value):
                nodes, edges = self.graph({FIELD: value})
                self.assertEqual((len(baseline[0].rows) + 1, len(baseline[1].rows) + 1),
                                 (len(nodes.rows), len(edges.rows)))
                row, = self.property(nodes)
                self.assertEqual({"name": NAME, "value": expected}, json.loads(row["METADATA_JSON"]))
                parent = next(node for node in nodes.rows if node["ELEMENT_PATH"] == PATH.rsplit(".", 1)[0])
                edge = next(edge for edge in edges.rows if edge["FK_TARGET_ELEMENT_HASH"] == row["NODE_KEY"])
                self.assertEqual(parent["NODE_KEY"], edge["FK_SOURCE_ELEMENT_HASH"])
                self.ns["_load_graph"](nodes, edges, self.context["config"])
                self.assertEqual(tuple(map(business, (nodes, edges))),
                                 tuple(map(business, self.graph({FIELD: value}))))

    def test_unknown_objects_and_nested_containers_reject(self):
        for value in ({"unexpected": 10}, [{"unexpected": 10}], [[10]]):
            with self.subTest(container=type(value).__name__), self.assertRaises(ValueError):
                self.graph({FIELD: value})

    def test_null_insert_readback_retry_and_existing_changed_value_guard(self):
        session = storage.Session()
        self.addCleanup(session.db.close)
        config = self.context["config"]
        contract = config["STORAGE_CONTRACT"]
        for table_key, pk_key, fields in (("TARGET_DIM", "DIM_PK_COLUMN", storage.P["_DIM_FIELDS"]),
                                          ("TARGET_FACT", "FACT_PK_COLUMN", storage.P["_FACT_FIELDS"])):
            table, pk = contract[table_key], contract[pk_key]
            session.schema[table] = [dict(name=name, type=dtype, kind="COLUMN", expression=None,
                **{"null?": "N" if table_key == "TARGET_FACT" or name == pk else "Y"})
                for name, dtype in {pk: "BINARY(16)", **fields}.items()]
            session.query(f"CREATE TABLE {table} ({', '.join(row['name'] for row in session.schema[table])})")

        def load(value, writes):
            frames = []
            for frame in self.graph({FIELD: value}):
                rows = [{key: item.isoformat() if isinstance(item, (datetime.date, datetime.datetime)) else item
                         for key, item in row.items()} for row in frame.rows]
                frames.append(storage.Frame(session, rows, frame.columns))
            with patch.dict(self.ns, session=session):
                return self.ns["validate_and_load_oscal"](*frames, dict(config, EXECUTE_WRITES=writes))

        expected_counts = tuple(len(frame.rows) for frame in self.graph({FIELD: None}))
        self.assertEqual("PREVIEW_PASSED_NO_TARGET_DML", load(None, False)["status"])
        self.assertFalse(any(statement.startswith("MERGE") for statement in session.events))
        inserted = load(None, True)
        self.assertEqual("COMMITTED_AND_VERIFIED", inserted["status"])
        self.assertEqual(expected_counts, tuple(inserted["expected_changes"][kind]["INSERTS"] for kind in ("D", "F")))
        saved = [session.query("SELECT * FROM " + contract[key]) for key in ("TARGET_DIM", "TARGET_FACT")]
        prop, = [row for row in saved[0] if row["ELEMENT_TYPE"] == "props"]
        self.assertEqual({"name": NAME, "value": None}, json.loads(prop["METADATA_JSON"]))
        retry = load(None, True)
        self.assertEqual({kind: {"INSERTS": 0, "UPDATES": 0, "UNCHANGED": count}
                          for kind, count in zip(("D", "F"), expected_counts)}, retry["expected_changes"])
        null_property, = self.property(self.graph({FIELD: None})[0])
        amount_property, = self.property(self.graph({FIELD: 100})[0])
        self.assertNotEqual(null_property["NODE_KEY"], amount_property["NODE_KEY"])
        self.assertNotEqual(null_property["OSCAL_UUID"], amount_property["OSCAL_UUID"])
        before = sum(statement.startswith("MERGE") for statement in session.events)
        with self.assertRaisesRegex(self.ns["LoadError"], "OBSOLETE_TARGET_ROWS_BLOCKED"):
            load(100, True)
        self.assertEqual(before, sum(statement.startswith("MERGE") for statement in session.events))
        self.assertEqual(saved, [session.query("SELECT * FROM " + contract[key])
                                 for key in ("TARGET_DIM", "TARGET_FACT")])


if __name__ == "__main__":
    unittest.main()
