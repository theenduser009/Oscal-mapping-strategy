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
    REPO_ROOT / "notebooks" / "cells" / "05_registry_graph_builder.py"
)
FULL_NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "NB_ARCHER_OSCAL_MAPPER_V1.py"

METADATA_PATH = "system-security-plan.metadata"
ROLES_PATH = METADATA_PATH + ".roles[]"
PARTIES_PATH = METADATA_PATH + ".parties[]"
RESPONSIBLE_PARTIES_PATH = METADATA_PATH + ".responsible-parties[]"

APPROVED_FIELDS = (
    "INFORMATION_OWNER_IO",
    "INFORMATION_SYSTEM_OWNER_ISO",
    "AUTHORIZING_OFFICIAL_AO",
    "INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO",
    "PRIVACY_OFFICER_PO",
)
EXPECTED_ROLE_IDS = {
    "INFORMATION_OWNER_IO": "information-owner",
    "INFORMATION_SYSTEM_OWNER_ISO": "system-owner",
    "AUTHORIZING_OFFICIAL_AO": "authorizing-official",
    "INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO": (
        "system-security-officer"
    ),
    "PRIVACY_OFFICER_PO": "privacy-officer",
}
TBD_FIELDS = (
    "INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE",
    "INFORMATION_SYSTEM_ADMINISTRATOR_ISA",
    "AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR",
    "SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO",
)



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


def _responsible_party_rows(include_duplicate=False):
    rows = [
        {
            "SOURCE_FIELD_NAME": field_name,
            "OWNER_ELEMENT_PATH": RESPONSIBLE_PARTIES_PATH,
            "OSCAL_ELEMENT_PATH": RESPONSIBLE_PARTIES_PATH,
            "MAPPING_TYPE": "Transform",
            "TRANSFORMATION_LOGIC": "Create party and role relationship",
            "STATUS": "Mapped",
        }
        for field_name in APPROVED_FIELDS
    ]
    rows.extend(
        {
            "SOURCE_FIELD_NAME": field_name,
            "OWNER_ELEMENT_PATH": RESPONSIBLE_PARTIES_PATH,
            "OSCAL_ELEMENT_PATH": RESPONSIBLE_PARTIES_PATH,
            "MAPPING_TYPE": "TBD",
            "TRANSFORMATION_LOGIC": "",
            "STATUS": "More Information Required",
        }
        for field_name in TBD_FIELDS
    )
    if include_duplicate:
        rows.insert(1, dict(rows[0]))
    return rows


def _source_object():
    return {
        "AUTHORIZATION_PACKAGE_NAME": "Example Authorization Package",
        "INFORMATION_OWNER_IO": {
            "UserList": [
                {"Id": "person-1"},
                {"UserId": "person-1"},
            ]
        },
        "INFORMATION_SYSTEM_OWNER_ISO": {
            "ContentIds": ["person-1", "person-2", "person-2"]
        },
        "AUTHORIZING_OFFICIAL_AO": {"Id": "person-3"},
        "INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO": {
            "UserId": "person-4"
        },
        "PRIVACY_OFFICER_PO": {"ContentId": "person-5"},
        "INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE": {"Id": "person-6"},
        "INFORMATION_SYSTEM_ADMINISTRATOR_ISA": {"Id": "person-7"},
        "AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR": {
            "Id": "person-8"
        },
        "SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO": {
            "Id": "person-9"
        },
    }


def _load_cell_4(mapping_rows=None):
    rows = _responsible_party_rows() if mapping_rows is None else mapping_rows
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(CELL_4_PATH),
            init_globals={
                "ARCHER_VALUE_LOOKUP": {},
                "CONFIG": {"SOURCE_SYSTEM_NAME": "unit-test-source"},
                "FIPS_199_VALUE_LOOKUP": {},
                "MAPPINGS_BY_ELEMENT_PATH": {
                    RESPONSIBLE_PARTIES_PATH: rows,
                },
                "hashlib": hashlib,
                "json": json,
                "re": re,
                "uuid": uuid,
            },
        )


