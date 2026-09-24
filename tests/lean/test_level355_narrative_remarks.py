"""CSV-only Level-355 narrative correction: pure compiler/emitter regressions.

No Snowflake session or DML. This is not full SSP schema validation.
Allowed native member names were checked against the v1.2.3 SSP metaschema:
https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_ssp_metaschema.xml
"""
import ast
import copy
import csv
import hashlib
import json
import math
import re
import unittest
import uuid
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IR = "system-security-plan.control-implementation.implemented-requirements[]"
RULE = "ssp-control:IMPLEMENTATION_DETAILS:description"  # Stable historical rule ID.
NATIVE_IR_MEMBERS = {
    "uuid", "control-id", "props", "links", "set-parameters",
    "responsible-roles", "statements", "by-components", "remarks",
}


def namespace():
    """Read actual maintained pure functions; never execute cell orchestration."""
    ns = dict(copy=copy, csv=csv, hashlib=hashlib, json=json, math=math,
              re=re, uuid=uuid, Decimal=Decimal, SKIP_VALUE=object())
    needed = {
        "_metadata_column_text", "_metadata_items", "_registry_meta_bool",
        "_metadata_params", "_metadata_target", "_compile_mapping",
        "_to_python", "_has_value", "resolve_json_path", "_json_text",
        "_scalar_text", "_metadata_text", "_metadata_transform",
        "_metadata_mapped_value", "_metadata_assign", "_metadata_get",
        "_metadata_parent_key", "_append_unique_collection_instance",
        "_joined_variant_value", "_metadata_joined_record_instances",
        "_deterministic_hash",
    }
    for filename in ("03_canonical_mapping_contract.py",
                     "04_parsing_transform_payload_helpers.py"):
        path = ROOT / "notebooks/cells" / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        selected = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in needed:
                selected.append(node)
            elif (isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "METADATA_TRANSFORM_IDS"
                          for t in node.targets)):
                selected.append(node)
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), ns)
    missing = needed - ns.keys()
    if missing:
        raise AssertionError("Maintained functions unavailable: " + repr(sorted(missing)))
    return ns


