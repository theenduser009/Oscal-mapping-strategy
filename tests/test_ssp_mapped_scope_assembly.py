import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import runpy
import unittest
import uuid


REPO_ROOT = Path(__file__).parents[1]
ASSEMBLY_PATH = (
    REPO_ROOT
    / "notebooks"
    / "validation"
    / "RUN_AFTER_07_ssp_mapped_scope_assembly.py"
)

ROOT_PATH = "system-security-plan"
METADATA_PATH = ROOT_PATH + ".metadata"
ROLES_PATH = METADATA_PATH + ".roles[]"
PARTIES_PATH = METADATA_PATH + ".parties[]"
RESPONSIBLE_PATH = METADATA_PATH + ".responsible-parties[]"
CHARACTERISTICS_PATH = ROOT_PATH + ".system-characteristics"
PROPS_PATH = CHARACTERISTICS_PATH + ".props[]"
IMPLEMENTATION_PATH = ROOT_PATH + ".system-implementation"
COMPONENTS_PATH = IMPLEMENTATION_PATH + ".components[]"


def _load_helpers():
    return runpy.run_path(
        str(ASSEMBLY_PATH),
        init_globals={"_MAPPED_SCOPE_ASSEMBLY_SKIP_EXECUTION": True},
    )


def _stable_uuid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, label))


def _registry_rows():
    return [
        {
            "element_path": ROOT_PATH,
            "parent_path": None,
            "is_collection": False,
        },
        {
            "element_path": METADATA_PATH,
            "parent_path": ROOT_PATH,
            "is_collection": False,
        },
        {
            "element_path": ROLES_PATH,
            "parent_path": METADATA_PATH,
            "is_collection": True,
        },
        {
            "element_path": PARTIES_PATH,
            "parent_path": METADATA_PATH,
            "is_collection": True,
        },
        {
            "element_path": RESPONSIBLE_PATH,
            "parent_path": METADATA_PATH,
            "is_collection": True,
        },
        {
            "element_path": CHARACTERISTICS_PATH,
            "parent_path": ROOT_PATH,
            "is_collection": False,
        },
        {
            "element_path": PROPS_PATH,
            "parent_path": CHARACTERISTICS_PATH,
            "is_collection": True,
        },
        {
            "element_path": IMPLEMENTATION_PATH,
            "parent_path": ROOT_PATH,
            "is_collection": False,
        },
        {
            "element_path": COMPONENTS_PATH,
            "parent_path": IMPLEMENTATION_PATH,
            "is_collection": True,
        },
    ]


def _node(key, source, path, instance, payload=None, node_uuid=None):
    return {
        "NODE_KEY": key,
        "SOURCE_RECORD_ID": source,
        "ELEMENT_PATH": path,
        "INSTANCE_KEY": instance,
        "OSCAL_UUID": node_uuid or _stable_uuid(key),
        "METADATA_JSON": json.dumps(payload or {}, sort_keys=True),
    }


def _edge(key, parent, child, nodes):
    node_index = {row["NODE_KEY"]: row for row in nodes}
    return {
        "EDGE_KEY": key,
        "FK_SOURCE_ELEMENT_HASH": parent,
        "FK_TARGET_ELEMENT_HASH": child,
        "DEPENDENCY_TYPE": "CONTAINS",
        "SOURCE_OSCAL_UUID": node_index[parent]["OSCAL_UUID"],
        "TARGET_OSCAL_UUID": node_index[child]["OSCAL_UUID"],
    }


