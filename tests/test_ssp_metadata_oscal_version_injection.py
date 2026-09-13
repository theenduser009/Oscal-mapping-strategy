import contextlib
import copy
import io
from pathlib import Path

# Historical field-policy regression oracle; never imported by production.
LEGACY_CELL_4_PATH = Path(__file__).parents[1] / "tests/fixtures/legacy_cell4_pre_declarative.py"
import runpy
import unittest


CELL_5_PATH = (
    Path(__file__).parents[1]
    / "notebooks"
    / "cells"
    / "05_registry_graph_builder.py"
)
FULL_NOTEBOOK_PATH = (
    Path(__file__).parents[1]
    / "notebooks"
    / "NB_ARCHER_OSCAL_MAPPER_V1.py"
)
METADATA_PATH = "system-security-plan.metadata"
OTHER_PATH = "system-security-plan.system-characteristics"



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


def _metadata_config(**overrides):
    config = {
        "OSCAL_VERSION": "1.2.3",
        "SSP_DOCUMENT_VERSION": "1.0",
    }
    config.update(overrides)
    return config


def _load_helper(config):
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        namespace = _run_graph_cells(
            str(CELL_5_PATH),
            init_globals={"CONFIG": config},
        )
    return namespace["_inject_controlled_metadata_fields"]


def _metadata_instance(payload=None, instance_key="singleton"):
    return {
        "instance_key": instance_key,
        "payload": {} if payload is None else payload,
        "parent_instance_key": None,
        "lineage_marker": "preserve-me",
    }


class MetadataOscalVersionInjectionTests(unittest.TestCase):
    def test_authoritative_notebook_cell_5_matches_copy_ready_file(self):
        notebook = FULL_NOTEBOOK_PATH.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        split_cell = CELL_5_PATH.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        start_marker = "# %% Cell 5 - Registry-driven canonical node and edge graph"
        end_marker = "# %% Cell 6 - Validation, guarded idempotent DIM/FACT MERGE, verification"
        extracted = notebook.split(start_marker, 1)[1].split(end_marker, 1)[0]
        extracted = f"{start_marker}{extracted}".rstrip()

        self.assertEqual(extracted, split_cell.rstrip())

    def test_non_metadata_path_is_unchanged(self):
        helper = _load_helper({})
        instances = [
            _metadata_instance({"system-name": "Example"}),
            _metadata_instance({"description": "Example"}, "second"),
        ]
        before = copy.deepcopy(instances)

        result = helper(OTHER_PATH, instances)

        self.assertEqual(result, before)
        self.assertEqual(instances, before)

    def test_injects_configured_version_into_one_metadata_singleton(self):
        helper = _load_helper(_metadata_config())
        payload = {"title": "Example SSP", "nested": {"keep": True}}
        instance = _metadata_instance(payload)
        instances = [instance]
        before = copy.deepcopy(instances)

        result = helper(METADATA_PATH, instances)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["instance_key"], "singleton")
        self.assertEqual(result[0]["parent_instance_key"], None)
        self.assertEqual(result[0]["lineage_marker"], "preserve-me")
        self.assertEqual(result[0]["payload"]["title"], "Example SSP")
        self.assertEqual(result[0]["payload"]["nested"], {"keep": True})
        self.assertEqual(result[0]["payload"]["oscal-version"], "1.2.3")
        self.assertEqual(result[0]["payload"]["version"], "1.0")

        self.assertEqual(instances, before)
        self.assertIsNot(result, instances)
        self.assertIsNot(result[0], instance)
        self.assertIsNot(result[0]["payload"], payload)

    def test_matching_existing_version_is_allowed_without_mutation(self):
        helper = _load_helper(_metadata_config())
        payload = {
            "oscal-version": "1.2.3",
            "title": "Example SSP",
            "version": "1.0",
        }
        instances = [_metadata_instance(payload)]
        before = copy.deepcopy(instances)

        result = helper(METADATA_PATH, instances)

        self.assertEqual(result[0]["payload"], payload)
        self.assertEqual(instances, before)
        self.assertIsNot(result[0]["payload"], payload)

    def test_conflicting_existing_version_fails_closed(self):
        helper = _load_helper(_metadata_config())
        instances = [
            _metadata_instance(
                {"oscal-version": "1.1.3", "title": "Example SSP"}
            )
        ]
        before = copy.deepcopy(instances)

        with self.assertRaisesRegex(ValueError, "oscal-version"):
            helper(METADATA_PATH, instances)

        self.assertEqual(instances, before)

    def test_missing_or_blank_configured_version_fails_closed(self):
        invalid_configs = (
            {"SSP_DOCUMENT_VERSION": "1.0"},
            _metadata_config(OSCAL_VERSION=None),
            _metadata_config(OSCAL_VERSION=""),
            _metadata_config(OSCAL_VERSION="   "),
        )
        for config in invalid_configs:
            with self.subTest(config=config):
                helper = _load_helper(config)
                instances = [_metadata_instance({"title": "Example SSP"})]
                before = copy.deepcopy(instances)

                with self.assertRaisesRegex(ValueError, "OSCAL_VERSION"):
                    helper(METADATA_PATH, instances)

                self.assertEqual(instances, before)

    def test_zero_metadata_instances_fail_closed(self):
        helper = _load_helper(_metadata_config())

        with self.assertRaisesRegex(ValueError, "exactly one"):
            helper(METADATA_PATH, [])

    def test_multiple_metadata_instances_fail_closed_without_mutation(self):
        helper = _load_helper(_metadata_config())
        instances = [
            _metadata_instance({"title": "First"}),
            _metadata_instance({"title": "Second"}, "second"),
        ]
        before = copy.deepcopy(instances)

        with self.assertRaisesRegex(ValueError, "exactly one"):
            helper(METADATA_PATH, instances)

        self.assertEqual(instances, before)

    def test_non_singleton_metadata_instance_fails_closed_without_mutation(self):
        helper = _load_helper(_metadata_config())
        instances = [
            _metadata_instance({"title": "Example SSP"}, "unexpected")
        ]
        before = copy.deepcopy(instances)

        with self.assertRaisesRegex(ValueError, "singleton"):
            helper(METADATA_PATH, instances)

        self.assertEqual(instances, before)

    def test_non_object_metadata_payload_fails_closed(self):
        helper = _load_helper(_metadata_config())
        instances = [_metadata_instance(["not", "an", "object"])]
        before = copy.deepcopy(instances)

        with self.assertRaisesRegex(ValueError, "payload must be an object"):
            helper(METADATA_PATH, instances)

        self.assertEqual(instances, before)


if __name__ == "__main__":
    unittest.main()
