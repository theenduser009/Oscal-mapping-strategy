# ============================================================
# Cell 6 — Validate + Idempotent DIM / FACT MERGE
# ============================================================
# Uses:
#   canonical_nodes_df
#   canonical_edges_df
#
# First run:
#   EXECUTE_WRITES = False
#
# After validation is approved:
#   change to True and rerun.
# ============================================================

EXECUTE_WRITES = False


# ------------------------------------------------------------
# 1. Create temporary validation views
# ------------------------------------------------------------

canonical_nodes_df.create_or_replace_temp_view(
    "TMP_OSCAL_CANONICAL_NODES"
)

canonical_edges_df.create_or_replace_temp_view(
    "TMP_OSCAL_CANONICAL_EDGES"
)


# ------------------------------------------------------------
# 2. Compact pre-load validation
# ------------------------------------------------------------

validation = session.sql("""
SELECT

    (SELECT COUNT(*)
     FROM TMP_OSCAL_CANONICAL_NODES)
        AS NODE_COUNT,

    (SELECT COUNT(*)
     FROM TMP_OSCAL_CANONICAL_EDGES)
        AS EDGE_COUNT,

    (SELECT COUNT(*)
     FROM TMP_OSCAL_CANONICAL_NODES
     WHERE NODE_KEY IS NULL)
        AS NULL_NODE_KEYS,

    (
        SELECT COUNT(*)
        FROM (
            SELECT NODE_KEY
            FROM TMP_OSCAL_CANONICAL_NODES
            GROUP BY NODE_KEY
            HAVING COUNT(*) > 1
        )
    ) AS DUPLICATE_NODE_KEYS,

    (SELECT COUNT(*)
     FROM TMP_OSCAL_CANONICAL_EDGES
     WHERE EDGE_KEY IS NULL)
        AS NULL_EDGE_KEYS,

    (
        SELECT COUNT(*)
        FROM (
            SELECT EDGE_KEY
            FROM TMP_OSCAL_CANONICAL_EDGES
            GROUP BY EDGE_KEY
            HAVING COUNT(*) > 1
        )
    ) AS DUPLICATE_EDGE_KEYS,

    (
        SELECT COUNT(*)
        FROM TMP_OSCAL_CANONICAL_EDGES e
        LEFT JOIN TMP_OSCAL_CANONICAL_NODES n
          ON e.SOURCE_NODE_KEY = n.NODE_KEY
        WHERE n.NODE_KEY IS NULL
    ) AS MISSING_SOURCE_NODES,

    (
        SELECT COUNT(*)
        FROM TMP_OSCAL_CANONICAL_EDGES e
        LEFT JOIN TMP_OSCAL_CANONICAL_NODES n
          ON e.TARGET_NODE_KEY = n.NODE_KEY
        WHERE n.NODE_KEY IS NULL
    ) AS MISSING_TARGET_NODES
""").collect()[0]


print("=== Cell 6 Validation ===")
print(f"Nodes:                {validation['NODE_COUNT']}")
print(f"Edges:                {validation['EDGE_COUNT']}")
print(f"Null node keys:       {validation['NULL_NODE_KEYS']}")
print(f"Duplicate node keys:  {validation['DUPLICATE_NODE_KEYS']}")
print(f"Null edge keys:       {validation['NULL_EDGE_KEYS']}")
print(f"Duplicate edge keys:  {validation['DUPLICATE_EDGE_KEYS']}")
print(f"Missing parents:      {validation['MISSING_SOURCE_NODES']}")
print(f"Missing children:     {validation['MISSING_TARGET_NODES']}")


# ------------------------------------------------------------
# 3. Stop automatically if canonical data is unsafe
# ------------------------------------------------------------

validation_failures = (
    validation["NULL_NODE_KEYS"]
    + validation["DUPLICATE_NODE_KEYS"]
    + validation["NULL_EDGE_KEYS"]
    + validation["DUPLICATE_EDGE_KEYS"]
    + validation["MISSING_SOURCE_NODES"]
    + validation["MISSING_TARGET_NODES"]
)

