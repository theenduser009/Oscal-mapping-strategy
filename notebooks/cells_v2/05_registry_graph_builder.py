# %% Cell 5 - Registry-driven canonical node and edge graph

def _create_canonical_graph_frame(rows, graph_kind):
    """Give empty graph results a schema without altering populated inference."""
    if graph_kind not in {"nodes", "edges"}:
        raise ValueError("Unknown canonical graph frame kind")
    if rows:
        return session.create_dataframe(rows)

    # Canonical transport columns, not model-specific mapping rules.
    from snowflake.snowpark.types import (
        StringType, StructField, StructType, TimestampType, TimestampTimeZone,
    )

    if graph_kind == "nodes":
        columns = (
            "NODE_KEY", "ELEMENT_PATH", "INSTANCE_KEY", "PARENT_INSTANCE_KEY",
            "OSCAL_UUID", "ELEMENT_TYPE", "METADATA_JSON", "SOURCE_SYSTEM_NAME",
            "SOURCE_TABLE_NAME", "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID",
            "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ",
        )
    else:
        columns = (
            "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH",
            "DEPENDENCY_TYPE", "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID",
        )
    timestamps = {"DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}
    schema = StructType([
        StructField(name, TimestampType(TimestampTimeZone.TZ)
                    if name in timestamps else StringType(), nullable=True)
        for name in columns
    ])
    return session.create_dataframe(rows, schema=schema)


def build_oscal_graph(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    model_key,
    source_system,
    source_table,
    context=None,
):
    # Cell 4 owns metadata execution; this cell connects its nodes and edges.
    # This loop owns only graph mechanics and never swaps notebook globals.
    del canonical_mapping_df
    context = _prepare_model_context(context, model_key, source_system, source_table)
    config, policy = context["config"], context["policy"]
    report = context["graph_report"]
    registry_rows = _canonical_registry_rows(element_registry_df, model_key, context)
    root_paths = [row["element_path"] for row in registry_rows if not row["parent_path"]]
    if root_paths != [context["model_contract"]["ROOT_PATH"]]:
        raise ValueError("Expected exactly the configured registry root")
    root_row = next(row for row in registry_rows if row["element_path"] == root_paths[0])
    context["root_element_type"] = root_row.get("element_type") or _element_type(root_paths[0])
    _metadata_prepare(source_df, context)

    node_rows, edge_rows, seen_records = [], [], set()
    load_timestamp = datetime.datetime.now(datetime.timezone.utc)
    for record in source_df.to_local_iterator():
        report["SOURCE_RECORDS"] += 1
        source_record_id = record["SOURCE_RECORD_ID"]
        if not isinstance(source_record_id, str) or not source_record_id.strip() or source_record_id != source_record_id.strip():
            report["INVALID_SOURCE_RECORDS"] += 1
            if policy["aggregate_invalid"]:
                continue
            raise ValueError("Source record identity must be a nonblank canonical string")
        if source_record_id in seen_records:
            report["DUPLICATE_SOURCE_RECORDS"] += 1
            if policy["aggregate_invalid"]:
                continue
            raise ValueError("Duplicate source record identity")
        seen_records.add(source_record_id)
        try:
            source_obj = _metadata_parse(record, context)
        except (TypeError, ValueError, ArithmeticError):
            report["INVALID_SOURCE_RECORDS"] += 1
            if policy["aggregate_invalid"]:
                continue
            raise
        nodes_by_path = {}
        for registry_row in registry_rows:
            path, parent_path = registry_row["element_path"], registry_row["parent_path"]
            instances = _metadata_instances(source_obj, source_record_id, registry_row, context)
            created_nodes = []
            seen_instances = set()
            for instance in instances:
                instance_key = instance["instance_key"]
                if not isinstance(instance_key, str) or not instance_key.strip():
                    raise ValueError("Element instance requires a stable nonblank identity")
                if instance_key in seen_instances:
                    raise ValueError("Duplicate element instance identity")
                seen_instances.add(instance_key)
                node_key = _deterministic_hash(
                    config["IDENTITY_VERSION"], source_system, source_table,
                    source_record_id, model_key, path, instance_key,
                )
                oscal_uuid = _metadata_uuid(
                    path, instance, source_system, source_table, source_record_id, model_key, context,
                )
                payload = _metadata_payload(path, instance["payload"], oscal_uuid, context)
                if not isinstance(payload, dict):
                    raise ValueError("An element payload must be an object")
                node = {
                    "NODE_KEY": node_key, "ELEMENT_PATH": path, "INSTANCE_KEY": instance_key,
                    "PARENT_INSTANCE_KEY": instance.get("parent_instance_key"),
                    "OSCAL_UUID": oscal_uuid,
                    "ELEMENT_TYPE": registry_row.get("element_type") or _element_type(path),
                    "METADATA_JSON": json.dumps(payload, sort_keys=True, default=str, allow_nan=policy["allow_nan"]),
                    "SOURCE_SYSTEM_NAME": source_system, "SOURCE_TABLE_NAME": source_table,
                    "SOURCE_RECORD_ID": source_record_id, "DW_PIPELINE_RUN_ID": config["RUN_ID"],
                    "DW_LOAD_TIMESTAMP": load_timestamp, "DW_LOAD_TIMESTAMP_TZ": load_timestamp,
                }
                node_rows.append(node)
                created_nodes.append(node)
            nodes_by_path[path] = created_nodes
            if not parent_path:
                continue
            parent_nodes = nodes_by_path.get(parent_path, [])
            for child_node in created_nodes:
                if not parent_nodes:
                    raise ValueError(f"Missing parent {parent_path} for child {path}")
                parent_key = child_node["PARENT_INSTANCE_KEY"]
                if parent_key is not None:
                    matches = [node for node in parent_nodes if node["INSTANCE_KEY"] == parent_key]
                    if len(matches) != 1:
                        raise ValueError("Unresolved explicit collection parent instance")
                    parent_node = matches[0]
                elif len(parent_nodes) == 1:
                    parent_node = parent_nodes[0]
                else:
                    raise ValueError(f"Ambiguous collection parent for {path}")
                edge_key = _deterministic_hash(
                    "edge-v1", parent_node["NODE_KEY"], child_node["NODE_KEY"], "CONTAINS",
                )
                edge_rows.append({
                    "EDGE_KEY": edge_key,
                    "FK_SOURCE_ELEMENT_HASH": parent_node["NODE_KEY"],
                    "FK_TARGET_ELEMENT_HASH": child_node["NODE_KEY"],
                    "DEPENDENCY_TYPE": "CONTAINS",
                    "SOURCE_OSCAL_UUID": parent_node["OSCAL_UUID"],
                    "TARGET_OSCAL_UUID": child_node["OSCAL_UUID"],
                })
        _metadata_record_complete(nodes_by_path, context)

    node_keys = {row["NODE_KEY"] for row in node_rows}
    report["DUPLICATE_NODE_KEYS"] = len(node_rows) - len(node_keys)
    report["DUPLICATE_EDGE_KEYS"] = len(edge_rows) - len({row["EDGE_KEY"] for row in edge_rows})
    report["DANGLING_EDGES"] = sum(
        row["FK_SOURCE_ELEMENT_HASH"] not in node_keys or row["FK_TARGET_ELEMENT_HASH"] not in node_keys
        for row in edge_rows
    )
    if any(report[key] for key in ("DUPLICATE_NODE_KEYS", "DUPLICATE_EDGE_KEYS", "DANGLING_EDGES")):
        raise ValueError("Canonical graph key integrity failed")
    _metadata_finish(node_rows, edge_rows, context)
    if not node_rows:
        raise ValueError("Graph builder produced no nodes")
    canonical_nodes_df = _create_canonical_graph_frame(node_rows, "nodes")
    canonical_edges_df = _create_canonical_graph_frame(edge_rows, "edges")
    return canonical_nodes_df, canonical_edges_df


print("Cell 5 graph builder initialized")
