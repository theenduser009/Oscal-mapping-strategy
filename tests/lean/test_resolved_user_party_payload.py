import runpy
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CELL = ROOT / "notebooks" / "cells" / "04_parsing_transform_payload_helpers.py"

ROLES = "system-security-plan.metadata.roles[]"
PARTIES = "system-security-plan.metadata.parties[]"
ASSIGNMENTS = "system-security-plan.metadata.responsible-parties[]"


def _params(row):
    return row.get("TRANSFORM_PARAMS") or {}


def _cell():
    return runpy.run_path(str(CELL), init_globals={"_metadata_params": _params})


def _row(field="INFORMATION_OWNER_IO", role="information-owner"):
    return {
        "SOURCE_FIELD_NAME": field,
        "TRANSFORM_ID": "direct",
        "RULE_ID": "test:" + field,
        "TRANSFORM_PARAMS": {
            "role_id": role,
            "role_title": role.replace("-", " ").title(),
            "parent_instance_rule": "singleton",
        },
    }


def _context(rows, scheme=None):
    config = {"SOURCE_SYSTEM_NAME": "ARCHER"}
    if scheme is not None:
        config["ARCHER_EEID_SCHEME"] = scheme
    return {
        "config": config,
        "compiled_plan": {
            "options": {},
            "reference_groups": [{
                "roles_path": ROLES,
                "parties_path": PARTIES,
                "assignments_path": ASSIGNMENTS,
                "party_type": "person",
            }],
        },
        "mappings_by_path": {ASSIGNMENTS: rows},
        "graph_report": {"STATUS": "NOT_RUN", "MAPPED_VALUES": 0, "MISSING_VALUES": 0},
    }


def _member(identifier="42", status="MATCHED"):
    return {
        "Id": identifier,
        "ResolvedUser": {
            "ContractVersion": "archer-meta-user-v1",
            "LookupStatus": status,
            "EEID": "E00042" if status == "MATCHED" else None,
            "FIRST_NAME": "Ada" if status != "USER_NOT_FOUND" else None,
            "MIDDLE_NAME": None,
            "LAST_NAME": "Lovelace" if status != "USER_NOT_FOUND" else None,
        },
    }


class ResolvedUserPartyLeanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _cell()

    def _parties(self, source, context):
        return self.ns["_metadata_party_instances"](
            PARTIES, source, "ssp-1", "parties",
            {"parent_instance_rule": "singleton"}, context,
        )

    def test_name_enrichment_preserves_party_identity(self):
        row = _row()
        enriched = self._parties(
            {"INFORMATION_OWNER_IO": {"UserList": [_member()]}},
            _context([row]),
        )
        plain = self._parties(
            {"INFORMATION_OWNER_IO": {"UserList": [{"Id": "42"}]}},
            _context([row]),
        )
        self.assertEqual(enriched[0]["instance_key"], plain[0]["instance_key"])
        self.assertEqual(enriched[0]["payload"]["uuid"], plain[0]["payload"]["uuid"])
        self.assertEqual("Ada Lovelace", enriched[0]["payload"]["name"])
        self.assertNotIn("external-ids", enriched[0]["payload"])

    def test_eeid_emits_only_with_configured_absolute_uri_scheme(self):
        row = _row()
        parties = self._parties(
            {"INFORMATION_OWNER_IO": {"UserList": [_member()]}},
            _context([row], "urn:example:eeid"),
        )
        self.assertEqual(
            [{"scheme": "urn:example:eeid", "id": "E00042"}],
            parties[0]["payload"]["external-ids"],
        )

    def test_user_not_found_keeps_identity_only(self):
        row = _row()
        parties = self._parties(
            {"INFORMATION_OWNER_IO": {"UserList": [_member(status="USER_NOT_FOUND")]}},
            _context([row]),
        )
        self.assertEqual({"uuid", "type"}, set(parties[0]["payload"]))

    def test_conflicting_enriched_names_fail_closed(self):
        rows = [_row("FIELD_A", "role-a"), _row("FIELD_B", "role-b")]
        a, b = _member(), _member()
        b["ResolvedUser"]["FIRST_NAME"] = "Grace"
        with self.assertRaisesRegex(ValueError, "conflicting enriched payload"):
            self._parties(
                {"FIELD_A": {"UserList": [a]}, "FIELD_B": {"UserList": [b]}},
                _context(rows),
            )


if __name__ == "__main__":
    unittest.main()
