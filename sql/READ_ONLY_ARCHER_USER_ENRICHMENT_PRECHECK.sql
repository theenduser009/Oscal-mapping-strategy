-- OSCAL / Archer user enrichment precheck
-- Date: 2026-09-29
-- Baseline: simplify-metadata-boundary at c3563a82b6ef6d095b0ec1f1b75c250f3c8478f2
-- READ ONLY: two SELECT statements. No UPDATE, DDL, or notebook rerun.
-- Run both statements and review both result grids.
-- No private record IDs or personal values are embedded in this file.
-- Keep result payloads private; do not commit result rows/screenshots to GitHub.
-- User columns confirmed from the owner's 35-row schema screenshot.
-- Group lookup columns are not established by that result.

-- A. Verify the proposed user lookup key before allowing a many-match UPDATE.
-- Expected: nonempty lookup, no null IDs, no duplicate IDs.
-- Missing EEIDs are reported separately; do not manufacture or substitute them.
WITH user_keys AS (
    SELECT
        ARCHER_USER_ID,
        COUNT(*) AS ROWS_PER_ID,
        COUNT(DISTINCT NULLIF(TRIM(EEID), '')) AS DISTINCT_NONBLANK_EEIDS,
        COALESCE(COUNT_IF(NULLIF(TRIM(EEID), '') IS NULL), 0) AS MISSING_EEID_ROWS
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER
    GROUP BY ARCHER_USER_ID
)
SELECT
    'META_USER_KEY_CHECK' AS CHECK_NAME,
    COALESCE(SUM(ROWS_PER_ID), 0) AS LOOKUP_ROWS,
    COUNT(ARCHER_USER_ID) AS DISTINCT_NON_NULL_ARCHER_IDS,
    COALESCE(SUM(IFF(ARCHER_USER_ID IS NULL, ROWS_PER_ID, 0)), 0) AS NULL_ID_ROWS,
    COALESCE(COUNT_IF(ARCHER_USER_ID IS NOT NULL AND ROWS_PER_ID > 1), 0)
        AS DUPLICATE_ARCHER_ID_GROUPS,
    COALESCE(COUNT_IF(ARCHER_USER_ID IS NOT NULL AND DISTINCT_NONBLANK_EEIDS > 1), 0)
        AS ARCHER_IDS_WITH_CONFLICTING_EEIDS,
    COALESCE(SUM(MISSING_EEID_ROWS), 0) AS MISSING_EEID_ROWS
FROM user_keys;

-- B. Show complete user/group containers for one automatically selected record.
-- This discovers the actual member ID key (for example Id versus UserId);
-- it does not assume those alternatives are equivalent or choose one silently.
-- Every matching top-level field for the selected raw RequestedObject.Id appears.
-- The original member arrays and permission flags remain untouched in the payload.
-- Raw arrays with more than one object are deliberately ineligible for this sample:
-- the existing converter uses only element [0], so their lineage needs separate review.
-- Zero result rows mean no eligible sample was found, NOT that mapping has passed.
WITH source_objects AS (
    SELECT
        CONTENT_ID::VARCHAR AS STORED_CONTENT_ID,
        CURATED_JSON,
        CASE
            WHEN TYPEOF(RAW_DATA) = 'OBJECT' THEN RAW_DATA
            WHEN TYPEOF(RAW_DATA) = 'ARRAY' AND ARRAY_SIZE(RAW_DATA) = 1
                THEN RAW_DATA[0]
            ELSE NULL
        END AS RAW_OBJECT
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
), source_records AS (
    SELECT
        STORED_CONTENT_ID,
        RAW_OBJECT:"RequestedObject":"Id"::VARCHAR AS SOURCE_CONTENT_ID,
        RAW_OBJECT:"RequestedObject":"LevelId"::VARCHAR AS SOURCE_LEVEL_ID,
        CURATED_JSON
    FROM source_objects
    WHERE RAW_OBJECT IS NOT NULL
), counted_records AS (
    SELECT
        *,
        COUNT(*) OVER (PARTITION BY SOURCE_CONTENT_ID) AS SOURCE_ROWS_FOR_CONTENT_ID
    FROM source_records
    WHERE SOURCE_CONTENT_ID IS NOT NULL
), reference_fields AS (
    SELECT
        r.SOURCE_CONTENT_ID,
        r.STORED_CONTENT_ID,
        r.SOURCE_LEVEL_ID,
        r.SOURCE_ROWS_FOR_CONTENT_ID,
        f.KEY::VARCHAR AS SOURCE_FIELD_NAME,
        TYPEOF(f.VALUE:"UserList") AS USER_LIST_TYPE,
        ARRAY_SIZE(f.VALUE:"UserList") AS USER_COUNT,
        TYPEOF(f.VALUE:"GroupList") AS GROUP_LIST_TYPE,
        ARRAY_SIZE(f.VALUE:"GroupList") AS GROUP_COUNT,
        f.VALUE AS ORIGINAL_FIELD_PAYLOAD
    FROM counted_records r,
         LATERAL FLATTEN(INPUT => r.CURATED_JSON) f
    WHERE TYPEOF(r.CURATED_JSON) = 'OBJECT'
      AND TYPEOF(f.VALUE) = 'OBJECT'
      AND (COALESCE(ARRAY_SIZE(f.VALUE:"UserList"), 0) > 0
        OR COALESCE(ARRAY_SIZE(f.VALUE:"GroupList"), 0) > 0)
), sample_record AS (
    SELECT MIN(SOURCE_CONTENT_ID) AS SOURCE_CONTENT_ID
    FROM reference_fields
    WHERE COALESCE(USER_COUNT, 0) > 0
)
SELECT
    f.*,
    CASE
        WHEN f.STORED_CONTENT_ID IS NULL THEN 'STORED_ID_MISSING'
        WHEN f.STORED_CONTENT_ID = f.SOURCE_CONTENT_ID THEN 'MATCH'
        ELSE 'DIFFERS_REVIEW_BEFORE_UPDATE'
    END AS CONTENT_ID_CHECK
FROM reference_fields f
JOIN sample_record s ON s.SOURCE_CONTENT_ID = f.SOURCE_CONTENT_ID
ORDER BY f.SOURCE_FIELD_NAME, f.STORED_CONTENT_ID;
