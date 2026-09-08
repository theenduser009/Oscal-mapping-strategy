# %% Cell 6 - Validation, guarded idempotent DIM/FACT MERGE, verification

def _assert_safe_identifier(identifier):
    if not re.fullmatch(r"[A-Za-z0-9_.$]+", identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier}")


def _duplicate_count(dataframe, key_column):
    return (
        dataframe.group_by(col(key_column))
        .count()
        .filter(col("COUNT") > lit(1))
        .count()
    )


def _build_merge_sql(target_table, source_view, pk_column, columns):
    update_columns = [name for name in columns if name.upper() != pk_column.upper()]
    update_set = ",\n".join(f"t.{name} = s.{name}" for name in update_columns)
    insert_columns = ",\n".join(columns)
    insert_values = ",\n".join(f"s.{name}" for name in columns)
    return f"""
MERGE INTO {target_table} t
USING {source_view} s
ON t.{pk_column} = s.{pk_column}
WHEN MATCHED THEN UPDATE SET
{update_set}
WHEN NOT MATCHED THEN INSERT (
{insert_columns}
) VALUES (
{insert_values}
)
"""


def validate_and_load_oscal(canonical_nodes_df, canonical_edges_df, config):
    node_count = canonical_nodes_df.count()
    edge_count = canonical_edges_df.count()
    node_duplicate_count = _duplicate_count(canonical_nodes_df, "NODE_KEY")
    edge_duplicate_count = _duplicate_count(canonical_edges_df, "EDGE_KEY")
    node_null_count = canonical_nodes_df.filter(col("NODE_KEY").is_null()).count()
    edge_null_count = canonical_edges_df.filter(col("EDGE_KEY").is_null()).count()

    node_keys_df = canonical_nodes_df.select(col("NODE_KEY").alias("GRAPH_NODE_KEY"))
    missing_sources = (
        canonical_edges_df.join(
            node_keys_df,
            canonical_edges_df["FK_SOURCE_ELEMENT_HASH"] == node_keys_df["GRAPH_NODE_KEY"],
            "left_anti",
        ).count()
    )
    missing_targets = (
        canonical_edges_df.join(
            node_keys_df,
            canonical_edges_df["FK_TARGET_ELEMENT_HASH"] == node_keys_df["GRAPH_NODE_KEY"],
            "left_anti",
        ).count()
    )

    print("Graph nodes:", node_count)
    print("Graph edges:", edge_count)
    print("Duplicate node keys:", node_duplicate_count)
    print("Duplicate edge keys:", edge_duplicate_count)
    print("Dangling source edges:", missing_sources)
    print("Dangling target edges:", missing_targets)

    validation_errors = sum(
        [
            node_duplicate_count,
            edge_duplicate_count,
            node_null_count,
            edge_null_count,
            missing_sources,
            missing_targets,
        ]
    )
    if validation_errors:
        raise ValueError("OSCAL graph validation FAILED")

    dim_table = config["TARGET_DIM"]
    fact_table = config["TARGET_FACT"]
    dim_pk = config["DIM_PK_COLUMN"]
    fact_pk = config["FACT_PK_COLUMN"]
    for identifier in (dim_table, fact_table, dim_pk, fact_pk):
        _assert_safe_identifier(identifier)

    dim_target_columns = session.table(dim_table).columns
    fact_target_columns = session.table(fact_table).columns

    dim_expression_map = {
        dim_pk.upper(): col("NODE_KEY").alias(dim_pk),
        "ELEMENT_TYPE": col("ELEMENT_TYPE"),
        "OSCAL_UUID": col("OSCAL_UUID"),
        "METADATA_JSON": col("METADATA_JSON"),
        "SOURCE_SYSTEM_NAME": col("SOURCE_SYSTEM_NAME"),
        "SOURCE_TABLE_NAME": col("SOURCE_TABLE_NAME"),
        "SOURCE_RECORD_ID": col("SOURCE_RECORD_ID"),
        "DW_PIPELINE_RUN_ID": col("DW_PIPELINE_RUN_ID"),
        "DW_LOAD_TIMESTAMP": col("DW_LOAD_TIMESTAMP"),
        "DW_LOAD_TIMESTAMP_TZ": col("DW_LOAD_TIMESTAMP_TZ"),
    }
    fact_expression_map = {
        fact_pk.upper(): col("EDGE_KEY").alias(fact_pk),
        "FK_SOURCE_ELEMENT_HASH": col("FK_SOURCE_ELEMENT_HASH"),
        "FK_TARGET_ELEMENT_HASH": col("FK_TARGET_ELEMENT_HASH"),
        "DEPENDENCY_TYPE": col("DEPENDENCY_TYPE"),
        "SOURCE_OSCAL_UUID": col("SOURCE_OSCAL_UUID"),
        "TARGET_OSCAL_UUID": col("TARGET_OSCAL_UUID"),
    }

    dim_load_columns = [
        name for name in dim_target_columns if name.upper() in dim_expression_map
    ]
    fact_load_columns = [
        name for name in fact_target_columns if name.upper() in fact_expression_map
    ]

    if dim_pk.upper() not in {name.upper() for name in dim_load_columns}:
        raise ValueError(f"Target DIM does not expose configured PK {dim_pk}")
    if fact_pk.upper() not in {name.upper() for name in fact_load_columns}:
        raise ValueError(f"Target FACT does not expose configured PK {fact_pk}")

    dim_load_df = canonical_nodes_df.select(
        *[dim_expression_map[name.upper()] for name in dim_load_columns]
    )
    fact_load_df = canonical_edges_df.select(
        *[fact_expression_map[name.upper()] for name in fact_load_columns]
    )

    dim_load_count = dim_load_df.count()
    fact_load_count = fact_load_df.count()
    if _duplicate_count(dim_load_df, dim_pk) or _duplicate_count(fact_load_df, fact_pk):
        raise ValueError("OSCAL pre-write validation FAILED: duplicate target PK")
    if dim_load_df.filter(col(dim_pk).is_null()).count():
        raise ValueError("OSCAL pre-write validation FAILED: NULL DIM PK")
    if fact_load_df.filter(col(fact_pk).is_null()).count():
        raise ValueError("OSCAL pre-write validation FAILED: NULL FACT PK")

    print("PRE-WRITE VALIDATION PASSED")

    if not config["EXECUTE_WRITES"]:
        print("EXECUTE_WRITES = False; no DIM/FACT changes were made")
        return {
            "nodes": node_count,
            "edges": edge_count,
            "validation_passed": True,
            "pre_write_validation_passed": True,
            "dim_load_rows": dim_load_count,
            "fact_load_rows": fact_load_count,
            "writes_executed": False,
        }

    dim_source_view = "TMP_OSCAL_DIM_LOAD"
    fact_source_view = "TMP_OSCAL_FACT_LOAD"
    dim_load_df.create_or_replace_temp_view(dim_source_view)
    fact_load_df.create_or_replace_temp_view(fact_source_view)

    dim_merge_result = session.sql(
        _build_merge_sql(
            dim_table, dim_source_view, dim_pk, dim_load_columns
        )
    ).collect()
    fact_merge_result = session.sql(
        _build_merge_sql(
            fact_table, fact_source_view, fact_pk, fact_load_columns
        )
    ).collect()

    verification = verify_oscal_load(canonical_nodes_df, canonical_edges_df, config)
    return {
        "nodes": node_count,
        "edges": edge_count,
        "validation_passed": True,
        "pre_write_validation_passed": True,
        "dim_load_rows": dim_load_count,
        "fact_load_rows": fact_load_count,
        "writes_executed": True,
        "dim_merge_result": dim_merge_result,
        "fact_merge_result": fact_merge_result,
        "verification": verification,
    }


