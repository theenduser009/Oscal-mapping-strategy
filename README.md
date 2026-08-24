Yes. **Much cleaner.** Replace the entire existing `validate_and_load_oscal()` function with the version below. Do not patch individual lines.

This version is generic for **SSP + POA&M + future models** as long as CONFIG supplies the target tables and PK column names.

```python
# ============================================================
# Generic OSCAL Validation + Idempotent Loader
# Supports SSP, POA&M, and future OSCAL models
# ============================================================

from snowflake.snowpark.functions import col, current_timestamp, lit


def validate_and_load_oscal(
    canonical_nodes_df,
    canonical_edges_df,
    config
):

    # ========================================================
    # A. GRAPH VALIDATION
    # ========================================================

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

    node_keys_df = (
        canonical_nodes_df
        .select(col("NODE_KEY"))
        .distinct()
    )

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


    # ========================================================
    # B. RESPECT WRITE GATE
    # ========================================================

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


    # ========================================================
    # C. TARGET CONFIGURATION
    # ========================================================

    dim_table = config["TARGET_DIM"]
    fact_table = config["TARGET_FACT"]

    # Defaults preserve existing SSP behavior.
    # Other models provide these through CONFIG.
    dim_pk = config.get(
        "DIM_PK_COLUMN",
        "PK_OSCAL_SSP_ELEMENT_HASH"
    )

    fact_pk = config.get(
        "FACT_PK_COLUMN",
        "PK_FACT_OSCAL_DEPENDENCY_HASH"
    )

    # Read actual target schemas.
    # This allows optional columns such as
    # DW_LOAD_TIMESTAMP_TZ to differ by model.
    dim_target_columns = {
        field.name.upper()
        for field in session.table(dim_table).schema.fields
    }

    fact_target_columns = {
        field.name.upper()
        for field in session.table(fact_table).schema.fields
    }

    if dim_pk.upper() not in dim_target_columns:
        raise ValueError(
            f"DIM PK column {dim_pk} does not exist in {dim_table}"
        )

    if fact_pk.upper() not in fact_target_columns:
        raise ValueError(
            f"FACT PK column {fact_pk} does not exist in {fact_table}"
        )


    # ========================================================
    # D. PREPARE DIM LOAD
    # ========================================================

    dim_expression_map = {
        dim_pk.upper():
            col("NODE_KEY").alias(dim_pk),

        "ELEMENT_TYPE":
            col("ELEMENT_TYPE"),

        "OSCAL_UUID":
            col("OSCAL_UUID"),

        "METADATA_JSON":
            col("ELEMENT_JSON").alias("METADATA_JSON"),

        "SOURCE_SYSTEM_NAME":
            col("SOURCE_SYSTEM_NAME"),

        "SOURCE_TABLE_NAME":
            col("SOURCE_TABLE_NAME"),

        "SOURCE_RECORD_ID":
            col("SOURCE_RECORD_ID"),

        "DW_PIPELINE_RUN_ID":
            lit(config["RUN_ID"]).alias(
                "DW_PIPELINE_RUN_ID"
            ),

        "DW_LOAD_TIMESTAMP":
            current_timestamp().alias(
                "DW_LOAD_TIMESTAMP"
            ),

        "DW_LOAD_TIMESTAMP_TZ":
            current_timestamp().alias(
                "DW_LOAD_TIMESTAMP_TZ"
            )
    }

    dim_column_order = [
        dim_pk.upper(),
        "ELEMENT_TYPE",
        "OSCAL_UUID",
        "METADATA_JSON",
        "SOURCE_SYSTEM_NAME",
        "SOURCE_TABLE_NAME",
        "SOURCE_RECORD_ID",
        "DW_PIPELINE_RUN_ID",
        "DW_LOAD_TIMESTAMP",
        "DW_LOAD_TIMESTAMP_TZ"
    ]

    # Only write columns that physically exist
    # in the configured target table.
    dim_load_columns = [
        c
        for c in dim_column_order
        if c in dim_target_columns
    ]

    dim_load_df = canonical_nodes_df.select(
        *[
            dim_expression_map[c]
            for c in dim_load_columns
        ]
    )


    # ========================================================
    # E. PREPARE FACT LOAD
    # ========================================================

    fact_expression_map = {
        fact_pk.upper():
            col("EDGE_KEY").alias(fact_pk),

        "FK_SOURCE_ELEMENT_HASH":
            col("SOURCE_NODE_KEY").alias(
                "FK_SOURCE_ELEMENT_HASH"
            ),

        "FK_TARGET_ELEMENT_HASH":
            col("TARGET_NODE_KEY").alias(
                "FK_TARGET_ELEMENT_HASH"
            ),

        "DEPENDENCY_TYPE":
            col("DEPENDENCY_TYPE"),

        "SOURCE_OSCAL_UUID":
            col("SOURCE_OSCAL_UUID"),

        "TARGET_OSCAL_UUID":
            col("TARGET_OSCAL_UUID")
    }

    fact_column_order = [
        fact_pk.upper(),
        "FK_SOURCE_ELEMENT_HASH",
        "FK_TARGET_ELEMENT_HASH",
        "DEPENDENCY_TYPE",
        "SOURCE_OSCAL_UUID",
        "TARGET_OSCAL_UUID"
    ]

    fact_load_columns = [
        c
        for c in fact_column_order
        if c in fact_target_columns
    ]

    fact_load_df = canonical_edges_df.select(
        *[
            fact_expression_map[c]
            for c in fact_load_columns
        ]
    )


    # ========================================================
    # F. TEMPORARY MERGE SOURCES
    # ========================================================

    dim_load_df.create_or_replace_temp_view(
        "TMP_OSCAL_DIM_LOAD"
    )

    fact_load_df.create_or_replace_temp_view(
        "TMP_OSCAL_FACT_LOAD"
    )


    # ========================================================
    # G. IDEMPOTENT DIM MERGE
    # ========================================================

    dim_update_columns = [
        c
        for c in dim_load_columns
        if c != dim_pk.upper()
    ]

    dim_update_set = ",\n".join(
        f"t.{c} = s.{c}"
        for c in dim_update_columns
    )

    dim_insert_columns = ",\n".join(
        dim_load_columns
    )

    dim_insert_values = ",\n".join(
        f"s.{c}"
        for c in dim_load_columns
    )

    dim_merge_sql = f"""
        MERGE INTO {dim_table} t
        USING TMP_OSCAL_DIM_LOAD s

        ON t.{dim_pk} = s.{dim_pk}

        WHEN MATCHED THEN UPDATE SET
            {dim_update_set}

        WHEN NOT MATCHED THEN INSERT (
            {dim_insert_columns}
        )
        VALUES (
            {dim_insert_values}
        )
    """

    dim_merge_result = (
        session.sql(dim_merge_sql)
        .collect()
    )


    # ========================================================
    # H. IDEMPOTENT FACT MERGE
    # ========================================================

    fact_update_columns = [
        c
        for c in fact_load_columns
        if c != fact_pk.upper()
    ]

    fact_update_set = ",\n".join(
        f"t.{c} = s.{c}"
        for c in fact_update_columns
    )

    fact_insert_columns = ",\n".join(
        fact_load_columns
    )

    fact_insert_values = ",\n".join(
        f"s.{c}"
        for c in fact_load_columns
    )

    fact_merge_sql = f"""
        MERGE INTO {fact_table} t
        USING TMP_OSCAL_FACT_LOAD s

        ON t.{fact_pk} = s.{fact_pk}

        WHEN MATCHED THEN UPDATE SET
            {fact_update_set}

        WHEN NOT MATCHED THEN INSERT (
            {fact_insert_columns}
        )
        VALUES (
            {fact_insert_values}
        )
    """

    fact_merge_result = (
        session.sql(fact_merge_sql)
        .collect()
    )


    print("\n=== MERGE COMPLETE ===")
    print("DIM :", dim_merge_result)
    print("FACT:", fact_merge_result)


    # ========================================================
    # I. POST-LOAD VERIFICATION
    # ========================================================

    dim_matches = (
        session.sql(
            f"""
            SELECT COUNT(*) AS CNT
            FROM TMP_OSCAL_DIM_LOAD s
            JOIN {dim_table} t
              ON s.{dim_pk} = t.{dim_pk}
            """
        )
        .collect()[0]["CNT"]
    )

    fact_matches = (
        session.sql(
            f"""
            SELECT COUNT(*) AS CNT
            FROM TMP_OSCAL_FACT_LOAD s
            JOIN {fact_table} t
              ON s.{fact_pk} = t.{fact_pk}
            """
        )
        .collect()[0]["CNT"]
    )

    print("\n=== Post-Load Verification ===")
    print("DIM expected :", node_count)
    print("DIM matched  :", dim_matches)
    print("FACT expected:", edge_count)
    print("FACT matched :", fact_matches)

    if (
        dim_matches != node_count
        or fact_matches != edge_count
    ):
        raise ValueError(
            "OSCAL post-load verification FAILED"
        )

    print("LOAD VERIFIED")


    # ========================================================
    # J. RESULT
    # ========================================================

    return {
        "nodes": node_count,
        "edges": edge_count,
        "validation_passed": True,
        "writes_executed": True,
        "dim_matches": dim_matches,
        "fact_matches": fact_matches,
        "dim_merge_result": dim_merge_result,
        "fact_merge_result": fact_merge_result
    }
```

### Now do only this

1. Replace the **entire old function** with this.
2. Run the function cell.
3. Leave:

```python
POAM_CONFIG["EXECUTE_WRITES"] = False
```

4. Rerun your POA&M validation cell.

We should still get:

```text
Nodes               : 3099
Edges               : 2563
Validation PASSED
EXECUTE_WRITES = False
No DIM/FACT changes were made.
```

If that stays clean, then the generic loader refactor is safe and the next step is the **first POA&M write**. We won't modify this function again just because another OSCAL model has a different PK name.
