import contextlib
import datetime
import io
import json
from pathlib import Path
import runpy
import unittest
import uuid


REPO_ROOT = Path(__file__).parents[1]
AUDIT_PATH = (
    REPO_ROOT
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_component_source_contract.py"
)
CELL_5_PATH = (
    REPO_ROOT
    / "notebooks"
    / "cells"
    / "05_registry_graph_builder.py"
)
COMPONENT_PATH = (
    "system-security-plan.system-implementation.components[]"
)
COMPONENT_FIELDS = (
    "SUBSYSTEMS",
    "SOFTWARE",
    "HARDWARE",
    "INTERCONNECTIONS",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM",
    "SAP_INTAKE_FORM_INTERCONNECTIONS",
)


class _SourceDataFrame:
    def __init__(self, rows):
        self.rows = rows

    def to_local_iterator(self):
        return iter(self.rows)


class _RegistryRow:
    def __init__(self, values):
        self.values = values

    def as_dict(self, recursive=True):
        del recursive
        return dict(self.values)


class _RegistryDataFrame:
    def __init__(self, rows):
        self.rows = rows

    def collect(self):
        return [_RegistryRow(row) for row in self.rows]


def _mapping_rows():
    rows = []
    for source_field in COMPONENT_FIELDS:
        rows.append(
            {
                "SOURCE_FIELD_NAME": source_field,
                "OWNER_ELEMENT_PATH": COMPONENT_PATH,
                "MAPPING_TYPE": "Reference",
                "TRANSFORMATION_LOGIC": "Create software component",
            }
        )
    return rows


def _run_contract(rows):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        runpy.run_path(
            str(AUDIT_PATH),
            init_globals={
                "CONFIG": {
                    "OSCAL_MODEL": "SSP",
                    "EXECUTE_WRITES": False,
                },
                "source_df": _SourceDataFrame(rows),
                "CANONICAL_MAPPING_ROWS": _mapping_rows(),
                "run_result": {
                    "validation_passed": True,
                    "pre_write_validation_passed": True,
                    "writes_executed": False,
                },
                "_parse_source_json": lambda row: row,
                "resolve_json_path": lambda obj, path: obj.get(path),
            },
        )
    return output.getvalue()


def _load_cell_5():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        return runpy.run_path(
            str(CELL_5_PATH),
            init_globals={
                "CONFIG": {
                    "IDENTITY_VERSION": "test-v1",
                    "OSCAL_VERSION": "1.2.3",
                    "SSP_DOCUMENT_VERSION": "1.0",
                },
                "MAPPINGS_BY_ELEMENT_PATH": {},
                "RESPONSIBLE_PARTY_ROLE_IDS": {},
                "datetime": datetime,
                "json": json,
                "_deterministic_hash": lambda *parts: "|".join(
                    str(part) for part in parts
                ),
                "_deterministic_uuid": lambda *parts: str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        "|".join(str(part) for part in parts),
                    )
                ),
            },
        )


def _component_registry_row(**overrides):
    row = {
        "OSCAL_MODEL_KEY": "SSP",
        "NODE_PATH": COMPONENT_PATH,
        "PARENT_NODE_PATH": "system-security-plan.system-implementation",
        "IS_COLLECTION": True,
        "INSTANCE_KEY_RULE": "CONTENT_ID",
        "PROCESS_ORDER": 3,
        "IS_ACTIVE": True,
        "ITEM_PATH": "$",
    }
    row.update(overrides)
    return row


class ComponentSourceContractTests(unittest.TestCase):
    def test_reports_aggregate_shape_without_values_or_identifiers(self):
        output = _run_contract(
            [
                {
                    "SUBSYSTEMS": [
                        {
                            "ContentId": "private-content-101",
                            "Name": "Private component name",
                            "Description": "Private component description",
                            "Status": "Private status",
                        },
                        {
                            "ContentId": "private-content-101",
                            "Name": "Private component name",
                        },
                    ],
                    "SOFTWARE": {
                        "ContentIds": [
                            "private-content-101",
                            "private-content-202",
                        ]
                    },
                    "HARDWARE": {"Id": "private-generic-id"},
                }
            ]
        )

        self.assertIn("COMPONENT SOURCE CONTRACT", output)
        self.assertIn("Fields with component mapping rows: 6", output)
        self.assertIn(
            "Records with cross-field shared governed IDs: 1",
            output,
        )
        self.assertIn("RESULT: COMPONENT SOURCE CONTRACT EVIDENCE CAPTURED", output)
        self.assertNotIn("private-content", output)
        self.assertNotIn("Private component", output)
        self.assertNotIn("private-generic", output)

    def test_refuses_to_run_when_mapper_writes_are_enabled(self):
        with self.assertRaisesRegex(RuntimeError, "EXECUTE_WRITES = False"):
            with contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(
                    str(AUDIT_PATH),
                    init_globals={
                        "CONFIG": {
                            "OSCAL_MODEL": "SSP",
                            "EXECUTE_WRITES": True,
                        },
                        "source_df": _SourceDataFrame([]),
                        "CANONICAL_MAPPING_ROWS": _mapping_rows(),
                        "run_result": {
                            "validation_passed": True,
                            "pre_write_validation_passed": True,
                            "writes_executed": False,
                        },
                        "_parse_source_json": lambda row: row,
                        "resolve_json_path": lambda obj, path: obj.get(path),
                    },
                )


class ComponentRegistryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell_5 = _load_cell_5()

    def test_recorded_component_collection_contract_is_accepted(self):
        rows = self.cell_5["_canonical_registry_rows"](
            _RegistryDataFrame([_component_registry_row()]),
            "SSP",
        )
        self.assertEqual(len(rows), 1)

    def test_component_identity_drift_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "Governed registry instance rule is invalid",
        ):
            self.cell_5["_canonical_registry_rows"](
                _RegistryDataFrame(
                    [_component_registry_row(INSTANCE_KEY_RULE="SOURCE_FIELD_NAME")]
                ),
                "SSP",
            )

    def test_component_parent_drift_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "Governed registry parent path is invalid",
        ):
            self.cell_5["_canonical_registry_rows"](
                _RegistryDataFrame(
                    [_component_registry_row(PARENT_NODE_PATH="wrong-parent")]
                ),
                "SSP",
            )


if __name__ == "__main__":
    unittest.main()