def _load_cell_5(mapping_rows=None, config=None):
    rows = _responsible_party_rows() if mapping_rows is None else mapping_rows
    if config is None:
        config = {
            "OSCAL_VERSION": "1.2.3",
            "SSP_DOCUMENT_VERSION": "1.0",
        }
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return _run_graph_cells(
            str(CELL_5_PATH),
            init_globals={
                "CONFIG": config,
                "MAPPINGS_BY_ELEMENT_PATH": {
                    RESPONSIBLE_PARTIES_PATH: rows,
                },
                "RESPONSIBLE_PARTY_ROLE_IDS": EXPECTED_ROLE_IDS,
                "resolve_json_path": (
                    lambda source_obj, field_name: source_obj.get(field_name)
                ),
            },
        )


class _PassthroughSession:
    def create_dataframe(self, rows):
        return list(rows)


class _SourceDataFrame:
    def __init__(self, records):
        self._records = records

    def to_local_iterator(self):
        return iter(self._records)


def _load_cell_5_for_graph(cell_4, mapping_rows=None, build_override=None):
    rows = _responsible_party_rows() if mapping_rows is None else mapping_rows
    mappings = {
        RESPONSIBLE_PARTIES_PATH: rows,
    }
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return _run_graph_cells(
            str(CELL_5_PATH),
            init_globals={
                "CONFIG": {
                    "IDENTITY_VERSION": "unit-test-v1",
                    "SOURCE_SYSTEM_NAME": "unit-test-source",
                    "OSCAL_VERSION": "1.2.3",
                    "SSP_DOCUMENT_VERSION": "1.0",
                    "RUN_ID": "unit-test-run",
                },
                "MAPPINGS_BY_ELEMENT_PATH": mappings,
                "COMPONENT_HYDRATION_SOURCE_DFS": {},
                "_build_component_hydration_lookups": lambda *args: None,
                "RESPONSIBLE_PARTY_ROLE_IDS": EXPECTED_ROLE_IDS,
                "build_element_instances": (
                    build_override
                    if build_override is not None
                    else cell_4["build_element_instances"]
                ),
                "datetime": datetime,
                "json": json,
                "session": _PassthroughSession(),
                "_parse_source_json": lambda record: record["CURATED_JSON"],
                "_deterministic_hash": cell_4["_deterministic_hash"],
                "_deterministic_uuid": cell_4["_deterministic_uuid"],
                "resolve_json_path": cell_4["resolve_json_path"],
            },
        )


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


def _registry_rows(
    *,
    include_roles=True,
    include_parties=True,
    include_responsible_parties=True,
):
    rows = [
        {
            "NODE_PATH": "system-security-plan",
            "PARENT_NODE_PATH": None,
            "PROCESS_ORDER": 1,
        },
        {
            "NODE_PATH": METADATA_PATH,
            "PARENT_NODE_PATH": "system-security-plan",
            "PROCESS_ORDER": 2,
        },
    ]
    if include_responsible_parties:
        rows.append(
            {
                "NODE_PATH": RESPONSIBLE_PARTIES_PATH,
                "PARENT_NODE_PATH": METADATA_PATH,
                "PROCESS_ORDER": 12,
            }
        )
    if include_roles:
        rows.append(
            {
                "NODE_PATH": ROLES_PATH,
                "PARENT_NODE_PATH": METADATA_PATH,
                "PROCESS_ORDER": 10,
            }
        )
    if include_parties:
        rows.append(
            {
                "NODE_PATH": PARTIES_PATH,
                "PARENT_NODE_PATH": METADATA_PATH,
                "PROCESS_ORDER": 11,
            }
        )
    return rows


class CompleteMetadataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell_4 = _load_cell_4(_responsible_party_rows(True))
        cls.source_obj = _source_object()

    def test_split_cells_4_and_5_match_monolithic_notebook(self):
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
        for path, start_marker, end_marker in cases:
            with self.subTest(cell=path.name):
                split_cell = path.read_text(encoding="utf-8").replace(
                    "\r\n", "\n"
                )
                self.assertEqual(
                    _extract_notebook_cell(
                        notebook,
                        start_marker,
                        end_marker,
                    ),
                    split_cell.rstrip(),
                )

    def test_title_comes_from_authorization_package_name(self):
        instances = self.cell_4["build_element_instances"](
            self.source_obj,
            "ssp-record",
            METADATA_PATH,
            [],
        )

        self.assertEqual(len(instances), 1)
        self.assertEqual(
            instances[0]["payload"]["title"],
            self.source_obj["AUTHORIZATION_PACKAGE_NAME"],
        )

    def test_missing_or_blank_metadata_title_fails_closed(self):
        for source_obj in ({}, {"AUTHORIZATION_PACKAGE_NAME": "   "}):
            with self.subTest(source_obj=source_obj):
                with self.assertRaisesRegex(ValueError, "title"):
                    self.cell_4["build_element_instances"](
                        source_obj,
                        "ssp-record",
                        METADATA_PATH,
                        [],
                    )

    def test_non_string_metadata_title_fails_closed(self):
        for invalid_title in (False, 42, ["Example"], {"name": "Example"}):
            with self.subTest(title_type=type(invalid_title).__name__):
                with self.assertRaisesRegex(ValueError, "title"):
                    self.cell_4["build_element_instances"](
                        {"AUTHORIZATION_PACKAGE_NAME": invalid_title},
                        "ssp-record",
                        METADATA_PATH,
                        [],
                    )

    def test_metadata_document_version_is_fixed_at_one_point_zero(self):
        cell_5 = _load_cell_5()
        instances = [
            {
                "instance_key": "singleton",
                "payload": {"title": "Example Authorization Package"},
                "parent_instance_key": None,
            }
        ]

        result = cell_5["_inject_controlled_metadata_fields"](
            METADATA_PATH,
            instances,
        )

        self.assertEqual(result[0]["payload"]["version"], "1.0")
        self.assertEqual(result[0]["payload"]["oscal-version"], "1.2.3")

    def test_conflicting_document_version_fails_closed(self):
        cell_5 = _load_cell_5()
        instances = [
            {
                "instance_key": "singleton",
                "payload": {
                    "title": "Example Authorization Package",
                    "version": "2.0",
                },
                "parent_instance_key": None,
            }
        ]

        with self.assertRaisesRegex(ValueError, "version"):
            cell_5["_inject_controlled_metadata_fields"](
                METADATA_PATH,
                instances,
            )

    def test_missing_configured_document_version_fails_closed(self):
        cell_5 = _load_cell_5(
            config={
                "OSCAL_VERSION": "1.2.3",
            }
        )
        instances = [
            {
                "instance_key": "singleton",
                "payload": {"title": "Example Authorization Package"},
                "parent_instance_key": None,
            }
        ]

        with self.assertRaisesRegex(ValueError, "SSP_DOCUMENT_VERSION"):
            cell_5["_inject_controlled_metadata_fields"](
                METADATA_PATH,
                instances,
            )

    def _metadata_relationship_instances(self):
        outputs = {}
        for path in (ROLES_PATH, PARTIES_PATH, RESPONSIBLE_PARTIES_PATH):
            outputs[path] = self.cell_4["build_element_instances"](
                self.source_obj,
                "ssp-record",
                path,
                _responsible_party_rows(True)
                if path == RESPONSIBLE_PARTIES_PATH
                else [],
            )
        return outputs

    def test_five_approved_fields_create_roles_and_person_parties(self):
        outputs = self._metadata_relationship_instances()
        roles = outputs[ROLES_PATH]
        parties = outputs[PARTIES_PATH]
        assignments = outputs[RESPONSIBLE_PARTIES_PATH]

        self.assertEqual(len(roles), 5)
        self.assertEqual(len(assignments), 5)
        self.assertEqual(
            {instance["payload"]["id"] for instance in roles},
            set(EXPECTED_ROLE_IDS.values()),
        )
        self.assertTrue(parties)
        self.assertTrue(
            all(instance["payload"]["type"] == "person" for instance in parties)
        )

    def test_every_assignment_resolves_to_emitted_role_and_party(self):
        outputs = self._metadata_relationship_instances()
        role_ids = {
            instance["payload"]["id"] for instance in outputs[ROLES_PATH]
        }
        party_uuids = {
            instance["payload"]["uuid"] for instance in outputs[PARTIES_PATH]
        }

        for assignment in outputs[RESPONSIBLE_PARTIES_PATH]:
            payload = assignment["payload"]
            self.assertIn(payload["role-id"], role_ids)
            self.assertTrue(payload["party-uuids"])
            self.assertLessEqual(set(payload["party-uuids"]), party_uuids)

        referenced_party_uuids = {
            party_uuid
            for assignment in outputs[RESPONSIBLE_PARTIES_PATH]
            for party_uuid in assignment["payload"]["party-uuids"]
        }
        self.assertEqual(referenced_party_uuids, party_uuids)

    def test_tbd_fields_are_excluded_from_all_role_party_outputs(self):
        outputs = self._metadata_relationship_instances()
        serialized = json.dumps(outputs, sort_keys=True)

        for field_name in TBD_FIELDS:
            with self.subTest(field=field_name):
                self.assertNotIn(field_name, serialized)
        for party_number in range(6, 10):
            with self.subTest(party=party_number):
                excluded_uuid = self.cell_4["_party_uuid"](
                    "ssp-record",
                    f"person-{party_number}",
                )
                self.assertNotIn(excluded_uuid, serialized)

    def test_duplicate_references_and_mapping_rows_are_deduplicated(self):
        outputs = self._metadata_relationship_instances()

        role_ids = [
            instance["payload"]["id"] for instance in outputs[ROLES_PATH]
        ]
        assignment_role_ids = [
            instance["payload"]["role-id"]
            for instance in outputs[RESPONSIBLE_PARTIES_PATH]
        ]
        party_uuids = [
            instance["payload"]["uuid"] for instance in outputs[PARTIES_PATH]
        ]

        self.assertEqual(len(role_ids), len(set(role_ids)))
        self.assertEqual(
            len(assignment_role_ids),
            len(set(assignment_role_ids)),
        )
        self.assertEqual(len(party_uuids), len(set(party_uuids)))

    def test_role_party_output_order_is_deterministic(self):
        first = self._metadata_relationship_instances()
        second = self._metadata_relationship_instances()

        self.assertEqual(first, second)

    def test_registry_requires_roles_and_parties_paths(self):
        cell_5 = _load_cell_5()
        cases = (
            (False, True, "metadata.roles"),
            (True, False, "metadata.parties"),
        )
        for include_roles, include_parties, expected_error in cases:
            with self.subTest(missing=expected_error):
                registry = _RegistryDataFrame(
                    _registry_rows(
                        include_roles=include_roles,
                        include_parties=include_parties,
                    )
                )
                with self.assertRaisesRegex(ValueError, expected_error):
                    cell_5["_canonical_registry_rows"](registry, "SSP")

    def test_registry_requires_responsible_parties_path(self):
        cell_5 = _load_cell_5()
        registry = _RegistryDataFrame(
            _registry_rows(include_responsible_parties=False)
        )

        with self.assertRaisesRegex(ValueError, "responsible-parties"):
            cell_5["_canonical_registry_rows"](registry, "SSP")

    def test_registry_rejects_wrong_metadata_collection_parent(self):
        cell_5 = _load_cell_5()
        for path, expected_error in (
            (ROLES_PATH, "metadata.roles"),
            (PARTIES_PATH, "metadata.parties"),
            (RESPONSIBLE_PARTIES_PATH, "responsible-parties"),
        ):
            with self.subTest(path=path):
                rows = _registry_rows()
                for row in rows:
                    if row["NODE_PATH"] == path:
                        row["PARENT_NODE_PATH"] = "system-security-plan"
                with self.assertRaisesRegex(ValueError, expected_error):
                    cell_5["_canonical_registry_rows"](
                        _RegistryDataFrame(rows),
                        "SSP",
                    )

    def test_governed_role_and_party_registry_paths_are_accepted(self):
        cell_5 = _load_cell_5()
        rows = cell_5["_canonical_registry_rows"](
            _RegistryDataFrame(_registry_rows()),
            "SSP",
        )
        by_path = {row["element_path"]: row for row in rows}

        self.assertEqual(by_path[ROLES_PATH]["parent_path"], METADATA_PATH)
        self.assertEqual(by_path[PARTIES_PATH]["parent_path"], METADATA_PATH)

    def test_graph_closes_every_role_and_party_reference(self):
        cell_5 = _load_cell_5_for_graph(self.cell_4, _responsible_party_rows(True))
        nodes, _ = cell_5["build_oscal_graph"](
            _SourceDataFrame(
                [
                    {
                        "SOURCE_RECORD_ID": "ssp-record",
                        "CURATED_JSON": self.source_obj,
                    }
                ]
            ),
            None,
            _RegistryDataFrame(_registry_rows()),
            "SSP",
            "unit-test-source",
            "unit-test-table",
        )

        roles = [node for node in nodes if node["ELEMENT_PATH"] == ROLES_PATH]
        parties = [
            node for node in nodes if node["ELEMENT_PATH"] == PARTIES_PATH
        ]
        assignments = [
            node
            for node in nodes
            if node["ELEMENT_PATH"] == RESPONSIBLE_PARTIES_PATH
        ]
        role_id_counts = {}
        for node in roles:
            role_id = json.loads(node["METADATA_JSON"])["id"]
            role_id_counts[role_id] = role_id_counts.get(role_id, 0) + 1
        party_uuid_counts = {}
        for node in parties:
            payload = json.loads(node["METADATA_JSON"])
            self.assertEqual(payload["uuid"], node["OSCAL_UUID"])
            self.assertEqual(payload["uuid"], node["INSTANCE_KEY"])
            party_uuid_counts[node["OSCAL_UUID"]] = (
                party_uuid_counts.get(node["OSCAL_UUID"], 0) + 1
            )

        for node in assignments:
            payload = json.loads(node["METADATA_JSON"])
            self.assertEqual(role_id_counts.get(payload["role-id"]), 1)
            for party_uuid in payload["party-uuids"]:
                self.assertEqual(party_uuid_counts.get(party_uuid), 1)

    def test_graph_rejects_party_payload_uuid_mismatch(self):
        def build_with_mismatch(
            source_obj,
            source_record_id,
            path,
            rows,
            component_hydration_lookups=None,
        ):
            del (
                source_obj,
                source_record_id,
                rows,
                component_hydration_lookups,
            )
            if path == PARTIES_PATH:
                return [
                    {
                        "instance_key": "expected-party-uuid",
                        "payload": {
                            "uuid": "different-party-uuid",
                            "type": "person",
                        },
                        "parent_instance_key": None,
                    }
                ]
            if path == METADATA_PATH:
                return [
                    {
                        "instance_key": "singleton",
                        "payload": {"title": "Example Authorization Package"},
                        "parent_instance_key": None,
                    }
                ]
            return []

        cell_5 = _load_cell_5_for_graph(
            self.cell_4,
            build_override=build_with_mismatch,
        )
        with self.assertRaisesRegex(
            ValueError,
            "(?i)party.*uuid|uuid.*party",
        ):
            cell_5["build_oscal_graph"](
                _SourceDataFrame(
                    [
                        {
                            "SOURCE_RECORD_ID": "ssp-record",
                            "CURATED_JSON": self.source_obj,
                        }
                    ]
                ),
                None,
                _RegistryDataFrame(_registry_rows()),
                "SSP",
                "unit-test-source",
                "unit-test-table",
            )


if __name__ == "__main__":
    unittest.main()
