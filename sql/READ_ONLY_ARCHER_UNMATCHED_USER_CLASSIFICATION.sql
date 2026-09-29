-- OSCAL / Archer unmatched UserList reference classification
-- Date: 2026-09-29
-- Baseline reviewed: simplify-metadata-boundary at 2ceef28a7e4cc99779a9bbedb13970d28487a579
-- READ ONLY: three SELECT statements. No UPDATE, DDL, temp tables, or pipeline writes.
--
-- Owner clarification: ARCHER_META_USER_STG is the same user source for this
-- purpose, so this diagnostic does NOT use STG as an independent fallback.
--
-- Purpose:
--   Explain the 546 UserList member occurrences that did not match
--   ARCHER_META_USER. Do not guess whether they are deleted users, workflow/service
--   identities, stale references, or another namespace. This query shows the
--   actual unmatched ID repetition pattern and the Archer field metadata.
--
-- Privacy:
--   Query 2 returns internal Archer IDs only; it does not return EEID or names.
--   Keep result grids private and do not commit them to GitHub.
--
WITH reference_fields AS (
    SELECT
        r.CONTENT_ID::VARCHAR AS SOURCE_RECORD_ID,
        f.KEY::VARCHAR AS SOURCE_FIELD_NAME,
        f.VALUE AS FIELD_PAYLOAD
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r,
         LATERAL FLATTEN(INPUT => AS_OBJECT(r.CURATED_JSON)) f
    WHERE TYPEOF(r.CURATED_JSON) = 'OBJECT'
      AND COALESCE(IS_ARRAY(f.VALUE:"UserList"), FALSE)
),
user_members AS (
    SELECT
        f.SOURCE_RECORD_ID,
        f.SOURCE_FIELD_NAME,
        u.INDEX AS MEMBER_INDEX,
        u.VALUE AS MEMBER_PAYLOAD,
        CASE
            WHEN TYPEOF(u.VALUE:"Id") IN ('INTEGER', 'DECIMAL', 'VARCHAR')
             AND REGEXP_LIKE(u.VALUE:"Id"::VARCHAR, '^[0-9]+$')
                THEN TRY_TO_NUMBER(u.VALUE:"Id"::VARCHAR, 38, 0)
        END AS ARCHER_USER_ID,
        u.VALUE:"HasRead"::BOOLEAN AS HAS_READ,
        u.VALUE:"HasUpdate"::BOOLEAN AS HAS_UPDATE,
        u.VALUE:"HasDelete"::BOOLEAN AS HAS_DELETE
    FROM reference_fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_PAYLOAD:"UserList")) u
),
unmatched AS (
    SELECT m.*
    FROM user_members m
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER u
      ON u.ARCHER_USER_ID = m.ARCHER_USER_ID
    WHERE m.ARCHER_USER_ID IS NOT NULL
      AND u.ARCHER_USER_ID IS NULL
)
-- 1. Which source fields contain the unresolved references, and how repetitive are they?
SELECT
    SOURCE_FIELD_NAME,
    COUNT(*) AS UNMATCHED_OCCURRENCES,
    COUNT(DISTINCT ARCHER_USER_ID) AS DISTINCT_UNMATCHED_IDS,
    COUNT(DISTINCT SOURCE_RECORD_ID) AS DISTINCT_SOURCE_RECORDS,
    MIN(ARCHER_USER_ID) AS MIN_UNMATCHED_ID,
    MAX(ARCHER_USER_ID) AS MAX_UNMATCHED_ID,
    COUNT(DISTINCT
        COALESCE(HAS_READ::VARCHAR, 'NULL') || '|' ||
        COALESCE(HAS_UPDATE::VARCHAR, 'NULL') || '|' ||
        COALESCE(HAS_DELETE::VARCHAR, 'NULL')
    ) AS DISTINCT_PERMISSION_PATTERNS
FROM unmatched
GROUP BY SOURCE_FIELD_NAME
ORDER BY UNMATCHED_OCCURRENCES DESC, SOURCE_FIELD_NAME;

