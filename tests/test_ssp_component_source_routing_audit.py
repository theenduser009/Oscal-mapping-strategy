import ast
from pathlib import Path
import re
import runpy
import unittest


REPO_ROOT = Path(__file__).parents[1]
AUDIT_PATH = (
    REPO_ROOT
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_component_source_routing_audit.py"
)

EXPECTED_COMPONENT_PATH = (
    "system-security-plan.system-implementation.components[]"
)
EXPECTED_COMPONENT_SOURCE_TYPES = {
    "SUBSYSTEMS": "system",
    "SOFTWARE": "software",
    "HARDWARE": "hardware",
    "INTERCONNECTIONS": "interconnection",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": "interconnection",
    "SAP_INTAKE_FORM_INTERCONNECTIONS": "interconnection",
}
EXPECTED_EVIDENCE_SOURCES = {
    "ARCHER_CONTENT_INTERCONNECTIONS_RAW": {
        "field_candidates": {
            "title": ("INTERCONNECTION_NAME", "THIRD_PARTY_NAME"),
            "description": ("DESCRIPTION", "THIRD_PARTY_DESCRIPTION"),
            "status": (),
        },
    },
    "ARCHER_CONTENT_SOFTWARE_RAW": {
        "field_candidates": {
            "title": ("SOFTWARE_NAME", "BUSINESS_NAME"),
            "description": ("DESCRIPTION",),
            "status": (
                "INSTALL_STATUS",
                "OPERATIONAL_STATUS",
                "RECORD_STATUS",
                "SERVICENOW_LIFE_CYCLE_STAGE_STATUS",
            ),
        },
    },
}
EXPECTED_ACCEPTED_BASELINE = {
    "reference_occurrences": 4804,
    "source_record_component_pairs": 4792,
    "graph_component_nodes": 4792,
    "distinct_component_ids": 1436,
    "field_occurrences": {
        "SUBSYSTEMS": 0,
        "SOFTWARE": 7,
        "HARDWARE": 1,
        "INTERCONNECTIONS": 4444,
        "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": 352,
        "SAP_INTAKE_FORM_INTERCONNECTIONS": 0,
    },
}


def _load_helpers():
    return runpy.run_path(
        str(AUDIT_PATH),
        init_globals={"_ROUTING_AUDIT_SKIP_EXECUTION": True},
    )


def _mapping_row(source_field, component_type, **overrides):
    row = {
        "SOURCE_FIELD_NAME": source_field,
        "OWNER_ELEMENT_PATH": EXPECTED_COMPONENT_PATH,
        "OSCAL_ELEMENT_PATH": EXPECTED_COMPONENT_PATH,
        "OSCAL_FIELD_NAME": "",
        "MAPPING_TYPE": "Reference",
        "TRANSFORMATION_LOGIC": f"Create {component_type} component",
        "STATUS": "Mapped",
    }
    row.update(overrides)
    return row


def _mapping_rows():
    return [
        _mapping_row(source_field, component_type)
        for source_field, component_type
        in EXPECTED_COMPONENT_SOURCE_TYPES.items()
    ]


def _type_resolver(mapping_row):
    return EXPECTED_COMPONENT_SOURCE_TYPES[
        mapping_row["SOURCE_FIELD_NAME"]
    ]


def _subscript_root_name(node):
    current = node
    while isinstance(current, ast.Subscript):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


class ComponentSourceRoutingAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helpers = _load_helpers()
        cls.source = AUDIT_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_constants_match_exact_excel_component_scope(self):
        self.assertEqual(
            self.helpers["ROUTING_COMPONENT_PATH"],
            EXPECTED_COMPONENT_PATH,
        )
        self.assertEqual(
            self.helpers["ROUTING_COMPONENT_SOURCE_TYPES"],
            EXPECTED_COMPONENT_SOURCE_TYPES,
        )

    def test_evidence_contract_matches_the_accepted_discovery(self):
        self.assertEqual(
            self.helpers["ROUTING_EVIDENCE_SOURCES"],
            EXPECTED_EVIDENCE_SOURCES,
        )
        self.assertEqual(
            self.helpers["ROUTING_ACCEPTED_BASELINE"],
            EXPECTED_ACCEPTED_BASELINE,
        )
        self.assertIn("AMBIGUOUS_{}_SOURCE_ROUTE", self.source)
        self.assertIn("category_populated_ids", self.source)

    def test_exact_six_excel_rows_produce_the_source_type_contract(self):
        contract = self.helpers["_routing_mapping_contract"](
            _mapping_rows(),
            _type_resolver,
        )
        self.assertEqual(
            contract,
            [
                {
                    "source_field": source_field,
                    "component_type": component_type,
                }
                for source_field, component_type in (
                    EXPECTED_COMPONENT_SOURCE_TYPES.items()
                )
            ],
        )

    def test_missing_duplicate_and_unexpected_component_rows_fail_closed(self):
        validate = self.helpers["_routing_mapping_contract"]
        valid_rows = _mapping_rows()
        cases = (
            (valid_rows[:-1], "missing"),
            (valid_rows + [dict(valid_rows[0])], "duplicate"),
            (
                valid_rows
                + [_mapping_row("UNAPPROVED_COMPONENT_SOURCE", "software")],
                "unexpected",
            ),
        )
        for rows, label in cases:
            with self.subTest(label=label):
                with self.assertRaises((RuntimeError, ValueError)):
                    validate(rows, _type_resolver)

    def test_mapping_owner_type_and_component_type_drift_fail_closed(self):
        validate = self.helpers["_routing_mapping_contract"]
        cases = []

        wrong_owner = _mapping_rows()
        wrong_owner[0] = {
            **wrong_owner[0],
            "OWNER_ELEMENT_PATH": "system-security-plan.metadata",
        }
        cases.append((wrong_owner, _type_resolver, "owner"))

        wrong_mapping_type = _mapping_rows()
        wrong_mapping_type[1] = {
            **wrong_mapping_type[1],
            "MAPPING_TYPE": "Direct",
        }
        cases.append((wrong_mapping_type, _type_resolver, "mapping type"))

        def wrong_type_resolver(mapping_row):
            if mapping_row["SOURCE_FIELD_NAME"] == "HARDWARE":
                return "software"
            return _type_resolver(mapping_row)

        cases.append((_mapping_rows(), wrong_type_resolver, "component type"))

        for rows, resolver, label in cases:
            with self.subTest(label=label):
                with self.assertRaises((RuntimeError, ValueError)):
                    validate(rows, resolver)

    def test_runtime_state_requires_a_read_only_validated_ssp(self):
        validate = self.helpers["_routing_validate_runtime_state"]
        valid_config = {
            "OSCAL_MODEL": "SSP",
            "EXECUTE_WRITES": False,
        }
        valid_result = {
            "validation_passed": True,
            "pre_write_validation_passed": True,
            "writes_executed": False,
        }
        validate(valid_config, valid_result)

        cases = (
            (
                {**valid_config, "OSCAL_MODEL": "SAP"},
                valid_result,
                "SSP",
            ),
            (
                {**valid_config, "EXECUTE_WRITES": True},
                valid_result,
                "EXECUTE_WRITES",
            ),
            (
                valid_config,
                {**valid_result, "validation_passed": False},
                "validation",
            ),
            (
                valid_config,
                {**valid_result, "pre_write_validation_passed": False},
                "pre-write",
            ),
            (
                valid_config,
                {**valid_result, "writes_executed": True},
                "read-only",
            ),
            (valid_config, None, "run result"),
        )
        for config, run_result, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(RuntimeError, message):
                    validate(config, run_result)

    def test_safe_name_removes_control_and_identifier_punctuation(self):
        safe_name = self.helpers["_routing_safe_name"]
        self.assertEqual(
            safe_name('TABLE\n"private"; DROP'),
            "TABLE_private_DROP",
        )
        self.assertEqual(safe_name(" DB.SCHEMA.TABLE "), "DB.SCHEMA.TABLE")
        self.assertEqual(safe_name(None), "")
        self.assertLessEqual(len(safe_name("x" * 1000)), 256)

    def test_evidence_sources_are_a_bounded_explicit_allowlist(self):
        evidence_sources = self.helpers["ROUTING_EVIDENCE_SOURCES"]
        if isinstance(evidence_sources, dict):
            evidence_sources = list(evidence_sources)

        self.assertIsInstance(
            evidence_sources,
            (list, tuple, set, frozenset),
        )
        self.assertTrue(evidence_sources)
        for object_name in evidence_sources:
            with self.subTest(object_name=object_name):
                self.assertIsInstance(object_name, str)
                self.assertEqual(object_name, object_name.strip())
                self.assertTrue(object_name)
                self.assertNotRegex(object_name, r"[*%?]")
                normalized = re.sub(
                    r"[^A-Z0-9]+",
                    "",
                    object_name.upper(),
                )
                self.assertNotIn("JSUSRTARGETTABLETMP", normalized)

        self.assertIn("INFORMATION_SCHEMA", self.source.upper())
        self.assertIn(
            'upper(col("TABLE_NAME")).isin(*evidence_table_names)',
            self.source,
        )
        self.assertGreaterEqual(
            self.source.count("ROUTING_EVIDENCE_SOURCES"),
            2,
        )

    def test_source_has_no_dml_ddl_writes_or_client_row_iteration(self):
        called_attributes = {
            node.func.attr.lower()
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        forbidden_attributes = {
            "cache_result",
            "create_dataframe",
            "create_or_replace_temp_view",
            "delete",
            "drop_table",
            "insert",
            "insert_into",
            "merge",
            "remove",
            "save_as_table",
            "sql",
            "to_local_iterator",
            "to_pandas",
            "truncate",
            "update",
            "use_database",
            "use_schema",
            "write",
        }
        self.assertFalse(called_attributes & forbidden_attributes)

    def test_component_identifiers_and_payloads_are_never_collected(self):
        collect_receivers = []
        for node in ast.walk(self.tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr.lower() == "collect"
            ):
                collect_receivers.append(
                    ast.unparse(node.func.value).lower()
                )

        sensitive_receiver = re.compile(
            r"(?:component.*id|reference.*id|source_df|payload|curated)"
        )
        for receiver in collect_receivers:
            with self.subTest(receiver=receiver):
                if sensitive_receiver.search(receiver):
                    self.assertTrue(
                        ".agg(" in receiver or ".group_by(" in receiver,
                        "Sensitive rows may only be collected after an "
                        "aggregate operation",
                    )

    def test_incomplete_audit_cannot_configure_or_approve_a_source(self):
        source_upper = self.source.upper()
        self.assertIn("INCOMPLETE", source_upper)
        self.assertIn("CANNOT APPROVE", source_upper)

        mutated_config_targets = []
        for node in ast.walk(self.tree):
            targets = []
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                if isinstance(node, ast.Assign):
                    targets = node.targets
                else:
                    targets = [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Subscript)
                    and (
                        _subscript_root_name(target) or ""
                    ).lower() == "config"
                ):
                    mutated_config_targets.append(ast.unparse(target))
        self.assertFalse(mutated_config_targets)

        self.assertNotIn("SOURCE APPROVED", source_upper)
        self.assertNotIn("ROUTE APPROVED", source_upper)


if __name__ == "__main__":
    unittest.main()

