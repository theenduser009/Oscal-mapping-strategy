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
CELL_4_PATH = (
    REPO_ROOT
    / "notebooks"
    / "cells"
    / "04_parsing_transform_payload_helpers.py"
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



def _run_graph_cells(path, init_globals=None):
    """Run dependent notebook cells in the same namespace, as Snowflake does."""
    import datetime
    import hashlib
    import json
    import re
    import uuid

    cell_4_path = Path(path).with_name("04_parsing_transform_payload_helpers.py")
    namespace = {
        "datetime": datetime, "hashlib": hashlib, "json": json,
        "re": re, "uuid": uuid, "ARCHER_VALUE_LOOKUP": {},
        "FIPS_199_VALUE_LOOKUP": {}, "MAPPINGS_BY_ELEMENT_PATH": {},
    }
    supplied = dict(init_globals or {})
    namespace.update(supplied)
    exec(compile(cell_4_path.read_text(encoding="utf-8"),
                 str(cell_4_path), "exec"), namespace)
    for name, value in supplied.items():
        code = getattr(value, "__code__", None)
        # Keep freshly defined production helpers attached to this namespace.
        # Intentional test doubles still override their production counterparts.
        if code is not None and Path(code.co_filename) == cell_4_path:
            continue
        namespace[name] = value
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"),
         namespace)
    return namespace


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
        return _run_graph_cells(
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


def _load_cell_4():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
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


def _component_mapping_row(source_field, component_type):
    return {
        "SOURCE_FIELD_NAME": source_field,
        "OWNER_ELEMENT_PATH": COMPONENT_PATH,
        "OSCAL_ELEMENT_PATH": COMPONENT_PATH,
        "OSCAL_FIELD_NAME": "",
        "MAPPING_TYPE": "Reference",
        "TRANSFORMATION_LOGIC": f"Create {component_type} component",
        "STATUS": "Mapped",
    }


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

    def test_component_payload_receives_node_uuid(self):
        component_uuid = str(uuid.uuid4())
        payload = self.cell_5["_payload_with_instance_uuid"](
            COMPONENT_PATH,
            {"type": "software"},
            component_uuid,
        )
        self.assertEqual(
            payload,
            {"type": "software", "uuid": component_uuid},
        )

    def test_component_payload_rejects_conflicting_uuid(self):
        with self.assertRaisesRegex(
            ValueError,
            "Component payload uuid conflicts with node uuid",
        ):
            self.cell_5["_payload_with_instance_uuid"](
                COMPONENT_PATH,
                {"type": "software", "uuid": str(uuid.uuid4())},
                str(uuid.uuid4()),
            )


class ComponentReferenceEmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell_4 = _load_cell_4()

    def test_object_references_use_canonical_content_id_and_type(self):
        rows = [_component_mapping_row("SOFTWARE", "software")]
        instances = self.cell_4["build_element_instances"](
            {
                "SOFTWARE": [
                    {"ContentId": 202, "LevelId": 7},
                    {"ContentId": "101", "LevelId": 7},
                ]
            },
            "private-source-record",
            COMPONENT_PATH,
            rows,
        )
        self.assertEqual(
            instances,
            [
                {
                    "instance_key": "101",
                    "payload": {"type": "software"},
                    "parent_instance_key": None,
                },
                {
                    "instance_key": "202",
                    "payload": {"type": "software"},
                    "parent_instance_key": None,
                },
            ],
        )

    def test_scalar_reference_members_are_supported(self):
        rows = [
            _component_mapping_row(
                "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM",
                "interconnection",
            )
        ]
        instances = self.cell_4["build_element_instances"](
            {
                "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": [
                    303,
                    "404",
                ]
            },
            "private-source-record",
            COMPONENT_PATH,
            rows,
        )
        self.assertEqual(
            [item["instance_key"] for item in instances],
            ["303", "404"],
        )
        self.assertTrue(
            all(
                item["payload"] == {"type": "interconnection"}
                for item in instances
            )
        )

    def test_same_content_id_and_type_deduplicates_across_fields(self):
        rows = [
            _component_mapping_row("INTERCONNECTIONS", "interconnection"),
            _component_mapping_row(
                "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM",
                "interconnection",
            ),
        ]
        instances = self.cell_4["build_element_instances"](
            {
                "INTERCONNECTIONS": [
                    {"ContentId": "same-private-id", "LevelId": 9}
                ],
                "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": [
                    "same-private-id"
                ],
            },
            "private-source-record",
            COMPONENT_PATH,
            rows,
        )
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["instance_key"], "same-private-id")

    def test_same_content_id_with_conflicting_types_fails_without_value(self):
        rows = [
            _component_mapping_row("SOFTWARE", "software"),
            _component_mapping_row("HARDWARE", "hardware"),
        ]
        with self.assertRaisesRegex(
            ValueError,
            "Component ContentId resolves to conflicting types",
        ) as raised:
            self.cell_4["build_element_instances"](
                {
                    "SOFTWARE": [{"ContentId": "private-conflict-id"}],
                    "HARDWARE": [{"ContentId": "private-conflict-id"}],
                },
                "private-source-record",
                COMPONENT_PATH,
                rows,
            )
        self.assertNotIn("private-conflict-id", str(raised.exception))

    def test_populated_object_without_content_id_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "Component reference is missing ContentId",
        ):
            self.cell_4["build_element_instances"](
                {"SOFTWARE": [{"LevelId": 7}]},
                "private-source-record",
                COMPONENT_PATH,
                [_component_mapping_row("SOFTWARE", "software")],
            )

    def test_mapping_type_signal_drift_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "Component mapping type signal does not match approved contract",
        ):
            self.cell_4["build_element_instances"](
                {"SOFTWARE": [{"ContentId": "private-id"}]},
                "private-source-record",
                COMPONENT_PATH,
                [_component_mapping_row("SOFTWARE", "hardware")],
            )


if __name__ == "__main__":
    unittest.main()