def _fixture(source="private-source-record"):
    party_uuid = _stable_uuid("party")
    component_a_uuid = _stable_uuid("component-a")
    component_z_uuid = _stable_uuid("component-z")
    nodes = [
        _node("root", source, ROOT_PATH, "singleton"),
        _node(
            "metadata",
            source,
            METADATA_PATH,
            "singleton",
            {
                "title": "Private package title",
                "last-modified": "2026-09-10T12:00:00",
                "version": "1.0",
                "oscal-version": "1.2.3",
            },
        ),
        _node(
            "role",
            source,
            ROLES_PATH,
            "system-owner",
            {"id": "system-owner", "title": "System Owner"},
        ),
        _node(
            "party",
            source,
            PARTIES_PATH,
            party_uuid,
            {"uuid": party_uuid, "type": "person"},
            party_uuid,
        ),
        _node(
            "responsible",
            source,
            RESPONSIBLE_PATH,
            "INFORMATION_SYSTEM_OWNER_ISO",
            {"role-id": "system-owner", "party-uuids": [party_uuid]},
        ),
        _node(
            "characteristics",
            source,
            CHARACTERISTICS_PATH,
            "singleton",
            {"system-name": "Private system"},
        ),
        _node(
            "prop-z",
            source,
            PROPS_PATH,
            "z-field:z-value",
            {"name": "z-field", "value": "z-value"},
        ),
        _node(
            "prop-a",
            source,
            PROPS_PATH,
            "a-field:a-value",
            {"name": "a-field", "value": "a-value"},
        ),
        _node(
            "implementation",
            source,
            IMPLEMENTATION_PATH,
            "singleton",
        ),
        _node(
            "component-z",
            source,
            COMPONENTS_PATH,
            "z-component",
            {
                "uuid": component_z_uuid,
                "type": "interconnection",
                "title": "Private interconnection",
            },
            component_z_uuid,
        ),
        _node(
            "component-a",
            source,
            COMPONENTS_PATH,
            "a-component",
            {
                "uuid": component_a_uuid,
                "type": "software",
                "title": "Private software",
                "description": "Private description",
            },
            component_a_uuid,
        ),
    ]
    edge_pairs = [
        ("root", "metadata"),
        ("metadata", "role"),
        ("metadata", "party"),
        ("metadata", "responsible"),
        ("root", "characteristics"),
        ("characteristics", "prop-z"),
        ("characteristics", "prop-a"),
        ("root", "implementation"),
        ("implementation", "component-z"),
        ("implementation", "component-a"),
    ]
    edges = [
        _edge("edge-" + child, parent, child, nodes)
        for parent, child in edge_pairs
    ]
    return nodes, edges, _registry_rows()


class _RowsDataFrame:
    def __init__(self, rows):
        self.rows = rows
        self.selected = None

    def select(self, *columns):
        selected = _RowsDataFrame(self.rows)
        selected.selected = tuple(columns)
        return selected

    def to_local_iterator(self):
        for row in self.rows:
            if self.selected is None:
                yield dict(row)
            else:
                yield {name: row[name] for name in self.selected}


class MappedScopeAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helpers = _load_helpers()
        cls.assemble = staticmethod(
            cls.helpers["assemble_mapped_scope_ssp"]
        )

    def test_assembles_all_current_mapping_groups_deterministically(self):
        nodes, edges, registry = _fixture()
        documents, canonical, result = self.assemble(
            nodes,
            edges,
            registry,
        )
        reversed_documents, reversed_canonical, reversed_result = self.assemble(
            list(reversed(nodes)),
            list(reversed(edges)),
            list(reversed(registry)),
        )

        self.assertEqual(documents, reversed_documents)
        self.assertEqual(canonical, reversed_canonical)
        self.assertEqual(result, reversed_result)
        self.assertEqual(result["documents"], 1)
        self.assertEqual(result["nodes"], len(nodes))
        self.assertEqual(result["edges"], len(edges))
        self.assertFalse(result["complete_claim"])
        self.assertFalse(result["schema_valid_claim"])

        ssp = documents["private-source-record"][ROOT_PATH]
        self.assertEqual(ssp["uuid"], _stable_uuid("root"))
        self.assertEqual(ssp["metadata"]["title"], "Private package title")
        self.assertEqual(
            [item["name"] for item in ssp["system-characteristics"]["props"]],
            ["a-field", "z-field"],
        )
        self.assertEqual(
            [item["title"] for item in ssp["system-implementation"]["components"]],
            ["Private software", "Private interconnection"],
        )
        self.assertEqual(
            ssp["metadata"]["responsible-parties"][0]["role-id"],
            "system-owner",
        )

    def test_requires_exactly_one_singleton_root_per_source(self):
        nodes, edges, registry = _fixture()
        without_root = [row for row in nodes if row["ELEMENT_PATH"] != ROOT_PATH]
        with self.assertRaisesRegex(RuntimeError, "exactly one root"):
            self.assemble(without_root, edges, registry)

        second_root = _node(
            "second-root",
            "private-source-record",
            ROOT_PATH,
            "singleton",
        )
        with self.assertRaisesRegex(RuntimeError, "exactly one root"):
            self.assemble(nodes + [second_root], edges, registry)

        nodes[0]["INSTANCE_KEY"] = "not-singleton"
        with self.assertRaisesRegex(RuntimeError, "root identity"):
            self.assemble(nodes, edges, registry)

    def test_requires_exactly_one_parent_for_every_non_root(self):
        nodes, edges, registry = _fixture()
        missing_parent_edge = [
            row for row in edges
            if row["FK_TARGET_ELEMENT_HASH"] != "prop-a"
        ]
        with self.assertRaisesRegex(RuntimeError, "one parent"):
            self.assemble(nodes, missing_parent_edge, registry)

        duplicate_parent_edge = _edge(
            "second-edge-prop-a",
            "characteristics",
            "prop-a",
            nodes,
        )
        with self.assertRaisesRegex(RuntimeError, "one parent"):
            self.assemble(nodes, edges + [duplicate_parent_edge], registry)

    def test_cross_source_edges_fail_without_exposing_identity(self):
        nodes, edges, registry = _fixture()
        second_root = _node(
            "other-root",
            "other-private-source",
            ROOT_PATH,
            "singleton",
        )
        nodes.append(second_root)
        edges[0] = _edge(
            "cross-source-edge",
            "other-root",
            "metadata",
            nodes,
        )
        with self.assertRaisesRegex(RuntimeError, "cross-source") as raised:
            self.assemble(nodes, edges, registry)
        self.assertNotIn("other-private-source", str(raised.exception))

    def test_detached_cycle_and_orphan_fail_closed(self):
        root_uuid = _stable_uuid("cycle-root")
        node_a_uuid = _stable_uuid("cycle-a")
        node_b_uuid = _stable_uuid("cycle-b")
        registry = [
            {
                "element_path": ROOT_PATH,
                "parent_path": None,
                "is_collection": False,
            },
            {
                "element_path": ROOT_PATH + ".a",
                "parent_path": ROOT_PATH + ".b",
                "is_collection": False,
            },
            {
                "element_path": ROOT_PATH + ".b",
                "parent_path": ROOT_PATH + ".a",
                "is_collection": False,
            },
        ]
        nodes = [
            _node(
                "cycle-root",
                "private-source",
                ROOT_PATH,
                "singleton",
                node_uuid=root_uuid,
            ),
            _node(
                "cycle-a",
                "private-source",
                ROOT_PATH + ".a",
                "singleton-a",
                node_uuid=node_a_uuid,
            ),
            _node(
                "cycle-b",
                "private-source",
                ROOT_PATH + ".b",
                "singleton-b",
                node_uuid=node_b_uuid,
            ),
        ]
        edges = [
            _edge("cycle-edge-a", "cycle-b", "cycle-a", nodes),
            _edge("cycle-edge-b", "cycle-a", "cycle-b", nodes),
        ]
        with self.assertRaisesRegex(RuntimeError, "cycle"):
            self.assemble(nodes, edges, registry)

        nodes, edges, registry = _fixture()
        orphan_edges = [
            row for row in edges
            if row["FK_TARGET_ELEMENT_HASH"] != "prop-a"
        ]
        with self.assertRaisesRegex(RuntimeError, "one parent"):
            self.assemble(nodes, orphan_edges, registry)

    def test_registry_parent_mismatch_fails_closed(self):
        nodes, edges, registry = _fixture()
        for row in registry:
            if row["element_path"] == PROPS_PATH:
                row["parent_path"] = ROOT_PATH
        with self.assertRaisesRegex(RuntimeError, "registry parent"):
            self.assemble(nodes, edges, registry)

    def test_registry_collection_flag_must_match_path(self):
        nodes, edges, registry = _fixture()
        for row in registry:
            if row["element_path"] == PROPS_PATH:
                row["is_collection"] = False
        with self.assertRaisesRegex(RuntimeError, "collection semantics"):
            self.assemble(nodes, edges, registry)

    def test_singleton_and_collection_semantics_are_enforced(self):
        nodes, edges, registry = _fixture()
        second_metadata = _node(
            "metadata-two",
            "private-source-record",
            METADATA_PATH,
            "singleton-two",
            {"title": "Second"},
        )
        nodes.append(second_metadata)
        edges.append(_edge("edge-metadata-two", "root", "metadata-two", nodes))
        with self.assertRaisesRegex(RuntimeError, "multiple singleton"):
            self.assemble(nodes, edges, registry)

        nodes, edges, registry = _fixture()
        duplicate_prop = _node(
            "prop-a-two",
            "private-source-record",
            PROPS_PATH,
            "a-field:a-value",
            {"name": "a-field", "value": "a-value"},
        )
        nodes.append(duplicate_prop)
        edges.append(_edge("edge-prop-a-two", "characteristics", "prop-a-two", nodes))
        with self.assertRaisesRegex(RuntimeError, "duplicate collection"):
            self.assemble(nodes, edges, registry)

    def test_payload_shape_and_child_key_collisions_fail_closed(self):
        nodes, edges, registry = _fixture()
        nodes[0]["METADATA_JSON"] = "[]"
        with self.assertRaisesRegex(RuntimeError, "non-object payload"):
            self.assemble(nodes, edges, registry)

        nodes, edges, registry = _fixture()
        nodes[0]["METADATA_JSON"] = json.dumps({"metadata": {}})
        with self.assertRaisesRegex(RuntimeError, "payload/child-key"):
            self.assemble(nodes, edges, registry)

    def test_node_payload_and_edge_uuid_conflicts_fail_closed(self):
        nodes, edges, registry = _fixture()
        component = next(
            row for row in nodes if row["NODE_KEY"] == "component-a"
        )
        payload = json.loads(component["METADATA_JSON"])
        payload["uuid"] = _stable_uuid("wrong-component")
        component["METADATA_JSON"] = json.dumps(payload)
        with self.assertRaisesRegex(RuntimeError, "payload/node UUID"):
            self.assemble(nodes, edges, registry)

        nodes, edges, registry = _fixture()
        edges[0]["SOURCE_OSCAL_UUID"] = _stable_uuid("wrong-edge")
        with self.assertRaisesRegex(RuntimeError, "edge/node UUID"):
            self.assemble(nodes, edges, registry)

    def test_missing_collection_payload_uuid_fails_closed(self):
        nodes, edges, registry = _fixture()
        component = next(
            row for row in nodes if row["NODE_KEY"] == "component-a"
        )
        payload = json.loads(component["METADATA_JSON"])
        del payload["uuid"]
        component["METADATA_JSON"] = json.dumps(payload)
        with self.assertRaisesRegex(RuntimeError, "missing governed payload UUID"):
            self.assemble(nodes, edges, registry)

    def test_runtime_state_requires_read_only_validated_ssp(self):
        validate = self.helpers["_assembly_validate_runtime_state"]
        valid_config = {"OSCAL_MODEL": "SSP", "EXECUTE_WRITES": False}
        valid_result = {
            "validation_passed": True,
            "pre_write_validation_passed": True,
            "writes_executed": False,
        }
        validate(valid_config, valid_result)

        cases = (
            ({**valid_config, "OSCAL_MODEL": "POAM"}, valid_result),
            ({**valid_config, "EXECUTE_WRITES": True}, valid_result),
            (valid_config, {**valid_result, "validation_passed": False}),
            (
                valid_config,
                {**valid_result, "pre_write_validation_passed": False},
            ),
            (valid_config, {**valid_result, "writes_executed": True}),
            (valid_config, None),
        )
        for config, result in cases:
            with self.subTest(config=config, result=result):
                with self.assertRaises(RuntimeError):
                    validate(config, result)

    def test_runtime_output_is_aggregate_only(self):
        nodes, edges, registry = _fixture("secret-source-identifier")
        run_result = {
            "validation_passed": True,
            "pre_write_validation_passed": True,
            "writes_executed": False,
            "nodes": len(nodes),
            "edges": len(edges),
        }
        output = io.StringIO()
        with redirect_stdout(output):
            documents, canonical, result = self.helpers[
                "run_mapped_scope_assembly"
            ](
                {"OSCAL_MODEL": "SSP", "EXECUTE_WRITES": False},
                run_result,
                _RowsDataFrame(nodes),
                _RowsDataFrame(edges),
                object(),
                lambda dataframe, model: registry,
            )

        self.assertEqual(len(documents), 1)
        self.assertEqual(len(canonical), 1)
        self.assertEqual(result["documents"], 1)
        rendered = output.getvalue()
        self.assertIn("MAPPED-SCOPE ASSEMBLY PASSED", rendered)
        self.assertIn("Complete SSP claim: False", rendered)
        self.assertNotIn("secret-source-identifier", rendered)
        self.assertNotIn("Private package title", rendered)
        self.assertNotIn("Private software", rendered)


class MappedScopeAssemblyRepositoryTests(unittest.TestCase):
    def test_cell_has_no_database_or_temporary_object_writes(self):
        source = ASSEMBLY_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_attributes = {
            "create_or_replace_temp_view",
            "delete",
            "insert_into",
            "merge",
            "save_as_table",
            "sql",
            "truncate",
            "update",
            "write",
        }
        called_attributes = {
            node.func.attr.lower()
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        self.assertFalse(called_attributes & forbidden_attributes)

    def test_cell_is_explicit_about_partial_nonconformant_scope(self):
        source = ASSEMBLY_PATH.read_text(encoding="utf-8")
        self.assertIn("MAPPED-SCOPE ASSEMBLY", source)
        self.assertIn('"complete_claim": False', source)
        self.assertIn('"schema_valid_claim": False', source)
        self.assertIn("no identifiers or payloads printed", source)


if __name__ == "__main__":
    unittest.main()
