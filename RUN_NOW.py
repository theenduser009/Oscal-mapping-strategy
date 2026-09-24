# RUN NOW — Resolve the actual Level-355 join key
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Known from the prior run:
# - ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW exists
# - 160,000 rows / 34,071 distinct top-level CONTENT_ID values
# - Authorization Package exposes 252,165 distinct Level-355 ContentId references
# - zero of those references matched top-level CONTROL_RAW.CONTENT_ID
#
# This check answers only one question:
#   Where, if anywhere, do those Authorization Package ContentId values occur
#   inside the current Level-355 RAW record?
#
# It uses a deterministic 100-reference sample and prints aggregate/path evidence
# only. It never prints the reference IDs themselves.

CONTROL_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW"
AUTH_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
SAMPLE_SIZE = 100

# ------------------------------------------------------------------
# 1) ID-shape comparison: reference IDs vs top-level control CONTENT_ID.
# ------------------------------------------------------------------
ref_stats = session.sql(f"""
WITH refs AS (
    SELECT DISTINCT TRIM(f.value:ContentId::STRING) AS REF_ID
    FROM {AUTH_TABLE} a,
         LATERAL FLATTEN(INPUT => a.CURATED_JSON:ALLOCATED_CONTROLS) f
    WHERE f.value:LevelId::STRING = '355'
      AND f.value:ContentId IS NOT NULL
)
SELECT
    COUNT(*) AS DISTINCT_REFS,
    MIN(LENGTH(REF_ID)) AS MIN_LEN,
    MAX(LENGTH(REF_ID)) AS MAX_LEN,
    COUNT_IF(TRY_TO_NUMBER(REF_ID) IS NOT NULL) AS NUMERIC_REFS
FROM refs
""").collect()[0]

control_stats = session.sql(f"""
SELECT
    COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) AS DISTINCT_IDS,
    MIN(LENGTH(TRIM(CONTENT_ID::STRING))) AS MIN_LEN,
    MAX(LENGTH(TRIM(CONTENT_ID::STRING))) AS MAX_LEN,
    COUNT(DISTINCT IFF(TRY_TO_NUMBER(TRIM(CONTENT_ID::STRING)) IS NOT NULL,
                       TRIM(CONTENT_ID::STRING), NULL)) AS NUMERIC_IDS
FROM {CONTROL_TABLE}
WHERE CONTENT_ID IS NOT NULL
""").collect()[0]

print("LEVEL355_JOIN_KEY_DIAGNOSTIC")
print("REFERENCE_ID_STATS =", ref_stats.as_dict())
print("TOP_LEVEL_CONTENT_ID_STATS =", control_stats.as_dict())

# Numeric-normalized join test rules out formatting differences like leading zeroes.
normalized = session.sql(f"""
WITH refs AS (
    SELECT DISTINCT TRY_TO_NUMBER(TRIM(f.value:ContentId::STRING)) AS REF_ID
    FROM {AUTH_TABLE} a,
         LATERAL FLATTEN(INPUT => a.CURATED_JSON:ALLOCATED_CONTROLS) f
    WHERE f.value:LevelId::STRING = '355'
      AND TRY_TO_NUMBER(TRIM(f.value:ContentId::STRING)) IS NOT NULL
),
controls AS (
    SELECT DISTINCT TRY_TO_NUMBER(TRIM(CONTENT_ID::STRING)) AS CONTROL_ID
    FROM {CONTROL_TABLE}
    WHERE TRY_TO_NUMBER(TRIM(CONTENT_ID::STRING)) IS NOT NULL
)
SELECT COUNT(*) AS NUMERIC_NORMALIZED_MATCHES
FROM refs r
JOIN controls c
  ON r.REF_ID = c.CONTROL_ID
""").collect()[0]

print("NUMERIC_NORMALIZED_TOP_LEVEL_MATCHES =", normalized["NUMERIC_NORMALIZED_MATCHES"])

# ------------------------------------------------------------------
# 2) Whole-table Level-355 field sanity, independent of the failed join.
#    This confirms whether the expected control fields are actually populated.
# ------------------------------------------------------------------
field_profile = session.sql(f"""
WITH latest AS (
    SELECT *
    FROM {CONTROL_TABLE}
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY TRIM(CONTENT_ID::STRING)
        ORDER BY ETL_LOAD_TS DESC NULLS LAST, LOAD_TIMESTAMP DESC NULLS LAST
    ) = 1
)
SELECT
    COUNT(*) AS CURRENT_CONTROL_RECORDS,
    COUNT_IF(CURATED_JSON:CONTROL_NUMBER IS NOT NULL) AS CONTROL_NUMBER_POPULATED,
    COUNT_IF(CURATED_JSON:CONTROL_NAME IS NOT NULL) AS CONTROL_NAME_POPULATED,
    COUNT_IF(CURATED_JSON:IMPLEMENTATION_DETAILS IS NOT NULL) AS IMPLEMENTATION_DETAILS_POPULATED,
    COUNT_IF(CURATED_JSON:OVERALL_IMPLEMENTATION_DETAILS IS NOT NULL) AS OVERALL_IMPLEMENTATION_DETAILS_POPULATED,
    COUNT_IF(CURATED_JSON:IMPLEMENTATION_STATUS IS NOT NULL) AS IMPLEMENTATION_STATUS_POPULATED,
    COUNT_IF(CURATED_JSON:CONTROL_PARAMETERS IS NOT NULL) AS CONTROL_PARAMETERS_POPULATED,
    COUNT_IF(CURATED_JSON:RESPONSIBLE_ROLE IS NOT NULL) AS RESPONSIBLE_ROLE_POPULATED,
    COUNT_IF(CURATED_JSON:AUTHORIZATION_PACKAGE IS NOT NULL) AS AUTHORIZATION_PACKAGE_POPULATED,
    COUNT_IF(CURATED_JSON:ALLOCATED_CONTROL_ID IS NOT NULL) AS ALLOCATED_CONTROL_ID_POPULATED,
    COUNT_IF(CURATED_JSON:TRACKING_ID IS NOT NULL) AS TRACKING_ID_POPULATED
FROM latest
""").collect()[0]

