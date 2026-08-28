Yes. Replace the entire existing build_oscal_graph() function in Cell 5 with the version below. Keep EXECUTE_WRITES = False.

The key change is that it carries an INSTANCE_KEY on every node and uses that to match a collection child to the correct collection parent instead of assuming there is only one parent node.

def build_oscal_graph(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    model_key,
    source_system,
    source_table
):

    # ================================================================
    # A. Load active registry for requested model
    # ================================================================

    registry_rows = (
        element_registry_df
        .filter(
            col("OSCAL_MODEL_KEY") == model_key
        )
        .order_by(
            col("PROCESS_ORDER"),
            col("NODE_PATH")
        )
        .collect()
    )

    if not registry_rows:
        raise ValueError(
            f"No active registry rows for model {model_key}"
        )

    registry_by_path = {
        row["NODE_PATH"]: row
        for row in registry_rows
    }

    # ================================================================
    # B. Resolve mapping ownership once
    # ================================================================

    mappings_by_node = {}

    for registry_row in registry_rows:

        node_path = registry_row["NODE_PATH"]

        mappings_by_node[node_path] = (
            get_mappings_for_node(
                canonical_mapping_df,
                element_registry_df,
                node_path,
                model_key
            )
        )

    # ================================================================
    # C. Build nodes + edges
    # ================================================================

    node_rows = []
    edge_rows = []

    for source_record in source_df.to_local_iterator():

        raw_record_id = source_record["SOURCE_RECORD_ID"]

        if raw_record_id is None:
            continue

        source_record_id = str(
            raw_record_id
        ).strip()

        if not source_record_id:
            continue

        # ------------------------------------------------------------
        # Nodes created for this Archer source record
        #
        # Structure:
        # {
        #   node_path: [
        #       {
        #          NODE_KEY,
        #          OSCAL_UUID,
        #          ELEMENT_TYPE,
        #          NODE_PATH,
        #          PARENT_NODE_PATH,
        #          INSTANCE_KEY
        #       }
        #   ]
        # }
        # ------------------------------------------------------------

        record_nodes = {}

        # ============================================================
        # C1. Build direct nodes
        # ============================================================

        for registry_row in registry_rows:

            node_path = registry_row["NODE_PATH"]
            element_type = registry_row["ELEMENT_TYPE"]
            parent_path = registry_row["PARENT_NODE_PATH"]
            process_order = registry_row["PROCESS_ORDER"]

            is_collection = registry_row["IS_COLLECTION"]

            instance_key_rule = (
                registry_row["INSTANCE_KEY_RULE"]
            )

            item_path = (
                registry_row["ITEM_PATH"]
                or "$"
            )

            mappings = mappings_by_node.get(
                node_path,
                []
            )

            # --------------------------------------------------------
            # Collection node
            # --------------------------------------------------------

            if (
                is_collection
                or is_collection_node(node_path)
            ):

                instances = _get_collection_instances(
                    source_record,
                    mappings,
                    instance_key_rule,
                    item_path
                )

                for instance in instances:

                    instance_key = instance[
                        "INSTANCE_KEY"
                    ]

                    payload = instance[
                        "PAYLOAD"
                    ]

                    if instance_key is None:
                        continue

                    instance_key = str(
                        instance_key
                    ).strip()

                    if not instance_key:
                        continue

                    # ------------------------------------------------
                    # Critical:
                    # collection identity includes NODE_PATH +
                    # INSTANCE_KEY so two logical collections sharing
                    # the same CONTENT_ID do not collapse together.
                    # ------------------------------------------------

                    base_seed = build_node_seed(
                        source_system,
                        source_table,
                        source_record_id,
                        element_type
                    )

                    seed = (
                        f"{base_seed}|"
                        f"{node_path}|"
                        f"{instance_key}"
                    )

                    node_key = compute_node_key(seed)
                    node_uuid = compute_node_uuid(seed)

                    payload_json = json.dumps(
                        payload,
                        default=str,
                        separators=(",", ":")
                    )

                    node_instance = {
                        "NODE_KEY": node_key,
                        "OSCAL_UUID": node_uuid,
                        "ELEMENT_TYPE": element_type,
                        "NODE_PATH": node_path,
                        "PARENT_NODE_PATH": parent_path,
                        "INSTANCE_KEY": instance_key
                    }

                    record_nodes.setdefault(
                        node_path,
                        []
                    ).append(
                        node_instance
                    )

                    node_rows.append(
                        (
                            node_key,
                            element_type,
                            node_uuid,
                            payload_json,
                            source_system,
                            source_table,
                            source_record_id,
                            model_key,
                            node_path,
                            parent_path,
                            process_order
                        )
                    )

            # --------------------------------------------------------
            # Singleton node
            # --------------------------------------------------------

            else:

                payload = build_element_payload(
                    source_record,
                    mappings
                )

                is_root = (
                    parent_path is None
                )

                # Root always exists.
                # Non-root singleton exists only if it owns payload.
                if not is_root and not payload:
                    continue

                seed = build_node_seed(
                    source_system,
                    source_table,
                    source_record_id,
                    element_type
                )

                node_key = compute_node_key(seed)
                node_uuid = compute_node_uuid(seed)

                payload_json = json.dumps(
                    payload,
                    default=str,
                    separators=(",", ":")
                )

                node_instance = {
                    "NODE_KEY": node_key,
                    "OSCAL_UUID": node_uuid,
                    "ELEMENT_TYPE": element_type,
                    "NODE_PATH": node_path,
                    "PARENT_NODE_PATH": parent_path,
                    "INSTANCE_KEY": None
                }

                record_nodes.setdefault(
                    node_path,
                    []
                ).append(
                    node_instance
                )

                node_rows.append(
                    (
                        node_key,
                        element_type,
                        node_uuid,
                        payload_json,
                        source_system,
                        source_table,
                        source_record_id,
                        model_key,
                        node_path,
                        parent_path,
                        process_order
                    )
                )

        # ============================================================
        # C2. Create missing structural singleton parents
        # ============================================================

        created_paths = list(
            record_nodes.keys()
        )

        for created_path in created_paths:

            current_path = created_path

            while True:

                current_registry = (
                    registry_by_path.get(
                        current_path
                    )
                )

                if current_registry is None:
                    break

                parent_path = (
                    current_registry[
                        "PARENT_NODE_PATH"
                    ]
                )

                if parent_path is None:
                    break

                if parent_path in record_nodes:
                    current_path = parent_path
                    continue

                parent_registry = (
                    registry_by_path.get(
                        parent_path
                    )
                )

                if parent_registry is None:
                    break

                # ----------------------------------------------------
                # Never synthesize a missing collection parent.
                # A collection parent must have real instance lineage.
                # ----------------------------------------------------

                if (
                    parent_registry["IS_COLLECTION"]
                    or is_collection_node(
                        parent_path
                    )
                ):
                    break

                parent_element_type = (
                    parent_registry[
                        "ELEMENT_TYPE"
                    ]
                )

                parent_parent_path = (
                    parent_registry[
                        "PARENT_NODE_PATH"
                    ]
                )

                parent_process_order = (
                    parent_registry[
                        "PROCESS_ORDER"
                    ]
                )

                seed = build_node_seed(
                    source_system,
                    source_table,
                    source_record_id,
                    parent_element_type
                )

                node_key = compute_node_key(seed)
                node_uuid = compute_node_uuid(seed)

                node_instance = {
                    "NODE_KEY": node_key,
                    "OSCAL_UUID": node_uuid,
                    "ELEMENT_TYPE": parent_element_type,
                    "NODE_PATH": parent_path,
                    "PARENT_NODE_PATH": parent_parent_path,
                    "INSTANCE_KEY": None
                }

                record_nodes[
                    parent_path
                ] = [
                    node_instance
                ]

                node_rows.append(
                    (
                        node_key,
                        parent_element_type,
                        node_uuid,
                        "{}",
                        source_system,
                        source_table,
                        source_record_id,
                        model_key,
                        parent_path,
                        parent_parent_path,
                        parent_process_order
                    )
                )

                current_path = parent_path

        # ============================================================
        # C3. Build parent -> child relationships
        # ============================================================

        for child_path, child_nodes in (
            record_nodes.items()
        ):

            child_registry = (
                registry_by_path.get(
                    child_path
                )
            )

            if child_registry is None:
                continue

            parent_path = (
                child_registry[
                    "PARENT_NODE_PATH"
                ]
            )

            if parent_path is None:
                continue

            parent_nodes = record_nodes.get(
                parent_path,
                []
            )

            if not parent_nodes:
                continue

            parent_registry = (
                registry_by_path.get(
                    parent_path
                )
            )

            parent_is_collection = (
                parent_registry is not None
                and (
                    parent_registry["IS_COLLECTION"]
                    or is_collection_node(
                        parent_path
                    )
                )
            )

            child_is_collection = (
                child_registry["IS_COLLECTION"]
                or is_collection_node(
                    child_path
                )
            )

            # --------------------------------------------------------
            # CASE 1:
            # Singleton parent -> any child
            # --------------------------------------------------------

            if not parent_is_collection:

                if len(parent_nodes) != 1:
                    raise ValueError(
                        "Singleton parent produced multiple "
                        f"instances: {parent_path}"
                    )

                parent_node = parent_nodes[0]

                for child_node in child_nodes:

                    _append_parent_child_edge(
                        edge_rows,
                        parent_node,
                        child_node,
                        source_record_id,
                        parent_path,
                        child_path
                    )

                continue

            # --------------------------------------------------------
            # CASE 2:
            # Collection parent -> child
            #
            # Match using INSTANCE_KEY.
            #
            # This is the missing behavior required for:
            #
            # components[]
            #   -> component
            #   -> props[]
            #   -> links[]
            #   -> protocols[]
            #   -> responsible-roles[]
            # --------------------------------------------------------

            parent_by_instance_key = {}

            for parent_node in parent_nodes:

                parent_instance_key = (
                    parent_node.get(
                        "INSTANCE_KEY"
                    )
                )

                if parent_instance_key is None:
                    continue

                parent_by_instance_key[
                    str(parent_instance_key).strip()
                ] = parent_node

            for child_node in child_nodes:

                child_instance_key = (
                    child_node.get(
                        "INSTANCE_KEY"
                    )
                )

                if child_instance_key is None:

                    # ------------------------------------------------
                    # A singleton child under a collection parent
                    # requires explicit lineage.
                    #
                    # Until registry metadata provides a distinct
                    # parent-instance key, do not cross-join every
                    # component to every child.
                    # ------------------------------------------------

                    continue

                child_instance_key = str(
                    child_instance_key
                ).strip()

                parent_node = (
                    parent_by_instance_key.get(
                        child_instance_key
                    )
                )

                if parent_node is None:
                    continue

                _append_parent_child_edge(
                    edge_rows,
                    parent_node,
                    child_node,
                    source_record_id,
                    parent_path,
                    child_path
                )

    # ================================================================
    # D. Canonical Nodes DataFrame
    # ================================================================

    node_schema = StructType([
        StructField(
            "NODE_KEY",
            BinaryType()
        ),
        StructField(
            "ELEMENT_TYPE",
            StringType()
        ),
        StructField(
            "OSCAL_UUID",
            StringType()
        ),
        StructField(
            "ELEMENT_JSON_TEXT",
            StringType()
        ),
        StructField(
            "SOURCE_SYSTEM_NAME",
            StringType()
        ),
        StructField(
            "SOURCE_TABLE_NAME",
            StringType()
        ),
        StructField(
            "SOURCE_RECORD_ID",
            StringType()
        ),
        StructField(
            "OSCAL_MODEL_KEY",
            StringType()
        ),
        StructField(
            "NODE_PATH",
            StringType()
        ),
        StructField(
            "PARENT_NODE_PATH",
            StringType()
        ),
        StructField(
            "PROCESS_ORDER",
            IntegerType()
        )
    ])

    canonical_nodes_raw_df = (
        session.create_dataframe(
            node_rows,
            schema=node_schema
        )
    )

    canonical_nodes_df = (
        canonical_nodes_raw_df
        .select(
            col("NODE_KEY"),
            col("ELEMENT_TYPE"),
            col("OSCAL_UUID"),
            parse_json(
                col("ELEMENT_JSON_TEXT")
            ).alias("ELEMENT_JSON"),
            col("SOURCE_SYSTEM_NAME"),
            col("SOURCE_TABLE_NAME"),
            col("SOURCE_RECORD_ID"),
            col("OSCAL_MODEL_KEY"),
            col("NODE_PATH"),
            col("PARENT_NODE_PATH"),
            col("PROCESS_ORDER")
        )
    )

    # ================================================================
    # E. Canonical Edges DataFrame
    # ================================================================

    edge_schema = StructType([
        StructField(
            "EDGE_KEY",
            BinaryType()
        ),
        StructField(
            "SOURCE_NODE_KEY",
            BinaryType()
        ),
        StructField(
            "TARGET_NODE_KEY",
            BinaryType()
        ),
        StructField(
            "DEPENDENCY_TYPE",
            StringType()
        ),
        StructField(
            "SOURCE_OSCAL_UUID",
            StringType()
        ),
        StructField(
            "TARGET_OSCAL_UUID",
            StringType()
        ),
        StructField(
            "SOURCE_RECORD_ID",
            StringType()
        ),
        StructField(
            "SOURCE_NODE_PATH",
            StringType()
        ),
        StructField(
            "TARGET_NODE_PATH",
            StringType()
        )
    ])

    canonical_edges_df = (
        session.create_dataframe(
            edge_rows,
            schema=edge_schema
        )
    )

    return (
        canonical_nodes_df,
        canonical_edges_df
    )


def _append_parent_child_edge(
    edge_rows,
    parent_node,
    child_node,
    source_record_id,
    parent_path,
    child_path
):

    parent_key = parent_node[
        "NODE_KEY"
    ]

    child_key = child_node[
        "NODE_KEY"
    ]

    dependency_type = "parent_of"

    edge_seed = build_edge_seed(
        parent_key.hex().upper(),
        child_key.hex().upper(),
        dependency_type
    )

    edge_key = compute_edge_key(
        edge_seed
    )

    edge_rows.append(
        (
            edge_key,
            parent_key,
            child_key,
            dependency_type,
            parent_node["OSCAL_UUID"],
            child_node["OSCAL_UUID"],
            source_record_id,
            parent_path,
            child_path
        )
    )

One important point before you run it: this fixes the engine’s ability to maintain instance lineage, but it does not magically create props[], links[], protocols[], etc. while those registry rows are inactive.

So after replacing Cell 5, rerun Cell 5 and then Cell 7 with writes still false. Do not activate anything yet.

Send me only the new Cell 7 output. I want to see whether the baseline stays at 59,232 / 56,419 before we activate one deeper child branch.