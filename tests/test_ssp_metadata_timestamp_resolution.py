import contextlib
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


CELL_4_PATH = (
    Path(__file__).parents[1]
    / "notebooks"
    / "cells"
    / "04_parsing_transform_payload_helpers.py"
)
FULL_NOTEBOOK_PATH = (
    Path(__file__).parents[1]
    / "notebooks"
    / "NB_ARCHER_OSCAL_MAPPER_V1.py"
)
METADATA_PATH = "system-security-plan.metadata"
OTHER_PATH = "system-security-plan.system-characteristics"
TEST_METADATA_TITLE = "Example SSP"


def _load_helpers():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(LEGACY_CELL_4_PATH),
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


def _timestamp_row(source_field, target_field, mapping_type="Transform"):
    return {
        "SOURCE_FIELD_NAME": source_field,
        "OWNER_ELEMENT_PATH": METADATA_PATH,
        "OSCAL_ELEMENT_PATH": f"{METADATA_PATH}.{target_field}",
        "OSCAL_FIELD_NAME": target_field,
        "MAPPING_TYPE": mapping_type,
        "TRANSFORMATION_LOGIC": "Preserve the source timestamp exactly",
        "STATUS": "Mapped",
    }


def _direct_row(source_field, owner_path, target_field):
    return {
        "SOURCE_FIELD_NAME": source_field,
        "OWNER_ELEMENT_PATH": owner_path,
        "OSCAL_ELEMENT_PATH": f"{owner_path}.{target_field}",
        "OSCAL_FIELD_NAME": target_field,
        "MAPPING_TYPE": "Direct",
        "TRANSFORMATION_LOGIC": "",
        "STATUS": "Mapped",
    }


class MetadataTimestampResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helpers = _load_helpers()

    def _build(self, source_obj, mapping_rows, element_path=METADATA_PATH):
        source_obj = dict(source_obj)
        if element_path == METADATA_PATH:
            source_obj.setdefault(
                "AUTHORIZATION_PACKAGE_NAME",
                TEST_METADATA_TITLE,
            )
        return self.helpers["build_element_instances"](
            source_obj,
            "private-source-record",
            element_path,
            mapping_rows,
        )

    def test_authoritative_notebook_cell_4_matches_copy_ready_file(self):
        notebook = FULL_NOTEBOOK_PATH.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        split_cell = CELL_4_PATH.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        start_marker = (
            "# %% Cell 4 - Shared metadata runtime and reusable transformations"
        )
        end_marker = (
            "# %% Cell 5 - Registry-driven canonical node and edge graph"
        )
        extracted = notebook.split(start_marker, 1)[1].split(
            end_marker, 1
        )[0]
        extracted = f"{start_marker}{extracted}".rstrip()

        self.assertEqual(extracted, split_cell.rstrip())

    def test_one_candidate_is_preserved_exactly(self):
        values = {
            "published": "  2026-09-09T08:15:00  ",
            "last-modified": "2026-09-09 08:16:17.123",
        }
        for target_field, source_value in values.items():
            with self.subTest(target_field=target_field):
                instances = self._build(
                    {"ONLY_SOURCE": source_value},
                    [_timestamp_row("ONLY_SOURCE", target_field)],
                )

                self.assertEqual(len(instances), 1)
                self.assertEqual(instances[0]["instance_key"], "singleton")
                self.assertEqual(
                    instances[0]["payload"],
                    {
                        "title": TEST_METADATA_TITLE,
                        target_field: source_value,
                    },
                )

    def test_identical_populated_candidates_resolve_once(self):
        source_value = "2026-09-09T08:15:00-04:00"
        for target_field in ("published", "last-modified"):
            with self.subTest(target_field=target_field):
                instances = self._build(
                    {"FIRST_SOURCE": source_value, "SECOND_SOURCE": source_value},
                    [
                        _timestamp_row("FIRST_SOURCE", target_field),
                        _timestamp_row("SECOND_SOURCE", target_field),
                    ],
                )

                self.assertEqual(
                    instances[0]["payload"],
                    {
                        "title": TEST_METADATA_TITLE,
                        target_field: source_value,
                    },
                )

    def test_conflicting_candidates_fail_in_any_row_order_without_values(self):
        first_value = "private-first-timestamp"
        second_value = "private-second-timestamp"
        for target_field in ("published", "last-modified"):
            rows = [
                _timestamp_row("FIRST_SOURCE", target_field),
                _timestamp_row("SECOND_SOURCE", target_field),
            ]
            messages = []
            for ordered_rows in (rows, list(reversed(rows))):
                with self.subTest(
                    target_field=target_field,
                    order=ordered_rows[0]["SOURCE_FIELD_NAME"],
                ):
                    with self.assertRaises(ValueError) as raised:
                        self._build(
                            {
                                "FIRST_SOURCE": first_value,
                                "SECOND_SOURCE": second_value,
                            },
                            ordered_rows,
                        )
                    message = str(raised.exception)
                    messages.append(message)
                    self.assertEqual(
                        message,
                        f"Conflicting populated metadata {target_field} sources",
                    )
                    self.assertNotIn(first_value, message)
                    self.assertNotIn(second_value, message)

            self.assertEqual(messages[0], messages[1])

    def test_missing_candidates_omit_timestamp_field(self):
        rows = [
            _timestamp_row("FIRST_SOURCE", "published"),
            _timestamp_row("SECOND_SOURCE", "published"),
            _direct_row("TITLE", METADATA_PATH, "title"),
        ]

        instances = self._build(
            {"FIRST_SOURCE": None, "SECOND_SOURCE": "", "TITLE": "Example SSP"},
            rows,
        )

        self.assertEqual(
            instances[0]["payload"],
            {"title": TEST_METADATA_TITLE},
        )
        self.assertNotIn("published", instances[0]["payload"])

    def test_invalid_or_non_string_candidate_fails_closed(self):
        invalid_values = (
            20260909,
            True,
            {"value": "2026-09-09"},
            ["2026-09-09"],
            "   ",
        )
        for target_field in ("published", "last-modified"):
            for source_value in invalid_values:
                with self.subTest(
                    target_field=target_field,
                    value_type=type(source_value).__name__,
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        rf"Metadata {re.escape(target_field)} must be a nonblank source string",
                    ):
                        self._build(
                            {"ONLY_SOURCE": source_value},
                            [_timestamp_row("ONLY_SOURCE", target_field)],
                        )

    def test_timestamp_mapping_type_must_be_transform(self):
        for target_field in ("published", "last-modified"):
            with self.subTest(target_field=target_field):
                with self.assertRaisesRegex(
                    ValueError,
                    rf"Metadata {re.escape(target_field)} mapping type must be Transform",
                ):
                    self._build(
                        {"ONLY_SOURCE": "2026-09-09T08:15:00"},
                        [
                            _timestamp_row(
                                "ONLY_SOURCE",
                                target_field,
                                mapping_type="Direct",
                            )
                        ],
                    )

    def test_unrelated_direct_mapping_behavior_is_unchanged(self):
        instances = self._build(
            {"SYSTEM_NAME": "Example System"},
            [_direct_row("SYSTEM_NAME", OTHER_PATH, "system-name")],
            element_path=OTHER_PATH,
        )

        self.assertEqual(
            instances,
            [
                {
                    "instance_key": "singleton",
                    "payload": {"system-name": "Example System"},
                    "parent_instance_key": None,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