-- 2. Are the 546 occurrences many missing people, or a small set of repeated IDs?
WITH reference_fields AS (
    SELECT
        r.CONTENT_ID::VARCHAR AS SOURCE_RECORD_ID,
        f.KEY::VARCHAR AS SOURCE_FIELD_NAME,
        f.VALUE AS FIELD_PAYLOAD
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r,
         LATERAL FLATTEN(INPUT => AS_OBJECT(r.CURATED_JSON)) f
    WHERE TYPEOF(r.CURATED_JSON) = 'OBJECT'
      AND COALESCE(IS_ARRAY(f.VALUE:"UserList"), FALSE)
),
user_members AS (
    SELECT
        f.SOURCE_RECORD_ID,
        f.SOURCE_FIELD_NAME,
        u.INDEX AS MEMBER_INDEX,
        u.VALUE AS MEMBER_PAYLOAD,
        CASE
            WHEN TYPEOF(u.VALUE:"Id") IN ('INTEGER', 'DECIMAL', 'VARCHAR')
             AND REGEXP_LIKE(u.VALUE:"Id"::VARCHAR, '^[0-9]+$')
                THEN TRY_TO_NUMBER(u.VALUE:"Id"::VARCHAR, 38, 0)
        END AS ARCHER_USER_ID,
        u.VALUE:"HasRead"::BOOLEAN AS HAS_READ,
        u.VALUE:"HasUpdate"::BOOLEAN AS HAS_UPDATE,
        u.VALUE:"HasDelete"::BOOLEAN AS HAS_DELETE
    FROM reference_fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_PAYLOAD:"UserList")) u
),
unmatched AS (
    SELECT m.*
    FROM user_members m
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER u
      ON u.ARCHER_USER_ID = m.ARCHER_USER_ID
    WHERE m.ARCHER_USER_ID IS NOT NULL
      AND u.ARCHER_USER_ID IS NULL
)
SELECT
    ARCHER_USER_ID,
    COUNT(*) AS OCCURRENCES,
    COUNT(DISTINCT SOURCE_RECORD_ID) AS DISTINCT_SOURCE_RECORDS,
    COUNT(DISTINCT SOURCE_FIELD_NAME) AS SOURCE_FIELD_COUNT,
    LISTAGG(DISTINCT SOURCE_FIELD_NAME, ', ')
        WITHIN GROUP (ORDER BY SOURCE_FIELD_NAME) AS SOURCE_FIELDS,
    COUNT_IF(HAS_READ = TRUE) AS HAS_READ_TRUE,
    COUNT_IF(HAS_UPDATE = TRUE) AS HAS_UPDATE_TRUE,
    COUNT_IF(HAS_DELETE = TRUE) AS HAS_DELETE_TRUE
FROM unmatched
GROUP BY ARCHER_USER_ID
ORDER BY OCCURRENCES DESC, ARCHER_USER_ID;

-- 3. What does Archer metadata say these four source fields actually are?
--    Do not choose one row if SQL_FIELD_NAME appears in multiple levels/modules.
WITH unresolved_fields AS (
    SELECT DISTINCT SOURCE_FIELD_NAME
    FROM (
        SELECT
            f.KEY::VARCHAR AS SOURCE_FIELD_NAME,
            u.VALUE:"Id"::NUMBER AS ARCHER_USER_ID
        FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r,
             LATERAL FLATTEN(INPUT => AS_OBJECT(r.CURATED_JSON)) f,
             LATERAL FLATTEN(INPUT => AS_ARRAY(f.VALUE:"UserList")) u
        WHERE TYPEOF(r.CURATED_JSON) = 'OBJECT'
          AND COALESCE(IS_ARRAY(f.VALUE:"UserList"), FALSE)
          AND TYPEOF(u.VALUE:"Id") IN ('INTEGER', 'DECIMAL')
    ) m
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER u
      ON u.ARCHER_USER_ID = m.ARCHER_USER_ID
    WHERE u.ARCHER_USER_ID IS NULL
)
SELECT
    uf.SOURCE_FIELD_NAME,
    mf.FIELD_ID,
    mf.FIELD_TYPE_ID,
    mf.LEVEL_ID,
    mf.MODULE_ID,
    mf.FIELD_NAME,
    mf.SQL_FIELD_NAME,
    mf.KEY_FIELD
FROM unresolved_fields uf
LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD mf
  ON UPPER(mf.SQL_FIELD_NAME) = UPPER(uf.SOURCE_FIELD_NAME)
ORDER BY uf.SOURCE_FIELD_NAME, mf.LEVEL_ID, mf.FIELD_ID;
