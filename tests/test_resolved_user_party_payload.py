import runpy
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
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


def _resolved_member(identifier="42", status="MATCHED"):
    return {
        "Id": identifier,
        "HasRead": True,
        "HasUpdate": False,
        "HasDelete": False,
        "ResolvedUser": {
            "ContractVersion": "archer-meta-user-v1",
            "LookupStatus": status,
            "EEID": "E00042" if status == "MATCHED" else None,
            "FIRST_NAME": "Ada" if status != "USER_NOT_FOUND" else None,
            "MIDDLE_NAME": None,
            "LAST_NAME": "Lovelace" if status != "USER_NOT_FOUND" else None,
        },
    }


class ResolvedUserPartyPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _cell()

    def test_resolved_name_enriches_party_without_changing_identity(self):
        row = _row()
        enriched_context = _context([row])
        plain_context = _context([row])

        enriched_source = {"INFORMATION_OWNER_IO": {"UserList": [_resolved_member()]}}
        plain_source = {"INFORMATION_OWNER_IO": {"UserList": [{"Id": "42"}]}}

        enriched = self.ns["_metadata_party_instances"](
            PARTIES, enriched_source, "ssp-1", "parties",
            {"parent_instance_rule": "singleton"}, enriched_context,
        )
        plain = self.ns["_metadata_party_instances"](
            PARTIES, plain_source, "ssp-1", "parties",
            {"parent_instance_rule": "singleton"}, plain_context,
        )

        self.assertEqual(enriched[0]["instance_key"], plain[0]["instance_key"])
        self.assertEqual(enriched[0]["payload"]["uuid"], plain[0]["payload"]["uuid"])
        self.assertEqual(enriched[0]["payload"]["type"], "person")
        self.assertEqual(enriched[0]["payload"]["name"], "Ada Lovelace")
        self.assertNotIn("external-ids", enriched[0]["payload"])

    def test_eeid_external_id_requires_configured_absolute_uri_scheme(self):
        context = _context([_row()], scheme="urn:example:eeid")
        source = {"INFORMATION_OWNER_IO": {"UserList": [_resolved_member()]}}
        parties = self.ns["_metadata_party_instances"](
            PARTIES, source, "ssp-1", "parties",
            {"parent_instance_rule": "singleton"}, context,
        )
        self.assertEqual(
            parties[0]["payload"]["external-ids"],
            [{"scheme": "urn:example:eeid", "id": "E00042"}],
        )

    def test_user_not_found_preserves_identity_only(self):
        context = _context([_row()])
        source = {"INFORMATION_OWNER_IO": {"UserList": [_resolved_member(status="USER_NOT_FOUND")]}}
        parties = self.ns["_metadata_party_instances"](
            PARTIES, source, "ssp-1", "parties",
            {"parent_instance_rule": "singleton"}, context,
        )
        self.assertEqual(set(parties[0]["payload"]), {"uuid", "type"})

    def test_same_party_plain_and_enriched_references_merge_without_rekey(self):
        rows = [_row("FIELD_A", "role-a"), _row("FIELD_B", "role-b")]
        context = _context(rows)
        source = {
            "FIELD_A": {"UserList": [_resolved_member("42")]},
            "FIELD_B": {"UserList": [{"Id": "42"}]},
        }
        parties = self.ns["_metadata_party_instances"](
            PARTIES, source, "ssp-1", "parties",
            {"parent_instance_rule": "singleton"}, context,
        )
        assignments = self.ns["_metadata_party_instances"](
            ASSIGNMENTS, source, "ssp-1", "assignments",
            {"parent_instance_rule": "singleton"}, context,
        )
        self.assertEqual(len(parties), 1)
        self.assertEqual(parties[0]["payload"]["name"], "Ada Lovelace")
        self.assertEqual(len(assignments), 2)
        self.assertTrue(all(
            item["payload"]["party-uuids"] == [parties[0]["instance_key"]]
            for item in assignments
        ))

    def test_conflicting_resolved_names_fail_closed(self):
        rows = [_row("FIELD_A", "role-a"), _row("FIELD_B", "role-b")]
        context = _context(rows)
        first = _resolved_member("42")
        second = _resolved_member("42")
        second["ResolvedUser"]["FIRST_NAME"] = "Grace"
        source = {"FIELD_A": {"UserList": [first]}, "FIELD_B": {"UserList": [second]}}
        with self.assertRaisesRegex(ValueError, "conflicting enriched payload"):
            self.ns["_metadata_party_instances"](
                PARTIES, source, "ssp-1", "parties",
                {"parent_instance_rule": "singleton"}, context,
            )


if __name__ == "__main__":
    unittest.main()
