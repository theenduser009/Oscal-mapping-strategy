import ast
import hashlib
import json
from pathlib import Path

# Historical field-policy regression oracle; never imported by production.
LEGACY_CELL_4_PATH = Path(__file__).parents[1] / "tests/fixtures/legacy_cell4_pre_declarative.py"
import re
import runpy
import unittest
import uuid


REPO_ROOT = Path(__file__).parents[1]
FULL_NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "NB_ARCHER_OSCAL_MAPPER_V1.py"
CELL_1_PATH = (
    REPO_ROOT
    / "notebooks"
    / "cells"
    / "01_initialization_and_configuration.py"
)
CELL_2_PATH = (
    REPO_ROOT
    / "notebooks"
    / "cells"
    / "02_source_mapping_registry_inputs.py"
)
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
COMPONENT_PATH = "system-security-plan.system-implementation.components[]"

EXPECTED_HYDRATION_CONTRACT = {
    "software": {
        "source_table": (
            "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_SOFTWARE_RAW"
        ),
        "title_field": "SOFTWARE_NAME",
        "description_field": "DESCRIPTION",
    },
    "interconnection": {
        "source_table": (
            "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_INTERCONNECTIONS_RAW"
        ),
        "title_field": "INTERCONNECTION_NAME",
        "description_field": "DESCRIPTION",
    },
}
EXPECTED_HYDRATION_SOURCE_FIELDS = {
    "SOFTWARE",
    "INTERCONNECTIONS",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM",
}
EXPECTED_COMPONENT_SOURCE_TYPES = {
    "SUBSYSTEMS": "system",
    "SOFTWARE": "software",
    "HARDWARE": "hardware",
    "INTERCONNECTIONS": "interconnection",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": "interconnection",
    "SAP_INTAKE_FORM_INTERCONNECTIONS": "interconnection",
}


def _load_cell_4(**extra_globals):
    init_globals = {
        "ARCHER_VALUE_LOOKUP": {},
        "CONFIG": {"SOURCE_SYSTEM_NAME": "unit-test"},
        "FIPS_199_VALUE_LOOKUP": {},
        "hashlib": hashlib,
        "json": json,
        "re": re,
        "uuid": uuid,
    }
    init_globals.update(extra_globals)
    return runpy.run_path(str(LEGACY_CELL_4_PATH), init_globals=init_globals)


def _extract_notebook_cell(notebook, start_marker, end_marker):
    return (
        start_marker
        + notebook.split(start_marker, 1)[1].split(end_marker, 1)[0]
    ).rstrip()


def _load_standalone_function(path, function_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    function_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    namespace = {}
    exec(
        compile(
            ast.Module(body=[function_node], type_ignores=[]),
            str(path),
            "exec",
        ),
        namespace,
    )
    return namespace[function_name]


def _literal_assignment(path, assignment_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == assignment_name
            for target in node.targets
        )
    )
    return ast.literal_eval(assignment.value)



def _source_one_hydration_contract():
    from test_model_selection import cell_namespace
    for profile in cell_namespace("SSP")["SOURCE_PROFILES"]:
        if profile["SOURCE_KEY"] == "source-one":
            return profile["LOOKUP_CONTRACTS"]
    raise AssertionError("Source One hydration contract is missing")


def _database_write_attributes(source):
    """Do not confuse explicitly scoped report/config dict updates with DML."""
    writes = {"delete", "insert_into", "merge", "save_as_table",
              "truncate", "update", "write"}
    memory_updates = {
        ("_score_prepare", "report"),
        ("_score_finish", "report"),
        ("_ssp_finish", "context['graph_report']"),
        ("_prepare_model_context", "config"),
        ("_legacy_prepare_model_context", "config"),
        ("_metadata_prepare", "report"),
        ("_metadata_record_complete", "used_parties"),
        ("_metadata_party_instances", "parties"),
        ("_metadata_party_instances", "assigned_parties"),
        ("_metadata_finish", "report"),
        ("_prepare_model_context", "options"),
    }

    class Calls(ast.NodeVisitor):
        def __init__(self):
            self.scope = None
            self.found = set()

        def visit_FunctionDef(self, node):
            previous = self.scope
            self.scope = node.name
            self.generic_visit(node)
            self.scope = previous

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                attribute = node.func.attr.lower()
                memory_update = (
                    attribute == "update"
                    and (self.scope, ast.unparse(node.func.value)) in memory_updates
                )
                if attribute in writes and not memory_update:
                    self.found.add(attribute)
            self.generic_visit(node)

    calls = Calls()
    calls.visit(ast.parse(source))
    return calls.found


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


class ComponentPartialHydrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell_4 = _load_cell_4()
        cls.hydrate = staticmethod(
            cls.cell_4["_hydrate_component_payload"]
        )

    def test_contract_is_exactly_the_owner_approved_partial_scope(self):
        self.assertEqual(
            self.cell_4["COMPONENT_HYDRATION_CONTRACT"],
            EXPECTED_HYDRATION_CONTRACT,
        )
        self.assertEqual(
            set(self.cell_4["COMPONENT_HYDRATION_SOURCE_FIELDS"]),
            EXPECTED_HYDRATION_SOURCE_FIELDS,
        )

    def test_seventh_unexpected_component_mapping_fails_before_lookup_scan(self):
        cell_4 = _load_cell_4(
            COMPONENT_HYDRATION_SOURCE_CONTRACT=(
                EXPECTED_HYDRATION_CONTRACT
            ),
        )
        mapping_rows = [
            _component_mapping_row(source_field, component_type)
            for source_field, component_type
            in EXPECTED_COMPONENT_SOURCE_TYPES.items()
        ]
        mapping_rows.append(
            _component_mapping_row(
                "UNAPPROVED_COMPONENT_ROUTE",
                "software",
            )
        )
        hydration_source_dfs = {
            component_type: object()
            for component_type in EXPECTED_HYDRATION_CONTRACT
        }

        with self.assertRaisesRegex(
            RuntimeError,
            "Canonical component mapping contract has drifted",
        ):
            cell_4["_build_component_hydration_lookups"](
                object(),
                mapping_rows,
                hydration_source_dfs,
            )

    def test_software_uses_only_software_name_and_description(self):
        lookups = {
            "software": {
                "software-101": {
                    "title": "Approved software name",
                    "description": "Approved software description",
                    "status": "unapproved status",
                    "BUSINESS_NAME": "unapproved alternate name",
                }
            }
        }

        payload = self.hydrate("software", "software-101", lookups)

        self.assertEqual(
            payload,
            {
                "type": "software",
                "title": "Approved software name",
                "description": "Approved software description",
            },
        )
        self.assertNotIn("status", payload)
        self.assertNotIn("uuid", payload)
        self.assertNotIn("id", payload)

    def test_interconnection_uses_only_name_and_populated_description(self):
        lookups = {
            "interconnection": {
                "interconnection-202": {
                    "title": "Approved interconnection name",
                    "description": "Approved interconnection description",
                    "status": "unapproved status",
                    "THIRD_PARTY_NAME": "unapproved alternate name",
                }
            }
        }

        payload = self.hydrate(
            "interconnection",
            "interconnection-202",
            lookups,
        )

        self.assertEqual(
            payload,
            {
                "type": "interconnection",
                "title": "Approved interconnection name",
                "description": "Approved interconnection description",
            },
        )

    def test_blank_interconnection_description_is_omitted_not_invented(self):
        lookups = {
            "interconnection": {
                "interconnection-303": {
                    "title": "Interconnection with no description",
                    "description": "   ",
                }
            }
        }

        payload = self.hydrate(
            "interconnection",
            "interconnection-303",
            lookups,
        )

        self.assertEqual(
            payload,
            {
                "type": "interconnection",
                "title": "Interconnection with no description",
            },
        )

    def test_hardware_system_and_status_remain_deferred(self):
        lookups = {
            "hardware": {
                "hardware-404": {
                    "title": "must not hydrate",
                    "description": "must not hydrate",
                    "status": "must not hydrate",
                }
            },
            "system": {
                "system-505": {
                    "title": "must not hydrate",
                }
            },
        }

        self.assertEqual(
            self.hydrate("hardware", "hardware-404", lookups),
            {"type": "hardware"},
        )
        self.assertEqual(
            self.hydrate("system", "system-505", lookups),
            {"type": "system"},
        )

    def test_supported_type_with_missing_lookup_fails_closed(self):
        for component_type in ("software", "interconnection"):
            with self.subTest(component_type=component_type):
                with self.assertRaisesRegex(
                    (KeyError, RuntimeError, ValueError),
                    "lookup|hydrate|component",
                ) as raised:
                    self.hydrate(component_type, "missing-606", {})
                self.assertNotIn("missing-606", str(raised.exception))

    def test_blank_or_missing_approved_title_fails_closed(self):
        for title in (None, "", "   "):
            with self.subTest(title=title):
                lookups = {
                    "software": {
                        "software-707": {
                            "title": title,
                            "description": "Description",
                        }
                    }
                }
                with self.assertRaisesRegex(
                    (RuntimeError, ValueError),
                    "title|hydrate|component",
                ):
                    self.hydrate("software", "software-707", lookups)

    def test_blank_or_missing_software_description_fails_closed(self):
        for description in (None, "", "   "):
            with self.subTest(description=description):
                lookups = {
                    "software": {
                        "software-717": {
                            "title": "Software title",
                            "description": description,
                        }
                    }
                }
                with self.assertRaisesRegex(
                    (RuntimeError, ValueError),
                    "description|hydrate|component",
                ):
                    self.hydrate("software", "software-717", lookups)

    def test_cross_type_lookup_is_never_used_as_a_fallback(self):
        lookups = {
            "interconnection": {
                "shared-727": {
                    "title": "Wrong type title",
                    "description": "Wrong type description",
                }
            }
        }
        with self.assertRaisesRegex(
            (KeyError, RuntimeError, ValueError),
            "lookup|hydrate|component",
        ):
            self.hydrate("software", "shared-727", lookups)

    def test_lookup_payload_cannot_override_type_or_identity(self):
        lookup_entry = {
            "title": "Software name",
            "description": "Software description",
            "type": "hardware",
            "id": "attacker-controlled-id",
            "uuid": "attacker-controlled-uuid",
        }
        lookups = {"software": {"stable-808": lookup_entry}}

        payload = self.hydrate("software", "stable-808", lookups)

        self.assertEqual(payload["type"], "software")
        self.assertNotIn("id", payload)
        self.assertNotIn("uuid", payload)
        self.assertEqual(lookups["software"]["stable-808"], lookup_entry)

    def test_invalid_lookup_payload_shape_fails_closed(self):
        lookups = {
            "software": {
                "duplicate-shaped-813": [
                    {"title": "First", "description": "First"},
                    {"title": "Second", "description": "Second"},
                ]
            }
        }
        with self.assertRaisesRegex(
            (RuntimeError, ValueError),
            "lookup|payload|component",
        ):
            self.hydrate("software", "duplicate-shaped-813", lookups)

    def test_none_lookup_fails_closed_for_supported_type(self):
        with self.assertRaisesRegex(
            (RuntimeError, ValueError),
            "lookup|hydrate|component",
        ):
            self.hydrate("software", "legacy-818", None)

    def test_build_element_instances_hydrates_without_changing_identity(self):
        mapping_rows = [_component_mapping_row("SOFTWARE", "software")]
        lookups = {
            "software": {
                "stable-828": {
                    "title": "Software title",
                    "description": "Software description",
                }
            }
        }

        instances = self.cell_4["build_element_instances"](
            {"SOFTWARE": [{"ContentId": " stable-828 "}]},
            "private-source-record",
            COMPONENT_PATH,
            mapping_rows,
            lookups,
        )

        self.assertEqual(
            instances,
            [
                {
                    "instance_key": "stable-828",
                    "payload": {
                        "type": "software",
                        "title": "Software title",
                        "description": "Software description",
                    },
                    "parent_instance_key": None,
                }
            ],
        )

    def test_deferred_sap_route_does_not_hydrate_from_type_alone(self):
        lookups = {
            "interconnection": {
                "sap-only-838": {
                    "title": "Must not hydrate without approved occurrence",
                    "description": "Must not hydrate",
                }
            }
        }
        instances = self.cell_4["build_element_instances"](
            {"SAP_INTAKE_FORM_INTERCONNECTIONS": ["sap-only-838"]},
            "private-source-record",
            COMPONENT_PATH,
            [
                _component_mapping_row(
                    "SAP_INTAKE_FORM_INTERCONNECTIONS",
                    "interconnection",
                )
            ],
            lookups,
        )
        self.assertEqual(
            instances,
            [
                {
                    "instance_key": "sap-only-838",
                    "payload": {"type": "interconnection"},
                    "parent_instance_key": None,
                }
            ],
        )

    def test_approved_and_deferred_occurrences_emit_one_hydrated_instance(self):
        lookups = {
            "interconnection": {
                "shared-848": {
                    "title": "Approved interconnection",
                    "description": "Approved description",
                }
            }
        }
        mapping_rows = [
            _component_mapping_row(
                "SAP_INTAKE_FORM_INTERCONNECTIONS",
                "interconnection",
            ),
            _component_mapping_row("INTERCONNECTIONS", "interconnection"),
        ]
        source_obj = {
            "SAP_INTAKE_FORM_INTERCONNECTIONS": ["shared-848"],
            "INTERCONNECTIONS": [{"ContentId": "shared-848"}],
        }

        for rows in (mapping_rows, list(reversed(mapping_rows))):
            with self.subTest(order=rows[0]["SOURCE_FIELD_NAME"]):
                instances = self.cell_4["build_element_instances"](
                    source_obj,
                    "private-source-record",
                    COMPONENT_PATH,
                    rows,
                    lookups,
                )
                self.assertEqual(
                    instances,
                    [
                        {
                            "instance_key": "shared-848",
                            "payload": {
                                "type": "interconnection",
                                "title": "Approved interconnection",
                                "description": "Approved description",
                            },
                            "parent_instance_key": None,
                        }
                    ],
                )


