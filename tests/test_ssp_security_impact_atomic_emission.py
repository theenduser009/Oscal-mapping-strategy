import contextlib
import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import unittest
import uuid


REPO_ROOT = Path(__file__).parents[1]
CELL_4_PATH = (
    REPO_ROOT
    / "notebooks"
    / "cells"
    / "04_parsing_transform_payload_helpers.py"
)
CELL_5_PATH = (
    REPO_ROOT
    / "notebooks"
    / "cells"
    / "05_registry_graph_builder.py"
)
FULL_NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "NB_ARCHER_OSCAL_MAPPER_V1.py"

ROOT_PATH = "system-security-plan"
CHARACTERISTICS_PATH = ROOT_PATH + ".system-characteristics"
SECURITY_IMPACT_PATH = CHARACTERISTICS_PATH + ".security-impact-level"
COLLECTION_PATH = CHARACTERISTICS_PATH + ".system-ids[]"

OBJECTIVE_FIELDS = (
    "security-objective-confidentiality",
    "security-objective-integrity",
    "security-objective-availability",
)
SOURCE_FIELDS = ("CONFIDENTIALITY", "INTEGRITY", "AVAILABILITY")


def _load_cell_4():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(CELL_4_PATH),
            init_globals={
                "ARCHER_VALUE_LOOKUP": {},
                "CONFIG": {"SOURCE_SYSTEM_NAME": "unit-test"},
                "FIPS_199_VALUE_LOOKUP": {},
                "hashlib": hashlib,
                "json": json,
                "re": re,
                "uuid": uuid,
            },
        )


def _security_objective_rows():
    return [
        {
            "SOURCE_FIELD_NAME": source_field,
            "OWNER_ELEMENT_PATH": SECURITY_IMPACT_PATH,
            "OSCAL_ELEMENT_PATH": f"{SECURITY_IMPACT_PATH}.{target_field}",
            "OSCAL_FIELD_NAME": target_field,
            "MAPPING_TYPE": "Transform",
            "TRANSFORMATION_LOGIC": "Map to FIPS 199 security objective",
            "STATUS": "Mapped",
        }
        for source_field, target_field in zip(SOURCE_FIELDS, OBJECTIVE_FIELDS)
    ]


def _extract_notebook_cell(notebook, start_marker, end_marker):
    extracted = notebook.split(start_marker, 1)[1].split(end_marker, 1)[0]
    return f"{start_marker}{extracted}".rstrip()


class _RegistryRow:
    def __init__(self, values):
        self._values = values

    def as_dict(self, recursive=True):
        del recursive
        return dict(self._values)


class _RegistryDataFrame:
    def __init__(self, rows):
        self._rows = rows

    def collect(self):
        return [_RegistryRow(row) for row in self._rows]


class _SourceDataFrame:
    def to_local_iterator(self):
        return iter(
            [{"SOURCE_RECORD_ID": "private-source", "CURATED_JSON": {}}]
        )


class _PassthroughSession:
    def create_dataframe(self, rows):
        return list(rows)


def _load_cell_5_for_empty_graph():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(CELL_5_PATH),
            init_globals={
                "CONFIG": {
                    "IDENTITY_VERSION": "unit-test-v1",
                    "OSCAL_VERSION": "1.2.3",
                    "RUN_ID": "unit-test-run",
                },
                "MAPPINGS_BY_ELEMENT_PATH": {},
                "COMPONENT_HYDRATION_SOURCE_DFS": {},
                "_build_component_hydration_lookups": lambda *args: None,
                "build_element_instances": lambda *args: [],
                "datetime": datetime,
                "json": json,
                "session": _PassthroughSession(),
                "_parse_source_json": lambda record: record["CURATED_JSON"],
                "_deterministic_hash": lambda *parts: "|".join(
                    str(part) for part in parts
                ),
                "_deterministic_uuid": lambda *parts: "uuid|" + "|".join(
                    str(part) for part in parts
                ),
            },
        )


class SecurityImpactAtomicEmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell_4 = _load_cell_4()
        cls.mapping_rows = _security_objective_rows()

    def _build(self, source_obj):
        return self.cell_4["build_element_instances"](
            source_obj,
            "private-source-record",
            SECURITY_IMPACT_PATH,
            self.mapping_rows,
        )

    def test_split_cells_4_and_5_match_the_monolithic_notebook(self):
        notebook = FULL_NOTEBOOK_PATH.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        cases = (
            (
                CELL_4_PATH,
                "# %% Cell 4 - Generic parsing, transformation, and payload helpers",
                "# %% Cell 5 - Registry-driven canonical node and edge graph",
            ),
            (
                CELL_5_PATH,
                "# %% Cell 5 - Registry-driven canonical node and edge graph",
                "# %% Cell 6 - Validation, guarded idempotent DIM/FACT MERGE, verification",
            ),
        )

        for split_path, start_marker, end_marker in cases:
            with self.subTest(cell=split_path.name):
                split_cell = split_path.read_text(encoding="utf-8").replace(
                    "\r\n", "\n"
                )
                self.assertEqual(
                    _extract_notebook_cell(
                        notebook, start_marker, end_marker
                    ),
                    split_cell.rstrip(),
                )

    def test_complete_cia_emits_one_singleton(self):
        instances = self._build(
            {
                "CONFIDENTIALITY": "Low",
                "INTEGRITY": "Moderate",
                "AVAILABILITY": "High",
            }
        )

        self.assertEqual(
            instances,
            [
                {
                    "instance_key": "singleton",
                    "payload": {
                        "security-objective-confidentiality": "low",
                        "security-objective-integrity": "moderate",
                        "security-objective-availability": "high",
                    },
                    "parent_instance_key": None,
                }
            ],
        )

    def test_zero_one_or_two_objectives_emit_no_instance(self):
        cases = (
            {},
            {"CONFIDENTIALITY": "Low"},
            {"CONFIDENTIALITY": "Low", "INTEGRITY": "Moderate"},
        )

        for populated_source in cases:
            with self.subTest(populated=len(populated_source)):
                self.assertEqual(self._build(populated_source), [])

    def test_reviewed_legacy_labels_remain_allowed_and_unchanged(self):
        source_values = {
            "CONFIDENTIALITY": "Legacy LOE A",
            "INTEGRITY": "Legacy LOE C + DFARS",
            "AVAILABILITY": "Legacy LOE D + DFARS",
        }

        instances = self._build(source_values)

        self.assertEqual(len(instances), 1)
        self.assertEqual(
            instances[0]["payload"],
            dict(zip(OBJECTIVE_FIELDS, source_values.values())),
        )

    def test_cell_5_does_not_recreate_empty_optional_security_impact(self):
        cell_5 = _load_cell_5_for_empty_graph()
        registry_df = _RegistryDataFrame(
            [
                {"NODE_PATH": ROOT_PATH, "PARENT_NODE_PATH": None},
                {
                    "NODE_PATH": CHARACTERISTICS_PATH,
                    "PARENT_NODE_PATH": ROOT_PATH,
                },
                {
                    "NODE_PATH": SECURITY_IMPACT_PATH,
                    "PARENT_NODE_PATH": CHARACTERISTICS_PATH,
                },
            ]
        )

        nodes, edges = cell_5["build_oscal_graph"](
            _SourceDataFrame(),
            object(),
            registry_df,
            "SSP",
            "unit-test-source",
            "unit-test-table",
        )

        self.assertEqual(
            [node["ELEMENT_PATH"] for node in nodes],
            [ROOT_PATH, CHARACTERISTICS_PATH],
        )
        self.assertNotIn(
            SECURITY_IMPACT_PATH,
            {node["ELEMENT_PATH"] for node in nodes},
        )
        self.assertEqual(len(edges), 1)

    def test_other_structural_singleton_behavior_is_unchanged(self):
        cell_5 = _load_cell_5_for_empty_graph()
        should_materialize = cell_5[
            "_should_materialize_structural_singleton"
        ]

        self.assertTrue(should_materialize(ROOT_PATH, ROOT_PATH))
        self.assertTrue(
            should_materialize(CHARACTERISTICS_PATH, ROOT_PATH)
        )
        self.assertFalse(should_materialize(COLLECTION_PATH, ROOT_PATH))
        self.assertFalse(
            should_materialize(SECURITY_IMPACT_PATH, ROOT_PATH)
        )


if __name__ == "__main__":
    unittest.main()
