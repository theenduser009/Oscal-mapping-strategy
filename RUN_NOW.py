# RUN NOW — Level-355 Control Implementation source readiness
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Purpose:
# Confirm the current Level-355 source contract and whether Authorization Package
# ALLOCATED_CONTROLS references resolve to the actual control records needed for:
#   system-security-plan.control-implementation.implemented-requirements[]
#
# Expected source:
#   RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW
#
# This is the only next discovery step. It profiles the actual referenced control
# records and the existing live registry branch. No broad table search.

CONTROL_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW"
AUTH_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"

KEY_FIELDS = (
    "CONTROL_NUMBER",
    "FEED_CONTROL_NUMBER",
    "CONTROL_NAME",
    "CONTROL",
    "IMPLEMENTATION_DETAILS",
    "OVERALL_IMPLEMENTATION_DETAILS",
    "IMPLEMENTATION_STATUS",
    "CONTROL_PARAMETERS",
    "RESPONSIBLE_ROLE",
    "CONTROL_ENTITY",
    "CONTROL_SET",
    "CONTROL_ORIGINATION",
    "ALLOCATION_STATUS",
    "INHERITED_IMPLEMENTATION_DETAILS",
    "PARTIAL_INHERITED_IMPLEMENTATION_DETAILS",
    "ASSESSMENT_STATUS",
    "OVERALL_ASSESSMENT_STATUS",
)

print("LEVEL355_CONTROL_IMPLEMENTATION_READINESS")

# ------------------------------------------------------------------
# 1) Physical source contract
# ------------------------------------------------------------------
table_name = CONTROL_TABLE.split(".")[-1]
schema_rows = session.sql(f"""
SELECT ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME = '{table_name}'
ORDER BY ORDINAL_POSITION
""").collect()

print("CONTROL_TABLE =", CONTROL_TABLE)
print("COLUMN_COUNT =", len(schema_rows))
print("COLUMNS =", [(r["COLUMN_NAME"], r["DATA_TYPE"]) for r in schema_rows])

columns = {str(r["COLUMN_NAME"]).upper() for r in schema_rows}
has_contract = {"CONTENT_ID", "CURATED_JSON"}.issubset(columns)
print("HAS_CONTENT_ID_CURATED_JSON =", has_contract)

if not schema_rows:
    print("RESULT: LEVEL355_CONTROL_TABLE_NOT_FOUND")
elif not has_contract:
    print("RESULT: LEVEL355_CONTROL_TABLE_CONTRACT_NEEDS_REVIEW")
