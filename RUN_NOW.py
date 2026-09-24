# RUN NOW — Trace Authorization Package ALLOCATED_CONTROLS through Archer CR/RR metadata
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Goal:
# Resolve the exact reciprocal Archer field for:
#   Level 353 / Module 547 / ALLOCATED_CONTROLS
# and test whether a Level-355 reciprocal field links control rows back to
# Authorization Package records.
#
# This avoids guessing from field names.

AUTH_LEVEL_ID = 353
AUTH_MODULE_ID = 547
CONTROL_LEVEL_ID = 355

AUTH_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
CONTROL_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW"

def norm(name):
    return "".join(ch for ch in str(name).upper() if ch.isalnum())

print("ALLOCATED_CONTROLS_CR_RR_RELATIONSHIP_TRACE")

# ------------------------------------------------------------------
# 1) Source field identity.
# ------------------------------------------------------------------
source_fields = session.sql(f"""
SELECT
    FIELD_ID,
    SQL_FIELD_NAME,
    FIELD_TYPE_ID,
    LEVEL_ID,
    MODULE_ID,
    SELECT_ID
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(TRIM(SQL_FIELD_NAME)) = 'ALLOCATED_CONTROLS'
  AND LEVEL_ID = {AUTH_LEVEL_ID}
  AND MODULE_ID = {AUTH_MODULE_ID}
ORDER BY FIELD_ID
""").collect()

print("SOURCE_FIELD_ROWS =", len(source_fields))
for row in source_fields:
    print("SOURCE_FIELD =", row.as_dict())

if not source_fields:
    raise ValueError("Source One ALLOCATED_CONTROLS metadata row was not found")

source_field_ids = {str(row["FIELD_ID"]).strip() for row in source_fields}

# ------------------------------------------------------------------
# 2) Discover the current relationship metadata table by its CR/RR columns.
# ------------------------------------------------------------------
column_rows = session.sql("""
SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND STARTSWITH(UPPER(TABLE_NAME), 'ARCHER_META')
ORDER BY TABLE_NAME, ORDINAL_POSITION
""").collect()

columns_by_table = {}
for row in column_rows:
    columns_by_table.setdefault(row["TABLE_NAME"], []).append(
        (row["COLUMN_NAME"], row["DATA_TYPE"])
    )

relationship_tables = []
for table, cols in columns_by_table.items():
    by_norm = {norm(name): name for name, _ in cols}
    cr = by_norm.get("CRFIELDID")
    rr = by_norm.get("RRFIELDID")
    if cr and rr:
        relationship_tables.append((table, cr, rr, cols))

print()
print("RELATIONSHIP_TABLE_CANDIDATES =", len(relationship_tables))
for table, cr, rr, cols in relationship_tables:
    print(
        "RELATIONSHIP_TABLE =", table,
        "| CR_COLUMN =", cr,
        "| RR_COLUMN =", rr,
        "| COLUMNS =", cols,
    )

if not relationship_tables:
    print("RESULT: ARCHER_CR_RR_RELATIONSHIP_TABLE_NOT_FOUND")