class Level355NarrativeRemarksTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace()
        with (ROOT / "Mapping/ARCHER_OSCAL_MAPPINGS.csv").open(
                encoding="utf-8-sig", newline="") as stream:
            self.rows = list(csv.DictReader(stream))
        self.description = self.one(RULE)
        self.control = self.one("ssp-control:CONTROL_NUMBER:control-id")
        self.params = dict(joined_instance_field="ALLOCATED_CONTROL_ID",
                           required_members=["control-id"], parent_instance_rule="singleton")

    def one(self, rule):
        rows = [r for r in self.rows if r["RULE_ID"] == rule]
        self.assertEqual(1, len(rows))
        return rows[0]

    def compiled(self, row):
        row = dict(row, OWNER_ELEMENT_PATH=IR,
                   FIELD_RELATIVE_PATH=row["RUNTIME_TARGET_PATH"][len(IR) + 1:])
        return self.ns["_compile_mapping"](row, {IR: {"operator": "joined-records"}})

    def emit(self, children, narrative_row=None):
        ctx = dict(config={}, compiled_plan={"options": {"parse_decimal": False}},
                   graph_report={"MAPPED_VALUES": 0, "MISSING_VALUES": 0},
                   joined_record_lookups={"allocated-controls": {"package-a": children}})
        mappings = [self.compiled(self.control), self.compiled(narrative_row or self.description)]
        items = self.ns["_metadata_joined_record_instances"](
            "package-a", mappings, self.params, ctx)
        return items, ctx

    def child(self, **changes):
        result = dict(ALLOCATED_CONTROL_ID='"allocated-a"', CONTROL_NUMBER="03.01.01",
                      IMPLEMENTATION_DETAILS="A reviewed source narrative.")
        result.update(changes)
        return result

    def test_csv_changes_destination_not_identity_or_optional_policy(self):
        self.assertEqual(IR + ".remarks", self.description["OSCAL_ELEMENT_PATH"])
        self.assertEqual(IR + ".remarks", self.description["RUNTIME_TARGET_PATH"])
        for field, expected in (("TRANSFORM_ID", "text"), ("LOOKUP_KEY", "allocated-controls"),
                                ("SOURCE_KEY", "source-one"), ("VALUE_REQUIRED", "false"),
                                ("EXECUTION_STATUS", "APPROVED")):
            self.assertEqual(expected, self.description[field])
        self.assertFalse(any(r["EXECUTION_STATUS"] == "APPROVED"
                             and r["RUNTIME_TARGET_PATH"] == IR + ".description"
                             for r in self.rows))
        self.assertEqual(IR + ".control-id", self.control["RUNTIME_TARGET_PATH"])
        self.assertEqual("false", self.control["VALUE_REQUIRED"])

    def test_current_compiler_accepts_remarks_on_joined_records(self):
        params = self.compiled(self.description)["REPRESENTATION_PARAMS"]
        self.assertEqual("remarks", params["target"])
        self.assertEqual("allocated-controls", params["joined_lookup"])
        self.assertIs(params["required"], False)

    def test_narrative_emitted_only_in_supported_native_member(self):
        items, _ = self.emit([self.child()])
        payload = items[0]["payload"]
        self.assertEqual("A reviewed source narrative.", payload["remarks"])
        self.assertNotIn("description", payload)
        self.assertTrue(set(payload) <= NATIVE_IR_MEMBERS)
        self.assertNotIn("by-components", payload)  # Do not infer ownership.

    def test_json_null_and_absent_text_are_omitted(self):
        for child in [self.child(IMPLEMENTATION_DETAILS=None),
                      {k: v for k, v in self.child().items() if k != "IMPLEMENTATION_DETAILS"}]:
            with self.subTest(child=child):
                items, _ = self.emit([child])
                self.assertEqual({"control-id": "03.01.01"}, items[0]["payload"])

    def test_empty_text_is_omitted_without_dropping_valid_control(self):
        items, _ = self.emit([self.child(IMPLEMENTATION_DETAILS="")])
        self.assertEqual(1, len(items))
        self.assertNotIn("remarks", items[0]["payload"])

    def test_whitespace_only_text_keeps_existing_fail_closed_behavior(self):
        with self.assertRaises(ValueError):
            self.emit([self.child(IMPLEMENTATION_DETAILS=" \n\t")])

    def test_transport_decode_distinguishes_json_null_and_literal_null_text(self):
        ctx = {"compiled_plan": {"options": {"parse_decimal": False}}}
        decode = self.ns["_joined_variant_value"]
        self.assertIsNone(decode("null", ctx))
        self.assertEqual("null", decode('"null"', ctx))
        self.assertEqual("03.01.01", decode('"03.01.01"', ctx))

    def test_unicode_multiline_text_is_retained(self):
        text = "Source paragraph one.\nSecond paragraph: caf\u00e9 / \u03b2."
        items, _ = self.emit([self.child(IMPLEMENTATION_DETAILS=text)])
        self.assertEqual(text, items[0]["payload"]["remarks"])

    def test_missing_control_number_stays_one_counted_skip(self):
        items, ctx = self.emit([self.child(), self.child(
            ALLOCATED_CONTROL_ID='"allocated-b"', CONTROL_NUMBER=None)])
        self.assertEqual(1, len(items))
        self.assertEqual(1, ctx["graph_report"]["SKIPPED_JOINED_RECORDS"])

    def test_distinct_allocations_with_same_control_number_are_not_collapsed(self):
        items, _ = self.emit([self.child(), self.child(ALLOCATED_CONTROL_ID='"allocated-b"')])
        self.assertEqual(2, len(items))
        self.assertEqual(2, len({r["instance_key"] for r in items}))

    def test_duplicate_identity_conflict_is_not_silently_overwritten(self):
        with self.assertRaises(ValueError):
            self.emit([self.child(), self.child(IMPLEMENTATION_DETAILS="Different narrative.")])

    def test_existing_node_and_parent_identity_are_unchanged(self):
        previous = dict(self.description, RUNTIME_TARGET_PATH=IR + ".description")
        old, _ = self.emit([self.child()], previous)
        new, _ = self.emit([self.child()])
        self.assertEqual(old[0]["instance_key"], new[0]["instance_key"])
        self.assertEqual(old[0]["parent_instance_key"], new[0]["parent_instance_key"])
        seed = ("v1_registry_path_instance", "ARCHER", "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
                "package-a", "SSP", IR)
        h = self.ns["_deterministic_hash"]
        self.assertEqual(h(*seed, old[0]["instance_key"]), h(*seed, new[0]["instance_key"]))
        self.assertNotIn("description", new[0]["payload"])

    def test_object_narrative_is_rejected_not_stringified(self):
        with self.assertRaises(ValueError):
            self.emit([self.child(IMPLEMENTATION_DETAILS={"unexpected": "object"})])


if __name__ == "__main__":
    unittest.main()
