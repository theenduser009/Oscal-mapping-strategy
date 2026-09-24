# RUN NOW — Source One RISK_ASSESSMENT_REPORT attachment resolution discovery
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Known evidence:
# - RISK_ASSESSMENT_REPORT is an Archer attachment field (FIELD_TYPE_ID 11)
# - prior live review found 316 populated Source One rows / 742 attachment IDs
# - multi-valued rows exist
# - mapping stays DEFERRED unless current RAW data exposes a stable identifier or href contract
#
# Purpose:
# 1) reconfirm the current attachment shape/counts;
# 2) discover current Archer *_RAW tables whose names suggest document/file/attachment/report repositories;
# 3) search those candidate CURATED_JSON payloads recursively for the attachment IDs;
# 4) report only aggregate match counts and candidate JSON paths/keys.
#
# Privacy:
# - attachment IDs are used internally but never printed
# - URLs/file names/record values are not printed
# - output is table names, schema names, counts and JSON paths only

from collections import Counter

SOURCE_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
FIELD = "RISK_ASSESSMENT_REPORT"
SOURCE_LEVEL_ID = 353
SOURCE_MODULE_ID = 547

def py(v):
    if hasattr(v, "as_dict"):
        return v.as_dict(recursive=True)
    if hasattr(v, "as_list"):
        return v.as_list()
    return v

# ------------------------------------------------------------------
# 1) Current Source One attachment profile
# ------------------------------------------------------------------
source_rows = session.sql(f"""
SELECT CONTENT_ID, CURATED_JSON:{FIELD} AS FIELD_VALUE
FROM {SOURCE_TABLE}
""").collect()

shape_counts = Counter()
populated_rows = 0
total_items = 0
distinct_ids = set()
array_lengths = Counter()

for row in source_rows:
    value = py(row["FIELD_VALUE"])
    if value is None:
        shape_counts["NULL"] += 1
        continue

    if isinstance(value, list):
        shape_counts["ARRAY"] += 1
        array_lengths[len(value)] += 1
        if value:
            populated_rows += 1
        total_items += len(value)
        for item in value:
            item = py(item)
            if item not in (None, ""):
                distinct_ids.add(str(item).strip())
    else:
        shape_counts[type(value).__name__.upper()] += 1
        if value not in ("", {}, []):
            populated_rows += 1
            total_items += 1
            distinct_ids.add(str(value).strip())

print("SOURCE_ONE_RISK_ASSESSMENT_REPORT_ATTACHMENT_DISCOVERY")
print("SOURCE_RECORDS =", len(source_rows))
print("SHAPES =", dict(sorted(shape_counts.items())))
print("POPULATED_ROWS =", populated_rows)
print("TOTAL_ATTACHMENT_ITEMS =", total_items)
print("DISTINCT_ATTACHMENT_IDS =", len(distinct_ids))
if array_lengths:
    print("ARRAY_LENGTH_MIN_MAX =", min(array_lengths), max(array_lengths))
    if len(array_lengths) <= 12:
        print("ARRAY_LENGTH_COUNTS =", dict(sorted(array_lengths.items())))

# Reconfirm authoritative Source One Archer metadata.
meta = session.sql(f"""
SELECT FIELD_ID, SQL_FIELD_NAME, FIELD_TYPE_ID, LEVEL_ID, MODULE_ID, SELECT_ID
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(TRIM(SQL_FIELD_NAME)) = '{FIELD}'
  AND LEVEL_ID = {SOURCE_LEVEL_ID}
  AND MODULE_ID = {SOURCE_MODULE_ID}
ORDER BY FIELD_ID
""").collect()

print()
print("SOURCE_ONE_ATTACHMENT_METADATA")
for row in meta:
    print(row.as_dict())

