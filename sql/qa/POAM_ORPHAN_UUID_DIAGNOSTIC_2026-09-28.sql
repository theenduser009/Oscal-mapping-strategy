-- POAM ORPHAN UUID DIAGNOSTIC - 2026-09-28
-- SELECT ONLY. Run the entire file; no substitutions are needed.
-- Reviewed table/key/UUID bindings on simplify-metadata-boundary at
-- e0f9b7dff2c26481b88c8dd1892ccddb52a567a4 in:
-- sql/qa/SOURCE_ONE_CONTENT_ID_ALL_ATTRIBUTES_2026-09-28.sql
--
-- Purpose: for FACT rows whose hash endpoints are missing from the full POAM
-- DIM, check whether the endpoint UUIDs identify existing POAM DIM rows.
-- This is table-wide, NOT filtered to an Authorization Package Content ID.
-- Ten aggregate rows only: no private identifiers or payloads in the output.
-- All seven UUID buckets are mutually exclusive, and include zero counts.
-- Hash comparisons use original BINARY keys. UUID case/hyphen/outer-space
-- normalization is diagnostic only; duplicate normalized UUIDs are ambiguous.
-- No arbitrary match selection, key repair, source attribution, or deletion.
-- Same-owner UUID candidates do not prove correct hierarchy or permit rekeying.
-- No UUID match does NOT prove that a FACT is old, disposable, or unrecoverable.
-- No history/Time Travel, other model DIM, or raw-source identity search here.
-- Local synthetic checks are not a live Snowflake compilation or QA pass.

