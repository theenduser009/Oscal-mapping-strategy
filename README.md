Yes. Here is the full Cell 5 replacement. This keeps the same function interface and output columns you already have, but changes the graph construction so a structural singleton such as component can inherit the identity of its specific components[] instance instead of collapsing to one node per Archer record.

Keep EXECUTE_WRITES = False. Replace the existing Cell 5 with this entire cell.

# ================================================================
# CELL 5
# BUILD CANONICAL OSCAL GRAPH
# ================================================================

import json

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

    # ============================================================
    # A. Load active registry for requested model
    # ============================================================

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
            f"No active registry rows for model {model_key}"
        )

    registry_by_path = {
        row["NODE_PATH"]: row
        for row in registry_rows
    }


    # ============================================================
    # B. Resolve mapping ownership once
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
    # Internal helpers
    # ============================================================

    def _binary_hex(value):
        if value is None:
            return ""
        if hasattr(value, "hex"):
            return value.hex().upper()
        return str(value)


    def _make_node(
        source_record_id,
        element_type,
        node_path,
        parent_path,
        process_order,
        payload,
        instance_key=None,
        lineage_key=None
    ):
        """
        Create deterministic node identity.

        Singleton nodes keep their original identity behavior.

        Nodes underneath a collection receive lineage_key so that
        separate collection instances do not collapse into one node.
        """

        base_seed = build_node_seed(
            source_system,
            source_table,
            source_record_id,
            element_type
        )

        if lineage_key is not None:
            seed = (
                f"{base_seed}|"
                f"{node_path}|"
                f"{lineage_key}"
            )
        elif instance_key is not None:
            seed = (
                f"{base_seed}|"
                f"{node_path}|"
                f"{instance_key}"
            )
        else:
            seed = base_seed

        node_key = compute_node_key(seed)
        node_uuid = compute_node_uuid(seed)

        payload_json = json.dumps(
            payload if payload is not None else {},
            default=str,
            separators=(",", ":")
        )

        node_instance = {
            "NODE_KEY": node_key,
            "OSCAL_UUID": node_uuid,
            "ELEMENT_TYPE": element_type,
            "NODE_PATH": node_path,
            "PARENT_NODE_PATH": parent_path,
            "INSTANCE_KEY": instance_key,
            "LINEAGE_KEY": lineage_key,
            "PAYLOAD": payload
        }

        node_row = (
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

        return node_instance, node_row


    def _make_edge(
        parent_node,
        child_node,
        source_record_id,
        parent_path,
        child_path
    ):

        parent_key = parent_node["NODE_KEY"]
        child_key = child_node["NODE_KEY"]

        dependency_type = "parent-of"

        edge_seed = build_edge_seed(
            _binary_hex(parent_key),
            _binary_hex(child_key),
            dependency_type
        )

        edge_key = compute_edge_key(edge_seed)

        return (
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


    # ============================================================
    # C. Build nodes + edges
    # ============================================================

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

        # --------------------------------------------------------
        # Nodes created for this Archer source record
        #
        # {
        #     node_path: [node_instance, ...]
        # }
        # --------------------------------------------------------

        record_nodes = {}


        # ========================================================
        # C1. Build direct nodes
        # ========================================================

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


            # ----------------------------------------------------
            # Collection node
            # ----------------------------------------------------

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

                    # Collection instance itself establishes lineage.
                    lineage_key = str(instance_key)

                    node_instance, node_row = _make_node(
                        source_record_id=source_record_id,
                        element_type=element_type,
                        node_path=node_path,
                        parent_path=parent_path,
                        process_order=process_order,
                        payload=payload,
                        instance_key=instance_key,
                        lineage_key=lineage_key
                    )

                    record_nodes.setdefault(
                        node_path,
                        []
                    ).append(
                        node_instance
                    )

                    node_rows.append(
                        node_row
                    )


            # ----------------------------------------------------
            # Singleton node
            # ----------------------------------------------------

            else:

                payload = build_element_payload(
                    source_record,
                    mappings
                )

                is_root = (
                    parent_path is None
                )

                # Root always exists.
                # Non-root singleton only exists directly when
                # mapped payload exists. Structural parents are
                # manufactured in C2 when descendants exist.
                if not is_root and not payload:
                    continue

                node_instance, node_row = _make_node(
                    source_record_id=source_record_id,
                    element_type=element_type,
                    node_path=node_path,
                    parent_path=parent_path,
                    process_order=process_order,
                    payload=payload,
                    instance_key=None,
                    lineage_key=None
                )

                record_nodes.setdefault(
                    node_path,
                    []
                ).append(
                    node_instance
                )

                node_rows.append(
                    node_row
                )


        # ========================================================
        # C2. Create missing structural singleton parents
        #
        # IMPORTANT:
        #
        # Old behavior created ONE singleton structural parent for
        # the whole Archer source record.
        #
        # New behavior:
        #
        # collection[] -> singleton
        #
        # creates one singleton for EACH collection instance.
        #
        # Example:
        #
        # components[] #1 -> component #1
        # components[] #2 -> component #2
        # components[] #3 -> component #3
        #
        # ========================================================

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


                # ------------------------------------------------
                # Parent already exists.
                #
                # HOWEVER:
                # if it exists only as an ordinary singleton but
                # should inherit collection-instance lineage,
                # C3 handles only compatible lineage.
                # ------------------------------------------------

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


                # A missing collection parent cannot be inferred.
                # Collection instances must come from source data.
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


                # ------------------------------------------------
                # Determine whether this structural singleton sits
                # directly underneath instantiated parent nodes.
                #
                # Example:
                #
                # components[] -> component
                #
                # parent_parent_path = components[]
                # ------------------------------------------------

                upstream_nodes = []

                if parent_parent_path is not None:
                    upstream_nodes = (
                        record_nodes.get(
                            parent_parent_path,
                            []
                        )
                    )


                generated_parents = []


                # ------------------------------------------------
                # Instance-aware structural singleton
                # ------------------------------------------------

                if upstream_nodes:

                    for upstream_node in upstream_nodes:

                        lineage_key = (
                            upstream_node.get(
                                "LINEAGE_KEY"
                            )
                            or upstream_node.get(
                                "INSTANCE_KEY"
                            )
                            or _binary_hex(
                                upstream_node[
                                    "NODE_KEY"
                                ]
                            )
                        )

                        node_instance, node_row = _make_node(
                            source_record_id=source_record_id,
                            element_type=parent_element_type,
                            node_path=parent_path,
                            parent_path=parent_parent_path,
                            process_order=parent_process_order,
                            payload={},
                            instance_key=(
                                upstream_node.get(
                                    "INSTANCE_KEY"
                                )
                            ),
                            lineage_key=str(
                                lineage_key
                            )
                        )

                        generated_parents.append(
                            node_instance
                        )

                        node_rows.append(
                            node_row
                        )


                # ------------------------------------------------
                # Ordinary structural singleton
                # ------------------------------------------------

                else:

                    node_instance, node_row = _make_node(
                        source_record_id=source_record_id,
                        element_type=parent_element_type,
                        node_path=parent_path,
                        parent_path=parent_parent_path,
                        process_order=parent_process_order,
                        payload={},
                        instance_key=None,
                        lineage_key=None
                    )

                    generated_parents.append(
                        node_instance
                    )

                    node_rows.append(
                        node_row
                    )


                record_nodes[
                    parent_path
                ] = generated_parents

                current_path = parent_path


        # ========================================================
        # C3. Build parent -> child FACT relationships
        # ========================================================

        for child_path, child_nodes in list(
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


            # ----------------------------------------------------
            # Simple singleton parent
            # ----------------------------------------------------

            if len(parent_nodes) == 1:

                parent_node = parent_nodes[0]

                for child_node in child_nodes:

                    edge_rows.append(
                        _make_edge(
                            parent_node,
                            child_node,
                            source_record_id,
                            parent_path,
                            child_path
                        )
                    )

                continue


            # ----------------------------------------------------
            # Multiple parent instances.
            #
            # Match using inherited lineage.
            #
            # This prevents:
            #
            # component #1 -> every props[]
            #
            # and instead gives:
            #
            # component #1 -> its props[]
            # component #2 -> its props[]
            # ----------------------------------------------------

            parent_by_lineage = {}

            for parent_node in parent_nodes:

                lineage = (
                    parent_node.get(
                        "LINEAGE_KEY"
                    )
                    or parent_node.get(
                        "INSTANCE_KEY"
                    )
                )

                if lineage is not None:
                    parent_by_lineage.setdefault(
                        str(lineage),
                        []
                    ).append(
                        parent_node
                    )


            for child_node in child_nodes:

                child_lineage = (
                    child_node.get(
                        "LINEAGE_KEY"
                    )
                    or child_node.get(
                        "INSTANCE_KEY"
                    )
                )


                # -----------------------------------------------
                # Exact lineage match
                # -----------------------------------------------

                matched_parents = []

                if child_lineage is not None:
                    matched_parents = (
                        parent_by_lineage.get(
                            str(child_lineage),
                            []
                        )
                    )


                # -----------------------------------------------
                # If there is no lineage match, do NOT create a
                # cartesian product.
                #
                # A multi-instance parent requires explicit
                # instance lineage.
                # -----------------------------------------------

                if not matched_parents:
                    continue


                for parent_node in matched_parents:

                    edge_rows.append(
                        _make_edge(
                            parent_node,
                            child_node,
                            source_record_id,
                            parent_path,
                            child_path
                        )
                    )


    # ============================================================
    # D. Canonical Nodes DataFrame
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
    # E. Canonical Edges DataFrame
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


    return (
        canonical_nodes_df,
        canonical_edges_df
    )

Now do only this

Run Cell 5 first. If Cell 5 only defines the function and finishes successfully, then run your normal execution through Cell 7, still with:

EXECUTE_WRITES = False

Then run the component diagnostic.

The first thing we're checking is whether this changes:

components    4792
component        0
props         15120

to approximately:

components    4792
component     4792
props        15120

Don't turn writes on yet. Send me the Cell 7 output or the first error exactly as it appears.