else:
    # ------------------------------------------------------------------
    # 2) Row counts and Authorization Package reference coverage
    # ------------------------------------------------------------------
    control_stats = session.sql(f"""
    SELECT
        COUNT(*) AS RAW_ROWS,
        COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) AS DISTINCT_CONTENT_IDS,
        COUNT_IF(CONTENT_ID IS NULL OR LENGTH(TRIM(CONTENT_ID::STRING)) = 0) AS NULL_OR_BLANK_IDS
    FROM {CONTROL_TABLE}
    """).collect()[0]

    print("CONTROL_RAW_ROWS =", control_stats["RAW_ROWS"])
    print("CONTROL_DISTINCT_CONTENT_IDS =", control_stats["DISTINCT_CONTENT_IDS"])
    print("CONTROL_NULL_OR_BLANK_IDS =", control_stats["NULL_OR_BLANK_IDS"])

    coverage = session.sql(f"""
    WITH refs AS (
        SELECT DISTINCT TRIM(f.value:ContentId::STRING) AS CONTENT_ID
        FROM {AUTH_TABLE} a,
             LATERAL FLATTEN(INPUT => a.CURATED_JSON:ALLOCATED_CONTROLS) f
        WHERE f.value:LevelId::STRING = '355'
          AND f.value:ContentId IS NOT NULL
    ),
    controls AS (
        SELECT DISTINCT TRIM(CONTENT_ID::STRING) AS CONTENT_ID
        FROM {CONTROL_TABLE}
        WHERE CONTENT_ID IS NOT NULL
    )
    SELECT
        COUNT(*) AS REFERENCED_LEVEL355_IDS,
        COUNT_IF(c.CONTENT_ID IS NOT NULL) AS MATCHED_IDS,
        COUNT_IF(c.CONTENT_ID IS NULL) AS MISSING_IDS
    FROM refs r
    LEFT JOIN controls c USING (CONTENT_ID)
    """).collect()[0]

    print("REFERENCED_LEVEL355_IDS =", coverage["REFERENCED_LEVEL355_IDS"])
    print("MATCHED_LEVEL355_IDS =", coverage["MATCHED_IDS"])
    print("MISSING_LEVEL355_IDS =", coverage["MISSING_IDS"])

    # ------------------------------------------------------------------
    # 3) Profile the fields that matter first for implemented-requirements[]
    #    on only controls currently referenced by Source One.
    # ------------------------------------------------------------------
    print()
    print("REFERENCED_CONTROL_FIELD_PROFILE")

    for field in KEY_FIELDS:
        rows = session.sql(f"""
        WITH refs AS (
            SELECT DISTINCT TRIM(f.value:ContentId::STRING) AS CONTENT_ID
            FROM {AUTH_TABLE} a,
                 LATERAL FLATTEN(INPUT => a.CURATED_JSON:ALLOCATED_CONTROLS) f
            WHERE f.value:LevelId::STRING = '355'
              AND f.value:ContentId IS NOT NULL
        ),
        matched AS (
            SELECT c.CURATED_JSON
            FROM {CONTROL_TABLE} c
            JOIN refs r
              ON TRIM(c.CONTENT_ID::STRING) = r.CONTENT_ID
        )
        SELECT
            TYPEOF(CURATED_JSON:{field}) AS VALUE_TYPE,
            COUNT(*) AS ROW_COUNT
        FROM matched
        GROUP BY TYPEOF(CURATED_JSON:{field})
        ORDER BY ROW_COUNT DESC, VALUE_TYPE
        """).collect()

        type_counts = {
            ("ABSENT_OR_SQL_NULL" if r["VALUE_TYPE"] is None else str(r["VALUE_TYPE"])): int(r["ROW_COUNT"])
            for r in rows
        }
        populated = sum(
            n for t, n in type_counts.items()
            if t not in {"ABSENT_OR_SQL_NULL", "NULL_VALUE"}
        )

        print(
            field,
            "| POPULATED =", populated,
            "| TYPES =", type_counts,
        )

    # ------------------------------------------------------------------
    # 4) Existing live SSP control-implementation registry branch
    # ------------------------------------------------------------------
    print()
    print("CONTROL_IMPLEMENTATION_REGISTRY")
    registry = session.sql("""
    SELECT
        NODE_PATH,
        ELEMENT_TYPE,
        PARENT_NODE_PATH,
        IS_COLLECTION,
        INSTANCE_KEY_RULE,
        PROCESS_ORDER,
        IS_ACTIVE,
        ITEM_PATH,
        OPERATOR,
        UUID_POLICY,
        REQUIRED_MEMBERS
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) = 'SSP'
      AND NODE_PATH LIKE 'system-security-plan.control-implementation%'
    ORDER BY PROCESS_ORDER, NODE_PATH
    """).collect()

    for row in registry:
        print(row.as_dict())

    active_paths = {
        str(r["NODE_PATH"]).strip()
        for r in registry
        if bool(r["IS_ACTIVE"])
    }
    has_ci = "system-security-plan.control-implementation" in active_paths
    has_ir = "system-security-plan.control-implementation.implemented-requirements[]" in active_paths

    print("CONTROL_IMPLEMENTATION_PATH_READY =", has_ci)
    print("IMPLEMENTED_REQUIREMENTS_PATH_READY =", has_ir)

    missing = int(coverage["MISSING_IDS"] or 0)
    matched = int(coverage["MATCHED_IDS"] or 0)

    if matched > 0 and missing == 0 and has_ir:
        print("RESULT: LEVEL355_READY_FOR_IMPLEMENTED_REQUIREMENTS_MAPPING")
    elif matched > 0 and missing == 0 and not has_ir:
        print("RESULT: LEVEL355_SOURCE_READY_REGISTRY_BRANCH_NEEDED")
    elif matched > 0:
        print("RESULT: LEVEL355_SOURCE_PARTIAL_COVERAGE_REVIEW")
    else:
        print("RESULT: LEVEL355_SOURCE_NOT_JOINING_TO_AUTH_PACKAGE")
