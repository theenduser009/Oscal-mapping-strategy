# ============================================================
# Cell 5 — Build Canonical Nodes + Relationships
# ============================================================
# Uses frozen Cells 1–4.
#
# OUTPUT:
#   canonical_nodes_df
#   canonical_edges_df
#
# NO MERGE
# NO DIM/FACT writes
# ============================================================

import json

from snowflake.snowpark.functions import col, parse_json
from snowflake.snowpark.types import (
    StructType,
    StructField,
    StringType,
    BinaryType,
    IntegerType
)


# ============================================================
# 1. Active registry for selected OSCAL model
# ============================================================

model_key = CONFIG["OSCAL_MODEL"]

registry_rows = (
    element_registry_df
    .filter(
        (col("OSCAL_MODEL_KEY") == model_key)
        & (col("IS_ACTIVE") == True)
    )
    .order_by(
        col("PROCESS_ORDER"),
        col("NODE_PATH")
    )
    .collect()
)

if not registry_rows:
    raise ValueError(
        f"No active registry rows found for model: {model_key}"
    )


# ============================================================
# 2. Preload mappings once per registered node
# ============================================================

mappings_by_node = {}

for registry_row in registry_rows:

    node_path = registry_row["NODE_PATH"]

    mappings_by_node[node_path] = get_mappings_for_node(
        canonical_mapping_df,
        element_registry_df,
        node_path,
        oscal_model_key=model_key
    )


# ============================================================
# 3. Build canonical node + edge rows
# ============================================================

node_rows = []
edge_rows = []

source_system = CONFIG["SOURCE_SYSTEM_NAME"]
source_table = CONFIG["SOURCE_TABLE_NAME"]

for source_record in source_df.to_local_iterator():

    raw_record_id = source_record["SOURCE_RECORD_ID"]

    if raw_record_id is None:
        continue

    source_record_id = str(raw_record_id).strip()

    if not source_record_id:
        continue

    # Nodes created for THIS source record only.
    record_nodes = {}

    # --------------------------------------------------------
    # Build nodes
    # --------------------------------------------------------

    for registry_row in registry_rows:

        node_path = registry_row["NODE_PATH"]
        element_type = registry_row["ELEMENT_TYPE"]
        parent_node_path = registry_row["PARENT_NODE_PATH"]
        process_order = registry_row["PROCESS_ORDER"]

        mappings = mappings_by_node.get(
            node_path,
            []
        )

        payload = build_element_payload(
            source_record,
            mappings
        )

        # Generic creation rule:
        #
        # ROOT:
        #   always create once per source record
        #
        # CHILD:
        #   create only when mapped payload exists
        #
        is_root = parent_node_path is None

        if not is_root and not payload:
            continue

        # ----------------------------------------------------
        # Frozen V1 singleton identity
        # ----------------------------------------------------

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
                parent_node_path,
                process_order
            )
        )

        record_nodes[node_path] = {
            "NODE_KEY": node_key,
            "OSCAL_UUID": node_uuid,
            "ELEMENT_TYPE": element_type
        }


    # --------------------------------------------------------
    # Build parent -> child edges for THIS source record
    # --------------------------------------------------------

    for registry_row in registry_rows:

        child_path = registry_row["NODE_PATH"]
        parent_path = registry_row["PARENT_NODE_PATH"]

        # Root has no parent edge.
        if parent_path is None:
            continue

        # Child was not created because it had no payload.
        if child_path not in record_nodes:
            continue

        # Parent must exist for relationship.
        if parent_path not in record_nodes:
            continue

        parent_node = record_nodes[parent_path]
        child_node = record_nodes[child_path]

        parent_key = parent_node["NODE_KEY"]
        child_key = child_node["NODE_KEY"]

        # Frozen edge contract expects HEX keys.
        parent_key_hex = parent_key.hex().upper()
        child_key_hex = child_key.hex().upper()

        dependency_type = "parent_of"

        edge_seed = build_edge_seed(
            parent_key_hex,
            child_key_hex,
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


# ============================================================
# 4. Create canonical_nodes_df
# ============================================================

node_schema = StructType([
    StructField("NODE_KEY", BinaryType()),
    StructField("ELEMENT_TYPE", StringType()),
    StructField("OSCAL_UUID", StringType()),
    StructField("ELEMENT_JSON_TEXT", StringType()),
    StructField("SOURCE_SYSTEM_NAME", StringType()),
    StructField("SOURCE_TABLE_NAME", StringType()),
    StructField("SOURCE_RECORD_ID", StringType()),
    StructField("OSCAL_MODEL_KEY", StringType()),
    StructField("NODE_PATH", StringType()),
    StructField("PARENT_NODE_PATH", StringType()),
    StructField("PROCESS_ORDER", IntegerType())
])

canonical_nodes_raw_df = session.create_dataframe(
    node_rows,
    schema=node_schema
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


# ============================================================
# 5. Create canonical_edges_df
# ============================================================

edge_schema = StructType([
    StructField("EDGE_KEY", BinaryType()),
    StructField("SOURCE_NODE_KEY", BinaryType()),
    StructField("TARGET_NODE_KEY", BinaryType()),
    StructField("DEPENDENCY_TYPE", StringType()),
    StructField("SOURCE_OSCAL_UUID", StringType()),
    StructField("TARGET_OSCAL_UUID", StringType()),
    StructField("SOURCE_RECORD_ID", StringType()),
    StructField("SOURCE_NODE_PATH", StringType()),
    StructField("TARGET_NODE_PATH", StringType())
])

canonical_edges_df = session.create_dataframe(
    edge_rows,
    schema=edge_schema
)


# ============================================================
# 6. Compact validation only
# ============================================================

print("=== Cell 5 Build Summary ===")
print(
    f"Source records: {source_df.count()}"
)
print(
    f"Canonical nodes: {canonical_nodes_df.count()}"
)
print(
    f"Canonical edges: {canonical_edges_df.count()}"
)

print("\n=== Nodes by Element Type ===")

(
    canonical_nodes_df
    .group_by("ELEMENT_TYPE")
    .count()
    .sort("ELEMENT_TYPE")
    .show()
)

print("\n=== Edges by Relationship ===")

(
    canonical_edges_df
    .group_by(
        "SOURCE_NODE_PATH",
        "TARGET_NODE_PATH"
    )
    .count()
    .sort(
        "SOURCE_NODE_PATH",
        "TARGET_NODE_PATH"
    )
    .show()
)

print(
    "\nCell 5 complete - "
    "canonical_nodes_df and canonical_edges_df ready"
)