else:
    reciprocal_ids = set()
    relationship_evidence = []

    for table, cr_col, rr_col, _ in relationship_tables:
        full = "RTX_RAW_DEV.ES_ESC_GRC." + table
        ids_sql = ", ".join("'" + x.replace("'", "''") + "'" for x in sorted(source_field_ids))

        rels = session.sql(f"""
        SELECT
            TRIM({cr_col}::STRING) AS CR_FIELD_ID,
            TRIM({rr_col}::STRING) AS RR_FIELD_ID
        FROM {full}
        WHERE TRIM({cr_col}::STRING) IN ({ids_sql})
           OR TRIM({rr_col}::STRING) IN ({ids_sql})
        ORDER BY CR_FIELD_ID, RR_FIELD_ID
        """).collect()

        print()
        print("RELATIONSHIP_ROWS", table, "=", len(rels))
        for rel in rels:
            cr_id = str(rel["CR_FIELD_ID"]).strip()
            rr_id = str(rel["RR_FIELD_ID"]).strip()

            if cr_id in source_field_ids:
                source_side = "CR"
                reciprocal = rr_id
            elif rr_id in source_field_ids:
                source_side = "RR"
                reciprocal = cr_id
            else:
                continue

            reciprocal_ids.add(reciprocal)
            relationship_evidence.append((table, source_side, reciprocal))
            print(
                "RELATIONSHIP",
                "| SOURCE_SIDE =", source_side,
                "| RECIPROCAL_FIELD_ID =", reciprocal,
            )

    # ------------------------------------------------------------------
    # 3) Resolve reciprocal IDs back to field + level/module metadata.
    # ------------------------------------------------------------------
    reciprocal_rows = []
    if reciprocal_ids:
        ids_sql = ", ".join("'" + x.replace("'", "''") + "'" for x in sorted(reciprocal_ids))
        reciprocal_rows = session.sql(f"""
        SELECT
            FIELD_ID,
            SQL_FIELD_NAME,
            FIELD_TYPE_ID,
            LEVEL_ID,
            MODULE_ID,
            SELECT_ID
        FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
        WHERE TRIM(FIELD_ID::STRING) IN ({ids_sql})
        ORDER BY LEVEL_ID, MODULE_ID, FIELD_ID
        """).collect()

    print()
    print("RECIPROCAL_FIELDS =", len(reciprocal_rows))
    for row in reciprocal_rows:
        print("RECIPROCAL_FIELD =", row.as_dict())

    level355_fields = [
        row for row in reciprocal_rows
        if int(row["LEVEL_ID"]) == CONTROL_LEVEL_ID
    ]

    print("LEVEL355_RECIPROCAL_FIELD_COUNT =", len(level355_fields))

    # ------------------------------------------------------------------
    # 4) Test Level-355 reciprocal fields as reverse links to Authorization Package.
    #    We compare any embedded ContentId values to Authorization Package CONTENT_ID.
    # ------------------------------------------------------------------
    runtime_results = []

    for field_row in level355_fields:
        field = str(field_row["SQL_FIELD_NAME"]).strip()

        profile = session.sql(f"""
        WITH latest_controls AS (
            SELECT *
            FROM {CONTROL_TABLE}
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY TRIM(CONTENT_ID::STRING)
                ORDER BY ETL_LOAD_TS DESC NULLS LAST, LOAD_TIMESTAMP DESC NULLS LAST
            ) = 1
        ),
        field_values AS (
            SELECT
                TRIM(c.CONTENT_ID::STRING) AS CONTROL_CONTENT_ID,
                GET(c.CURATED_JSON, '{field}') AS FIELD_VALUE
            FROM latest_controls c
        )
        SELECT
            TYPEOF(FIELD_VALUE) AS VALUE_TYPE,
            COUNT(*) AS ROW_COUNT
        FROM field_values
        GROUP BY TYPEOF(FIELD_VALUE)
        ORDER BY ROW_COUNT DESC, VALUE_TYPE
        """).collect()

        shapes = {
            ("SQL_NULL" if r["VALUE_TYPE"] is None else str(r["VALUE_TYPE"])): int(r["ROW_COUNT"])
            for r in profile
        }

        reverse = session.sql(f"""
        WITH auth_ids AS (
            SELECT DISTINCT TRIM(CONTENT_ID::STRING) AS AUTH_CONTENT_ID
            FROM {AUTH_TABLE}
            WHERE CONTENT_ID IS NOT NULL
        ),
        latest_controls AS (
            SELECT *
            FROM {CONTROL_TABLE}
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY TRIM(CONTENT_ID::STRING)
                ORDER BY ETL_LOAD_TS DESC NULLS LAST, LOAD_TIMESTAMP DESC NULLS LAST
            ) = 1
        ),
        exploded AS (
            SELECT DISTINCT
                TRIM(c.CONTENT_ID::STRING) AS CONTROL_CONTENT_ID,
                TRIM(f.VALUE:ContentId::STRING) AS REFERENCED_CONTENT_ID
            FROM latest_controls c,
                 LATERAL FLATTEN(INPUT => GET(c.CURATED_JSON, '{field}')) f
            WHERE f.VALUE:ContentId IS NOT NULL

            UNION

            SELECT DISTINCT
                TRIM(c.CONTENT_ID::STRING) AS CONTROL_CONTENT_ID,
                TRIM(GET(GET(c.CURATED_JSON, '{field}'), 'ContentId')::STRING) AS REFERENCED_CONTENT_ID
            FROM latest_controls c
            WHERE TYPEOF(GET(c.CURATED_JSON, '{field}')) = 'OBJECT'
              AND GET(GET(c.CURATED_JSON, '{field}'), 'ContentId') IS NOT NULL
        )
        SELECT
            COUNT(DISTINCT e.CONTROL_CONTENT_ID) AS CONTROLS_WITH_REFERENCE,
            COUNT(DISTINCT e.REFERENCED_CONTENT_ID) AS DISTINCT_REFERENCED_IDS,
            COUNT(DISTINCT IFF(a.AUTH_CONTENT_ID IS NOT NULL, e.CONTROL_CONTENT_ID, NULL)) AS CONTROLS_LINKED_TO_AUTH_PACKAGE,
            COUNT(DISTINCT IFF(a.AUTH_CONTENT_ID IS NOT NULL, e.REFERENCED_CONTENT_ID, NULL)) AS MATCHED_AUTH_PACKAGE_IDS
        FROM exploded e
        LEFT JOIN auth_ids a
          ON e.REFERENCED_CONTENT_ID = a.AUTH_CONTENT_ID
        """).collect()[0]

        result = {
            "field": field,
            "field_type_id": field_row["FIELD_TYPE_ID"],
            "shapes": shapes,
            "controls_with_reference": int(reverse["CONTROLS_WITH_REFERENCE"] or 0),
            "distinct_referenced_ids": int(reverse["DISTINCT_REFERENCED_IDS"] or 0),
            "controls_linked_to_auth_package": int(reverse["CONTROLS_LINKED_TO_AUTH_PACKAGE"] or 0),
            "matched_auth_package_ids": int(reverse["MATCHED_AUTH_PACKAGE_IDS"] or 0),
        }
        runtime_results.append(result)

        print()
        print("LEVEL355_RUNTIME_RELATIONSHIP =", result)

    strong = [
        r for r in runtime_results
        if r["controls_linked_to_auth_package"] > 0
    ]

    print()
    print("LEVEL355_REVERSE_LINK_CANDIDATES =", len(strong))
    for item in strong:
        print(
            "REVERSE_LINK_CANDIDATE",
            "| FIELD =", item["field"],
            "| CONTROLS_LINKED =", item["controls_linked_to_auth_package"],
            "| AUTH_PACKAGES_MATCHED =", item["matched_auth_package_ids"],
        )

    if len(strong) == 1:
        print("RESULT: ALLOCATED_CONTROLS_RECIPROCAL_LEVEL355_LINK_IDENTIFIED")
    elif len(strong) > 1:
        print("RESULT: MULTIPLE_LEVEL355_RECIPROCAL_LINKS_NEED_SELECTION")
    elif level355_fields:
        print("RESULT: LEVEL355_RECIPROCAL_METADATA_FOUND_BUT_RUNTIME_LINK_NOT_POPULATED")
    else:
        print("RESULT: ALLOCATED_CONTROLS_HAS_NO_LEVEL355_RECIPROCAL_FIELD")
