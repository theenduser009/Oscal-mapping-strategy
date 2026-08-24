Perfect. Now **Cell 5 only** — this is where the proven graph-building logic becomes the reusable production function.

Nothing writes to Snowflake here.

```python
# ============================================================
# Cell 5 — Generic OSCAL Graph Builder
# PRODUCTION / REUSABLE
# ============================================================

from snowflake.snowpark.functions import col, parse_json
from snowflake.snowpark.types import (
    StructType,
    StructField,
    StringType,
    BinaryType,
    IntegerType
)


def build_oscal_graph(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    model_key,
    source_system,
    source_table
):

    # ========================================================
    # A. Load active registry for requested model
    # ========================================================

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


    # ========================================================
    # B. Resolve mapping ownership once
    # ========================================================

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


    # ========================================================
    # C. Build nodes + edges
    # ========================================================

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


        # Nodes created for this Archer record
        record_nodes = {}


        # ====================================================
        # C1. Build direct nodes
        # ====================================================

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


            # ------------------------------------------------
            # Collection node
            # ------------------------------------------------

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


                    # Preserve frozen singleton identity
                    # and extend it for collection instances.
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


                    node_rows.append((
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
                    ))


            # ------------------------------------------------
            # Singleton node
            # ------------------------------------------------

            else:

                payload = build_element_payload(
                    source_record,
                    mappings
                )

                is_root = (
                    parent_path is None
                )


                # Root always exists.
                # Other singleton nodes only exist when
                # mapped payload exists.
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


                node_rows.append((
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
                ))


        # ====================================================
        # C2. Create missing structural singleton parents
        # ====================================================

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


                parent_path = current_registry[
                    "PARENT_NODE_PATH"
                ]

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


                # Current production engine deliberately
                # does not infer nested collection lineage.
                if (
                    parent_registry["IS_COLLECTION"]
                    or is_collection_node(
                        parent_path
                    )
                ):
                    raise ValueError(
                        "Nested collection parent requires "
                        "instance relationship metadata: "
                        f"{parent_path}"
                    )


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
                    "ELEMENT_TYPE":
                        parent_element_type,
                    "NODE_PATH":
                        parent_path,
                    "PARENT_NODE_PATH":
                        parent_parent_path,
                    "INSTANCE_KEY":
                        None
                }


                record_nodes[parent_path] = [
                    node_instance
                ]


                # Structural parent exists because its
                # descendant exists, but has no direct payload.
                node_rows.append((
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
                ))


                current_path = parent_path


        # ====================================================
        # C3. Build parent -> child FACT relationships
        # ====================================================

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


            parent_path = child_registry[
                "PARENT_NODE_PATH"
            ]

            if parent_path is None:
                continue


            parent_nodes = record_nodes.get(
                parent_path,
                []
            )

            if not parent_nodes:
                continue


            # Current supported relationship:
            # singleton parent -> singleton/collection child
            if len(parent_nodes) != 1:

                raise ValueError(
                    "Collection parent relationship "
                    "requires instance-level "
                    f"relationship metadata: {parent_path}"
                )


            parent_node = parent_nodes[0]


            for child_node in child_nodes:

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


                edge_rows.append((
                    edge_key,
                    parent_key,
                    child_key,
                    dependency_type,
                    parent_node["OSCAL_UUID"],
                    child_node["OSCAL_UUID"],
                    source_record_id,
                    parent_path,
                    child_path
                ))


    # ========================================================
    # D. Canonical Nodes DataFrame
    # ========================================================

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


    # ========================================================
    # E. Canonical Edges DataFrame
    # ========================================================

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


# ============================================================
# F. Execute builder for configured model
# READ ONLY
# ============================================================

canonical_nodes_df, canonical_edges_df = (
    build_oscal_graph(
        source_df=source_df,
        canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df,
        model_key=CONFIG["OSCAL_MODEL"],
        source_system=CONFIG["SOURCE_SYSTEM_NAME"],
        source_table=CONFIG["SOURCE_TABLE_NAME"]
    )
)


# ============================================================
# G. Production baseline check
# ============================================================

node_count = canonical_nodes_df.count()
edge_count = canonical_edges_df.count()

print("=== OSCAL Graph Build ===")
print("Model           :", CONFIG["OSCAL_MODEL"])
print("Canonical nodes :", node_count)
print("Canonical edges :", edge_count)

print("\n=== Nodes by Element Type ===")

canonical_nodes_df.group_by(
    "ELEMENT_TYPE"
).count().sort(
    "ELEMENT_TYPE"
).show()

print("\n=== Edges by Relationship ===")

canonical_edges_df.group_by(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).count().sort(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).show()

print(
    "\nCell 5 complete - "
    "generic OSCAL graph built"
)
```

### Our acceptance test

For SSP, **the new production notebook must reproduce the exact proven baseline**:

```text
Canonical nodes : 92,880
Canonical edges : 90,715
```

This is the important test: same 2,165 Archer records, same 608 mappings, same 12 active registry nodes, same generic identity rules → **same graph from the clean mapper notebook**.

`EXECUTE_WRITES` is still `False`, so Cell 5 cannot change your target tables.

Run Cell 5 only. If we get **92,880 / 90,715**, we freeze the graph-builder function and move to the reusable validation/load function.
