Excellent — **Cell 5 reproduced the exact verified baseline**:

```text
Canonical nodes : 92,880
Canonical edges : 90,715
```

So the new production `build_oscal_graph()` function is proven. **Freeze Cells 1–5 now.** 🔒

Next is **Cell 6 only: reusable validation + gated load**. Because `EXECUTE_WRITES=False`, the first run will validate everything but will not touch DIM/FACT.

```python
# ============================================================
# Cell 6 — Validate + Load OSCAL Graph
# PRODUCTION / REUSABLE
# ============================================================

from snowflake.snowpark.functions import col, current_timestamp, lit


def validate_and_load_oscal(
    canonical_nodes_df,
    canonical_edges_df,
    config
):

    # --------------------------------------------------------
    # A. Validation
    # --------------------------------------------------------

    node_count = canonical_nodes_df.count()
    edge_count = canonical_edges_df.count()

    null_node_keys = (
        canonical_nodes_df
        .filter(col("NODE_KEY").is_null())
        .count()
    )

    duplicate_node_keys = (
        canonical_nodes_df
        .group_by("NODE_KEY")
        .count()
        .filter(col("COUNT") > 1)
        .count()
    )

    null_edge_keys = (
        canonical_edges_df
        .filter(col("EDGE_KEY").is_null())
        .count()
    )

    duplicate_edge_keys = (
        canonical_edges_df
        .group_by("EDGE_KEY")
        .count()
        .filter(col("COUNT") > 1)
        .count()
    )


    node_keys_df = canonical_nodes_df.select(
        col("NODE_KEY")
    ).distinct()


    missing_parents = (
        canonical_edges_df
        .select(
            col("SOURCE_NODE_KEY").alias("NODE_KEY")
        )
        .join(
            node_keys_df,
            ["NODE_KEY"],
            "left_anti"
        )
        .count()
    )


    missing_children = (
        canonical_edges_df
        .select(
            col("TARGET_NODE_KEY").alias("NODE_KEY")
        )
        .join(
            node_keys_df,
            ["NODE_KEY"],
            "left_anti"
        )
        .count()
    )


    print("=== OSCAL Graph Validation ===")
    print("Nodes               :", node_count)
    print("Edges               :", edge_count)
    print("Null node keys      :", null_node_keys)
    print("Duplicate node keys :", duplicate_node_keys)
    print("Null edge keys      :", null_edge_keys)
    print("Duplicate edge keys :", duplicate_edge_keys)
    print("Missing parents     :", missing_parents)
    print("Missing children    :", missing_children)


    validation_errors = sum([
        null_node_keys,
        duplicate_node_keys,
        null_edge_keys,
        duplicate_edge_keys,
        missing_parents,
        missing_children
    ])


    if validation_errors != 0:
        raise ValueError(
            "OSCAL graph validation FAILED"
        )


    print("\nValidation PASSED")


    # --------------------------------------------------------
    # B. Respect write gate
    # --------------------------------------------------------

    if not config["EXECUTE_WRITES"]:

        print("\n=== WRITE GATE ===")
        print("EXECUTE_WRITES = False")
        print("No DIM/FACT changes were made.")

        return {
            "nodes": node_count,
            "edges": edge_count,
            "validation_passed": True,
            "writes_executed": False
        }


    # --------------------------------------------------------
    # C. Prepare DIM load
    # --------------------------------------------------------

    dim_load_df = (
        canonical_nodes_df
        .select(
            col("NODE_KEY")
                .alias("PK_OSCAL_SSP_ELEMENT_HASH"),

            col("ELEMENT_TYPE"),

            col("OSCAL_UUID"),

            col("ELEMENT_JSON")
                .alias("METADATA_JSON"),

            col("SOURCE_SYSTEM_NAME"),

            col("SOURCE_TABLE_NAME"),

            col("SOURCE_RECORD_ID"),

            lit(config["RUN_ID"])
                .alias("DW_PIPELINE_RUN_ID"),

            current_timestamp()
                .alias("DW_LOAD_TIMESTAMP"),

            current_timestamp()
                .alias("DW_LOAD_TIMESTAMP_TZ")
        )
    )


    # --------------------------------------------------------
    # D. Prepare FACT load
    # --------------------------------------------------------

    fact_load_df = (
        canonical_edges_df
        .select(
            col("EDGE_KEY")
                .alias("PK_FACT_OSCAL_DEPENDENCY_HASH"),

            col("SOURCE_NODE_KEY")
                .alias("FK_SOURCE_ELEMENT_HASH"),

            col("TARGET_NODE_KEY")
                .alias("FK_TARGET_ELEMENT_HASH"),

            col("DEPENDENCY_TYPE"),

            col("SOURCE_OSCAL_UUID"),

            col("TARGET_OSCAL_UUID")
        )
    )


    # --------------------------------------------------------
    # E. Temporary views used by MERGE
    # --------------------------------------------------------

    dim_load_df.create_or_replace_temp_view(
        "TMP_OSCAL_DIM_LOAD"
    )

    fact_load_df.create_or_replace_temp_view(
        "TMP_OSCAL_FACT_LOAD"
    )


    # --------------------------------------------------------
    # F. Idempotent DIM MERGE
    # --------------------------------------------------------

    dim_merge_result = session.sql(f"""
        MERGE INTO {config["TARGET_DIM"]} t
        USING TMP_OSCAL_DIM_LOAD s

        ON t.PK_OSCAL_SSP_ELEMENT_HASH
         = s.PK_OSCAL_SSP_ELEMENT_HASH

        WHEN MATCHED THEN UPDATE SET
            t.ELEMENT_TYPE = s.ELEMENT_TYPE,
            t.OSCAL_UUID = s.OSCAL_UUID,
            t.METADATA_JSON = s.METADATA_JSON,
            t.SOURCE_SYSTEM_NAME = s.SOURCE_SYSTEM_NAME,
            t.SOURCE_TABLE_NAME = s.SOURCE_TABLE_NAME,
            t.SOURCE_RECORD_ID = s.SOURCE_RECORD_ID,
            t.DW_PIPELINE_RUN_ID = s.DW_PIPELINE_RUN_ID,
            t.DW_LOAD_TIMESTAMP = s.DW_LOAD_TIMESTAMP,
            t.DW_LOAD_TIMESTAMP_TZ = s.DW_LOAD_TIMESTAMP_TZ

        WHEN NOT MATCHED THEN INSERT (
            PK_OSCAL_SSP_ELEMENT_HASH,
            ELEMENT_TYPE,
            OSCAL_UUID,
            METADATA_JSON,
            SOURCE_SYSTEM_NAME,
            SOURCE_TABLE_NAME,
            SOURCE_RECORD_ID,
            DW_PIPELINE_RUN_ID,
            DW_LOAD_TIMESTAMP,
            DW_LOAD_TIMESTAMP_TZ
        )
        VALUES (
            s.PK_OSCAL_SSP_ELEMENT_HASH,
            s.ELEMENT_TYPE,
            s.OSCAL_UUID,
            s.METADATA_JSON,
            s.SOURCE_SYSTEM_NAME,
            s.SOURCE_TABLE_NAME,
            s.SOURCE_RECORD_ID,
            s.DW_PIPELINE_RUN_ID,
            s.DW_LOAD_TIMESTAMP,
            s.DW_LOAD_TIMESTAMP_TZ
        )
    """).collect()


    # --------------------------------------------------------
    # G. Idempotent FACT MERGE
    # --------------------------------------------------------

    fact_merge_result = session.sql(f"""
        MERGE INTO {config["TARGET_FACT"]} t
        USING TMP_OSCAL_FACT_LOAD s

        ON t.PK_FACT_OSCAL_DEPENDENCY_HASH
         = s.PK_FACT_OSCAL_DEPENDENCY_HASH

        WHEN MATCHED THEN UPDATE SET
            t.FK_SOURCE_ELEMENT_HASH =
                s.FK_SOURCE_ELEMENT_HASH,

            t.FK_TARGET_ELEMENT_HASH =
                s.FK_TARGET_ELEMENT_HASH,

            t.DEPENDENCY_TYPE =
                s.DEPENDENCY_TYPE,

            t.SOURCE_OSCAL_UUID =
                s.SOURCE_OSCAL_UUID,

            t.TARGET_OSCAL_UUID =
                s.TARGET_OSCAL_UUID

        WHEN NOT MATCHED THEN INSERT (
            PK_FACT_OSCAL_DEPENDENCY_HASH,
            FK_SOURCE_ELEMENT_HASH,
            FK_TARGET_ELEMENT_HASH,
            DEPENDENCY_TYPE,
            SOURCE_OSCAL_UUID,
            TARGET_OSCAL_UUID
        )
        VALUES (
            s.PK_FACT_OSCAL_DEPENDENCY_HASH,
            s.FK_SOURCE_ELEMENT_HASH,
            s.FK_TARGET_ELEMENT_HASH,
            s.DEPENDENCY_TYPE,
            s.SOURCE_OSCAL_UUID,
            s.TARGET_OSCAL_UUID
        )
    """).collect()


    print("\n=== MERGE COMPLETE ===")
    print("DIM :", dim_merge_result)
    print("FACT:", fact_merge_result)


    return {
        "nodes": node_count,
        "edges": edge_count,
        "validation_passed": True,
        "writes_executed": True,
        "dim_merge_result": dim_merge_result,
        "fact_merge_result": fact_merge_result
    }


# ============================================================
# Execute
# ============================================================

load_result = validate_and_load_oscal(
    canonical_nodes_df,
    canonical_edges_df,
    CONFIG
)
```

Because Cell 1 currently has:

```python
"EXECUTE_WRITES": False
```

the expected ending is:

```text
Nodes               : 92880
Edges               : 90715
Null node keys      : 0
Duplicate node keys : 0
Null edge keys      : 0
Duplicate edge keys : 0
Missing parents     : 0
Missing children    : 0

Validation PASSED

EXECUTE_WRITES = False
No DIM/FACT changes were made.
```

Run **Cell 6 only**. If that matches, we freeze the validation/load function too.
