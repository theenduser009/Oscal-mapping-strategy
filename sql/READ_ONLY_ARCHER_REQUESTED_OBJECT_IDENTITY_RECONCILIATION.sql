-- Archer RequestedObject record-metadata / identity reconciliation
-- Date: 2026-09-29
-- READ ONLY. No UPDATE, DDL, temp objects, or writes.
--
-- Purpose:
--   Confirm how top-level RequestedObject identity metadata relates to the stored
--   CONTENT_ID before changing the one-update Matillion candidate.
--
-- Evidence being checked:
--   RequestedObject.Id
--   RequestedObject.Identity.BaseContentId
--   Identity.Locators[] aliases (ARCHER / SYS_REF / SYS_WF)
--   LevelId / SequentialId / Version / LastUpdated / UpdateInformation
--
-- Result set 1 is aggregate-only.
-- Result set 2 gives counts by locator alias; it does not expose raw IDs.

WITH norm AS (
    SELECT
        r.CONTENT_ID::VARCHAR AS STORED_CONTENT_ID,
        IFF(
            TYPEOF(r.RAW_DATA) = 'ARRAY',
            r.RAW_DATA[0],
            r.RAW_DATA
        ) AS OBJ
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r
    WHERE TYPEOF(r.RAW_DATA) IN ('ARRAY', 'OBJECT')
),
record_meta AS (
    SELECT
        STORED_CONTENT_ID,
        OBJ:"RequestedObject":"Id"::VARCHAR AS REQUESTED_OBJECT_ID,
        OBJ:"RequestedObject":"Identity":"BaseContentId"::VARCHAR AS BASE_CONTENT_ID,
        OBJ:"RequestedObject":"LevelId"::VARCHAR AS LEVEL_ID,
        OBJ:"RequestedObject":"SequentialId"::VARCHAR AS SEQUENTIAL_ID,
        OBJ:"RequestedObject":"Version"::VARCHAR AS RECORD_VERSION,
        OBJ:"RequestedObject":"LastUpdated"::VARCHAR AS LAST_UPDATED,
        OBJ:"RequestedObject":"UpdateInformation":"CreateDate"::VARCHAR AS CREATE_DATE,
        OBJ:"RequestedObject":"UpdateInformation":"CreateLogin"::VARCHAR AS CREATE_LOGIN,
        OBJ:"RequestedObject":"UpdateInformation":"UpdateDate"::VARCHAR AS UPDATE_DATE,
        OBJ:"RequestedObject":"UpdateInformation":"UpdateLogin"::VARCHAR AS UPDATE_LOGIN,
        OBJ:"RequestedObject":"Identity":"Locators" AS LOCATORS
    FROM norm
),
locator_rows AS (
    SELECT
        r.STORED_CONTENT_ID,
        r.REQUESTED_OBJECT_ID,
        r.BASE_CONTENT_ID,
        r.LEVEL_ID,
        r.SEQUENTIAL_ID,
        r.RECORD_VERSION,
        r.LAST_UPDATED,
        r.CREATE_DATE,
        r.CREATE_LOGIN,
        r.UPDATE_DATE,
        r.UPDATE_LOGIN,
        l.VALUE:"Location":"Alias"::VARCHAR AS LOCATOR_ALIAS,
        COALESCE(
            l.VALUE:"Identity":"Value"::VARCHAR,
            l.VALUE:"Identity":"value"::VARCHAR,
            l.VALUE:"Identity":"Id"::VARCHAR,
            l.VALUE:"Identity":"id"::VARCHAR
        ) AS LOCATOR_ID
    FROM record_meta r,
         LATERAL FLATTEN(INPUT => AS_ARRAY(r.LOCATORS), OUTER => TRUE) l
),
per_record AS (
    SELECT
        STORED_CONTENT_ID,
        REQUESTED_OBJECT_ID,
        BASE_CONTENT_ID,
        LEVEL_ID,
        SEQUENTIAL_ID,
        RECORD_VERSION,
        LAST_UPDATED,
        CREATE_DATE,
        CREATE_LOGIN,
        UPDATE_DATE,
        UPDATE_LOGIN,
        MAX(IFF(UPPER(LOCATOR_ALIAS) = 'ARCHER',  LOCATOR_ID, NULL)) AS ARCHER_LOCATOR_ID,
        MAX(IFF(UPPER(LOCATOR_ALIAS) = 'SYS_REF', LOCATOR_ID, NULL)) AS SYS_REF_LOCATOR_ID,
        MAX(IFF(UPPER(LOCATOR_ALIAS) = 'SYS_WF',  LOCATOR_ID, NULL)) AS SYS_WF_LOCATOR_ID
    FROM locator_rows
    GROUP BY
        STORED_CONTENT_ID,
        REQUESTED_OBJECT_ID,
        BASE_CONTENT_ID,
        LEVEL_ID,
        SEQUENTIAL_ID,
        RECORD_VERSION,
        LAST_UPDATED,
        CREATE_DATE,
        CREATE_LOGIN,
        UPDATE_DATE,
        UPDATE_LOGIN
)
SELECT
    COUNT(*) AS SOURCE_ROWS,
    COUNT(DISTINCT REQUESTED_OBJECT_ID) AS DISTINCT_REQUESTED_OBJECT_IDS,

    COUNT_IF(REQUESTED_OBJECT_ID IS NULL) AS MISSING_REQUESTED_OBJECT_ID,
    COUNT_IF(BASE_CONTENT_ID IS NULL) AS MISSING_BASE_CONTENT_ID,
    COUNT_IF(ARCHER_LOCATOR_ID IS NULL) AS MISSING_ARCHER_LOCATOR_ID,
    COUNT_IF(SYS_REF_LOCATOR_ID IS NULL) AS MISSING_SYS_REF_LOCATOR_ID,
    COUNT_IF(SYS_WF_LOCATOR_ID IS NULL) AS MISSING_SYS_WF_LOCATOR_ID,

    COUNT_IF(
        STORED_CONTENT_ID IS NOT NULL
        AND REQUESTED_OBJECT_ID IS NOT NULL
        AND STORED_CONTENT_ID <> REQUESTED_OBJECT_ID
    ) AS STORED_VS_REQUESTED_ID_MISMATCH,

    COUNT_IF(
        BASE_CONTENT_ID IS NOT NULL
        AND REQUESTED_OBJECT_ID IS NOT NULL
        AND BASE_CONTENT_ID <> REQUESTED_OBJECT_ID
    ) AS BASECONTENT_VS_REQUESTED_ID_MISMATCH,

    COUNT_IF(
        ARCHER_LOCATOR_ID IS NOT NULL
        AND REQUESTED_OBJECT_ID IS NOT NULL
        AND ARCHER_LOCATOR_ID <> REQUESTED_OBJECT_ID
    ) AS ARCHER_LOCATOR_VS_REQUESTED_ID_MISMATCH,

    COUNT_IF(
        SYS_REF_LOCATOR_ID IS NOT NULL
        AND REQUESTED_OBJECT_ID IS NOT NULL
        AND SYS_REF_LOCATOR_ID <> REQUESTED_OBJECT_ID
    ) AS SYS_REF_LOCATOR_VS_REQUESTED_ID_MISMATCH,

    COUNT_IF(LEVEL_ID IS NULL) AS MISSING_LEVEL_ID,
    COUNT_IF(SEQUENTIAL_ID IS NULL) AS MISSING_SEQUENTIAL_ID,
    COUNT_IF(RECORD_VERSION IS NULL) AS MISSING_RECORD_VERSION,
    COUNT_IF(LAST_UPDATED IS NULL) AS MISSING_LAST_UPDATED,
    COUNT_IF(CREATE_DATE IS NULL) AS MISSING_CREATE_DATE,
    COUNT_IF(CREATE_LOGIN IS NULL) AS MISSING_CREATE_LOGIN,
    COUNT_IF(UPDATE_DATE IS NULL) AS MISSING_UPDATE_DATE,
    COUNT_IF(UPDATE_LOGIN IS NULL) AS MISSING_UPDATE_LOGIN
