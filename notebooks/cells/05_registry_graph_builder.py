# %% Cell 5 - Registry-driven canonical node and edge graph

METADATA_ELEMENT_PATH = "system-security-plan.metadata"

def _registry_value(row, *names):
    row_dict = row.as_dict(recursive=True)
    normalized = {str(key).upper(): value for key, value in row_dict.items()}
    for name in names:
        if name.upper() in normalized and normalized[name.upper()] is not None:
            return normalized[name.upper()]
    return None


def _derive_parent_path(element_path):
    parts = element_path.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else None


def _element_type(element_path):
    return element_path.split(".")[-1].replace("[]", "")


def _inject_controlled_metadata_fields(element_path, instances):
    if element_path != METADATA_ELEMENT_PATH:
        return instances

    if len(instances) != 1 or instances[0].get("instance_key") != "singleton":
        raise ValueError("Expected exactly one singleton metadata instance")

    configured_version = str(CONFIG.get("OSCAL_VERSION") or "").strip()
    if not configured_version:
        raise ValueError("OSCAL_VERSION must be configured for metadata")

    payload = instances[0].get("payload")
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("Metadata payload must be an object")

    existing_version = payload.get("oscal-version")
    if (
        existing_version is not None
        and str(existing_version).strip()
        and str(existing_version).strip() != configured_version
    ):
        raise ValueError("Metadata oscal-version conflicts with configuration")

    updated_payload = dict(payload)
    updated_payload["oscal-version"] = configured_version
    updated_instance = dict(instances[0])
    updated_instance["payload"] = updated_payload
    return [updated_instance]


def _canonical_registry_rows(element_registry_dataframe, model_key):
    rows = []
    for row in element_registry_dataframe.collect():
        model = _registry_value(
            row,
            "OSCAL_MODEL_KEY",
            "OSCAL_MODEL",
            "MODEL_NAME",
            "MODEL",
        )
        if model and str(model).strip().upper() != model_key.upper():
            continue

        is_active = _registry_value(row, "IS_ACTIVE", "ACTIVE")
        if is_active is not None and str(is_active).strip().upper() in {
            "FALSE",
            "F",
            "NO",
            "N",
            "0",
        }:
            continue

        path = _registry_value(
            row,
            "NODE_PATH",
            "OSCAL_ELEMENT_PATH",
            "ELEMENT_PATH",
            "JSON_PATH",
        )
        if not path:
            continue
        path = str(path).strip()
        parent = _registry_value(
            row,
            "PARENT_NODE_PATH",
            "PARENT_ELEMENT_PATH",
            "PARENT_PATH",
        )
        level = _registry_value(
            row,
            "HIERARCHY_LEVEL",
            "ELEMENT_LEVEL",
            "LEVEL_NUMBER",
        )
        process_order = _registry_value(row, "PROCESS_ORDER")
        derived_level = path.count(".") + 1
        rows.append(
            {
                "element_path": path,
                "parent_path": str(parent).strip() if parent else _derive_parent_path(path),
                "level": int(level) if level is not None else derived_level,
                "process_order": (
                    int(process_order)
                    if process_order is not None
                    else derived_level * 1000000
                ),
            }
        )
    rows.sort(
        key=lambda item: (
            item["process_order"],
            item["level"],
            item["element_path"],
        )
    )
    if not rows:
        raise ValueError("No registry paths found for configured OSCAL model")
    return rows


