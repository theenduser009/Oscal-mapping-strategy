# ============================================================
# Cell 5 — Generic Canonical Node + Edge Builder
# ============================================================
#
# Driven by:
#   canonical_mapping_df
#   element_registry_df
#   OSCAL_ELEMENT_PATH
#
# Supports:
#   - singleton nodes
#   - [] collection nodes
#   - structural parents
#
# Does NOT use CARDINALITY.
# Does NOT contain SSP-specific element names.
# NO target writes.
# ============================================================

import json
import re

from snowflake.snowpark.functions import col, parse_json
from snowflake.snowpark.types import (
    StructType,
    StructField,
    StringType,
    BinaryType,
    IntegerType
)


# ============================================================
# A. Small generic collection helpers
# ============================================================

def _normalize_key_name(value):
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


def _get_instance_key(item, instance_key_rule):
    """
    Example:

    item:
        {"ContentId": 634658, "LevelId": 17}

    rule:
        CONTENT_ID

    result:
        634658
    """

    if item is None:
        return None

    # Object/reference
    if isinstance(item, dict):

        expected = _normalize_key_name(
            instance_key_rule
        )

        for key, value in item.items():

            if _normalize_key_name(key) == expected:
                return value

        return None

    # Scalar reference
    return item


def _parse_source_json(source_record):

    record = _row_to_dict(source_record)

    value = record.get("CURATED_JSON")

    if isinstance(value, str):

        try:
            return json.loads(value)

        except json.JSONDecodeError:
            return {}

    if isinstance(value, (dict, list)):
        return value

    return {}


def _get_collection_instances(
    source_record,
    mappings,
    instance_key_rule
):
    """
    Extract unique instances of a collection node.

    Deduplication is by INSTANCE_KEY_RULE.

    No CARDINALITY logic.
    """

    source_obj = _parse_source_json(
        source_record
    )

    instances = {}

    for mapping in mappings:

        source_field = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        if not source_field:
            continue

        value = resolve_json_path(
            source_obj,
            source_field
        )

        if value in (None, "", [], {}):
            continue

        values = (
            value
            if isinstance(value, list)
            else [value]
        )

        for item in values:

            instance_key = _get_instance_key(
                item,
                instance_key_rule
            )

            if instance_key is None:
                continue

            instance_key = str(
                instance_key
            ).strip()

            if not instance_key:
                continue

            # Same instance referenced more than once
            if instance_key not in instances:

                instances[instance_key] = {
                    "INSTANCE_KEY": instance_key,
                    "PAYLOAD": item
                }

            else:
                # Prefer richer dictionary form
                existing = instances[
                    instance_key
                ]["PAYLOAD"]

                if (
                    not isinstance(existing, dict)
                    and isinstance(item, dict)
                ):
                    instances[
                        instance_key
                    ]["PAYLOAD"] = item

    return list(
        instances.values()
    )


# ============================================================
# B. Load active registry
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
        f"No active registry rows for {model_key}"
    )


registry_by_path = {
    row["NODE_PATH"]: row
    for row in registry_rows
}


# ============================================================
# C. Resolve mapping ownership once
# ============================================================

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


# ============================================================
# D. Build canonical nodes
# ============================================================

node_rows = []
edge_rows = []

source_system = CONFIG["SOURCE_SYSTEM_NAME"]
source_table = CONFIG["SOURCE_TABLE_NAME"]

