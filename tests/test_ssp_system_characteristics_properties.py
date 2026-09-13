import contextlib
import datetime
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
PROPS_PATH = "system-security-plan.system-characteristics.props[]"
SYSTEM_IDS_PATH = "system-security-plan.system-characteristics.system-ids[]"
SECURITY_IMPACT_PATH = (
    "system-security-plan.system-characteristics.security-impact-level"
)



def _run_graph_cells(path, init_globals=None):
    """Exercise the frozen policy oracle with its matching frozen graph."""
    import datetime
    import hashlib
    import json
    import re
    import uuid

    cell_4_path = LEGACY_CELL_4_PATH
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
        # Keep freshly defined legacy oracle helpers attached to this namespace.
        # Intentional test doubles still override their production counterparts.
        if code is not None and Path(code.co_filename) == cell_4_path:
            continue
        namespace[name] = value
    path = LEGACY_CELL_4_PATH.with_name("legacy_cell5_pre_direct_dispatch.py")
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"),
         namespace)
    return namespace


def _load_cell_4():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return runpy.run_path(
            str(LEGACY_CELL_4_PATH),
            init_globals={
                "ARCHER_VALUE_LOOKUP": {
                    "101": "Mission Critical",
                    "102": "Business Support",
                },
                "CONFIG": {"SOURCE_SYSTEM_NAME": "unit-test"},
                "FIPS_199_VALUE_LOOKUP": {},
                "hashlib": hashlib,
                "json": json,
                "re": re,
                "uuid": uuid,
            },
        )


def _load_cell_5():
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        return _run_graph_cells(
            str(CELL_5_PATH),
            init_globals={
                "CONFIG": {
                    "IDENTITY_VERSION": "unit-test-v1",
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
                    uuid.uuid5(uuid.NAMESPACE_URL, "|".join(parts))
                ),
            },
        )


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


def _property_row(source_field="INFORMATION_SYSTEM_TYPE"):
    return {
        "SOURCE_FIELD_NAME": source_field,
        "OWNER_ELEMENT_PATH": PROPS_PATH,
        "OSCAL_ELEMENT_PATH": PROPS_PATH,
        "OSCAL_FIELD_NAME": "value",
        "MAPPING_TYPE": "Extension Property",
        "TRANSFORMATION_LOGIC": "Resolve Archer select value",
        "STATUS": "Mapped",
    }


def _system_id_row(source_field="SAP_ID"):
    return {
        "SOURCE_FIELD_NAME": source_field,
        "OWNER_ELEMENT_PATH": SYSTEM_IDS_PATH,
        "OSCAL_ELEMENT_PATH": SYSTEM_IDS_PATH + ".id",
        "OSCAL_FIELD_NAME": "id",
        "MAPPING_TYPE": "Direct",
        "TRANSFORMATION_LOGIC": "",
        "STATUS": "Mapped",
    }


def _security_objective_row(source_field, target_field):
    return {
        "SOURCE_FIELD_NAME": source_field,
        "OWNER_ELEMENT_PATH": SECURITY_IMPACT_PATH,
        "OSCAL_ELEMENT_PATH": SECURITY_IMPACT_PATH + "." + target_field,
        "OSCAL_FIELD_NAME": target_field,
        "MAPPING_TYPE": "Transform",
        "TRANSFORMATION_LOGIC": "Map to FIPS 199 security objective",
        "STATUS": "Mapped",
    }


class SystemCharacteristicsPropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell_4 = _load_cell_4()

    def _build(self, source_obj, mapping_rows=None):
        return self.cell_4["build_element_instances"](
            source_obj,
            "private-source-record",
            PROPS_PATH,
            mapping_rows or [_property_row()],
        )

    def test_archer_select_values_emit_oscal_string_properties(self):
        instances = self._build(
            {
                "INFORMATION_SYSTEM_TYPE": {
                    "ValuesListIds": ["101", "102"]
                }
            }
        )

        self.assertEqual(
            [instance["payload"]["value"] for instance in instances],
            ["Mission Critical", "Business Support"],
        )
        self.assertEqual(
            [instance["instance_key"] for instance in instances],
            [
                self.cell_4["_source_value_instance_key"](
                    "INFORMATION_SYSTEM_TYPE",
                    "Mission Critical",
                ),
                self.cell_4["_source_value_instance_key"](
                    "INFORMATION_SYSTEM_TYPE",
                    "Business Support",
                ),
            ],
        )

    def test_property_identity_is_value_based_and_deduplicated(self):
        forward = self._build(
            {"INFORMATION_SYSTEM_TYPE": ["first", "second", "first"]}
        )
        reverse = self._build(
            {"INFORMATION_SYSTEM_TYPE": ["second", "first"]}
        )

        self.assertEqual(len(forward), 2)
        self.assertEqual(
            {item["instance_key"] for item in forward},
            {item["instance_key"] for item in reverse},
        )

    def test_scalar_property_values_are_canonical_strings(self):
        cases = (
            (True, "true"),
            (False, "false"),
            (42, "42"),
            ("  reviewed text  ", "reviewed text"),
        )

        for source_value, expected in cases:
            with self.subTest(source_value=source_value):
                instances = self._build(
                    {"INFORMATION_SYSTEM_TYPE": source_value}
                )
                self.assertEqual(instances[0]["payload"]["value"], expected)

    def test_unresolved_structured_property_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "OSCAL property value must resolve to a scalar",
        ):
            self._build({"INFORMATION_SYSTEM_TYPE": {"Id": "101"}})

    def test_nonfinite_or_blank_property_fails_closed(self):
        for source_value in (float("nan"), float("inf"), "   "):
            with self.subTest(source_value=source_value):
                with self.assertRaisesRegex(
                    ValueError,
                    "nonblank finite scalar",
                ):
                    self._build({"INFORMATION_SYSTEM_TYPE": source_value})

    def test_transient_helper_does_not_emit_a_property(self):
        rows = [_property_row("HELPER_PTA_CALC")]
        self.assertEqual(
            self._build({"HELPER_PTA_CALC": True}, rows),
            [],
        )

    def test_system_id_uses_value_identity_and_string_payload(self):
        instances = self.cell_4["build_element_instances"](
            {"SAP_ID": 12345},
            "private-source-record",
            SYSTEM_IDS_PATH,
            [_system_id_row()],
        )

        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["payload"], {"id": "12345"})
        self.assertEqual(
            instances[0]["instance_key"],
            self.cell_4["_value_instance_key"]("12345"),
        )
        self.assertNotEqual(instances[0]["instance_key"], "singleton")

    def test_duplicate_system_id_mapping_is_deduplicated(self):
        rows = [_system_id_row("SAP_ID"), _system_id_row("SAP_ID")]
        instances = self.cell_4["build_element_instances"](
            {"SAP_ID": "same-id"},
            "private-source-record",
            SYSTEM_IDS_PATH,
            rows,
        )
        self.assertEqual(len(instances), 1)

    def test_conflicting_singleton_candidates_fail_without_values(self):
        target = "security-objective-confidentiality"
        rows = [
            _security_objective_row(
                "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY", target
            ),
            _security_objective_row(
                "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE", target
            ),
            _security_objective_row(
                "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY",
                "security-objective-integrity",
            ),
            _security_objective_row(
                "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY",
                "security-objective-availability",
            ),
        ]
        with self.assertRaisesRegex(
            ValueError,
            "Singleton target has conflicting populated mappings",
        ) as raised:
            self.cell_4["build_element_instances"](
                {
                    "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY": "Low",
                    "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE": "High",
                    "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY": "Moderate",
                    "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY": "Low",
                },
                "private-source-record",
                SECURITY_IMPACT_PATH,
                rows,
            )
        self.assertNotIn("Low", str(raised.exception))
        self.assertNotIn("High", str(raised.exception))

    def test_identical_singleton_candidates_are_order_independent(self):
        target = "security-objective-confidentiality"
        first = _security_objective_row(
            "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY", target
        )
        second = _security_objective_row(
            "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE", target
        )
        other_rows = [
            _security_objective_row(
                "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY",
                "security-objective-integrity",
            ),
            _security_objective_row(
                "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY",
                "security-objective-availability",
            ),
        ]
        source_obj = {
            "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY": "Low",
            "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE": "low",
            "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY": "Moderate",
            "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY": "High",
        }

        forward = self.cell_4["build_element_instances"](
            source_obj,
            "private-source-record",
            SECURITY_IMPACT_PATH,
            [first, second] + other_rows,
        )
        reverse = self.cell_4["build_element_instances"](
            source_obj,
            "private-source-record",
            SECURITY_IMPACT_PATH,
            [second, first] + other_rows,
        )
        self.assertEqual(forward, reverse)

    def test_unreviewed_security_objective_label_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "Security objective contains an unreviewed label",
        ):
            self.cell_4["transform_security_objective"]("Unreviewed")


class SystemCharacteristicsRegistryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell_5 = _load_cell_5()

    @staticmethod
    def _registry_rows(props_rule="SOURCE_FIELD_NAME+VALUE"):
        return [
            {
                "OSCAL_MODEL_KEY": "SSP",
                "NODE_PATH": PROPS_PATH,
                "PARENT_NODE_PATH": (
                    "system-security-plan.system-characteristics"
                ),
                "IS_COLLECTION": True,
                "INSTANCE_KEY_RULE": props_rule,
                "PROCESS_ORDER": 3,
                "IS_ACTIVE": True,
                "ITEM_PATH": "$",
            },
            {
                "OSCAL_MODEL_KEY": "SSP",
                "NODE_PATH": SYSTEM_IDS_PATH,
                "PARENT_NODE_PATH": (
                    "system-security-plan.system-characteristics"
                ),
                "IS_COLLECTION": True,
                "INSTANCE_KEY_RULE": "VALUE",
                "PROCESS_ORDER": 3,
                "IS_ACTIVE": True,
                "ITEM_PATH": "$",
            },
        ]

    def test_recorded_collection_contract_is_accepted(self):
        rows = self.cell_5["_canonical_registry_rows"](
            _RegistryDataFrame(self._registry_rows()),
            "SSP",
        )
        self.assertEqual(len(rows), 2)

    def test_collection_instance_rule_drift_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "registry instance rule is invalid",
        ):
            self.cell_5["_canonical_registry_rows"](
                _RegistryDataFrame(self._registry_rows("SOURCE_FIELD_NAME")),
                "SSP",
            )


if __name__ == "__main__":
    unittest.main()
