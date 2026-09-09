import contextlib
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
    REPO_ROOT / "notebooks" / "cells" / "05_registry_graph_builder.py"
)


def _load_cell_4(mapping_rows=None):
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(CELL_4_PATH),
            init_globals={
                "ARCHER_VALUE_LOOKUP": {},
                "CONFIG": {"SOURCE_SYSTEM_NAME": "unit-test-source"},
                "FIPS_199_VALUE_LOOKUP": {},
                "MAPPINGS_BY_ELEMENT_PATH": {
                    "system-security-plan.metadata.responsible-parties[]": (
                        mapping_rows or []
                    )
                },
                "hashlib": hashlib,
                "json": json,
                "re": re,
                "uuid": uuid,
            },
        )


def _load_cell_5():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(CELL_5_PATH),
            init_globals={
                "MAPPINGS_BY_ELEMENT_PATH": {
                    (
                        "system-security-plan.metadata."
                        "responsible-parties[]"
                    ): [
                        {
                            "SOURCE_FIELD_NAME": "INFORMATION_OWNER_IO",
                        }
                    ]
                },
                "RESPONSIBLE_PARTY_ROLE_IDS": {
                    "INFORMATION_OWNER_IO": "information-owner",
                },
            },
        )


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


class ResponsiblePartyIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell = _load_cell_4()

    def test_same_party_reuses_uuid_across_roles(self):
        information_owner = self.cell["transform_responsible_party"](
            "ssp-record",
            "INFORMATION_OWNER_IO",
            {"Id": "person-42"},
        )
        system_owner = self.cell["transform_responsible_party"](
            "ssp-record",
            "INFORMATION_SYSTEM_OWNER_ISO",
            {"UserId": "person-42"},
        )

        self.assertNotEqual(
            information_owner["role-id"], system_owner["role-id"]
        )
        self.assertEqual(
            information_owner["party-uuids"],
            system_owner["party-uuids"],
        )

    def test_duplicate_references_are_deduplicated_in_source_order(self):
        transformed = self.cell["transform_responsible_party"](
            "ssp-record",
            "AUTHORIZING_OFFICIAL_AO",
            [
                {"Id": "person-1"},
                {"UserId": "person-1"},
                {"ContentId": "person-2"},
            ],
        )

        self.assertEqual(len(transformed["party-uuids"]), 2)
        self.assertNotEqual(
            transformed["party-uuids"][0],
            transformed["party-uuids"][1],
        )

    def test_wrapper_reference_ids_are_stable(self):
        transformed = self.cell["transform_responsible_party"](
            "ssp-record",
            "PRIVACY_OFFICER_PO",
            {"ContentIds": [101, 101, 202]},
        )

        self.assertEqual(len(transformed["party-uuids"]), 2)

    def test_reference_without_stable_identifier_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "stable identifier"):
            self.cell["transform_responsible_party"](
                "ssp-record",
                "INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO",
                {"Name": "not-an-identity"},
            )

    def test_boolean_reference_identifier_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "identifier is invalid"):
            self.cell["transform_responsible_party"](
                "ssp-record",
                "INFORMATION_OWNER_IO",
                True,
            )

    def test_roles_are_emitted_only_for_populated_approved_mappings(self):
        mapping_rows = [
            {
                "SOURCE_FIELD_NAME": "INFORMATION_OWNER_IO",
                "MAPPING_TYPE": "Transform",
                "STATUS": "Mapped",
            },
            {
                "SOURCE_FIELD_NAME": "AUTHORIZING_OFFICIAL_AO",
                "MAPPING_TYPE": "Transform",
                "STATUS": "Mapped",
            },
            {
                "SOURCE_FIELD_NAME": "PRIVACY_OFFICER_PO",
                "MAPPING_TYPE": "TBD",
                "STATUS": "More Information Required",
            },
        ]
        cell = _load_cell_4(mapping_rows)

        instances = cell["build_element_instances"](
            {
                "INFORMATION_OWNER_IO": {"Id": "person-1"},
                "AUTHORIZING_OFFICIAL_AO": {"UserId": "person-2"},
                "PRIVACY_OFFICER_PO": {"Id": "person-3"},
            },
            "ssp-record",
            cell["METADATA_ROLES_ELEMENT_PATH"],
            [],
        )

        self.assertEqual(
            instances,
            [
                {
                    "instance_key": "information-owner",
                    "payload": {
                        "id": "information-owner",
                        "title": "Information Owner",
                    },
                    "parent_instance_key": None,
                },
                {
                    "instance_key": "authorizing-official",
                    "payload": {
                        "id": "authorizing-official",
                        "title": "Authorizing Official",
                    },
                    "parent_instance_key": None,
                },
            ],
        )

    def test_missing_roles_registry_path_fails_closed(self):
        cell = _load_cell_5()
        registry = _RegistryDataFrame(
            [
                {
                    "NODE_PATH": "system-security-plan",
                    "PARENT_NODE_PATH": None,
                    "PROCESS_ORDER": 1,
                },
                {
                    "NODE_PATH": "system-security-plan.metadata",
                    "PARENT_NODE_PATH": "system-security-plan",
                    "PROCESS_ORDER": 2,
                },
                {
                    "NODE_PATH": (
                        "system-security-plan.metadata.responsible-parties[]"
                    ),
                    "PARENT_NODE_PATH": "system-security-plan.metadata",
                    "PROCESS_ORDER": 10,
                },
            ]
        )

        with self.assertRaisesRegex(ValueError, "missing metadata.roles"):
            cell["_canonical_registry_rows"](registry, "SSP")

    def test_governed_roles_registry_path_is_accepted(self):
        cell = _load_cell_5()
        registry = _RegistryDataFrame(
            [
                {
                    "NODE_PATH": "system-security-plan",
                    "PARENT_NODE_PATH": None,
                    "PROCESS_ORDER": 1,
                },
                {
                    "NODE_PATH": "system-security-plan.metadata",
                    "PARENT_NODE_PATH": "system-security-plan",
                    "PROCESS_ORDER": 2,
                },
                {
                    "NODE_PATH": "system-security-plan.metadata.roles[]",
                    "PARENT_NODE_PATH": "system-security-plan.metadata",
                    "PROCESS_ORDER": 9,
                },
                {
                    "NODE_PATH": "system-security-plan.metadata.parties[]",
                    "PARENT_NODE_PATH": "system-security-plan.metadata",
                    "PROCESS_ORDER": 10,
                },
                {
                    "NODE_PATH": (
                        "system-security-plan.metadata.responsible-parties[]"
                    ),
                    "PARENT_NODE_PATH": "system-security-plan.metadata",
                    "PROCESS_ORDER": 11,
                },
            ]
        )

        rows = cell["_canonical_registry_rows"](registry, "SSP")
        role_rows = [
            row
            for row in rows
            if row["element_path"]
            == "system-security-plan.metadata.roles[]"
        ]
        self.assertEqual(len(role_rows), 1)
        self.assertEqual(
            role_rows[0]["parent_path"], "system-security-plan.metadata"
        )


if __name__ == "__main__":
    unittest.main()