def verify_oscal_load(canonical_nodes_df, canonical_edges_df, config):
    dim_table = config["TARGET_DIM"]
    fact_table = config["TARGET_FACT"]
    dim_pk = config["DIM_PK_COLUMN"]
    fact_pk = config["FACT_PK_COLUMN"]

    expected_dim = canonical_nodes_df.count()
    expected_fact = canonical_edges_df.count()
    canonical_nodes_df.select(col("NODE_KEY").alias(dim_pk)).create_or_replace_temp_view(
        "TMP_OSCAL_VERIFY_DIM"
    )
    canonical_edges_df.select(col("EDGE_KEY").alias(fact_pk)).create_or_replace_temp_view(
        "TMP_OSCAL_VERIFY_FACT"
    )

    dim_matches = session.sql(
        f"""
        SELECT COUNT(*) AS CNT
        FROM TMP_OSCAL_VERIFY_DIM s
        JOIN {dim_table} t ON s.{dim_pk} = t.{dim_pk}
        """
    ).collect()[0]["CNT"]
    fact_matches = session.sql(
        f"""
        SELECT COUNT(*) AS CNT
        FROM TMP_OSCAL_VERIFY_FACT s
        JOIN {fact_table} t ON s.{fact_pk} = t.{fact_pk}
        """
    ).collect()[0]["CNT"]

    if dim_matches != expected_dim or fact_matches != expected_fact:
        raise ValueError("OSCAL post-load verification FAILED")
    print("LOAD VERIFIED")
    return {
        "dim_expected": expected_dim,
        "dim_matched": dim_matches,
        "fact_expected": expected_fact,
        "fact_matched": fact_matches,
    }


print("Cell 6 validation and loader initialized; execution remains in Cell 7")
