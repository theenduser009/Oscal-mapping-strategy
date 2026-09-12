"""Regression from artifact row through Cells 3, 4 and graph construction.

Run with the bundled Python runtime (pandas installed). Snowflake transport and
unrelated component lookup I/O are fakes; mapping and graph logic are real.
"""
import contextlib
import ast
import datetime
import hashlib
import io
import json
from pathlib import Path

# Historical field-policy regression oracle; never imported by production.
LEGACY_CELL_4_PATH = Path(__file__).parents[1] / "tests/fixtures/legacy_cell4_pre_declarative.py"
import re
import runpy
import unittest
import uuid

try:
    import pandas as pd
except ImportError:
    pd = None


ROOT = Path(__file__).parents[1]
CELLS = ROOT / "notebooks" / "cells"
SSP = "system-security-plan"
SC = SSP + ".system-characteristics"
PROPS = SC + ".props[]"
APPROVED = (
    "INFORMATION_SYSTEM_TYPE", "FISMA_REPORTABLE", "FINANCIAL_SYSTEM",
    "MISSION_CRITICAL", "CRITICAL_INFRASTRUCTURE", "PACKAGE_TYPE",
    "PIA_REQUIRED", "INFORMATION_CLASSIFICATION",
)


class Row(dict):
    def as_dict(self, recursive=True):
        return dict(self)


class Frame:
    def __init__(self, rows):
        self.rows = [Row(row) for row in rows]

    def collect(self):
        return self.rows

    def to_local_iterator(self):
        return iter(self.rows)


class Session:
    def create_dataframe(self, data):
        if isinstance(data, pd.DataFrame):
            assert isinstance(data.index, pd.RangeIndex)
            return Frame(data.to_dict("records"))
        return Frame(data)


def registry(include_props=True, active=True):
    rows = [
        {"OSCAL_MODEL_KEY": "SSP", "NODE_PATH": SSP, "IS_ACTIVE": True},
        {"OSCAL_MODEL_KEY": "SSP", "NODE_PATH": SC, "IS_ACTIVE": True},
    ]
    if include_props:
        rows.append({
            "OSCAL_MODEL_KEY": "SSP", "NODE_PATH": PROPS,
            "IS_ACTIVE": active, "IS_COLLECTION": True,
            "PARENT_NODE_PATH": SC, "INSTANCE_KEY_RULE": "SOURCE_FIELD_NAME+VALUE",
            "ITEM_PATH": "$",
        })
    return Frame(rows)


def mapping(source="INFORMATION_SYSTEM_TYPE", path=SC, **overrides):
    result = {
        "SOURCE_FIELD_NAME": source,
        "OSCAL_MODEL": "System Security Plan",
        "OSCAL_ELEMENT_PATH": path,
        "OSCAL_FIELD_NAME": source.lower().replace("_", "-"),
        "MAPPING_TYPE": "Extension Property", "STATUS": "Mapped",
        "TRANSFORMATION_LOGIC": "Resolve Archer select value",
    }
    result.update(overrides)
    return result