for source_record in source_df.to_local_iterator():

    raw_record_id = source_record[
        "SOURCE_RECORD_ID"
    ]

    if raw_record_id is None:
        continue

    source_record_id = str(
        raw_record_id
    ).strip()

    if not source_record_id:
        continue


    # --------------------------------------------------------
    # Nodes created for THIS source record
    #
    # node_path -> list of node instances
    # --------------------------------------------------------

    record_nodes = {}


    # --------------------------------------------------------
    # D1. Build direct nodes
    # --------------------------------------------------------

    for registry_row in registry_rows:

        node_path = registry_row[
            "NODE_PATH"
        ]

        element_type = registry_row[
            "ELEMENT_TYPE"
        ]

        parent_path = registry_row[
            "PARENT_NODE_PATH"
        ]

        process_order = registry_row[
            "PROCESS_ORDER"
        ]

        is_collection = registry_row[
            "IS_COLLECTION"
        ]

        instance_key_rule = registry_row[
            "INSTANCE_KEY_RULE"
        ]

        mappings = mappings_by_node.get(
            node_path,
            []
        )


        # ====================================================
        # COLLECTION NODE
        # ====================================================

        if is_collection or "[]" in node_path:

            instances = _get_collection_instances(
                source_record,
                mappings,
                instance_key_rule
            )

            for instance in instances:

                instance_key = instance[
                    "INSTANCE_KEY"
                ]

                payload = instance[
                    "PAYLOAD"
                ]

                # Collection identity:
                #
                # preserve existing singleton seed
                # + append NODE_PATH + INSTANCE_KEY
                #
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

                node_key = compute_node_key(
                    seed
                )

                node_uuid = compute_node_uuid(
                    seed
                )

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


        # ====================================================
        # SINGLETON NODE
        # ====================================================

        else:

            payload = build_element_payload(
                source_record,
                mappings
            )

            is_root = (
                parent_path is None
            )

            # Root always exists.
            #
            # Other singleton nodes initially exist
            # only when direct payload exists.
            # Structural parents are added below.
            if (
                not is_root
                and not payload
            ):
                continue

            seed = build_node_seed(
                source_system,
                source_table,
                source_record_id,
                element_type
            )

            node_key = compute_node_key(
                seed
            )

            node_uuid = compute_node_uuid(
                seed
            )

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

            record_nodes[
                node_path
            ] = [
                node_instance
            ]

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


    # ========================================================
    # D2. Create missing STRUCTURAL singleton parents
    # ========================================================
    #
    # Example:
    #
    # system-implementation has no direct mappings,
    # but components[] exists.
    #
    # Therefore system-implementation must still exist.
    # ========================================================

    created_paths = list(
        record_nodes.keys()
    )

    for created_path in created_paths:

        current_path = created_path

        while True:

            current_registry = registry_by_path.get(
                current_path
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

            parent_registry = registry_by_path.get(
                parent_path
            )

            if parent_registry is None:
                break

            # We can safely synthesize a structural
            # SINGLETON parent.
            #
            # Collection-parent relationships require
            # instance context and are intentionally blocked.
            if (
                parent_registry[
                    "IS_COLLECTION"
                ]
                or "[]" in parent_path
            ):
                raise ValueError(
                    "Nested collection parent requires "
                    f"instance relationship metadata: "
                    f"{parent_path}"
                )

            parent_element_type = parent_registry[
                "ELEMENT_TYPE"
            ]

            parent_process_order = parent_registry[
                "PROCESS_ORDER"
            ]

            parent_parent_path = parent_registry[
                "PARENT_NODE_PATH"
            ]

            seed = build_node_seed(
                source_system,
                source_table,
                source_record_id,
                parent_element_type
            )

            node_key = compute_node_key(
                seed
            )

            node_uuid = compute_node_uuid(
                seed
            )

            node_instance = {
                "NODE_KEY": node_key,
                "OSCAL_UUID": node_uuid,
                "ELEMENT_TYPE":
                    parent_element_type,
                "NODE_PATH": parent_path,
                "PARENT_NODE_PATH":
                    parent_parent_path,
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


    # ========================================================
    # E. Build parent -> child relationships
    # ========================================================

    for child_path, child_nodes in record_nodes.items():

        child_registry = registry_by_path.get(
            child_path
        )

        if child_registry is None:
            continue

        parent_path = child_registry[
            "PARENT_NODE_PATH"
        ]

        # Root
        if parent_path is None:
            continue

        parent_nodes = record_nodes.get(
            parent_path,
            []
        )

        if not parent_nodes:
            continue

        # Current supported relationship:
        # parent singleton -> child singleton/collection
        if len(parent_nodes) != 1:

            raise ValueError(
                "Collection parent relationship requires "
                f"instance-level relationship metadata: "
                f"{parent_path} -> {child_path}"
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

            edge_rows.append(
                (
                    edge_key,
                    parent_key,
                    child_key,
                    dependency_type,
                    parent_node[
                        "OSCAL_UUID"
                    ],
                    child_node[
                        "OSCAL_UUID"
                    ],
                    source_record_id,
                    parent_path,
                    child_path
                )
            )


# ============================================================
# F. canonical_nodes_df
# ============================================================

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
        ).alias(
            "ELEMENT_JSON"
        ),
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
# G. canonical_edges_df
# ============================================================

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


# ============================================================
# H. Compact summary
# ============================================================

print("=== Cell 5 Build Summary ===")

print(
    "Source records:",
    source_df.count()
)

print(
    "Canonical nodes:",
    canonical_nodes_df.count()
)

print(
    "Canonical edges:",
    canonical_edges_df.count()
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
    "generic canonical nodes and edges ready"
)
