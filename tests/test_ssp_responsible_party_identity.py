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


def _load_cell_4():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(CELL_4_PATH),
            init_globals={
                "ARCHER_VALUE_LOOKUP": {},
                "CONFIG": {"SOURCE_SYSTEM_NAME": "unit-test-source"},
                "FIPS_199_VALUE_LOOKUP": {},
                "hashlib": hashlib,
                "json": json,
                "re": re,
                "uuid": uuid,
            },
        )


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


if __name__ == "__main__":
    unittest.main()
