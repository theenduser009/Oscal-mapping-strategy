# Read-only SSP mapped-scope document assembly
#
# Run once after Mapper Cell 7 in the same Snowflake notebook session. This
# cell assembles the already validated in-memory node/edge forest into one
# transient JSON object per SSP source record. It adds no mappings, creates no
# database objects, and performs no DDL or DML. Output is aggregate-only: no
# source identifiers, payloads, or assembled documents are printed.
#
# This is deliberately a MAPPED-SCOPE ASSEMBLY. It is not a completeness,
# OSCAL JSON Schema, or OSCAL constraint-validation result.

from collections import defaultdict
import json
import uuid


ASSEMBLY_ROOT_PATH = "system-security-plan"
ASSEMBLY_CONTAINS_TYPE = "CONTAINS"
ASSEMBLY_PAYLOAD_UUID_PATHS = {
    ASSEMBLY_ROOT_PATH,
    "system-security-plan.metadata.parties[]",
    "system-security-plan.system-implementation.components[]",
}


def _assembly_clean(value):
    return str(value).strip() if value is not None else ""


def _assembly_row_dict(row):
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "as_dict"):
        return row.as_dict(recursive=True)
    raise RuntimeError("Mapped-scope assembly received an invalid row")


def _assembly_value(row, name):
    values = _assembly_row_dict(row)
    expected = name.strip().upper()
    matches = [
        value
        for key, value in values.items()
        if str(key).strip().upper() == expected
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Mapped-scope assembly row has a missing or ambiguous column"
        )
    return matches[0]