@unittest.skipUnless(pd is not None, "requires pandas: use bundled Python runtime")
class PropertyCanonicalRoutingTests(unittest.TestCase):
    def canonicalize(self, mappings, registry_frame=None):
        artifact = pd.DataFrame(mappings)
        original = artifact.copy(deep=True)
        # Execute pure configuration, including derived selector state;
        # exclude Snowflake imports/session acquisition, not its dependencies.
        import copy
        config_ns = {"datetime": datetime, "copy": copy, "Path": Path, "json": json,
                     "__file__": str(CELLS / "01_initialization_and_configuration.py")}
        tree = ast.parse((CELLS / "01_initialization_and_configuration.py").read_text(encoding="utf-8"))
        configuration = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Assign):
                names = {target.id for target in node.targets if isinstance(target, ast.Name)}
                if "session" in names:
                    continue
                if "SELECTED_MODELS" in names:
                    node.value = ast.Constant(value="SSP")
            configuration.append(node)
        module = ast.fix_missing_locations(ast.Module(body=configuration, type_ignores=[]))
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(module, "<test-config>", "exec"), config_ns)
        profiles = config_ns["SOURCE_PROFILES"]
        with contextlib.redirect_stdout(io.StringIO()):
            result = runpy.run_path(str(CELLS / "03_canonical_mapping_contract.py"),
                init_globals={
                    "CONFIG": config_ns["CONFIG"], "re": re, "pd": pd,
                    "SOURCE_PROFILES": profiles, "MODEL_CONTRACTS": config_ns["MODEL_CONTRACTS"],
                    "MAPPING_INPUTS": {"source-one": artifact.to_dict(orient="records")},
                    "REGISTRY_INPUT_ROWS": list((registry_frame or registry()).rows),
                    "session": Session(), "mapping_artifact_pdf": artifact,
                    "element_registry_df": registry_frame or registry(),
                })
        pd.testing.assert_frame_equal(artifact, original)
        return result

    def helpers(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return runpy.run_path(str(LEGACY_CELL_4_PATH),
                init_globals={
                    "CONFIG": {"SOURCE_SYSTEM_NAME": "unit-test"},
                    "ARCHER_VALUE_LOOKUP": {"101": "Mission Critical"},
                    "FIPS_199_VALUE_LOOKUP": {},
                    "hashlib": hashlib, "json": json, "re": re, "uuid": uuid,
                })

    def test_all_eight_approved_sources_route_without_changing_artifact(self):
        for source in APPROVED:
            for path in (SC, SC + "." + source.lower().replace("_", "-"), PROPS):
                with self.subTest(source=source, path=path):
                    result = self.canonicalize([mapping(source, path)])
                    row = result["CANONICAL_MAPPING_ROWS"][0]
                    self.assertEqual(row["OWNER_ELEMENT_PATH"], PROPS)
                    self.assertEqual(row["CANONICAL_ELEMENT_PATH"], PROPS + ".value")
                    self.assertEqual(row["OSCAL_ELEMENT_PATH"], path)
                    self.assertEqual(row["OSCAL_FIELD_NAME"], source.lower().replace("_", "-"))
                    self.assertEqual(row["FIELD_RELATIVE_PATH"], "value")
                    self.assertEqual(set(result["MAPPINGS_BY_ELEMENT_PATH"]), {PROPS})

    def test_parent_row_reproduces_failure_before_canonical_routing(self):
        helpers = self.helpers()
        original = mapping(OWNER_ELEMENT_PATH=SC)
        with self.assertRaisesRegex(ValueError, "no approved transformation handler"):
            helpers["apply_mapping_transform"](original, {"ValuesListIds": ["101"]}, "r1")
        row = self.canonicalize([original])["CANONICAL_MAPPING_ROWS"][0]
        instances = helpers["build_element_instances"](
            {"INFORMATION_SYSTEM_TYPE": {"ValuesListIds": ["101", "101"]}},
            "r1", PROPS, [row])
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["payload"],
                         {"name": "information-system-type", "value": "Mission Critical"})

    def test_unknown_wrong_type_and_other_branches_are_not_rerouted(self):
        rows = [
            mapping("UNAPPROVED_FIELD"),
            mapping(MAPPING_TYPE="Transform"),
            mapping(path=SC + ".nested.unapproved"),
        ]
        helpers = self.helpers()
        for original in rows:
            with self.subTest(row=original):
                result = self.canonicalize([original])
                self.assertEqual(result["CANONICAL_MAPPING_ROWS"], [])
                report = result["MAPPING_CONTEXTS"][0]["routing_report"]
                self.assertEqual(report["SELECTED_ROWS"], 0)
                self.assertEqual(report["BLOCKED_ROWS"] + report["DEFERRED_ROWS"], 1)
        # An unknown collection is now rejected during routing, before dispatch.
        blocked = self.canonicalize([mapping(path=SSP + ".metadata.props[]")])
        self.assertEqual(blocked["MAPPING_CONTEXTS"][0]["routing_report"]["STATUS"], "BLOCKED")
        self.assertEqual(blocked["CANONICAL_MAPPING_ROWS"], [])

    def test_registered_status_remarks_remain_unchanged(self):
        frame = registry()
        frame.rows.append(Row(OSCAL_MODEL_KEY="SSP", NODE_PATH=SC + ".status", IS_ACTIVE=True))
        original = mapping("AUTHORIZATION_COMMENTS", SC + ".status.remarks", OSCAL_FIELD_NAME="remarks")
        row = self.canonicalize([original], frame)["CANONICAL_MAPPING_ROWS"][0]
        self.assertEqual(row["OWNER_ELEMENT_PATH"], SC + ".status")
        self.assertEqual(self.helpers()["_mapping_handler_for_row"](row), "approved-text")

    def test_missing_or_inactive_properties_registry_fails_before_grouping(self):
        for frame in (registry(False), registry(active=False)):
            for path in (SC, PROPS + ".value"):
                with self.subTest(path=path):
                    with self.assertRaisesRegex(ValueError, "requires active registry path"):
                        self.canonicalize([mapping(path=path)], frame)

    def test_deferred_and_helper_rows_still_skip(self):
        rows = [mapping("HELPER_PTA_CALC", MAPPING_TYPE="Calculated"),
                mapping(MAPPING_TYPE="TBD"), mapping(STATUS="Needs more information")]
        for row in self.canonicalize(rows)["CANONICAL_MAPPING_ROWS"]:
            self.assertEqual(self.helpers()["_mapping_handler_for_row"](row), "skip")

    def test_real_graph_has_one_parent_and_linked_deduplicated_properties(self):
        rows = [mapping(), mapping(),
                mapping("ATOIATO_DATE", SC + ".date-authorized",
                        OSCAL_FIELD_NAME="date-authorized", MAPPING_TYPE="Transform"),
                mapping("ACRONYM", SC + ".system-name-short",
                        OSCAL_FIELD_NAME="system-name-short", MAPPING_TYPE="Direct")]
        canonical = self.canonicalize(rows)
        helpers = self.helpers()
        helpers.update({
            "CONFIG": {"IDENTITY_VERSION": "test-v1", "RUN_ID": "test-run"},
            "MAPPINGS_BY_ELEMENT_PATH": canonical["MAPPINGS_BY_ELEMENT_PATH"],
            "datetime": datetime, "session": Session(),
            "COMPONENT_HYDRATION_SOURCE_DFS": {},
            # No components are in this fixture; isolate unrelated lookup I/O.
            "_build_component_hydration_lookups": lambda *args: {},
        })
        with contextlib.redirect_stdout(io.StringIO()):
            graph = helpers["_context_config"].__globals__
            graph.update(helpers)
            exec(compile((CELLS / "05_registry_graph_builder.py").read_text(encoding="utf-8"),
                         str(CELLS / "05_registry_graph_builder.py"), "exec"), graph)
        source = Frame([{"SOURCE_RECORD_ID": record, "CURATED_JSON": {
            "ACRONYM": "Example", "INFORMATION_SYSTEM_TYPE": {"ValuesListIds": ["101", "101"]},
            "ATOIATO_DATE": "2026-09-10T23:50:00-12:00",
        }} for record in ("r1", "r2")])
        nodes, edges = graph["build_oscal_graph"](source, None, registry(), "SSP", "Archer", "fixture")
        self.assertEqual(len(nodes.rows), 6)
        self.assertEqual(len(edges.rows), 4)
        keyed = {node["NODE_KEY"]: node for node in nodes.rows}
        self.assertEqual(len(keyed), 6)
        for node in nodes.rows:
            if node["ELEMENT_PATH"] == SC:
                self.assertEqual(json.loads(node["METADATA_JSON"]),
                                 {"system-name-short": "Example", "date-authorized": "2026-09-10"})
            if node["ELEMENT_PATH"] == PROPS:
                self.assertEqual(json.loads(node["METADATA_JSON"]),
                                 {"name": "information-system-type", "value": "Mission Critical"})
        for edge in edges.rows:
            parent = keyed[edge["FK_SOURCE_ELEMENT_HASH"]]
            child = keyed[edge["FK_TARGET_ELEMENT_HASH"]]
            self.assertEqual(parent["SOURCE_RECORD_ID"], child["SOURCE_RECORD_ID"])
            if child["ELEMENT_PATH"] == PROPS:
                self.assertEqual(parent["ELEMENT_PATH"], SC)

    def test_cell_three_is_synchronized_and_repeatable(self):
        first = self.canonicalize([mapping()])["CANONICAL_MAPPING_ROWS"]
        second = self.canonicalize(first)["CANONICAL_MAPPING_ROWS"]
        self.assertEqual(first, second)
        notebook = (ROOT / "notebooks" / "NB_ARCHER_OSCAL_MAPPER_V1.py").read_text(encoding="utf-8")
        marker = "# %% Cell 3 - Canonical mapping contract"
        whole = marker + notebook.split(marker, 1)[1].split("# %% Cell 4 -", 1)[0]
        separate = (CELLS / "03_canonical_mapping_contract.py").read_text(encoding="utf-8")
        self.assertEqual(whole.rstrip(), separate.rstrip())


if __name__ == "__main__":
    unittest.main()
