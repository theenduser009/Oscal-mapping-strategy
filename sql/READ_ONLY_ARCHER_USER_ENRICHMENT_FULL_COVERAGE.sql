-- OSCAL / Archer user enrichment full-scope coverage
-- Date: 2026-09-29
-- Baseline reviewed: simplify-metadata-boundary at bc2ab66f7a60f5628ee42b1c270af4a74b73a464
-- READ ONLY: one SELECT. No UPDATE, DDL, temp tables, notebook run, or target writes.
--
-- Purpose:
--   Validate the user-enrichment contract across ALL current Source One rows
--   before integrating it into the Matillion CURATED_JSON UPDATE.
--
-- Confirmed source member key from owner evidence:
--   <field>.UserList[].Id
--   <field>.GroupList[].Id
--
-- Confirmed user lookup:
--   RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER.ARCHER_USER_ID
--
-- This query returns aggregate counts only. It does not expose user IDs, EEIDs,
-- names, Content IDs, or source payloads. Group IDs are validated structurally
-- but not resolved to names because the authoritative Meta Group lookup contract
-- has not yet been established.
--
-- Review rules:
--   * USER_NOT_FOUND, MATCHED_MISSING_EEID, invalid member IDs/shapes, duplicate
--     lookup IDs, or foreign ResolvedUser keys must be reviewed before UPDATE.
--   * GroupList stays a separate namespace; group lookup is not inferred here.
--   * A Content ID mismatch or unsupported RAW_DATA shape is a separate source
--     identity gate and is not silently corrected.
--
WITH source_base AS (
    SELECT
        CONTENT_ID::VARCHAR AS STORED_CONTENT_ID,
        CURATED_JSON,
        TYPEOF(RAW_DATA) AS RAW_TYPE,
        IFF(TYPEOF(RAW_DATA) = 'ARRAY', ARRAY_SIZE(RAW_DATA), NULL) AS RAW_ARRAY_SIZE,
        CASE
            WHEN TYPEOF(RAW_DATA) = 'OBJECT' THEN RAW_DATA
            WHEN TYPEOF(RAW_DATA) = 'ARRAY' AND ARRAY_SIZE(RAW_DATA) = 1 THEN RAW_DATA[0]
            ELSE NULL
        END AS RAW_OBJECT
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
),
source_rows AS (
    SELECT
        STORED_CONTENT_ID,
        CURATED_JSON,
        RAW_TYPE,
        RAW_ARRAY_SIZE,
        RAW_OBJECT:"RequestedObject":"Id"::VARCHAR AS SOURCE_CONTENT_ID,
        IFF(RAW_OBJECT IS NULL, 1, 0) AS UNSUPPORTED_RAW_SHAPE,
        IFF(RAW_OBJECT IS NOT NULL
            AND RAW_OBJECT:"RequestedObject":"Id" IS NULL, 1, 0) AS SOURCE_ID_MISSING,
        IFF(RAW_OBJECT IS NOT NULL
            AND RAW_OBJECT:"RequestedObject":"Id" IS NOT NULL
            AND STORED_CONTENT_ID IS DISTINCT FROM RAW_OBJECT:"RequestedObject":"Id"::VARCHAR,
            1, 0) AS CONTENT_ID_MISMATCH,
        IFF(TYPEOF(CURATED_JSON) = 'OBJECT', 0, 1) AS NON_OBJECT_CURATED_JSON
    FROM source_base
),
fields AS (
    SELECT
        r.STORED_CONTENT_ID,
        f.KEY::VARCHAR AS SOURCE_FIELD_NAME,
        f.VALUE AS FIELD_PAYLOAD,
        TYPEOF(f.VALUE:"UserList") AS USER_LIST_TYPE,
        TYPEOF(f.VALUE:"GroupList") AS GROUP_LIST_TYPE,
        ARRAY_SIZE(AS_ARRAY(f.VALUE:"UserList")) AS USER_COUNT,
        ARRAY_SIZE(AS_ARRAY(f.VALUE:"GroupList")) AS GROUP_COUNT,
        IFF(
            f.VALUE:"UserList" IS NOT NULL
            AND NOT COALESCE(IS_NULL_VALUE(f.VALUE:"UserList"), FALSE)
            AND NOT COALESCE(IS_ARRAY(f.VALUE:"UserList"), FALSE),
            1, 0
        ) AS INVALID_USERLIST_SHAPE,
        IFF(
            f.VALUE:"GroupList" IS NOT NULL
            AND NOT COALESCE(IS_NULL_VALUE(f.VALUE:"GroupList"), FALSE)
            AND NOT COALESCE(IS_ARRAY(f.VALUE:"GroupList"), FALSE),
            1, 0
        ) AS INVALID_GROUPLIST_SHAPE
    FROM source_rows r,
         LATERAL FLATTEN(INPUT => AS_OBJECT(r.CURATED_JSON)) f
    WHERE r.NON_OBJECT_CURATED_JSON = 0
      AND (
          TYPEOF(f.VALUE:"UserList") IS NOT NULL
          OR TYPEOF(f.VALUE:"GroupList") IS NOT NULL
      )
),
user_members AS (
    SELECT
        f.STORED_CONTENT_ID,
        f.SOURCE_FIELD_NAME,
        u.INDEX AS MEMBER_INDEX,
        u.VALUE AS MEMBER_PAYLOAD,
        CASE
            WHEN TYPEOF(u.VALUE:"Id") IN ('INTEGER', 'DECIMAL', 'VARCHAR')
             AND REGEXP_LIKE(u.VALUE:"Id"::VARCHAR, '^[0-9]+$')
                THEN TRY_TO_NUMBER(u.VALUE:"Id"::VARCHAR, 38, 0)
        END AS LOOKUP_USER_ID,
        IFF(
            u.VALUE:"ResolvedUser" IS NOT NULL
            AND NOT COALESCE(
                u.VALUE:"ResolvedUser":"ContractVersion"::VARCHAR = 'archer-meta-user-v1',
                FALSE
            ),
            1, 0
        ) AS FOREIGN_RESOLVEDUSER_KEY
    FROM fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_PAYLOAD:"UserList")) u
    WHERE COALESCE(IS_ARRAY(f.FIELD_PAYLOAD:"UserList"), FALSE)
),
user_lookup AS (
    SELECT
        ARCHER_USER_ID,
        COUNT(*) AS MATCH_COUNT,
        IFF(COUNT(*) = 1, MAX(NULLIF(TRIM(EEID), '')), NULL) AS EEID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER
    WHERE ARCHER_USER_ID IN (
        SELECT LOOKUP_USER_ID
        FROM user_members
        WHERE LOOKUP_USER_ID IS NOT NULL
    )
    GROUP BY ARCHER_USER_ID
),
user_status AS (
    SELECT
        m.STORED_CONTENT_ID,
        m.SOURCE_FIELD_NAME,
        m.MEMBER_INDEX,
        CASE
            WHEN NOT COALESCE(IS_OBJECT(m.MEMBER_PAYLOAD), FALSE)
                THEN 'INVALID_MEMBER_OBJECT'
            WHEN m.FOREIGN_RESOLVEDUSER_KEY = 1
                THEN 'ENRICHMENT_KEY_COLLISION'
            WHEN m.LOOKUP_USER_ID IS NULL
                THEN 'INVALID_USER_ID'
            WHEN l.MATCH_COUNT > 1
                THEN 'DUPLICATE_LOOKUP_ID'
            WHEN l.ARCHER_USER_ID IS NULL
                THEN 'USER_NOT_FOUND'
            WHEN l.EEID IS NULL
                THEN 'MATCHED_MISSING_EEID'
            ELSE 'MATCHED'
        END AS LOOKUP_STATUS
    FROM user_members m
    LEFT JOIN user_lookup l
      ON l.ARCHER_USER_ID = m.LOOKUP_USER_ID
),
group_members AS (
    SELECT
        f.STORED_CONTENT_ID,
        f.SOURCE_FIELD_NAME,
        g.INDEX AS MEMBER_INDEX,
        g.VALUE AS MEMBER_PAYLOAD,
        IFF(
            COALESCE(IS_OBJECT(g.VALUE), FALSE)
            AND TYPEOF(g.VALUE:"Id") IN ('INTEGER', 'DECIMAL', 'VARCHAR')
            AND REGEXP_LIKE(g.VALUE:"Id"::VARCHAR, '^[0-9]+$'),
            0, 1
        ) AS INVALID_GROUP_MEMBER_ID
    FROM fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_PAYLOAD:"GroupList")) g
    WHERE COALESCE(IS_ARRAY(f.FIELD_PAYLOAD:"GroupList"), FALSE)
),
field_rollup AS (
    SELECT
        f.SOURCE_FIELD_NAME,
        COUNT(*) AS FIELD_OCCURRENCES,
        COUNT_IF(COALESCE(f.USER_COUNT, 0) > 0) AS FIELDS_WITH_USERS,
        COALESCE(SUM(f.USER_COUNT), 0) AS USER_MEMBER_OCCURRENCES,
        COUNT_IF(COALESCE(f.GROUP_COUNT, 0) > 0) AS FIELDS_WITH_GROUPS,
        COALESCE(SUM(f.GROUP_COUNT), 0) AS GROUP_MEMBER_OCCURRENCES,
        COUNT_IF(COALESCE(f.USER_COUNT, 0) > 0
              AND COALESCE(f.GROUP_COUNT, 0) > 0) AS FIELDS_WITH_BOTH,
        SUM(f.INVALID_USERLIST_SHAPE) AS INVALID_USERLIST_SHAPES,
        SUM(f.INVALID_GROUPLIST_SHAPE) AS INVALID_GROUPLIST_SHAPES,
        COALESCE((
            SELECT COUNT(*)
            FROM user_status u
            WHERE u.SOURCE_FIELD_NAME = f.SOURCE_FIELD_NAME
              AND u.LOOKUP_STATUS = 'MATCHED'
        ), 0) AS MATCHED_USER_MEMBERS,
        COALESCE((
            SELECT COUNT(*)
            FROM user_status u
            WHERE u.SOURCE_FIELD_NAME = f.SOURCE_FIELD_NAME
              AND u.LOOKUP_STATUS = 'MATCHED_MISSING_EEID'
        ), 0) AS MISSING_EEID_USER_MEMBERS,
        COALESCE((
            SELECT COUNT(*)
            FROM user_status u
            WHERE u.SOURCE_FIELD_NAME = f.SOURCE_FIELD_NAME
              AND u.LOOKUP_STATUS = 'USER_NOT_FOUND'
        ), 0) AS UNMATCHED_USER_MEMBERS,
        COALESCE((
            SELECT COUNT(*)
            FROM user_status u
            WHERE u.SOURCE_FIELD_NAME = f.SOURCE_FIELD_NAME
              AND u.LOOKUP_STATUS IN (
                  'INVALID_MEMBER_OBJECT',
                  'INVALID_USER_ID',
                  'DUPLICATE_LOOKUP_ID',
                  'ENRICHMENT_KEY_COLLISION'
              )
        ), 0) AS BLOCKING_USER_MEMBERS,
        COALESCE((
            SELECT COUNT(*)
            FROM group_members g
            WHERE g.SOURCE_FIELD_NAME = f.SOURCE_FIELD_NAME
              AND g.INVALID_GROUP_MEMBER_ID = 1
        ), 0) AS INVALID_GROUP_MEMBER_IDS
    FROM fields f
    GROUP BY f.SOURCE_FIELD_NAME
),
source_quality AS (
    SELECT
        COUNT(*) AS SOURCE_ROWS,
        COUNT(DISTINCT STORED_CONTENT_ID) AS DISTINCT_STORED_CONTENT_IDS,
        SUM(UNSUPPORTED_RAW_SHAPE) AS UNSUPPORTED_RAW_SHAPE_ROWS,
        SUM(SOURCE_ID_MISSING) AS SOURCE_ID_MISSING_ROWS,
        SUM(CONTENT_ID_MISMATCH) AS CONTENT_ID_MISMATCH_ROWS,
        SUM(NON_OBJECT_CURATED_JSON) AS NON_OBJECT_CURATED_JSON_ROWS
    FROM source_rows
),
all_rollup AS (
    SELECT
        '__ALL__' AS SOURCE_FIELD_NAME,
        SUM(FIELD_OCCURRENCES) AS FIELD_OCCURRENCES,
        SUM(FIELDS_WITH_USERS) AS FIELDS_WITH_USERS,
        SUM(USER_MEMBER_OCCURRENCES) AS USER_MEMBER_OCCURRENCES,
        SUM(FIELDS_WITH_GROUPS) AS FIELDS_WITH_GROUPS,
        SUM(GROUP_MEMBER_OCCURRENCES) AS GROUP_MEMBER_OCCURRENCES,
        SUM(FIELDS_WITH_BOTH) AS FIELDS_WITH_BOTH,
        SUM(INVALID_USERLIST_SHAPES) AS INVALID_USERLIST_SHAPES,
        SUM(INVALID_GROUPLIST_SHAPES) AS INVALID_GROUPLIST_SHAPES,
        SUM(MATCHED_USER_MEMBERS) AS MATCHED_USER_MEMBERS,
        SUM(MISSING_EEID_USER_MEMBERS) AS MISSING_EEID_USER_MEMBERS,
        SUM(UNMATCHED_USER_MEMBERS) AS UNMATCHED_USER_MEMBERS,
        SUM(BLOCKING_USER_MEMBERS) AS BLOCKING_USER_MEMBERS,
        SUM(INVALID_GROUP_MEMBER_IDS) AS INVALID_GROUP_MEMBER_IDS
    FROM field_rollup
)
SELECT
    'ALL' AS ROW_SCOPE,
    a.SOURCE_FIELD_NAME,
    q.SOURCE_ROWS,
    q.DISTINCT_STORED_CONTENT_IDS,
    q.UNSUPPORTED_RAW_SHAPE_ROWS,
    q.SOURCE_ID_MISSING_ROWS,
    q.CONTENT_ID_MISMATCH_ROWS,
    q.NON_OBJECT_CURATED_JSON_ROWS,
    a.FIELD_OCCURRENCES,
    a.FIELDS_WITH_USERS,
    a.USER_MEMBER_OCCURRENCES,
    a.MATCHED_USER_MEMBERS,
    a.MISSING_EEID_USER_MEMBERS,
    a.UNMATCHED_USER_MEMBERS,
    a.BLOCKING_USER_MEMBERS,
    a.FIELDS_WITH_GROUPS,
    a.GROUP_MEMBER_OCCURRENCES,
    a.FIELDS_WITH_BOTH,
    a.INVALID_USERLIST_SHAPES,
    a.INVALID_GROUPLIST_SHAPES,
    a.INVALID_GROUP_MEMBER_IDS
FROM all_rollup a
CROSS JOIN source_quality q

UNION ALL

SELECT
    'FIELD' AS ROW_SCOPE,
    f.SOURCE_FIELD_NAME,
    NULL, NULL, NULL, NULL, NULL, NULL,
    f.FIELD_OCCURRENCES,
    f.FIELDS_WITH_USERS,
    f.USER_MEMBER_OCCURRENCES,
    f.MATCHED_USER_MEMBERS,
    f.MISSING_EEID_USER_MEMBERS,
    f.UNMATCHED_USER_MEMBERS,
    f.BLOCKING_USER_MEMBERS,
    f.FIELDS_WITH_GROUPS,
    f.GROUP_MEMBER_OCCURRENCES,
    f.FIELDS_WITH_BOTH,
    f.INVALID_USERLIST_SHAPES,
    f.INVALID_GROUPLIST_SHAPES,
    f.INVALID_GROUP_MEMBER_IDS
FROM field_rollup f

ORDER BY ROW_SCOPE, SOURCE_FIELD_NAME;
