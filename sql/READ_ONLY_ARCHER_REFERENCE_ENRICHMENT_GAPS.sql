-- OSCAL / Archer remaining reference-enrichment gaps
-- Date: 2026-09-29
-- Baseline reviewed: simplify-metadata-boundary at be45c1832792a56cabd85de161d04848dcc6793c
-- READ ONLY: two SELECT statements. No UPDATE, DDL, temp tables, or pipeline writes.
--
-- Why this exists:
--   Full-source coverage found 546 UserList member occurrences that do not match
--   ARCHER_META_USER, while all visible shape/blocking checks were clean.
--   GroupList is also heavily populated, but the authoritative group lookup table
--   and join columns have not yet been established.
--
-- Query A asks whether the unmatched user IDs are present in ARCHER_META_USER_STG.
-- STG is diagnostic evidence only; finding an ID there does NOT make STG the
-- approved production lookup. The query returns counts only, never user IDs/EEIDs.
--
-- Query B discovers accessible group-related metadata candidates in ES_ESC_GRC.
-- A returned table/column name is only a candidate; do not use it for enrichment
-- until the owner/SME confirms the authoritative group-ID -> group-name contract.

-- A. Diagnose the 546 currently unmatched UserList occurrences.
WITH fields AS (
    SELECT
        f.KEY::VARCHAR AS SOURCE_FIELD_NAME,
        f.VALUE AS FIELD_PAYLOAD
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r,
         LATERAL FLATTEN(INPUT => AS_OBJECT(r.CURATED_JSON)) f
    WHERE TYPEOF(r.CURATED_JSON) = 'OBJECT'
      AND COALESCE(IS_ARRAY(f.VALUE:"UserList"), FALSE)
),
user_members AS (
    SELECT
        f.SOURCE_FIELD_NAME,
        CASE
            WHEN TYPEOF(u.VALUE:"Id") IN ('INTEGER', 'DECIMAL', 'VARCHAR')
             AND REGEXP_LIKE(u.VALUE:"Id"::VARCHAR, '^[0-9]+$')
                THEN TRY_TO_NUMBER(u.VALUE:"Id"::VARCHAR, 38, 0)
        END AS ARCHER_USER_ID
    FROM fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_PAYLOAD:"UserList")) u
),
unmatched AS (
    SELECT
        m.SOURCE_FIELD_NAME,
        m.ARCHER_USER_ID
    FROM user_members m
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER u
      ON u.ARCHER_USER_ID = m.ARCHER_USER_ID
    WHERE m.ARCHER_USER_ID IS NOT NULL
      AND u.ARCHER_USER_ID IS NULL
),
stg AS (
    SELECT
        ARCHER_USER_ID,
        COUNT(*) AS STG_MATCH_COUNT,
        COUNT_IF(NULLIF(TRIM(EEID), '') IS NOT NULL) AS STG_NONBLANK_EEID_ROWS
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER_STG
    GROUP BY ARCHER_USER_ID
),
by_field AS (
    SELECT
        u.SOURCE_FIELD_NAME,
        COUNT(*) AS UNMATCHED_OCCURRENCES,
        COUNT(DISTINCT u.ARCHER_USER_ID) AS DISTINCT_UNMATCHED_IDS,
        COUNT_IF(s.ARCHER_USER_ID IS NOT NULL) AS OCCURRENCES_FOUND_IN_STG,
        COUNT(DISTINCT IFF(s.ARCHER_USER_ID IS NOT NULL, u.ARCHER_USER_ID, NULL))
            AS DISTINCT_IDS_FOUND_IN_STG,
        COUNT(DISTINCT IFF(s.STG_NONBLANK_EEID_ROWS > 0, u.ARCHER_USER_ID, NULL))
            AS DISTINCT_IDS_WITH_STG_EEID,
        COUNT(DISTINCT IFF(s.ARCHER_USER_ID IS NULL, u.ARCHER_USER_ID, NULL))
            AS DISTINCT_IDS_NOT_IN_STG,
        COUNT(DISTINCT IFF(s.STG_MATCH_COUNT > 1, u.ARCHER_USER_ID, NULL))
            AS DISTINCT_IDS_DUPLICATED_IN_STG
    FROM unmatched u
    LEFT JOIN stg s
      ON s.ARCHER_USER_ID = u.ARCHER_USER_ID
    GROUP BY u.SOURCE_FIELD_NAME
),
all_rows AS (
    SELECT
        '__ALL__' AS SOURCE_FIELD_NAME,
        COUNT(*) AS UNMATCHED_OCCURRENCES,
        COUNT(DISTINCT u.ARCHER_USER_ID) AS DISTINCT_UNMATCHED_IDS,
        COUNT_IF(s.ARCHER_USER_ID IS NOT NULL) AS OCCURRENCES_FOUND_IN_STG,
        COUNT(DISTINCT IFF(s.ARCHER_USER_ID IS NOT NULL, u.ARCHER_USER_ID, NULL))
            AS DISTINCT_IDS_FOUND_IN_STG,
        COUNT(DISTINCT IFF(s.STG_NONBLANK_EEID_ROWS > 0, u.ARCHER_USER_ID, NULL))
            AS DISTINCT_IDS_WITH_STG_EEID,
        COUNT(DISTINCT IFF(s.ARCHER_USER_ID IS NULL, u.ARCHER_USER_ID, NULL))
            AS DISTINCT_IDS_NOT_IN_STG,
        COUNT(DISTINCT IFF(s.STG_MATCH_COUNT > 1, u.ARCHER_USER_ID, NULL))
            AS DISTINCT_IDS_DUPLICATED_IN_STG
    FROM unmatched u
    LEFT JOIN stg s
      ON s.ARCHER_USER_ID = u.ARCHER_USER_ID
)
SELECT 'ALL' AS ROW_SCOPE, * FROM all_rows
UNION ALL
SELECT 'FIELD' AS ROW_SCOPE, * FROM by_field
ORDER BY ROW_SCOPE, SOURCE_FIELD_NAME;

-- B. Discover accessible group-related lookup candidates.
SELECT
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND (
       TABLE_NAME ILIKE '%GROUP%'
    OR COLUMN_NAME ILIKE '%GROUP_ID%'
    OR COLUMN_NAME ILIKE '%GROUP_NAME%'
    OR COLUMN_NAME ILIKE 'GROUP%'
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;