if validation["NODE_COUNT"] == 0:
    raise ValueError(
        "Validation failed: canonical_nodes_df is empty."
    )

if validation_failures > 0:
    raise ValueError(
        "Validation failed. DIM/FACT writes blocked."
    )

print("\nValidation PASSED.")


# ------------------------------------------------------------
# 4. Inspect actual target schemas
# ------------------------------------------------------------

dim_table = CONFIG["TARGET_DIM"]
fact_table = CONFIG["TARGET_FACT"]

dim_columns = [
    field.name.upper()
    for field in session.table(dim_table).schema.fields
]

fact_columns = [
    field.name.upper()
    for field in session.table(fact_table).schema.fields
]


# ------------------------------------------------------------
# 5. Resolve DIM physical columns
# ------------------------------------------------------------

dim_pk_candidates = [
    c for c in dim_columns
    if c.startswith("PK_") and c.endswith("_HASH")
]

if len(dim_pk_candidates) != 1:
    raise ValueError(
        f"Unable to identify DIM PK column: {dim_pk_candidates}"
    )

dim_pk = dim_pk_candidates[0]


payload_candidates = [
    c for c in dim_columns
    if c in (
        "ELEMENT_JSON",
        "PAYLOAD_JSON",
        "METADATA_JSON"
    )
]

if len(payload_candidates) != 1:
    raise ValueError(
        f"Unable to identify DIM JSON payload column: "
        f"{payload_candidates}"
    )

dim_payload = payload_candidates[0]


# ------------------------------------------------------------
# 6. Build target-shaped DIM temporary view
# ------------------------------------------------------------

run_id = str(CONFIG["RUN_ID"]).replace("'", "''")

dim_select = [
    f"NODE_KEY AS {dim_pk}",
    "ELEMENT_TYPE",
    "OSCAL_UUID",
    f"ELEMENT_JSON AS {dim_payload}",
    "SOURCE_SYSTEM_NAME",
    "SOURCE_TABLE_NAME",
    "SOURCE_RECORD_ID"
]

if "DW_PIPELINE_RUN_ID" in dim_columns:
    dim_select.append(
        f"'{run_id}' AS DW_PIPELINE_RUN_ID"
    )

if "DW_LOAD_TIMESTAMP" in dim_columns:
    dim_select.append(
        "CURRENT_TIMESTAMP() AS DW_LOAD_TIMESTAMP"
    )

if "DW_LOAD_TIMESTAMP_TZ" in dim_columns:
    dim_select.append(
        "CURRENT_TIMESTAMP() AS DW_LOAD_TIMESTAMP_TZ"
    )

session.sql(f"""
CREATE OR REPLACE TEMP VIEW TMP_OSCAL_DIM_LOAD AS
SELECT
    {", ".join(dim_select)}
FROM TMP_OSCAL_CANONICAL_NODES
""").collect()


# ------------------------------------------------------------
# 7. Resolve FACT physical columns
# ------------------------------------------------------------

fact_pk_candidates = [
    c for c in fact_columns
    if c.startswith("PK_") and c.endswith("_HASH")
]

if len(fact_pk_candidates) != 1:
    raise ValueError(
        f"Unable to identify FACT PK column: "
        f"{fact_pk_candidates}"
    )

fact_pk = fact_pk_candidates[0]


required_fact_columns = [
    "FK_SOURCE_ELEMENT_HASH",
    "FK_TARGET_ELEMENT_HASH",
    "DEPENDENCY_TYPE",
    "SOURCE_OSCAL_UUID",
    "TARGET_OSCAL_UUID"
]

missing_fact_columns = [
    c for c in required_fact_columns
    if c not in fact_columns
]

if missing_fact_columns:
    raise ValueError(
        f"Missing required FACT columns: "
        f"{missing_fact_columns}"
    )


# ------------------------------------------------------------
# 8. Build target-shaped FACT temporary view
# ------------------------------------------------------------