# ------------------------------------------------------------------
# 2) Discover current RAW candidates by business-relevant table names.
# ------------------------------------------------------------------
candidate_rows = session.sql("""
SELECT TABLE_NAME
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND STARTSWITH(UPPER(TABLE_NAME), 'ARCHER_')
  AND ENDSWITH(UPPER(TABLE_NAME), '_RAW')
  AND (
       UPPER(TABLE_NAME) LIKE '%DOCUMENT%'
    OR UPPER(TABLE_NAME) LIKE '%ATTACH%'
    OR UPPER(TABLE_NAME) LIKE '%FILE%'
    OR UPPER(TABLE_NAME) LIKE '%REPOSIT%'
    OR UPPER(TABLE_NAME) LIKE '%EVIDENCE%'
    OR UPPER(TABLE_NAME) LIKE '%REPORT%'
  )
ORDER BY TABLE_NAME
""").collect()

candidate_tables = [row["TABLE_NAME"] for row in candidate_rows]
print()
print("CURRENT_ATTACHMENT_REPOSITORY_CANDIDATES =", len(candidate_tables))
for table in candidate_tables:
    print("TABLE =", table)

# Get schema once for all candidates.
columns_by_table = {}
if candidate_tables:
    names = ", ".join("'" + x.replace("'", "''") + "'" for x in candidate_tables)
    col_rows = session.sql(f"""
    SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE
    FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
      AND TABLE_NAME IN ({names})
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """).collect()
    for row in col_rows:
        columns_by_table.setdefault(row["TABLE_NAME"], []).append(
            (row["COLUMN_NAME"], row["DATA_TYPE"])
        )

print()
print("CANDIDATE_SCHEMAS")
for table in candidate_tables:
    print(table, "|", columns_by_table.get(table, []))

# ------------------------------------------------------------------
# 3) Recursively match attachment IDs inside candidate CURATED_JSON payloads.
# ------------------------------------------------------------------
if distinct_ids:
    ids_df = session.create_dataframe(
        [(x,) for x in sorted(distinct_ids)],
        schema=["ATTACHMENT_ID"]
    )
    ids_df.create_or_replace_temp_view("TMP_OSCAL_ATTACHMENT_IDS")
else:
    ids_df = None

matches = []
for table in candidate_tables:
    cols = {str(name).upper(): dtype for name, dtype in columns_by_table.get(table, [])}
    if "CURATED_JSON" not in cols or not distinct_ids:
        continue

    full = "RTX_RAW_DEV.ES_ESC_GRC." + table
    result = session.sql(f"""
    WITH flattened AS (
        SELECT
            f.PATH::STRING AS JSON_PATH,
            f.KEY::STRING AS JSON_KEY,
            TRIM(f.VALUE::STRING) AS SCALAR_VALUE
        FROM {full} t,
             LATERAL FLATTEN(INPUT => t.CURATED_JSON, RECURSIVE => TRUE) f
        WHERE TYPEOF(f.VALUE) IN ('INTEGER','DECIMAL','DOUBLE','VARCHAR')
    ),
    matched AS (
        SELECT
            fl.JSON_PATH,
            fl.JSON_KEY,
            COUNT(DISTINCT ids.ATTACHMENT_ID) AS MATCHED_ATTACHMENT_IDS
        FROM flattened fl
        JOIN TMP_OSCAL_ATTACHMENT_IDS ids
          ON fl.SCALAR_VALUE = ids.ATTACHMENT_ID
        GROUP BY fl.JSON_PATH, fl.JSON_KEY
    )
    SELECT JSON_PATH, JSON_KEY, MATCHED_ATTACHMENT_IDS
    FROM matched
    ORDER BY MATCHED_ATTACHMENT_IDS DESC, JSON_PATH
    """).collect()

    total_matched = sum(int(r["MATCHED_ATTACHMENT_IDS"] or 0) for r in result)
    max_path_match = max([int(r["MATCHED_ATTACHMENT_IDS"] or 0) for r in result], default=0)

    # Because one attachment ID could occur at multiple paths, total_matched may double-count.
    distinct_match = session.sql(f"""
    WITH flattened AS (
        SELECT TRIM(f.VALUE::STRING) AS SCALAR_VALUE
        FROM {full} t,
             LATERAL FLATTEN(INPUT => t.CURATED_JSON, RECURSIVE => TRUE) f
        WHERE TYPEOF(f.VALUE) IN ('INTEGER','DECIMAL','DOUBLE','VARCHAR')
    )
    SELECT COUNT(DISTINCT ids.ATTACHMENT_ID) AS MATCHED
    FROM flattened fl
    JOIN TMP_OSCAL_ATTACHMENT_IDS ids
      ON fl.SCALAR_VALUE = ids.ATTACHMENT_ID
    """).collect()[0]["MATCHED"]

    if int(distinct_match or 0) > 0:
        matches.append((table, int(distinct_match or 0), result))
        print()
        print("MATCHING_TABLE =", table)
        print("MATCHED_DISTINCT_ATTACHMENT_IDS =", int(distinct_match or 0))
        print("MISSING_ATTACHMENT_IDS =", len(distinct_ids) - int(distinct_match or 0))
        print("MATCHING_JSON_PATHS =")
        for r in result[:20]:
            print(
                " ", r["MATCHED_ATTACHMENT_IDS"],
                "| PATH =", r["JSON_PATH"],
                "| KEY =", r["JSON_KEY"],
            )