FROM per_record;

WITH norm AS (
    SELECT
        IFF(
            TYPEOF(r.RAW_DATA) = 'ARRAY',
            r.RAW_DATA[0],
            r.RAW_DATA
        ) AS OBJ
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r
    WHERE TYPEOF(r.RAW_DATA) IN ('ARRAY', 'OBJECT')
),
locator_rows AS (
    SELECT
        l.VALUE:"Location":"Alias"::VARCHAR AS LOCATOR_ALIAS,
        COALESCE(
            l.VALUE:"Identity":"Value"::VARCHAR,
            l.VALUE:"Identity":"value"::VARCHAR,
            l.VALUE:"Identity":"Id"::VARCHAR,
            l.VALUE:"Identity":"id"::VARCHAR
        ) AS LOCATOR_ID
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => AS_ARRAY(n.OBJ:"RequestedObject":"Identity":"Locators"),
             OUTER => TRUE
         ) l
)
SELECT
    COALESCE(LOCATOR_ALIAS, '<NULL_ALIAS>') AS LOCATOR_ALIAS,
    COUNT(*) AS LOCATOR_OCCURRENCES,
    COUNT_IF(LOCATOR_ID IS NULL) AS MISSING_LOCATOR_ID,
    COUNT(DISTINCT LOCATOR_ID) AS DISTINCT_LOCATOR_IDS
FROM locator_rows
GROUP BY COALESCE(LOCATOR_ALIAS, '<NULL_ALIAS>')
ORDER BY LOCATOR_OCCURRENCES DESC, LOCATOR_ALIAS;