session.sql(f"""
CREATE OR REPLACE TEMP VIEW TMP_OSCAL_FACT_LOAD AS
SELECT
    EDGE_KEY AS {fact_pk},
    SOURCE_NODE_KEY AS FK_SOURCE_ELEMENT_HASH,
    TARGET_NODE_KEY AS FK_TARGET_ELEMENT_HASH,
    DEPENDENCY_TYPE,
    SOURCE_OSCAL_UUID,
    TARGET_OSCAL_UUID
FROM TMP_OSCAL_CANONICAL_EDGES
""").collect()


# ------------------------------------------------------------
# 9. Preview target load counts
# ------------------------------------------------------------

dim_load_count = session.table(
    "TMP_OSCAL_DIM_LOAD"
).count()

fact_load_count = session.table(
    "TMP_OSCAL_FACT_LOAD"
).count()

print("\n=== Load Preview ===")
print(f"DIM target:  {dim_table}")
print(f"DIM rows:    {dim_load_count}")
print(f"FACT target: {fact_table}")
print(f"FACT rows:   {fact_load_count}")


# ------------------------------------------------------------
# 10. WRITE SAFETY GATE
# ------------------------------------------------------------

if not EXECUTE_WRITES:

    print(
        "\nWRITE BLOCKED intentionally."
    )

    print(
        "Review this output first. "
        "Then set EXECUTE_WRITES = True."
    )


# ------------------------------------------------------------
# 11. Idempotent DIM + FACT MERGE
# ------------------------------------------------------------

else:

    # --------------------------------------------------------
    # DIM MERGE
    # --------------------------------------------------------

    dim_load_columns = [
        field.name.upper()
        for field
        in session.table("TMP_OSCAL_DIM_LOAD").schema.fields
    ]

    dim_update_columns = [
        c for c in dim_load_columns
        if c != dim_pk
    ]

    dim_update_sql = ",\n        ".join(
        f"t.{c} = s.{c}"
        for c in dim_update_columns
    )

    dim_insert_columns = ", ".join(
        dim_load_columns
    )

    dim_insert_values = ", ".join(
        f"s.{c}"
        for c in dim_load_columns
    )

    dim_merge_result = session.sql(f"""
        MERGE INTO {dim_table} t
        USING TMP_OSCAL_DIM_LOAD s

        ON t.{dim_pk} = s.{dim_pk}

        WHEN MATCHED THEN
            UPDATE SET
                {dim_update_sql}

        WHEN NOT MATCHED THEN
            INSERT (
                {dim_insert_columns}
            )
            VALUES (
                {dim_insert_values}
            )
    """).collect()


    # --------------------------------------------------------
    # FACT MERGE
    # --------------------------------------------------------

    fact_load_columns = [
        field.name.upper()
        for field
        in session.table("TMP_OSCAL_FACT_LOAD").schema.fields
    ]

    fact_update_columns = [
        c for c in fact_load_columns
        if c != fact_pk
    ]

    fact_update_sql = ",\n        ".join(
        f"t.{c} = s.{c}"
        for c in fact_update_columns
    )

    fact_insert_columns = ", ".join(
        fact_load_columns
    )

    fact_insert_values = ", ".join(
        f"s.{c}"
        for c in fact_load_columns
    )

    fact_merge_result = session.sql(f"""
        MERGE INTO {fact_table} t
        USING TMP_OSCAL_FACT_LOAD s

        ON t.{fact_pk} = s.{fact_pk}

        WHEN MATCHED THEN
            UPDATE SET
                {fact_update_sql}

        WHEN NOT MATCHED THEN
            INSERT (
                {fact_insert_columns}
            )
            VALUES (
                {fact_insert_values}
            )
    """).collect()


    print("\n=== MERGE COMPLETE ===")
    print("DIM:", dim_merge_result)
    print("FACT:", fact_merge_result)

    print(
        "\nCell 6 complete - "
        "DIM and FACT loaded idempotently"
    )