WITH
poam_dim AS (
    SELECT PK_DIM_OSCAL_POAM_ELEMENT_HASH AS NODE_KEY,
           LOWER(REPLACE(TRIM(OSCAL_UUID), '-', '')) AS UUID_KEY,
           SOURCE_SYSTEM_NAME, SOURCE_TABLE_NAME, SOURCE_RECORD_ID
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT
),
hash_index AS (
    SELECT NODE_KEY, COUNT(*) AS DIM_MATCHES
    FROM poam_dim WHERE NODE_KEY IS NOT NULL
    GROUP BY NODE_KEY
),
uuid_index AS (
    SELECT UUID_KEY, COUNT(*) AS DIM_MATCHES,
           CASE WHEN COUNT(*)=1 THEN MAX(SOURCE_SYSTEM_NAME) END AS SOURCE_SYSTEM_NAME,
           CASE WHEN COUNT(*)=1 THEN MAX(SOURCE_TABLE_NAME) END AS SOURCE_TABLE_NAME,
           CASE WHEN COUNT(*)=1 THEN MAX(SOURCE_RECORD_ID) END AS SOURCE_RECORD_ID
    FROM poam_dim WHERE REGEXP_LIKE(UUID_KEY, '^[0-9a-f]{32}$')
    GROUP BY UUID_KEY
),
fact_scope AS (
    SELECT f.PK_FACT_OSCAL_POAM_DEPENDENCY_HASH AS FACT_KEY,
           LOWER(REPLACE(TRIM(f.SOURCE_OSCAL_UUID), '-', '')) AS SOURCE_UUID_KEY,
           LOWER(REPLACE(TRIM(f.TARGET_OSCAL_UUID), '-', '')) AS TARGET_UUID_KEY,
           COALESCE(s.DIM_MATCHES,0) AS SOURCE_HASH_MATCHES,
           COALESCE(t.DIM_MATCHES,0) AS TARGET_HASH_MATCHES
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_POAM_DEPENDENCY f
    LEFT JOIN hash_index s ON s.NODE_KEY=f.FK_SOURCE_ELEMENT_HASH
    LEFT JOIN hash_index t ON t.NODE_KEY=f.FK_TARGET_ELEMENT_HASH
),
orphan_classified AS (
    SELECT f.FACT_KEY,
           CASE
             WHEN NOT COALESCE(REGEXP_LIKE(f.SOURCE_UUID_KEY, '^[0-9a-f]{32}$'),FALSE)
               OR NOT COALESCE(REGEXP_LIKE(f.TARGET_UUID_KEY, '^[0-9a-f]{32}$'),FALSE)
               THEN 'UUID_INVALID_OR_MISSING'
             WHEN COALESCE(s.DIM_MATCHES,0)>1 OR COALESCE(t.DIM_MATCHES,0)>1
               THEN 'UUID_AMBIGUOUS'
             WHEN s.DIM_MATCHES=1 AND t.DIM_MATCHES=1 THEN
               CASE
                 WHEN NULLIF(TRIM(s.SOURCE_SYSTEM_NAME),'') IS NULL
                   OR NULLIF(TRIM(s.SOURCE_TABLE_NAME),'') IS NULL
                   OR NULLIF(TRIM(s.SOURCE_RECORD_ID),'') IS NULL
                   OR NULLIF(TRIM(t.SOURCE_SYSTEM_NAME),'') IS NULL
                   OR NULLIF(TRIM(t.SOURCE_TABLE_NAME),'') IS NULL
                   OR NULLIF(TRIM(t.SOURCE_RECORD_ID),'') IS NULL
                   OR s.SOURCE_SYSTEM_NAME IS DISTINCT FROM t.SOURCE_SYSTEM_NAME
                   OR s.SOURCE_TABLE_NAME IS DISTINCT FROM t.SOURCE_TABLE_NAME
                   OR s.SOURCE_RECORD_ID IS DISTINCT FROM t.SOURCE_RECORD_ID
                   THEN 'BOTH_UUIDS_UNIQUE_OWNER_CONFLICT_OR_MISSING'
                 ELSE 'BOTH_UUIDS_UNIQUE_SAME_OWNER'
               END
             WHEN s.DIM_MATCHES=1 THEN 'SOURCE_UUID_ONLY'
             WHEN t.DIM_MATCHES=1 THEN 'TARGET_UUID_ONLY'
             ELSE 'NEITHER_UUID_FOUND'
           END AS UUID_BUCKET
    FROM fact_scope f
    LEFT JOIN uuid_index s ON s.UUID_KEY=f.SOURCE_UUID_KEY
    LEFT JOIN uuid_index t ON t.UUID_KEY=f.TARGET_UUID_KEY
    WHERE f.SOURCE_HASH_MATCHES=0 OR f.TARGET_HASH_MATCHES=0
),
bucket_counts AS (
    SELECT UUID_BUCKET, COUNT(*) AS FACT_ROWS
    FROM orphan_classified GROUP BY UUID_BUCKET
),
buckets AS (
    SELECT 3 AS CHECK_ORDER, 'UUID_INVALID_OR_MISSING' AS QA_CHECK,
           'At least one endpoint UUID is missing or not a 32-hex UUID after formatting normalization.' AS DETAIL
    UNION ALL SELECT 4, 'UUID_AMBIGUOUS',
           'At least one normalized endpoint UUID matches multiple current POAM DIM rows; no candidate selected.'
    UNION ALL SELECT 5, 'BOTH_UUIDS_UNIQUE_SAME_OWNER',
           'Both UUIDs match unique DIM rows with the same nonblank source namespace and record. Candidate only; NOT a repair approval.'
    UNION ALL SELECT 6, 'BOTH_UUIDS_UNIQUE_OWNER_CONFLICT_OR_MISSING',
           'Both UUIDs match unique DIM rows, but source namespace/record differs or is missing.'
    UNION ALL SELECT 7, 'SOURCE_UUID_ONLY',
           'Only the source/parent UUID matches a unique current POAM DIM row.'
    UNION ALL SELECT 8, 'TARGET_UUID_ONLY',
           'Only the target/child UUID matches a unique current POAM DIM row.'
    UNION ALL SELECT 9, 'NEITHER_UUID_FOUND',
           'Both UUIDs are well formed, but neither occurs in the current POAM DIM. Cause remains unknown.'
),
report AS (
    SELECT 1 AS CHECK_ORDER, 'FACT_ROWS_READ' AS QA_CHECK, COUNT(*) AS OBSERVED_COUNT,
           'INFO_TABLE_WIDE' AS STATUS,
           'All current POAM FACT rows; not a distinct Content ID count.' AS DETAIL
    FROM fact_scope
    UNION ALL
    SELECT 2, 'FACT_ROWS_WITH_MISSING_HASH_ENDPOINT', COUNT(*),
           CASE WHEN COUNT(*)=0 THEN 'NO_ORPHANS_IN_THIS_SNAPSHOT' ELSE 'OPEN_QA_DEFECT' END,
           'FACT rows missing at least one hash endpoint. Duplicate FACT rows, if any, remain counted.'
    FROM orphan_classified
    UNION ALL
    SELECT b.CHECK_ORDER, b.QA_CHECK, COALESCE(c.FACT_ROWS,0), 'DIAGNOSTIC_ONLY', b.DETAIL
    FROM buckets b LEFT JOIN bucket_counts c ON c.UUID_BUCKET=b.QA_CHECK
    UNION ALL
    SELECT 10, 'CLASSIFICATION_COUNT_DIFFERENCE',
           (SELECT COUNT(*) FROM orphan_classified) -
           (SELECT COALESCE(SUM(c.FACT_ROWS),0) FROM buckets b JOIN bucket_counts c ON c.UUID_BUCKET=b.QA_CHECK),
           'EXPECT_ZERO_NOT_REPAIR_SIGNOFF',
           'Zero means the seven mutually exclusive UUID buckets account for all inspected orphan FACT rows.'
)
SELECT CURRENT_TIMESTAMP() AS QA_EXECUTED_AT,
       CHECK_ORDER, QA_CHECK, OBSERVED_COUNT, STATUS, DETAIL
FROM report
ORDER BY CHECK_ORDER;
