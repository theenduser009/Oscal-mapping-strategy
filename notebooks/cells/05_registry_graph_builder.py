# %% Cell 5 - Build nodes and parent-child edges

def _create_canonical_graph_frame(rows, kind):
    columns = (
        "NODE_KEY", "ELEMENT_PATH", "PARENT_NODE_PATH", "INSTANCE_KEY", "PARENT_INSTANCE_KEY", "OSCAL_UUID",
        "ELEMENT_TYPE", "METADATA_JSON", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME",
        "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ",
    ) if kind == "nodes" else (
        "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE",
        "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID",
    )
    schema = StructType([StructField(name, TimestampType(TimestampTimeZone.TZ)
                        if name in {"DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"} else StringType())
                         for name in columns])
    return session.create_dataframe([tuple(row.get(name) for name in columns) for row in rows], schema=schema)


def build_oscal_graph(source_df, canonical_mapping_df, element_registry_df,
                      model_key, source_system, source_table, context=None):
    context = _prepare_model_context(context, model_key, source_system, source_table)
    config, report = context["config"], context["graph_report"]
    registry = _canonical_registry_rows(element_registry_df, model_key, context)
    root = context["model_contract"]["ROOT_PATH"]
    context["root_element_type"] = next(row["element_type"] for row in registry if row["element_path"] == root)
    _metadata_prepare(source_df, context)
    nodes, edges, records = [], [], set()
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    for record in source_df.to_local_iterator():
        record_id = record["SOURCE_RECORD_ID"]
        if not isinstance(record_id, str) or not record_id.strip() or record_id != record_id.strip():
            raise ValueError("Source record identity must be a nonblank canonical string")
        if record_id in records:
            raise ValueError("Duplicate source record identity")
        records.add(record_id)
        report["SOURCE_RECORDS"] += 1
        source = _metadata_parse(record, context)
        by_path = {}
        for row in registry:
            path, parent_path = row["element_path"], row["parent_path"]
            instances = {}
            by_path[path] = instances
            for item in _metadata_instances(source, record_id, row, context):
                key = item["instance_key"]
                if not isinstance(key, str) or not key.strip() or key in instances:
                    raise ValueError("Element instances require unique nonblank identities")
                node_key = _deterministic_hash(config["IDENTITY_VERSION"], source_system,
                                               source_table, record_id, model_key, path, key)
                node_uuid = _metadata_uuid(path, item, source_system, source_table, record_id, model_key, context)
                payload = _metadata_payload(path, item["payload"], node_uuid, context)
                if not isinstance(payload, dict):
                    raise ValueError("An element payload must be an object")
                node = {
                    "NODE_KEY": node_key, "ELEMENT_PATH": path, "PARENT_NODE_PATH": parent_path, "INSTANCE_KEY": key,
                    "PARENT_INSTANCE_KEY": item.get("parent_instance_key"), "OSCAL_UUID": node_uuid,
                    "ELEMENT_TYPE": row["element_type"],
                    "METADATA_JSON": json.dumps(payload, sort_keys=True, default=str, allow_nan=False),
                    "SOURCE_SYSTEM_NAME": source_system, "SOURCE_TABLE_NAME": source_table,
                    "SOURCE_RECORD_ID": record_id, "DW_PIPELINE_RUN_ID": config["RUN_ID"],
                    "DW_LOAD_TIMESTAMP": timestamp, "DW_LOAD_TIMESTAMP_TZ": timestamp,
                }
                instances[key] = node
                nodes.append(node)
                if not parent_path:
                    continue
                parents = by_path.get(parent_path, {})
                parent_key = item.get("parent_instance_key")
                parent = parents.get(parent_key) if parent_key is not None else (
                    next(iter(parents.values())) if len(parents) == 1 else None)
                if parent is None:
                    raise ValueError("Missing or ambiguous parent instance for " + path)
                edges.append({
                    "EDGE_KEY": _deterministic_hash("edge-v1", parent["NODE_KEY"], node_key, "CONTAINS"),
                    "FK_SOURCE_ELEMENT_HASH": parent["NODE_KEY"], "FK_TARGET_ELEMENT_HASH": node_key,
                    "DEPENDENCY_TYPE": "CONTAINS", "SOURCE_OSCAL_UUID": parent["OSCAL_UUID"],
                    "TARGET_OSCAL_UUID": node_uuid,
                })
        _metadata_record_complete({path: list(values.values()) for path, values in by_path.items()}, context)
    if not nodes:
        raise ValueError("Graph builder produced no nodes")
    _metadata_finish(nodes, edges, context)
    return _create_canonical_graph_frame(nodes, "nodes"), _create_canonical_graph_frame(edges, "edges")