print("LEVEL355_CURRENT_FIELD_SANITY =", field_profile.as_dict())

# ------------------------------------------------------------------
# 3) Search a deterministic sample of 100 Level-355 reference IDs recursively
#    inside current/latest CURATED_JSON and RAW_DATA. Output paths only.
# ------------------------------------------------------------------
sample_rows = session.sql(f"""
SELECT DISTINCT TRIM(f.value:ContentId::STRING) AS REF_ID
FROM {AUTH_TABLE} a,
     LATERAL FLATTEN(INPUT => a.CURATED_JSON:ALLOCATED_CONTROLS) f
WHERE f.value:LevelId::STRING = '355'
  AND f.value:ContentId IS NOT NULL
ORDER BY REF_ID
LIMIT {SAMPLE_SIZE}
""").collect()

sample_ids = [str(r["REF_ID"]).strip() for r in sample_rows if r["REF_ID"] is not None]
if not sample_ids:
    raise ValueError("No Level-355 Authorization Package references found")

values_sql = ",\n        ".join(
    "('" + value.replace("'", "''") + "')"
    for value in sample_ids
)

def search_variant(column_name):
    rows = session.sql(f"""
    WITH sample_refs(REF_ID) AS (
        SELECT COLUMN1 FROM VALUES
        {values_sql}
    ),
    latest AS (
        SELECT *
        FROM {CONTROL_TABLE}
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY TRIM(CONTENT_ID::STRING)
            ORDER BY ETL_LOAD_TS DESC NULLS LAST, LOAD_TIMESTAMP DESC NULLS LAST
        ) = 1
    ),
    matches AS (
        SELECT
            f.PATH::STRING AS JSON_PATH,
            f.KEY::STRING AS JSON_KEY,
            COUNT(DISTINCT s.REF_ID) AS MATCHED_SAMPLE_IDS
        FROM latest c,
             LATERAL FLATTEN(INPUT => c.{column_name}, RECURSIVE => TRUE) f
        JOIN sample_refs s
          ON TRIM(f.VALUE::STRING) = s.REF_ID
        WHERE TYPEOF(f.VALUE) IN ('INTEGER','DECIMAL','DOUBLE','VARCHAR')
        GROUP BY f.PATH::STRING, f.KEY::STRING
    )
    SELECT JSON_PATH, JSON_KEY, MATCHED_SAMPLE_IDS
    FROM matches
    ORDER BY MATCHED_SAMPLE_IDS DESC, JSON_PATH
    LIMIT 30
    """).collect()

    distinct_match = session.sql(f"""
    WITH sample_refs(REF_ID) AS (
        SELECT COLUMN1 FROM VALUES
        {values_sql}
    ),
    latest AS (
        SELECT *
        FROM {CONTROL_TABLE}
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY TRIM(CONTENT_ID::STRING)
            ORDER BY ETL_LOAD_TS DESC NULLS LAST, LOAD_TIMESTAMP DESC NULLS LAST
        ) = 1
    ),
    flattened AS (
        SELECT TRIM(f.VALUE::STRING) AS SCALAR_VALUE
        FROM latest c,
             LATERAL FLATTEN(INPUT => c.{column_name}, RECURSIVE => TRUE) f
        WHERE TYPEOF(f.VALUE) IN ('INTEGER','DECIMAL','DOUBLE','VARCHAR')
    )
    SELECT COUNT(DISTINCT s.REF_ID) AS MATCHED
    FROM flattened f
    JOIN sample_refs s
      ON f.SCALAR_VALUE = s.REF_ID
    """).collect()[0]["MATCHED"]

    print()
    print(column_name, "MATCHED_SAMPLE_IDS =", int(distinct_match or 0))
    print(column_name, "MATCH_PATHS =")
    for r in rows:
        print(
            " ", r["MATCHED_SAMPLE_IDS"],
            "| PATH =", r["JSON_PATH"],
            "| KEY =", r["JSON_KEY"],
        )
    return int(distinct_match or 0), rows

curated_matches, curated_paths = search_variant("CURATED_JSON")
raw_matches, raw_paths = search_variant("RAW_DATA")

print()
print("SAMPLE_SIZE =", len(sample_ids))
print("CURATED_JSON_MATCHED_SAMPLE_IDS =", curated_matches)
print("RAW_DATA_MATCHED_SAMPLE_IDS =", raw_matches)

if curated_matches > 0:
    print("RESULT: LEVEL355_JOIN_KEY_FOUND_IN_CURATED_JSON_REVIEW_PATH")
elif raw_matches > 0:
    print("RESULT: LEVEL355_JOIN_KEY_FOUND_IN_RAW_DATA_REVIEW_PATH")
else:
    print("RESULT: LEVEL355_REFERENCE_IDS_ABSENT_FROM_CURRENT_CONTROL_RECORDS")
