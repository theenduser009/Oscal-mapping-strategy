-- Diagnose the two Source One rows that have a valid RequestedObject.Id
-- but were not populated into CONTENT_ID / CURATED_JSON.
-- Date: 2026-10-01
-- READ ONLY. No DML / DDL.
--
-- Owner-observed affected RequestedObject IDs:
--   8257339
--   8257340
--
-- Purpose:
-- Prove whether the raw->curated UPDATE drops these rows because
-- RequestedObject.FieldContents produces zero rows in the flat CTE.

WITH base AS (
    SELECT
        IFF(TYPEOF(RAW_DATA) = 'ARRAY', RAW_DATA[0], RAW_DATA) AS OBJ
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
),
target AS (
    SELECT
        OBJ:"RequestedObject":"Id"::VARCHAR AS REQUESTED_OBJECT_ID,
        OBJ:"RequestedObject":"LevelId"::VARCHAR AS LEVEL_ID,
        OBJ:"RequestedObject":"FieldContents" AS FIELD_CONTENTS
    FROM base
    WHERE OBJ:"RequestedObject":"Id"::VARCHAR IN ('8257339', '8257340')
)
SELECT
    REQUESTED_OBJECT_ID,
    LEVEL_ID,
    TYPEOF(FIELD_CONTENTS) AS FIELD_CONTENTS_TYPE,
    CASE
        WHEN TYPEOF(FIELD_CONTENTS) = 'OBJECT' THEN OBJECT_SIZE(AS_OBJECT(FIELD_CONTENTS))
        WHEN TYPEOF(FIELD_CONTENTS) = 'ARRAY'  THEN ARRAY_SIZE(AS_ARRAY(FIELD_CONTENTS))
        ELSE NULL
    END AS FIELD_CONTENTS_MEMBER_COUNT,
    IFF(FIELD_CONTENTS IS NULL, 'Y', 'N') AS FIELD_CONTENTS_IS_SQL_NULL,
    IFF(COALESCE(IS_NULL_VALUE(FIELD_CONTENTS), FALSE), 'Y', 'N') AS FIELD_CONTENTS_IS_JSON_NULL
FROM target
ORDER BY REQUESTED_OBJECT_ID;


-- Show exactly how many rows the current Matillion flat CTE would produce.
WITH base AS (
    SELECT
        IFF(TYPEOF(RAW_DATA) = 'ARRAY', RAW_DATA[0], RAW_DATA) AS OBJ
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
),
target AS (
    SELECT
        OBJ:"RequestedObject":"Id"::VARCHAR AS REQUESTED_OBJECT_ID,
        OBJ:"RequestedObject":"FieldContents" AS FIELD_CONTENTS
    FROM base
    WHERE OBJ:"RequestedObject":"Id"::VARCHAR IN ('8257339', '8257340')
),
flat_counts AS (
    SELECT
        t.REQUESTED_OBJECT_ID,
        COUNT(f.key) AS FLAT_ROWS
    FROM target t
    LEFT JOIN LATERAL FLATTEN(INPUT => t.FIELD_CONTENTS, OUTER => TRUE) f ON TRUE
    GROUP BY t.REQUESTED_OBJECT_ID
)
SELECT
    REQUESTED_OBJECT_ID,
    FLAT_ROWS,
    CASE
        WHEN FLAT_ROWS = 0 THEN 'CURRENT_FLAT_CTE_DROPS_THIS_RECORD'
        ELSE 'FIELD_CONTENTS_PRODUCES_ROWS'
    END AS DIAGNOSIS
FROM flat_counts
ORDER BY REQUESTED_OBJECT_ID;