def _assembly_payload(value):
    if hasattr(value, "as_dict"):
        value = value.as_dict(recursive=True)
    try:
        if isinstance(value, str):
            value = json.loads(value)
        if not isinstance(value, dict):
            raise TypeError
        # Round-tripping rejects non-JSON Python values and prevents later
        # assembly from mutating a Snowpark Row-derived object in place.
        return json.loads(
            json.dumps(value, ensure_ascii=False, allow_nan=False)
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        raise RuntimeError(
            "Mapped-scope assembly found a malformed or non-object payload"
        ) from None


def _assembly_uuid(value):
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("Mapped-scope assembly found an invalid node UUID")
    try:
        canonical = str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise RuntimeError(
            "Mapped-scope assembly found an invalid node UUID"
        ) from None
    if value != canonical:
        raise RuntimeError("Mapped-scope assembly found a noncanonical UUID")
    return canonical


def _assembly_leaf_name(path):
    leaf = path.rsplit(".", 1)[-1]
    return leaf[:-2] if leaf.endswith("[]") else leaf


def _assembly_registry_contract(registry_rows):
    registry = {}
    for row in registry_rows:
        if not isinstance(row, dict):
            row = _assembly_row_dict(row)
        path = _assembly_clean(
            row.get("element_path", row.get("ELEMENT_PATH"))
        )
        if not path or path in registry:
            raise RuntimeError(
                "Mapped-scope assembly registry paths are blank or duplicated"
            )
        parent_value = row.get("parent_path", row.get("PARENT_PATH"))
        parent_path = _assembly_clean(parent_value) or None
        collection_value = row.get(
            "is_collection",
            row.get("IS_COLLECTION", False),
        )
        if isinstance(collection_value, bool):
            is_collection = collection_value
        else:
            is_collection = _assembly_clean(collection_value).upper() in {
                "TRUE",
                "T",
                "YES",
                "Y",
                "1",
            }
        if path.endswith("[]") != is_collection:
            raise RuntimeError(
                "Mapped-scope assembly registry collection semantics conflict"
            )
        registry[path] = {
            "path": path,
            "parent_path": parent_path,
            "is_collection": is_collection,
        }

    root_contract = registry.get(ASSEMBLY_ROOT_PATH)
    if root_contract is None or root_contract["parent_path"] is not None:
        raise RuntimeError(
            "Mapped-scope assembly requires the governed SSP root"
        )
    if root_contract["is_collection"]:
        raise RuntimeError("Mapped-scope assembly root cannot be a collection")
    return registry


def _assembly_node_rows(node_rows, registry):
    nodes = {}
    source_nodes = defaultdict(set)
    roots_by_source = defaultdict(list)

    for raw_row in node_rows:
        node_key = _assembly_clean(_assembly_value(raw_row, "NODE_KEY"))
        source_record_id = _assembly_clean(
            _assembly_value(raw_row, "SOURCE_RECORD_ID")
        )
        path = _assembly_clean(_assembly_value(raw_row, "ELEMENT_PATH"))
        instance_key = _assembly_clean(
            _assembly_value(raw_row, "INSTANCE_KEY")
        )
        oscal_uuid = _assembly_uuid(
            _assembly_value(raw_row, "OSCAL_UUID")
        )
        payload = _assembly_payload(
            _assembly_value(raw_row, "METADATA_JSON")
        )

        if not node_key or not source_record_id or not path or not instance_key:
            raise RuntimeError(
                "Mapped-scope assembly found a blank graph identity"
            )
        if node_key in nodes:
            raise RuntimeError(
                "Mapped-scope assembly found duplicate node keys"
            )
        if path not in registry:
            raise RuntimeError(
                "Mapped-scope assembly found a node outside the registry"
            )

        payload_uuid = payload.get("uuid")
        if payload_uuid is not None:
            if _assembly_uuid(payload_uuid) != oscal_uuid:
                raise RuntimeError(
                    "Mapped-scope assembly found a payload/node UUID conflict"
                )
        elif path in ASSEMBLY_PAYLOAD_UUID_PATHS and path != ASSEMBLY_ROOT_PATH:
            raise RuntimeError(
                "Mapped-scope assembly found a missing governed payload UUID"
            )

        nodes[node_key] = {
            "node_key": node_key,
            "source_record_id": source_record_id,
            "path": path,
            "instance_key": instance_key,
            "oscal_uuid": oscal_uuid,
            "payload": payload,
        }
        source_nodes[source_record_id].add(node_key)
        if path == ASSEMBLY_ROOT_PATH:
            if instance_key != "singleton":
                raise RuntimeError(
                    "Mapped-scope assembly root identity is not singleton"
                )
            roots_by_source[source_record_id].append(node_key)

    if not nodes:
        raise RuntimeError("Mapped-scope assembly received an empty graph")
    if any(len(roots_by_source[source_id]) != 1 for source_id in source_nodes):
        raise RuntimeError(
            "Mapped-scope assembly requires exactly one root per source"
        )
    if set(roots_by_source) != set(source_nodes):
        raise RuntimeError(
            "Mapped-scope assembly requires exactly one root per source"
        )
    return nodes, source_nodes, roots_by_source


def _assembly_edges(edge_rows, nodes, registry):
    adjacency = defaultdict(list)
    indegree = defaultdict(int)
    edge_keys = set()
    edge_count = 0

    for raw_row in edge_rows:
        edge_count += 1
        edge_key = _assembly_clean(_assembly_value(raw_row, "EDGE_KEY"))
        parent_key = _assembly_clean(
            _assembly_value(raw_row, "FK_SOURCE_ELEMENT_HASH")
        )
        child_key = _assembly_clean(
            _assembly_value(raw_row, "FK_TARGET_ELEMENT_HASH")
        )
        dependency_type = _assembly_clean(
            _assembly_value(raw_row, "DEPENDENCY_TYPE")
        ).upper()
        source_uuid = _assembly_uuid(
            _assembly_value(raw_row, "SOURCE_OSCAL_UUID")
        )
        target_uuid = _assembly_uuid(
            _assembly_value(raw_row, "TARGET_OSCAL_UUID")
        )

        if not edge_key or edge_key in edge_keys:
            raise RuntimeError(
                "Mapped-scope assembly found blank or duplicate edge keys"
            )
        edge_keys.add(edge_key)
        if dependency_type != ASSEMBLY_CONTAINS_TYPE:
            raise RuntimeError(
                "Mapped-scope assembly found a non-containment edge"
            )
        if parent_key not in nodes or child_key not in nodes:
            raise RuntimeError(
                "Mapped-scope assembly found an unresolved edge endpoint"
            )
        if parent_key == child_key:
            raise RuntimeError("Mapped-scope assembly found a graph cycle")

        parent = nodes[parent_key]
        child = nodes[child_key]
        if parent["source_record_id"] != child["source_record_id"]:
            raise RuntimeError(
                "Mapped-scope assembly found a cross-source edge"
            )
        if source_uuid != parent["oscal_uuid"] or target_uuid != child["oscal_uuid"]:
            raise RuntimeError(
                "Mapped-scope assembly found an edge/node UUID conflict"
            )
        if registry[child["path"]]["parent_path"] != parent["path"]:
            raise RuntimeError(
                "Mapped-scope assembly found a registry parent mismatch"
            )

        adjacency[parent_key].append(child_key)
        indegree[child_key] += 1

    root_keys = {
        key for key, node in nodes.items() if node["path"] == ASSEMBLY_ROOT_PATH
    }
    for node_key in nodes:
        expected_indegree = 0 if node_key in root_keys else 1
        if indegree[node_key] != expected_indegree:
            raise RuntimeError(
                "Mapped-scope assembly requires one parent per non-root"
            )
    if edge_count != len(nodes) - len(root_keys):
        raise RuntimeError(
            "Mapped-scope assembly graph is not a rooted forest"
        )
    return adjacency, edge_count


def _assembly_validate_reachability(nodes, source_nodes, roots_by_source, adjacency):
    visit_state = {}

    def detect_cycle(node_key):
        state = visit_state.get(node_key, 0)
        if state == 1:
            raise RuntimeError("Mapped-scope assembly found a graph cycle")
        if state == 2:
            return
        visit_state[node_key] = 1
        for child_key in adjacency.get(node_key, []):
            detect_cycle(child_key)
        visit_state[node_key] = 2

    for node_key in nodes:
        detect_cycle(node_key)

    for source_record_id, expected_keys in source_nodes.items():
        root_key = roots_by_source[source_record_id][0]
        visited = set()

        def visit(node_key):
            if node_key in visited:
                return
            for child_key in adjacency.get(node_key, []):
                visit(child_key)
            visited.add(node_key)

        visit(root_key)
        if visited != expected_keys:
            raise RuntimeError(
                "Mapped-scope assembly found orphaned graph nodes"
            )


def _assembly_document_for_root(root_key, nodes, registry, adjacency):
    def assemble_node(node_key):
        node = nodes[node_key]
        output = dict(node["payload"])

        child_groups = defaultdict(list)
        child_paths_by_name = defaultdict(set)
        for child_key in adjacency.get(node_key, []):
            child = nodes[child_key]
            child_name = _assembly_leaf_name(child["path"])
            child_groups[child_name].append(child_key)
            child_paths_by_name[child_name].add(child["path"])

        for child_name in sorted(child_groups):
            child_paths = child_paths_by_name[child_name]
            if len(child_paths) != 1:
                raise RuntimeError(
                    "Mapped-scope assembly found an ambiguous child name"
                )
            if child_name in output:
                raise RuntimeError(
                    "Mapped-scope assembly found a payload/child-key collision"
                )

            child_path = next(iter(child_paths))
            child_keys = child_groups[child_name]
            if registry[child_path]["is_collection"]:
                instance_keys = [
                    nodes[child_key]["instance_key"]
                    for child_key in child_keys
                ]
                if len(instance_keys) != len(set(instance_keys)):
                    raise RuntimeError(
                        "Mapped-scope assembly found duplicate collection "
                        "instance keys"
                    )
                child_keys.sort(
                    key=lambda key: (
                        nodes[key]["instance_key"],
                        nodes[key]["node_key"],
                    )
                )
                output[child_name] = [
                    assemble_node(child_key) for child_key in child_keys
                ]
            else:
                if len(child_keys) != 1:
                    raise RuntimeError(
                        "Mapped-scope assembly found multiple singleton children"
                    )
                output[child_name] = assemble_node(child_keys[0])

        if node["path"] == ASSEMBLY_ROOT_PATH:
            existing_uuid = output.get("uuid")
            if existing_uuid is not None and existing_uuid != node["oscal_uuid"]:
                raise RuntimeError(
                    "Mapped-scope assembly found a root UUID conflict"
                )
            output["uuid"] = node["oscal_uuid"]
        return output

    return {ASSEMBLY_ROOT_PATH: assemble_node(root_key)}


def assemble_mapped_scope_ssp(node_rows, edge_rows, registry_rows):
    """Assemble a validated transient SSP forest without printing data."""
    registry = _assembly_registry_contract(registry_rows)
    nodes, source_nodes, roots_by_source = _assembly_node_rows(
        node_rows,
        registry,
    )
    adjacency, edge_count = _assembly_edges(edge_rows, nodes, registry)
    _assembly_validate_reachability(
        nodes,
        source_nodes,
        roots_by_source,
        adjacency,
    )

    documents = {}
    canonical_documents = {}
    for source_record_id in sorted(source_nodes):
        root_key = roots_by_source[source_record_id][0]
        document = _assembly_document_for_root(
            root_key,
            nodes,
            registry,
            adjacency,
        )
        canonical_json = json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        documents[source_record_id] = document
        canonical_documents[source_record_id] = canonical_json

    return documents, canonical_documents, {
        "documents": len(documents),
        "nodes": len(nodes),
        "edges": edge_count,
        "roots": len(roots_by_source),
        "writes_executed": False,
        "mapped_scope_only": True,
        "complete_claim": False,
        "schema_valid_claim": False,
    }


def _assembly_validate_runtime_state(config, run_result):
    if not isinstance(config, dict):
        raise RuntimeError("Mapped-scope assembly requires Cell 1 CONFIG")
    if str(config.get("OSCAL_MODEL", "")).strip().upper() != "SSP":
        raise RuntimeError("Mapped-scope assembly requires the SSP model")
    if config.get("EXECUTE_WRITES", False):
        raise RuntimeError(
            "Set EXECUTE_WRITES = False before mapped-scope assembly"
        )
    if not isinstance(run_result, dict):
        raise RuntimeError("Mapped-scope assembly requires the Cell 7 result")
    if not run_result.get("validation_passed", False):
        raise RuntimeError("Cell 7 graph validation must pass first")
    if not run_result.get("pre_write_validation_passed", False):
        raise RuntimeError("Cell 7 pre-write validation must pass first")
    if run_result.get("writes_executed", True):
        raise RuntimeError(
            "Mapped-scope assembly requires a read-only Cell 7 run"
        )


def run_mapped_scope_assembly(
    config,
    run_result,
    final_nodes_dataframe,
    final_edges_dataframe,
    element_registry_dataframe,
    registry_canonicalizer,
):
    _assembly_validate_runtime_state(config, run_result)

    node_columns = (
        "NODE_KEY",
        "SOURCE_RECORD_ID",
        "ELEMENT_PATH",
        "INSTANCE_KEY",
        "OSCAL_UUID",
        "METADATA_JSON",
    )
    edge_columns = (
        "EDGE_KEY",
        "FK_SOURCE_ELEMENT_HASH",
        "FK_TARGET_ELEMENT_HASH",
        "DEPENDENCY_TYPE",
        "SOURCE_OSCAL_UUID",
        "TARGET_OSCAL_UUID",
    )
    node_rows = list(
        final_nodes_dataframe.select(*node_columns).to_local_iterator()
    )
    edge_rows = list(
        final_edges_dataframe.select(*edge_columns).to_local_iterator()
    )
    registry_rows = registry_canonicalizer(
        element_registry_dataframe,
        "SSP",
    )

    documents, canonical_documents, result = assemble_mapped_scope_ssp(
        node_rows,
        edge_rows,
        registry_rows,
    )
    if result["nodes"] != int(run_result.get("nodes", -1)):
        raise RuntimeError(
            "Mapped-scope assembly node count differs from Cell 7"
        )
    if result["edges"] != int(run_result.get("edges", -1)):
        raise RuntimeError(
            "Mapped-scope assembly edge count differs from Cell 7"
        )

    print("=== SSP MAPPED-SCOPE ASSEMBLY ===")
    print("Safety: aggregate-only; no identifiers or payloads printed")
    print("Documents assembled:", result["documents"])
    print("Graph nodes consumed:", result["nodes"])
    print("Graph edges consumed:", result["edges"])
    print("Root nodes consumed:", result["roots"])
    print("Writes executed: False")
    print("Result: MAPPED-SCOPE ASSEMBLY PASSED")
    print("Complete SSP claim: False")
    print("OSCAL schema-valid claim: False")
    return documents, canonical_documents, result


if not globals().get("_MAPPED_SCOPE_ASSEMBLY_SKIP_EXECUTION", False):
    required_state = {
        "CONFIG": globals().get("CONFIG"),
        "run_result": globals().get("run_result"),
        "final_nodes_df": globals().get("final_nodes_df"),
        "final_edges_df": globals().get("final_edges_df"),
        "element_registry_df": globals().get("element_registry_df"),
        "_canonical_registry_rows": globals().get(
            "_canonical_registry_rows"
        ),
    }
    missing_state = [
        name for name, value in required_state.items() if value is None
    ]
    if missing_state:
        raise RuntimeError(
            "Run Mapper Cells 1 through 7 first. Missing notebook state "
            "count: " + str(len(missing_state))
        )

    (
        MAPPED_SCOPE_SSP_DOCUMENTS,
        MAPPED_SCOPE_SSP_CANONICAL_JSON,
        MAPPED_SCOPE_ASSEMBLY_RESULT,
    ) = run_mapped_scope_assembly(
        required_state["CONFIG"],
        required_state["run_result"],
        required_state["final_nodes_df"],
        required_state["final_edges_df"],
        required_state["element_registry_df"],
        required_state["_canonical_registry_rows"],
    )