class ComponentPartialHydrationRepositoryTests(unittest.TestCase):
    def test_cell_2_catalog_preserves_frozen_hydration_source_contract(self):
        self.assertEqual(
            _source_one_hydration_contract(),
            EXPECTED_HYDRATION_CONTRACT,
        )

        self.assertEqual(
            _literal_assignment(LEGACY_CELL_4_PATH, "COMPONENT_HYDRATION_CONTRACT"),
            EXPECTED_HYDRATION_CONTRACT,
        )
        self.assertIn(
            'SOURCE_PROFILES[0].get("LOOKUP_CONTRACTS", {})',
            CELL_2_PATH.read_text(encoding="utf-8"),
        )

    def test_normalized_physical_column_ambiguity_fails_closed(self):
        normalize = _load_standalone_function(
            CELL_2_PATH,
            "_normalized_columns",
        )
        self.assertEqual(
            normalize(["CONTENT_ID", "CURATED_JSON"]),
            {
                "CONTENT_ID": "CONTENT_ID",
                "CURATED_JSON": "CURATED_JSON",
            },
        )
        for columns in (
            ["CONTENT_ID", " content_id ", "CURATED_JSON"],
            ["CONTENT_ID", "CURATED_JSON", " curated_json "],
        ):
            with self.subTest(columns=columns):
                with self.assertRaisesRegex(
                    (RuntimeError, ValueError),
                    "ambiguous|duplicate|column",
                ):
                    normalize(columns)

    def test_authoritative_notebook_matches_changed_copy_ready_cells(self):
        notebook = FULL_NOTEBOOK_PATH.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        cases = (
            (
                CELL_1_PATH,
                "# %% Cell 1 - Initialization and configuration",
                "# %% Cell 2 - Source, mapping, registry, and Archer value inputs",
            ),
            (
                CELL_2_PATH,
                "# %% Cell 2 - Source, mapping, registry, and Archer value inputs",
                "# %% Cell 3 - Canonical mapping contract",
            ),
            (
                CELL_4_PATH,
                "# %% Cell 4 - Shared metadata runtime and reusable transformations",
                "# %% Cell 5 - Registry-driven canonical node and edge graph",
            ),
            (
                CELL_5_PATH,
                "# %% Cell 5 - Registry-driven canonical node and edge graph",
                "# %% Cell 6 - Validation, guarded idempotent DIM/FACT MERGE, verification",
            ),
        )

        for split_path, start_marker, end_marker in cases:
            with self.subTest(cell=split_path.name):
                split_cell = split_path.read_text(encoding="utf-8").replace(
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

    def test_hydration_release_adds_no_database_write_calls(self):
        for path in (CELL_1_PATH, CELL_2_PATH, CELL_4_PATH, CELL_5_PATH):
            with self.subTest(cell=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertFalse(_database_write_attributes(source))

    def test_write_detector_keeps_database_updates_blocked(self):
        self.assertEqual(
            _database_write_attributes("def _metadata_party_instances(table):\n    table.update({})\n"),
            {"update"},
        )
        self.assertEqual(
            _database_write_attributes("def write_rows(table):\n    table.update({})\n"),
            {"update"},
        )
        self.assertEqual(
            _database_write_attributes("def _score_finish(table):\n    table.update({})\n"),
            {"update"},
        )
        self.assertEqual(
            _database_write_attributes("def unrelated(report):\n    report.update({})\n"),
            {"update"},
        )
        self.assertEqual(
            _database_write_attributes("def _score_finish(report):\n    report.update({})\n"),
            set(),
        )

    def test_unapproved_alternate_fields_are_not_in_production_cells(self):
        production_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (CELL_1_PATH, CELL_2_PATH, CELL_4_PATH)
        )
        for field_name in (
            "BUSINESS_NAME",
            "THIRD_PARTY_NAME",
            "THIRD_PARTY_DESCRIPTION",
            "INSTALL_STATUS",
            "RECORD_STATUS",
            "SERVICENOW_LIFE_CYCLE_STAGE_STATUS",
        ):
            with self.subTest(field_name=field_name):
                self.assertNotIn(field_name, production_source)

    def test_lookup_flow_has_explicit_duplicate_and_missing_guards(self):
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (CELL_2_PATH, CELL_4_PATH)
        )
        source_upper = source.upper()
        self.assertIn("DUPLICATE", source_upper)
        self.assertIn("MISSING", source_upper)
        self.assertIn("COMPONENT", source_upper)
        self.assertTrue(
            "LOOKUP" in source_upper or "HYDRAT" in source_upper
        )

    def test_lookup_builder_and_lazy_source_dataframe_contract_exist(self):
        cell_2_source = CELL_2_PATH.read_text(encoding="utf-8")
        cell_4_source = CELL_4_PATH.read_text(encoding="utf-8")
        self.assertIn("COMPONENT_HYDRATION_SOURCE_DFS", cell_2_source)
        self.assertIn("_build_component_hydration_lookups", cell_4_source)

        loader = next(
            node for node in ast.parse(cell_2_source).body
            if isinstance(node, ast.FunctionDef) and node.name == "load_source_lookups"
        )
        hydration_loop = next(
            node for node in ast.walk(loader)
            if isinstance(node, ast.For)
            and isinstance(node.target, ast.Tuple)
            and [item.id for item in node.target.elts] == ["kind", "contract"]
        )
        hydration_source_block = ast.get_source_segment(cell_2_source, hydration_loop)
        self.assertNotIn(".collect(", hydration_source_block)
        self.assertNotIn(".count(", hydration_source_block)


if __name__ == "__main__":
    unittest.main()
