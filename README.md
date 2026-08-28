Yes — now that I have the entire current Cell 6, we can do this safely. I would replace Cell 6 as a whole rather than patching pieces.

There is one important reason: in your current version, the EXECUTE_WRITES=False gate happens before dim_load_df and fact_load_df are constructed. That is why we could never validate the actual load DataFrames in dry-run mode. The corrected version below prepares and validates them first, then stops before any DML when writes are false.

I’m also keeping your existing merge logic intact and making verify_oscal_load() use the configured PK names instead of hard-coding SSP PKs.

Replace your entire Cell 6 with this

# ====================================================================
# Cell 6 - Validate + Load OSCAL Graph
# PRODUCTION / REUSABLE
# ====================================================================

from snowflake.snowpark.functions import (
    col,
    current_timestamp,
    lit
)

# ====================================================================
# Generic OSCAL Validation + Idempotent Loader
# Supports SSP, POA&M, and future OSCAL models
# ====================================================================


def validate_and_load_oscal(
    canonical_nodes_df,
    canonical_edges_df,
    config
):

    # ================================================================
    # A. GRAPH VALIDATION
    # ================================================================

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
    print("Nodes                 :", node_count)
    print("Edges                 :", edge_count)
    print("Null node keys        :", null_node_keys)
    print("Duplicate node keys   :", duplicate_node_keys)
    print("Null edge keys        :", null_edge_keys)
    print("Duplicate edge keys   :", duplicate_edge_keys)
    print("Missing parents       :", missing_parents)
    print("Missing children      :", missing_children)

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

    # ================================================================
    # B. TARGET CONFIGURATION
    # ================================================================

    dim_table = config["TARGET_DIM"]
    fact_table = config["TARGET_FACT"]

    # Defaults preserve existing SSP behavior.
    # Other models can override these through CONFIG.
    dim_pk = config.get(
        "DIM_PK_COLUMN",
        "PK_OSCAL_SSP_ELEMENT_HASH"
    )

    fact_pk = config.get(
        "FACT_PK_COLUMN",
        "PK_FACT_OSCAL_DEPENDENCY_HASH"
    )

    # Read actual target schemas.
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

    # ================================================================
    # C. PREPARE DIM LOAD
    # ================================================================

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

    # Only load columns that physically exist in the target.
    dim_load_columns = [
        column_name
        for column_name in dim_column_order
        if column_name in dim_target_columns
    ]

    dim_load_df = canonical_nodes_df.select(
        *[
            dim_expression_map[column_name]
            for column_name in dim_load_columns
        ]
    )

    # ================================================================
    # D. PREPARE FACT LOAD
    # ================================================================

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
        column_name
        for column_name in fact_column_order
        if column_name in fact_target_columns
    ]

    fact_load_df = canonical_edges_df.select(
        *[
            fact_expression_map[column_name]
            for column_name in fact_load_columns
        ]
    )

    # ================================================================
    # E. PRE-WRITE LOAD VALIDATION
    #
    # IMPORTANT:
    # This runs even when EXECUTE_WRITES = False.
    # No tables are changed here.
    # ================================================================

    dim_load_count = dim_load_df.count()

    dim_distinct_pk_count = (
        dim_load_df
        .select(col(dim_pk))
        .distinct()
        .count()
    )

    dim_null_pk_count = (
        dim_load_df
        .filter(col(dim_pk).is_null())
        .count()
    )

    fact_load_count = fact_load_df.count()

    fact_distinct_pk_count = (
        fact_load_df
        .select(col(fact_pk))
        .distinct()
        .count()
    )

    fact_null_pk_count = (
        fact_load_df
        .filter(col(fact_pk).is_null())
        .count()
    )

    print("\n=== PRE-WRITE LOAD VALIDATION ===")

    print("DIM rows             :", dim_load_count)
    print("DIM distinct PKs     :", dim_distinct_pk_count)
    print("DIM null PKs         :", dim_null_pk_count)

    print("FACT rows            :", fact_load_count)
    print("FACT distinct PKs    :", fact_distinct_pk_count)
    print("FACT null PKs        :", fact_null_pk_count)

    pre_write_errors = 0

    if dim_load_count != dim_distinct_pk_count:
        pre_write_errors += 1
        print(
            "ERROR: DIM load contains duplicate primary keys"
        )

    if dim_null_pk_count != 0:
        pre_write_errors += 1
        print(
            "ERROR: DIM load contains NULL primary keys"
        )

    if fact_load_count != fact_distinct_pk_count:
        pre_write_errors += 1
        print(
            "ERROR: FACT load contains duplicate primary keys"
        )

    if fact_null_pk_count != 0:
        pre_write_errors += 1
        print(
            "ERROR: FACT load contains NULL primary keys"
        )

    if pre_write_errors != 0:
        raise ValueError(
            "OSCAL pre-write validation FAILED"
        )

    print("PRE-WRITE VALIDATION PASSED")

    # ================================================================
    # F. WRITE GATE
    # ================================================================

    if not config["EXECUTE_WRITES"]:

        print("\n=== WRITE GATE ===")
        print("EXECUTE_WRITES = False")
        print("No DIM/FACT changes were made.")

        return {
            "nodes": node_count,
            "edges": edge_count,
            "validation_passed": True,
            "pre_write_validation_passed": True,
            "dim_load_rows": dim_load_count,
            "fact_load_rows": fact_load_count,
            "writes_executed": False
        }

    # ================================================================
    # G. TEMPORARY MERGE SOURCES
    # ================================================================

    dim_load_df.create_or_replace_temp_view(
        "TMP_OSCAL_DIM_LOAD"
    )

    fact_load_df.create_or_replace_temp_view(
        "TMP_OSCAL_FACT_LOAD"
    )

    # ================================================================
    # H. IDEMPOTENT DIM MERGE
    # ================================================================

    dim_update_columns = [
        column_name
        for column_name in dim_load_columns
        if column_name != dim_pk.upper()
    ]

    dim_update_set = ",\n".join(
        f"t.{column_name} = s.{column_name}"
        for column_name in dim_update_columns
    )

    dim_insert_columns = ",\n".join(
        dim_load_columns
    )

    dim_insert_values = ",\n".join(
        f"s.{column_name}"
        for column_name in dim_load_columns
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

    # ================================================================
    # I. IDEMPOTENT FACT MERGE
    # ================================================================

    fact_update_columns = [
        column_name
        for column_name in fact_load_columns
        if column_name != fact_pk.upper()
    ]

    fact_update_set = ",\n".join(
        f"t.{column_name} = s.{column_name}"
        for column_name in fact_update_columns
    )

    fact_insert_columns = ",\n".join(
        fact_load_columns
    )

    fact_insert_values = ",\n".join(
        f"s.{column_name}"
        for column_name in fact_load_columns
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

    # ================================================================
    # J. POST-LOAD VERIFICATION
    # ================================================================

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
    print("DIM expected :", dim_load_count)
    print("DIM matched  :", dim_matches)
    print("FACT expected:", fact_load_count)
    print("FACT matched :", fact_matches)

    if (
        dim_matches != dim_load_count
        or fact_matches != fact_load_count
    ):
        raise ValueError(
            "OSCAL post-load verification FAILED"
        )

    print("LOAD VERIFIED")

    # ================================================================
    # K. RESULT
    # ================================================================

    return {
        "nodes": node_count,
        "edges": edge_count,
        "validation_passed": True,
        "pre_write_validation_passed": True,
        "writes_executed": True,
        "dim_load_rows": dim_load_count,
        "fact_load_rows": fact_load_count,
        "dim_matches": dim_matches,
        "fact_matches": fact_matches,
        "dim_merge_result": dim_merge_result,
        "fact_merge_result": fact_merge_result
    }


# ====================================================================
# Generic Post-Load Verification Helper
# ====================================================================

def verify_oscal_load(
    canonical_nodes_df,
    canonical_edges_df,
    config
):
    """
    Verify that every node/edge produced by this run
    exists in the configured target DIM/FACT tables.
    """

    dim_table = config["TARGET_DIM"]
    fact_table = config["TARGET_FACT"]

    dim_pk = config.get(
        "DIM_PK_COLUMN",
        "PK_OSCAL_SSP_ELEMENT_HASH"
    )

    fact_pk = config.get(
        "FACT_PK_COLUMN",
        "PK_FACT_OSCAL_DEPENDENCY_HASH"
    )

    expected_dim = canonical_nodes_df.count()
    expected_fact = canonical_edges_df.count()

    canonical_nodes_df.select(
        col("NODE_KEY").alias(dim_pk)
    ).create_or_replace_temp_view(
        "TMP_OSCAL_VERIFY_DIM"
    )

    canonical_edges_df.select(
        col("EDGE_KEY").alias(fact_pk)
    ).create_or_replace_temp_view(
        "TMP_OSCAL_VERIFY_FACT"
    )

    dim_matches = (
        session.sql(
            f"""
            SELECT COUNT(*) AS CNT
            FROM TMP_OSCAL_VERIFY_DIM s
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
            FROM TMP_OSCAL_VERIFY_FACT s
            JOIN {fact_table} t
              ON s.{fact_pk} = t.{fact_pk}
            """
        )
        .collect()[0]["CNT"]
    )

    print("\n=== Post-Load Verification ===")
    print("DIM expected :", expected_dim)
    print("DIM matched  :", dim_matches)
    print("FACT expected:", expected_fact)
    print("FACT matched :", fact_matches)

    if (
        dim_matches != expected_dim
        or fact_matches != expected_fact
    ):
        raise ValueError(
            "OSCAL post-load verification FAILED"
        )

    print("LOAD VERIFIED")

    return {
        "dim_expected": expected_dim,
        "dim_matched": dim_matches,
        "fact_expected": expected_fact,
        "fact_matched": fact_matches
    }


# ====================================================================
# NOTE:
# Execution remains in Cell 7.
# Do NOT call validate_and_load_oscal() here.
# ====================================================================

The key change is not the MERGE. Your merge remains essentially the same. The important restructuring is:

Build graph
   ↓
Graph validation
   ↓
Prepare DIM/FACT load DataFrames
   ↓
PRE-WRITE validation       ← NEW
   ↓
EXECUTE_WRITES ?
   ├── False → STOP safely
   └── True  → MERGE

Now do only this

Keep:

CONFIG["EXECUTE_WRITES"] = False

Then run:

Cell 6 → Cell 7.

Do not rerun your exploratory cells 8 onward. Cell 7 should now give us both the normal graph validation and a new section:

=== PRE-WRITE LOAD VALIDATION ===
DIM rows             : ...
DIM distinct PKs     : ...
DIM null PKs         : 0
FACT rows            : ...
FACT distinct PKs    : ...
FACT null PKs        : 0
PRE-WRITE VALIDATION PASSED

=== WRITE GATE ===
EXECUTE_WRITES = False
No DIM/FACT changes were made.

Send me that output. We will not turn writes on until those six numbers are clean.