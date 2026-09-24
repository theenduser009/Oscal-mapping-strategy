# RUN NOW — Find Archer relationship metadata row for ALLOCATED_CONTROLS field 23429
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Prior result:
#   Source One ALLOCATED_CONTROLS = FIELD_ID 23429
#   FIELD_TYPE_ID = 9 (Cross-Reference)
#   LEVEL_ID = 353
#   MODULE_ID = 547
#   No ARCHER_META* table exposed literal CR_FIELD_ID + RR_FIELD_ID columns.
#
# This helper does one narrow schema search:
# find any current ES_ESC_GRC table/column whose name is field-id-like and
# contains the exact source field ID 23429. Then print only metadata-like columns
# from those matching rows so we can identify the reciprocal field/table.
#
# No business/source record values are printed.

SOURCE_FIELD_ID = "23429"
SCHEMA = "ES_ESC_GRC"

def n(text):
    return "".join(ch for ch in str(text).upper() if ch.isalnum())

print("ALLOCATED_CONTROLS_RELATIONSHIP_METADATA_DISCOVERY")
print("SOURCE_FIELD_ID =", SOURCE_FIELD_ID)

# ------------------------------------------------------------------
# 1) Candidate metadata/config tables and field-id-like columns.
# ------------------------------------------------------------------
cols = session.sql(f"""
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    ORDINAL_POSITION
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = '{SCHEMA}'
  AND (
       UPPER(TABLE_NAME) LIKE 'ARCHER_META%'
    OR UPPER(TABLE_NAME) LIKE '%RELATION%'
    OR UPPER(TABLE_NAME) LIKE '%REFERENCE%'
    OR UPPER(TABLE_NAME) LIKE '%XREF%'
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION
""").collect()

by_table = {}
for row in cols:
    by_table.setdefault(row["TABLE_NAME"], []).append(
        (row["COLUMN_NAME"], row["DATA_TYPE"], row["ORDINAL_POSITION"])
    )

candidate_pairs = []
for table, table_cols in by_table.items():
    for col, dtype, ordinal in table_cols:
        token = n(col)
        if "FIELDID" in token or token in {"FIELD", "SOURCEFIELD", "TARGETFIELD"}:
            candidate_pairs.append((table, col, dtype))

print("CANDIDATE_TABLES =", len(by_table))
print("FIELD_ID_LIKE_COLUMNS =", len(candidate_pairs))

# ------------------------------------------------------------------
# 2) Search the exact field ID in those metadata-like columns.
# ------------------------------------------------------------------
matches = []

for table, column, dtype in candidate_pairs:
    full = f"RTX_RAW_DEV.{SCHEMA}.{table}"
    try:
        count = session.sql(f"""
        SELECT COUNT(*) AS N
        FROM {full}
        WHERE TRIM({column}::STRING) = '{SOURCE_FIELD_ID}'
        """).collect()[0]["N"]
    except Exception:
        continue

    if int(count or 0) > 0:
        matches.append((table, column, int(count)))

print()
print("MATCHING_TABLE_COLUMN_COUNT =", len(matches))
for table, column, count in matches:
    print("MATCH =", table, "| COLUMN =", column, "| ROWS =", count)

# ------------------------------------------------------------------
# 3) For each matching table, print only metadata-like values from matching rows.
# ------------------------------------------------------------------
for table, match_col, count in matches:
    table_cols = by_table.get(table, [])
    safe_cols = []
    for col, dtype, ordinal in table_cols:
        token = n(col)
        if (
            "FIELD" in token
            or "LEVEL" in token
            or "MODULE" in token
            or "RELATION" in token
            or "REFERENCE" in token
            or "XREF" in token
            or token.endswith("ID")
            or token in {"ID", "TYPE", "NAME", "DESCRIPTION"}
        ):
            safe_cols.append(col)

    # Always include the matched column.
    if match_col not in safe_cols:
        safe_cols.append(match_col)

    select_list = ", ".join(safe_cols)
    full = f"RTX_RAW_DEV.{SCHEMA}.{table}"

    print()
    print("MATCHING_METADATA_TABLE =", table)
    print("MATCHED_ON_COLUMN =", match_col)
    print("SAFE_COLUMNS =", safe_cols)

    rows = session.sql(f"""
    SELECT {select_list}
    FROM {full}
    WHERE TRIM({match_col}::STRING) = '{SOURCE_FIELD_ID}'
    LIMIT 20
    """).collect()

    for row in rows:
        print("METADATA_ROW =", row.as_dict())

# ------------------------------------------------------------------
# 4) If nothing matched under metadata-ish table names, widen only by exact ID:
#    search all ES_ESC_GRC tables for columns explicitly containing FIELD + ID.
# ------------------------------------------------------------------
if not matches:
    all_field_cols = session.sql(f"""
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
    FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '{SCHEMA}'
      AND UPPER(COLUMN_NAME) LIKE '%FIELD%'
      AND UPPER(COLUMN_NAME) LIKE '%ID%'
    ORDER BY TABLE_NAME, COLUMN_NAME
    """).collect()

    fallback = []
    for row in all_field_cols:
        table = row["TABLE_NAME"]
        column = row["COLUMN_NAME"]
        full = f"RTX_RAW_DEV.{SCHEMA}.{table}"
        try:
            count = session.sql(f"""
            SELECT COUNT(*) AS N
            FROM {full}
            WHERE TRIM({column}::STRING) = '{SOURCE_FIELD_ID}'
            """).collect()[0]["N"]
        except Exception:
            continue

        if int(count or 0) > 0:
            fallback.append((table, column, int(count)))

    print()
    print("FALLBACK_EXACT_FIELD_ID_MATCHES =", len(fallback))
    for table, column, count in fallback:
        print("FALLBACK_MATCH =", table, "| COLUMN =", column, "| ROWS =", count)

    if fallback:
        print("RESULT: RELATIONSHIP_METADATA_LOCATION_IDENTIFIED")
    else:
        print("RESULT: FIELD_23429_NOT_FOUND_IN_RELATIONSHIP_METADATA_TABLES")
else:
    print()
    print("RESULT: RELATIONSHIP_METADATA_LOCATION_IDENTIFIED")