# ------------------------------------------------------------------
# 4) For matching tables, inventory potential href/identifier metadata paths
#    on only the rows that contain one of our attachment IDs.
# ------------------------------------------------------------------
for table, matched_count, _ in matches:
    full = "RTX_RAW_DEV.ES_ESC_GRC." + table
    paths = session.sql(f"""
    WITH matched_rows AS (
        SELECT DISTINCT t.CURATED_JSON
        FROM {full} t,
             LATERAL FLATTEN(INPUT => t.CURATED_JSON, RECURSIVE => TRUE) f
        JOIN TMP_OSCAL_ATTACHMENT_IDS ids
          ON TRIM(f.VALUE::STRING) = ids.ATTACHMENT_ID
    ),
    candidate_meta AS (
        SELECT
            f.PATH::STRING AS JSON_PATH,
            f.KEY::STRING AS JSON_KEY,
            COUNT(*) AS POPULATED_VALUES
        FROM matched_rows r,
             LATERAL FLATTEN(INPUT => r.CURATED_JSON, RECURSIVE => TRUE) f
        WHERE f.VALUE IS NOT NULL
          AND (
               REGEXP_LIKE(UPPER(COALESCE(f.KEY::STRING,'')), '.*(URL|URI|HREF|LINK|FILE|NAME|TITLE|IDENTIFIER|ID).*')
            OR REGEXP_LIKE(UPPER(COALESCE(f.PATH::STRING,'')), '.*(URL|URI|HREF|LINK|FILE|NAME|TITLE|IDENTIFIER|ID).*')
          )
        GROUP BY f.PATH::STRING, f.KEY::STRING
    )
    SELECT JSON_PATH, JSON_KEY, POPULATED_VALUES
    FROM candidate_meta
    ORDER BY POPULATED_VALUES DESC, JSON_PATH
    LIMIT 50
    """).collect()

    print()
    print("POTENTIAL_RESOURCE_METADATA_PATHS =", table)
    for r in paths:
        print(
            " ", r["POPULATED_VALUES"],
            "| PATH =", r["JSON_PATH"],
            "| KEY =", r["JSON_KEY"],
        )

print()
print("MATCHING_TABLE_COUNT =", len(matches))
print("MATCHING_TABLE_SUMMARY =", [(t, n) for t, n, _ in matches])

if not matches:
    print("RESULT: ATTACHMENT_IDS_NOT_RESOLVED_IN_CURRENT_CANDIDATE_RAW_TABLES")
elif any(n == len(distinct_ids) for _, n, _ in matches):
    print("RESULT: ATTACHMENT_ID_SOURCE_IDENTIFIED_REVIEW_RESOURCE_PATHS")
else:
    print("RESULT: ATTACHMENT_ID_SOURCE_PARTIALLY_IDENTIFIED_REVIEW_COVERAGE")