def build_oscal_graph(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    model_key,
    source_system,
    source_table,
):
    del canonical_mapping_df  # canonical rows are already materialized in Cell 3

    registry_rows = _canonical_registry_rows(element_registry_df, model_key)
    root_paths = [row["element_path"] for row in registry_rows if not row["parent_path"]]
    if len(root_paths) != 1:
        raise ValueError(f"Expected one registry root; found {root_paths}")
    root_path = root_paths[0]

    node_rows = []
    edge_rows = []
    load_timestamp = datetime.datetime.now(datetime.timezone.utc)

    for record in source_df.to_local_iterator():
        source_record_id = str(record["SOURCE_RECORD_ID"])
        source_obj = _parse_source_json(record)
        nodes_by_path = {}

        for registry_row in registry_rows:
            path = registry_row["element_path"]
            parent_path = registry_row["parent_path"]
            mapping_rows = MAPPINGS_BY_ELEMENT_PATH.get(path, [])
            instances = build_element_instances(
                source_obj,
                source_record_id,
                path,
                mapping_rows,
            )

            # Structural singleton containers are materialized even without a
            # direct mapping. Empty collections are not invented.
            if not instances and (path == root_path or "[]" not in path):
                instances = [
                    {
                        "instance_key": "singleton",
                        "payload": {},
                        "parent_instance_key": None,
                    }
                ]

            instances = _inject_controlled_metadata_fields(path, instances)

            created_nodes = []
            for instance in instances:
                instance_key = instance["instance_key"]
                node_key = _deterministic_hash(
                    CONFIG["IDENTITY_VERSION"],
                    source_system,
                    source_table,
                    source_record_id,
                    model_key,
                    path,
                    instance_key,
                )
                oscal_uuid = _deterministic_uuid(
                    CONFIG["IDENTITY_VERSION"],
                    source_system,
                    source_table,
                    source_record_id,
                    model_key,
                    path,
                    instance_key,
                )
                created = {
                    "NODE_KEY": node_key,
                    "ELEMENT_PATH": path,
                    "INSTANCE_KEY": instance_key,
                    "PARENT_INSTANCE_KEY": instance.get("parent_instance_key"),
                    "OSCAL_UUID": oscal_uuid,
                    "ELEMENT_TYPE": _element_type(path),
                    "METADATA_JSON": json.dumps(
                        instance["payload"], sort_keys=True, default=str
                    ),
                    "SOURCE_SYSTEM_NAME": source_system,
                    "SOURCE_TABLE_NAME": source_table,
                    "SOURCE_RECORD_ID": source_record_id,
                    "DW_PIPELINE_RUN_ID": CONFIG["RUN_ID"],
                    "DW_LOAD_TIMESTAMP": load_timestamp,
                    "DW_LOAD_TIMESTAMP_TZ": load_timestamp,
                }
                node_rows.append(created)
                created_nodes.append(created)

            nodes_by_path[path] = created_nodes

            if not parent_path:
                continue
            parent_nodes = nodes_by_path.get(parent_path, [])
            for child_node in created_nodes:
                if not parent_nodes:
                    raise ValueError(
                        f"Missing parent {parent_path} for child {path}"
                    )
                if len(parent_nodes) == 1:
                    parent_node = parent_nodes[0]
                else:
                    parent_key = child_node["PARENT_INSTANCE_KEY"]
                    matches = [
                        node
                        for node in parent_nodes
                        if node["INSTANCE_KEY"] == parent_key
                    ]
                    if len(matches) != 1:
                        raise ValueError(
                            "Ambiguous collection parent for "
                            f"{path} instance {child_node['INSTANCE_KEY']}"
                        )
                    parent_node = matches[0]

                edge_key = _deterministic_hash(
                    "edge-v1",
                    parent_node["NODE_KEY"],
                    child_node["NODE_KEY"],
                    "CONTAINS",
                )
                edge_rows.append(
                    {
                        "EDGE_KEY": edge_key,
                        "FK_SOURCE_ELEMENT_HASH": parent_node["NODE_KEY"],
                        "FK_TARGET_ELEMENT_HASH": child_node["NODE_KEY"],
                        "DEPENDENCY_TYPE": "CONTAINS",
                        "SOURCE_OSCAL_UUID": parent_node["OSCAL_UUID"],
                        "TARGET_OSCAL_UUID": child_node["OSCAL_UUID"],
                    }
                )

    if not node_rows:
        raise ValueError("Graph builder produced no nodes")

    canonical_nodes_df = session.create_dataframe(node_rows)
    canonical_edges_df = session.create_dataframe(edge_rows)
    return canonical_nodes_df, canonical_edges_df


print("Cell 5 graph builder initialized")
