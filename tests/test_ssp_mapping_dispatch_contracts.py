import ast
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
VALIDATION_PATHS = (
    REPO_ROOT
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_crosswalk_review.py",
    REPO_ROOT
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_payload_semantics_validation.py",
    REPO_ROOT
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_required_field_gap_review.py",
)

SYSTEM_CHARACTERISTICS_PATH = "system-security-plan.system-characteristics"
AUTHORIZATION_BOUNDARY_PATH = (
    SYSTEM_CHARACTERISTICS_PATH + ".authorization-boundary"
)
SECURITY_IMPACT_PATH = SYSTEM_CHARACTERISTICS_PATH + ".security-impact-level"
PROPS_PATH = SYSTEM_CHARACTERISTICS_PATH + ".props[]"
STATUS_PATH = SYSTEM_CHARACTERISTICS_PATH + ".status"

EXPECTED_TEXT_CONTRACTS = {
    "AUTHORIZATION_PACKAGE_NAME": {
        "owner_path": SYSTEM_CHARACTERISTICS_PATH,
        "target_field": "system-name",
    },
    "ACRONYM": {
        "owner_path": SYSTEM_CHARACTERISTICS_PATH,
        "target_field": "system-name-short",
    },
    "MISSION_PURPOSE": {
        "owner_path": SYSTEM_CHARACTERISTICS_PATH,
        "target_field": "description",
    },
    "AUTHORIZATION_BOUNDARY_DESCRIPTION": {
        "owner_path": AUTHORIZATION_BOUNDARY_PATH,
        "target_field": "description",
    },
}

EXPECTED_CIA_CONTRACTS = {
    "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY": (
        "security-objective-confidentiality"
    ),
    "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE": (
        "security-objective-confidentiality"
    ),
    "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY": "security-objective-integrity",
    "INTEGRITY_CONTROL_CATEGORY_OVERRIDE": "security-objective-integrity",
    "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY": (
        "security-objective-availability"
    ),
    "AVAILABILITY_CONTROL_CATEGORY_OVERRIDE": (
        "security-objective-availability"
    ),
    "PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY": "security-objective-integrity",
    "PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY": (
        "security-objective-availability"
    ),
    "CNSS_AVAILABILITY_RATING": "security-objective-availability",
    "CNSS_CONFIDENTIALITY_RATING": "security-objective-confidentiality",
    "CNSS_INTEGRITY_RATING": "security-objective-integrity",
}

EXPECTED_LEGACY_VALUES = {
    "Legacy LOE A",
    "Legacy LOE B",
    "Legacy LOE C",
    "Legacy LOE D",
    "Legacy LOE A + DFARS",
    "Legacy LOE B + DFARS",
    "Legacy LOE C + DFARS",
    "Legacy LOE D + DFARS",
}


def _load_cell_4():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(CELL_4_PATH),
            init_globals={
                "ARCHER_VALUE_LOOKUP": {
                    "101": "Mission Critical",
                    "102": "Business Support",
                },
                "CONFIG": {"SOURCE_SYSTEM_NAME": "unit-test"},
                "FIPS_199_VALUE_LOOKUP": {},
                "MAPPINGS_BY_ELEMENT_PATH": {},
                "hashlib": hashlib,
                "json": json,
                "re": re,
                "uuid": uuid,
            },
        )


def _mapping_row(source_field, owner_path, target_field, mapping_type):
    return {
        "SOURCE_FIELD_NAME": source_field,
        "OWNER_ELEMENT_PATH": owner_path,
        "OSCAL_ELEMENT_PATH": owner_path + "." + target_field,
        "OSCAL_FIELD_NAME": target_field,
        "MAPPING_TYPE": mapping_type,
        "TRANSFORMATION_LOGIC": "unit-test approved mapping",
        "STATUS": "Mapped",
    }


