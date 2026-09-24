# RUN NOW — Find ALLOCATED_CONTROLS relationship metadata by FIELD_GUID
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Prior exact FIELD_ID search found only:
#   ARCHER_META_FIELD.FIELD_ID = 23429
#   ARCHER_META_FIELD_STG.FIELD_ID = 23429
#
# The same metadata row exposes:
#   FIELD_GUID = E84D64F5-668F-47B5-AC50-89B6F6E67692
#
# Relationship/config metadata may store GUIDs instead of FIELD_ID values.
# This helper searches only GUID-like columns for that exact FIELD_GUID.
# It prints metadata-like columns only.

FIELD_GUID = "E84D64F5-668F-47B5-AC50-89B6F6E67692"
SCHEMA = "ES_ESC_GRC"

def norm(text):
    return "".join(ch for ch in str(text).upper() if ch.isalnum())

print("ALLOCATED_CONTROLS_RELATIONSHIP_GUID_DISCOVERY")
print("FIELD_GUID =", FIELD_GUID)

# ------------------------------------------------------------------
# 1) Find GUID-like columns in current schema.
# ------------------------------------------------------------------
guid_columns = session.sql(f"""
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, ORDINAL_POSITION
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = '{SCHEMA}'
  AND UPPER(COLUMN_NAME) LIKE '%GUID%'
ORDER BY TABLE_NAME, ORDINAL_POSITION
""").collect()

print("GUID_LIKE_COLUMNS =", len(guid_columns))

matches = []
for row in guid_columns:
    table = row["TABLE_NAME"]
    column = row["COLUMN_NAME"]
    full = f"RTX_RAW_DEV.{SCHEMA}.{table}"
    try:
        n = session.sql(f"""
        SELECT COUNT(*) AS N
        FROM {full}
        WHERE UPPER(TRIM({column}::STRING)) = '{FIELD_GUID}'
        """).collect()[0]["N"]
    except Exception:
        continue
    if int(n or 0) > 0:
        matches.append((table, column, int(n)))

print("MATCHING_GUID_TABLE_COLUMNS =", len(matches))
for table, column, count in matches:
    print("GUID_MATCH =", table, "| COLUMN =", column, "| ROWS =", count)

# ------------------------------------------------------------------
# 2) Print metadata-like columns from matching rows.
# ------------------------------------------------------------------
all_columns = session.sql(f"""
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, ORDINAL_POSITION
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = '{SCHEMA}'
ORDER BY TABLE_NAME, ORDINAL_POSITION
""").collect()

by_table = {}
for row in all_columns:
    by_table.setdefault(row["TABLE_NAME"], []).append(
        (row["COLUMN_NAME"], row["DATA_TYPE"], row["ORDINAL_POSITION"])
    )

for table, match_col, count in matches:
    safe_cols = []
    for col, dtype, ordinal in by_table.get(table, []):
        token = norm(col)
        if (
            "FIELD" in token
            or "GUID" in token
            or "LEVEL" in token
            or "MODULE" in token
            or "RELATION" in token
            or "REFERENCE" in token
            or "XREF" in token
            or "SOURCE" in token
            or "TARGET" in token
            or token.endswith("ID")
            or token in {"ID", "TYPE", "NAME", "DESCRIPTION"}
        ):
            safe_cols.append(col)

    if match_col not in safe_cols:
        safe_cols.append(match_col)

    full = f"RTX_RAW_DEV.{SCHEMA}.{table}"
    select_list = ", ".join(safe_cols)

    print()
    print("MATCHING_GUID_TABLE =", table)
    print("MATCHED_ON_COLUMN =", match_col)
    print("SAFE_COLUMNS =", safe_cols)

    rows = session.sql(f"""
    SELECT {select_list}
    FROM {full}
    WHERE UPPER(TRIM({match_col}::STRING)) = '{FIELD_GUID}'
    LIMIT 20
    """).collect()

    for row in rows:
        print("GUID_METADATA_ROW =", row.as_dict())

# ------------------------------------------------------------------
# 3) If GUID only appears in the field tables, inspect metadata-like table
#    schemas for source/target/related/reference columns so we know the next
#    exact metadata object to query without another broad source search.
# ------------------------------------------------------------------
interesting = []
for table, cols in by_table.items():
    table_token = norm(table)
    if not (
        table_token.startswith("ARCHERMETA")
        or "RELATION" in table_token
        or "REFERENCE" in table_token
        or "XREF" in table_token
    ):
        continue

    names = [c for c, _, _ in cols]
    tokens = [norm(c) for c in names]
    if any(
        ("SOURCE" in t or "TARGET" in t or "RELAT" in t or "REFER" in t or "XREF" in t)
        and ("FIELD" in t or "GUID" in t or "ID" in t)
        for t in tokens
    ):
        interesting.append((table, names))

print()
print("RELATIONSHIP_SCHEMA_CANDIDATES =", len(interesting))
for table, names in interesting:
    print("SCHEMA_CANDIDATE =", table, "| COLUMNS =", names)

if len(matches) > 2:
    print("RESULT: FIELD_GUID_FOUND_OUTSIDE_BASE_FIELD_TABLES")
elif interesting:
    print("RESULT: RELATIONSHIP_SCHEMA_CANDIDATES_FOUND")
else:
    print("RESULT: RELATIONSHIP_METADATA_NOT_EXPOSED_IN_CURRENT_SCHEMA")
