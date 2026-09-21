# RUN NOW — Search current RAW inventory for the Level-355 Allocated Controls source
# Date: 2026-09-21
# READ ONLY. No DIM/FACT/registry/mapping DML.
#
# Prior result:
# - LEVEL_ID 355 = CONTROL
# - MODULE_ID 549 = ALLOCATED CONTROLS
# - 100 private Level-355 ContentIds matched none of 45 current *_RAW tables
#   that expose BOTH CONTENT_ID and CURATED_JSON.
#
# Important: that does NOT yet prove the current RAW source is absent, because
# some newer RAW tables may expose RAW_DATA (or another VARIANT payload) instead.
#
# Purpose:
# Find current *_RAW tables whose names suggest CONTROL / ALLOCATED content,
# then show only their schema. No source values or IDs are printed.

candidate_tables = session.sql("""
SELECT TABLE_NAME
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND ENDSWITH(UPPER(TABLE_NAME), '_RAW')
  AND STARTSWITH(UPPER(TABLE_NAME), 'ARCHER_CONTENT')
  AND (
       UPPER(TABLE_NAME) LIKE '%CONTROL%'
    OR UPPER(TABLE_NAME) LIKE '%ALLOCAT%'
  )
ORDER BY TABLE_NAME
""").collect()

names = [row["TABLE_NAME"] for row in candidate_tables]

print("LEVEL_355_TARGETED_RAW_TABLE_SEARCH")
print("CANDIDATE_TABLE_COUNT =", len(names))
for name in names:
    print("TABLE =", name)

if names:
    quoted = ", ".join("'" + name.replace("'", "''") + "'" for name in names)
    columns = session.sql(f"""
SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME IN ({quoted})
ORDER BY TABLE_NAME, ORDINAL_POSITION
""").collect()

    print()
    print("CANDIDATE_TABLE_COLUMNS")
    for row in columns:
        print(
            row["TABLE_NAME"],
            "|", row["ORDINAL_POSITION"],
            "|", row["COLUMN_NAME"],
            "|", row["DATA_TYPE"],
        )

    payload_columns = {}
    for row in columns:
        table = row["TABLE_NAME"]
        col = str(row["COLUMN_NAME"]).upper()
        if col in {"RAW_DATA", "CURATED_JSON", "CONTENT_ID"}:
            payload_columns.setdefault(table, []).append(col)

    print()
    print("LIKELY_PAYLOAD_COLUMNS")
    for table in names:
        print(table, "|", sorted(payload_columns.get(table, [])))
else:
    print("RESULT: NO_CONTROL_OR_ALLOCATED_CURRENT_RAW_TABLE_BY_NAME")

print("RESULT: LEVEL_355_TARGETED_RAW_INVENTORY_COMPLETE")