def _normalized_legacy_values(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            continue
        for item in node.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                if item.value.startswith("legacy-loe-"):
                    found.add(item.value)
    return found


class MappingDispatchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell = _load_cell_4()

    def test_four_text_contracts_are_exact_and_nonblank(self):
        self.assertEqual(
            self.cell["APPROVED_TEXT_MAPPING_CONTRACTS"],
            EXPECTED_TEXT_CONTRACTS,
        )
        self.assertEqual(len(EXPECTED_TEXT_CONTRACTS), 4)

        for source_field, contract in EXPECTED_TEXT_CONTRACTS.items():
            row = _mapping_row(
                source_field,
                contract["owner_path"],
                contract["target_field"],
                "Direct",
            )
            with self.subTest(source_field=source_field, case="valid"):
                self.assertEqual(
                    self.cell["apply_mapping_transform"](
                        row, "  approved text  ", "private-record"
                    ),
                    "  approved text  ",
                )
            for invalid in ("   ", 7, True, ["text"], {"Value": "text"}):
                with self.subTest(source_field=source_field, invalid=invalid):
                    with self.assertRaisesRegex(ValueError, "nonblank text"):
                        self.cell["apply_mapping_transform"](
                            row, invalid, "private-record"
                        )

            mutations = (
                {"OWNER_ELEMENT_PATH": "system-security-plan.metadata"},
                {"OSCAL_FIELD_NAME": "wrong-target"},
                {"MAPPING_TYPE": "Transform"},
            )
            for mutation in mutations:
                invalid_row = dict(row)
                invalid_row.update(mutation)
                with self.subTest(source_field=source_field, mutation=mutation):
                    with self.assertRaisesRegex(ValueError, "contract"):
                        self.cell["apply_mapping_transform"](
                            invalid_row, "populated", "private-record"
                        )

    def test_eleven_cia_source_target_pairs_are_the_exact_allowlist(self):
        self.assertEqual(
            self.cell["SECURITY_IMPACT_SOURCE_OBJECTIVES"],
            EXPECTED_CIA_CONTRACTS,
        )
        self.assertEqual(len(EXPECTED_CIA_CONTRACTS), 11)

        objective_fields = {
            "security-objective-confidentiality",
            "security-objective-integrity",
            "security-objective-availability",
        }
        for source_field, target_field in EXPECTED_CIA_CONTRACTS.items():
            row = _mapping_row(
                source_field,
                SECURITY_IMPACT_PATH,
                target_field,
                "Transform",
            )
            with self.subTest(source_field=source_field, case="valid"):
                self.assertEqual(
                    self.cell["apply_mapping_transform"](
                        row, "Low", "private-record"
                    ),
                    "low",
                )
            wrong_target = sorted(objective_fields - {target_field})[0]
            wrong_row = dict(row)
            wrong_row["OSCAL_FIELD_NAME"] = wrong_target
            with self.subTest(source_field=source_field, case="wrong-target"):
                with self.assertRaisesRegex(ValueError, "source/target"):
                    self.cell["apply_mapping_transform"](
                        wrong_row, "Low", "private-record"
                    )

        for mapping_type in ("Direct", "Transform", "Direct / Transform"):
            row = _mapping_row(
                "CNSS_CONFIDENTIALITY_RATING",
                SECURITY_IMPACT_PATH,
                "security-objective-confidentiality",
                mapping_type,
            )
            with self.subTest(mapping_type=mapping_type):
                self.assertEqual(
                    self.cell["apply_mapping_transform"](
                        row, "High", "private-record"
                    ),
                    "high",
                )

    def test_security_impact_unknown_source_is_skipped_only_when_empty(self):
        row = _mapping_row(
            "RECOMMENDED_SECURITY_CATEGORY",
            SECURITY_IMPACT_PATH,
            "security-objective-confidentiality",
            "Transform",
        )
        self.assertIs(
            self.cell["apply_mapping_transform"](
                row, None, "private-record"
            ),
            self.cell["SKIP_VALUE"],
        )
        with self.assertRaisesRegex(ValueError, "source is not approved"):
            self.cell["apply_mapping_transform"](
                row, "Low", "private-record"
            )

    def test_wrapped_select_ids_resolve_strictly(self):
        row = _mapping_row(
            "INFORMATION_SYSTEM_TYPE",
            PROPS_PATH,
            "value",
            "Extension Property",
        )
        wrappers = (
            {"ValuesListIds": ["101", "102"]},
            {"ValueListIds": ["101"]},
            {"value_list_ids": ["102"]},
            {"VALUES-LIST-IDS": ["101"]},
        )
        expected = (
            ["Mission Critical", "Business Support"],
            ["Mission Critical"],
            ["Business Support"],
            ["Mission Critical"],
        )
        for wrapped, expected_values in zip(wrappers, expected):
            with self.subTest(wrapper=wrapped):
                self.assertEqual(
                    self.cell["apply_mapping_transform"](
                        row, wrapped, "private-record"
                    ),
                    expected_values,
                )

        for unresolved in (
            {"ValuesListIds": ["999999"]},
            {"ValueListIds": [{"Id": "101"}]},
        ):
            with self.subTest(unresolved=unresolved):
                with self.assertRaisesRegex(ValueError, "unresolved|invalid") as raised:
                    self.cell["apply_mapping_transform"](
                        row, unresolved, "private-record"
                    )
                self.assertNotIn("999999", str(raised.exception))

    def test_ordinary_scalar_extension_values_remain_valid(self):
        row = _mapping_row(
            "INFORMATION_SYSTEM_TYPE",
            PROPS_PATH,
            "value",
            "Extension Property",
        )
        cases = (("plain label", "plain label"), (42, 42), (True, True))
        for source_value, expected in cases:
            with self.subTest(source_value=source_value):
                self.assertEqual(
                    self.cell["apply_mapping_transform"](
                        row, source_value, "private-record"
                    ),
                    expected,
                )

    def test_unsupported_transform_families_have_no_raw_fallback(self):
        for mapping_type in (
            "Transform",
            "Direct / Transform",
            "Extension Property",
            "Reference",
        ):
            row = _mapping_row(
                "UNAPPROVED_POPULATED_FIELD",
                SYSTEM_CHARACTERISTICS_PATH,
                "unapproved-target",
                mapping_type,
            )
            with self.subTest(mapping_type=mapping_type):
                with self.assertRaisesRegex(ValueError, "no approved"):
                    self.cell["apply_mapping_transform"](
                        row, "must-not-leak", "private-record"
                    )

        tbd_row = _mapping_row(
            "UNAPPROVED_POPULATED_FIELD",
            SYSTEM_CHARACTERISTICS_PATH,
            "unapproved-target",
            "TBD",
        )
        self.assertIs(
            self.cell["apply_mapping_transform"](
                tbd_row, "value", "private-record"
            ),
            self.cell["SKIP_VALUE"],
        )

    def test_explicit_status_comments_and_party_handlers_are_preserved(self):
        status_row = _mapping_row(
            "OPERATIONAL_STATUS", STATUS_PATH, "state", "Transform"
        )
        self.assertEqual(
            self.cell["apply_mapping_transform"](
                status_row, "Operational", "private-record"
            ),
            {"state": "operational"},
        )

        comments_row = _mapping_row(
            "AUTHORIZATION_COMMENTS",
            STATUS_PATH,
            "remarks",
            "Extension Property",
        )
        self.assertEqual(
            self.cell["apply_mapping_transform"](
                comments_row, "approved remark", "private-record"
            ),
            "approved remark",
        )

        party_row = _mapping_row(
            "INFORMATION_OWNER_IO",
            "system-security-plan.metadata.responsible-parties[]",
            "party-uuids",
            "Direct",
        )
        with self.assertRaisesRegex(ValueError, "must be Transform"):
            self.cell["apply_mapping_transform"](
                party_row, {"Id": "private-party"}, "private-record"
            )

    def test_legacy_security_vocabulary_is_aligned_and_preserved(self):
        self.assertEqual(
            self.cell["REVIEWED_LEGACY_SECURITY_VALUES"],
            EXPECTED_LEGACY_VALUES,
        )
        self.assertEqual(len(EXPECTED_LEGACY_VALUES), 8)

        for value in EXPECTED_LEGACY_VALUES:
            with self.subTest(value=value):
                self.assertEqual(
                    self.cell["transform_security_objective"](value), value
                )

        expected_normalized = {
            "-".join(value.strip().lower().replace("_", "-").split())
            for value in EXPECTED_LEGACY_VALUES
        }
        self.assertEqual(len(expected_normalized), 8)
        for path in VALIDATION_PATHS:
            with self.subTest(validator=path.name):
                self.assertEqual(
                    _normalized_legacy_values(path), expected_normalized
                )


if __name__ == "__main__":
    unittest.main()
