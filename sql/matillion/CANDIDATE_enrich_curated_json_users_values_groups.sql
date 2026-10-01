-- OSCAL / Archer CURATED_JSON metadata enrichment
-- Date: 2026-10-01
-- CANDIDATE MATILLION UPDATE. DEV first.
--
-- Run after the existing raw -> CURATED_JSON conversion.
--
-- Preserves original Archer reference IDs and source member shapes.
-- Enriches:
--   UserList[].Id    -> ARCHER_META_USER.ARCHER_USER_ID
--   ValuesListIds[]  -> ARCHER_META_VALUES.VALUEID / VALUENAME
--   GroupList[]      -> ARCHER_META_GROUP.GROUP_ID / GROUP_NAME / GUID
--
-- Output additions:
--   UserList[].ResolvedUser
--   field.ResolvedValues[]
--   field.ResolvedGroups[]
--
-- Original UserList, ValuesListIds and GroupList identities remain available.
-- Unmatched valid IDs are retained with *_NOT_FOUND status.
-- Malformed IDs/shapes and duplicate lookup IDs block that source record from
-- this enrichment update rather than silently choosing a value.
--
-- This statement does not change RAW_DATA, CONTENT_ID, OSCAL UUIDs, mappings,
-- DIM/FACT rows, or the original Archer reference IDs.

UPDATE ${jv_raw_table_name} AS tgt
SET tgt.CURATED_JSON = src.ENRICHED_CURATED_JSON
FROM (
    WITH source_base AS (
        SELECT
            IFF(
                TYPEOF(r.RAW_DATA) = 'ARRAY',
                r.RAW_DATA[0],
                r.RAW_DATA
            ):"RequestedObject":"Id"::NUMBER AS RECORD_ID,
            r.CONTENT_ID::VARCHAR AS STORED_CONTENT_ID,
            r.CURATED_JSON
        FROM ${jv_raw_table_name} r
        WHERE TYPEOF(r.CURATED_JSON) = 'OBJECT'
    ),
    source_candidates AS (
        SELECT
            *,
            COUNT(*) OVER (PARTITION BY RECORD_ID) AS SOURCE_ROWS_FOR_RECORD
        FROM source_base
    ),
    source_rows AS (
        SELECT
            RECORD_ID,
            STORED_CONTENT_ID,
            CURATED_JSON
        FROM source_candidates
        WHERE RECORD_ID IS NOT NULL
          AND SOURCE_ROWS_FOR_RECORD = 1
          AND STORED_CONTENT_ID = RECORD_ID::VARCHAR
    ),
    fields AS (
        SELECT
            s.RECORD_ID,
            f.key::STRING AS SQL_KEY,
            f.value       AS FIELD_VALUE,
            IFF(
                f.value:"UserList" IS NOT NULL
                AND NOT COALESCE(IS_NULL_VALUE(f.value:"UserList"), FALSE)
                AND NOT COALESCE(IS_ARRAY(f.value:"UserList"), FALSE),
                1, 0
            ) AS INVALID_USERLIST_SHAPE,
            IFF(
                f.value:"ValuesListIds" IS NOT NULL
                AND NOT COALESCE(IS_NULL_VALUE(f.value:"ValuesListIds"), FALSE)
                AND NOT COALESCE(IS_ARRAY(f.value:"ValuesListIds"), FALSE),
                1, 0
            ) AS INVALID_VALUESLIST_SHAPE,
            IFF(
                f.value:"GroupList" IS NOT NULL
                AND NOT COALESCE(IS_NULL_VALUE(f.value:"GroupList"), FALSE)
                AND NOT COALESCE(IS_ARRAY(f.value:"GroupList"), FALSE),
                1, 0
            ) AS INVALID_GROUPLIST_SHAPE
        FROM source_rows s,
             LATERAL FLATTEN(INPUT => AS_OBJECT(s.CURATED_JSON)) f
    ),

    -- User lookup/enrichment.
    user_members AS (
        SELECT
            f.RECORD_ID,
            f.SQL_KEY,
            u.index AS MEMBER_INDEX,
            u.value AS MEMBER_VALUE,
            CASE
                WHEN TYPEOF(u.value:"Id") IN ('INTEGER','DECIMAL','VARCHAR')
                 AND REGEXP_LIKE(u.value:"Id"::VARCHAR, '^[0-9]+$')
                    THEN TRY_TO_NUMBER(u.value:"Id"::VARCHAR, 38, 0)
            END AS ARCHER_USER_ID
        FROM fields f,
             LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_VALUE:"UserList")) u
        WHERE COALESCE(IS_ARRAY(f.FIELD_VALUE:"UserList"), FALSE)
    ),
    user_lookup AS (
        SELECT
            ARCHER_USER_ID,
            COUNT(*) AS MATCH_COUNT,
            IFF(COUNT(*) = 1, MAX(EEID), NULL)        AS EEID,
            IFF(COUNT(*) = 1, MAX(FIRST_NAME), NULL)  AS FIRST_NAME,
            IFF(COUNT(*) = 1, MAX(MIDDLE_NAME), NULL) AS MIDDLE_NAME,
            IFF(COUNT(*) = 1, MAX(LAST_NAME), NULL)   AS LAST_NAME
        FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER
        WHERE ARCHER_USER_ID IN (
            SELECT ARCHER_USER_ID
            FROM user_members
            WHERE ARCHER_USER_ID IS NOT NULL
        )
        GROUP BY ARCHER_USER_ID
    ),
    resolved_user_members AS (
        SELECT
            m.*,
            u.EEID,
            u.FIRST_NAME,
            u.MIDDLE_NAME,
            u.LAST_NAME,
            CASE
                WHEN NOT COALESCE(IS_OBJECT(m.MEMBER_VALUE), FALSE)
                    THEN 'INVALID_MEMBER_OBJECT'
                WHEN m.MEMBER_VALUE:"ResolvedUser" IS NOT NULL
                 AND NOT COALESCE(
                     m.MEMBER_VALUE:"ResolvedUser":"ContractVersion"::VARCHAR
                         = 'archer-meta-user-v1',
                     FALSE
                 )
                    THEN 'ENRICHMENT_KEY_COLLISION'
                WHEN m.ARCHER_USER_ID IS NULL
                    THEN 'INVALID_USER_ID'
                WHEN u.MATCH_COUNT > 1
                    THEN 'DUPLICATE_LOOKUP_ID'
                WHEN u.ARCHER_USER_ID IS NULL
                    THEN 'USER_NOT_FOUND'
                WHEN NULLIF(TRIM(u.EEID), '') IS NULL
                    THEN 'MATCHED_MISSING_EEID'
                ELSE 'MATCHED'
            END AS LOOKUP_STATUS
        FROM user_members m
        LEFT JOIN user_lookup u
          ON u.ARCHER_USER_ID = m.ARCHER_USER_ID
    ),
    enriched_user_members AS (
        SELECT
            r.*,
            CASE
                WHEN LOOKUP_STATUS IN (
                    'INVALID_MEMBER_OBJECT',
                    'ENRICHMENT_KEY_COLLISION',
                    'INVALID_USER_ID',
                    'DUPLICATE_LOOKUP_ID'
                )
                    THEN MEMBER_VALUE
                ELSE TO_VARIANT(
                    OBJECT_INSERT(
                        AS_OBJECT(MEMBER_VALUE),
                        'ResolvedUser',
                        OBJECT_CONSTRUCT_KEEP_NULL(
                            'ContractVersion', 'archer-meta-user-v1',
                            'LookupStatus', LOOKUP_STATUS,
                            'EEID', EEID,
                            'FIRST_NAME', FIRST_NAME,
                            'MIDDLE_NAME', MIDDLE_NAME,
                            'LAST_NAME', LAST_NAME
                        ),
                        TRUE
                    )
                )
            END AS ENRICHED_MEMBER_VALUE,
            IFF(
                LOOKUP_STATUS IN (
                    'INVALID_MEMBER_OBJECT',
                    'ENRICHMENT_KEY_COLLISION',
                    'INVALID_USER_ID',
                    'DUPLICATE_LOOKUP_ID'
                ),
                1, 0
            ) AS BLOCKING_MEMBER
        FROM resolved_user_members r
    ),
    user_lists AS (
        SELECT
            RECORD_ID,
            SQL_KEY,
            COUNT(*) AS MEMBER_COUNT,
            ARRAY_AGG(
                COALESCE(ENRICHED_MEMBER_VALUE, PARSE_JSON('null'))
            ) WITHIN GROUP (ORDER BY MEMBER_INDEX) AS ENRICHED_USER_LIST,
            SUM(BLOCKING_MEMBER) AS BLOCKING_MEMBERS
        FROM enriched_user_members
        GROUP BY RECORD_ID, SQL_KEY
    ),

    -- Value-list lookup/enrichment.
    value_members AS (
        SELECT
            f.RECORD_ID,
            f.SQL_KEY,
            v.index AS MEMBER_INDEX,
            v.value AS MEMBER_VALUE,
            CASE
                WHEN TYPEOF(v.value) IN ('INTEGER','DECIMAL','VARCHAR')
                 AND REGEXP_LIKE(v.value::VARCHAR, '^[0-9]+$')
                    THEN TRIM(v.value::VARCHAR)
            END AS VALUE_ID
        FROM fields f,
             LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_VALUE:"ValuesListIds")) v
        WHERE COALESCE(IS_ARRAY(f.FIELD_VALUE:"ValuesListIds"), FALSE)
    ),
    value_lookup AS (
        SELECT
            TRIM(VALUEID::VARCHAR) AS VALUE_ID,
            COUNT(*) AS MATCH_COUNT,
            IFF(COUNT(*) = 1, MAX(VALUENAME::VARCHAR), NULL) AS VALUE_NAME
        FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUES
        WHERE TRIM(VALUEID::VARCHAR) IN (
            SELECT VALUE_ID
            FROM value_members
            WHERE VALUE_ID IS NOT NULL
        )
        GROUP BY TRIM(VALUEID::VARCHAR)
    ),
    resolved_value_members AS (
        SELECT
            m.*,
            v.VALUE_NAME,
            CASE
                WHEN m.VALUE_ID IS NULL
                    THEN 'INVALID_VALUE_ID'
                WHEN v.MATCH_COUNT > 1
                    THEN 'DUPLICATE_LOOKUP_ID'
                WHEN v.VALUE_ID IS NULL
                    THEN 'VALUE_NOT_FOUND'
                ELSE 'MATCHED'
            END AS LOOKUP_STATUS
        FROM value_members m
        LEFT JOIN value_lookup v
          ON v.VALUE_ID = m.VALUE_ID
    ),
    resolved_values AS (
        SELECT
            RECORD_ID,
            SQL_KEY,
            COUNT(*) AS MEMBER_COUNT,
            ARRAY_AGG(
                OBJECT_CONSTRUCT_KEEP_NULL(
                    'ValueId', VALUE_ID,
                    'ValueName', VALUE_NAME,
                    'LookupStatus', LOOKUP_STATUS
                )
            ) WITHIN GROUP (ORDER BY MEMBER_INDEX) AS ITEMS,
            SUM(
                IFF(
                    LOOKUP_STATUS IN ('INVALID_VALUE_ID','DUPLICATE_LOOKUP_ID'),
                    1, 0
                )
            ) AS BLOCKING_MEMBERS
        FROM resolved_value_members
        GROUP BY RECORD_ID, SQL_KEY
    ),

    -- Group-list lookup/enrichment.
    group_members AS (
        SELECT
            f.RECORD_ID,
            f.SQL_KEY,
            g.index AS MEMBER_INDEX,
            g.value AS MEMBER_VALUE,
            CASE
                WHEN TYPEOF(g.value) = 'OBJECT' THEN
                    TRY_TO_NUMBER(
                        COALESCE(
                            g.value:"Id"::VARCHAR,
                            g.value:"GroupId"::VARCHAR,
                            g.value:"GROUP_ID"::VARCHAR
                        ),
                        38, 0
                    )
                WHEN TYPEOF(g.value) IN ('INTEGER','DECIMAL','VARCHAR') THEN
                    TRY_TO_NUMBER(g.value::VARCHAR, 38, 0)
            END AS GROUP_ID
        FROM fields f,
             LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_VALUE:"GroupList")) g
        WHERE COALESCE(IS_ARRAY(f.FIELD_VALUE:"GroupList"), FALSE)
    ),
    group_lookup AS (
        SELECT
            GROUP_ID,
            COUNT(*) AS MATCH_COUNT,
            IFF(COUNT(*) = 1, MAX(GROUP_NAME::VARCHAR), NULL) AS GROUP_NAME,
            IFF(COUNT(*) = 1, MAX(GUID::VARCHAR), NULL)       AS GUID
        FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_GROUP
        WHERE GROUP_ID IN (
            SELECT GROUP_ID
            FROM group_members
            WHERE GROUP_ID IS NOT NULL
        )
        GROUP BY GROUP_ID
    ),
    resolved_group_members AS (
        SELECT
            m.*,
            g.GROUP_NAME,
            g.GUID,
            CASE
                WHEN m.GROUP_ID IS NULL
                    THEN 'INVALID_GROUP_ID'
                WHEN g.MATCH_COUNT > 1
                    THEN 'DUPLICATE_LOOKUP_ID'
                WHEN g.GROUP_ID IS NULL
                    THEN 'GROUP_NOT_FOUND'
                ELSE 'MATCHED'
            END AS LOOKUP_STATUS
        FROM group_members m
        LEFT JOIN group_lookup g
          ON g.GROUP_ID = m.GROUP_ID
    ),
    resolved_groups AS (
        SELECT
            RECORD_ID,
            SQL_KEY,
            COUNT(*) AS MEMBER_COUNT,
            ARRAY_AGG(
                OBJECT_CONSTRUCT_KEEP_NULL(
                    'GroupId', GROUP_ID,
                    'GroupName', GROUP_NAME,
                    'Guid', GUID,
                    'LookupStatus', LOOKUP_STATUS
                )
            ) WITHIN GROUP (ORDER BY MEMBER_INDEX) AS ITEMS,
            SUM(
                IFF(
                    LOOKUP_STATUS IN ('INVALID_GROUP_ID','DUPLICATE_LOOKUP_ID'),
                    1, 0
                )
            ) AS BLOCKING_MEMBERS
        FROM resolved_group_members
        GROUP BY RECORD_ID, SQL_KEY
    ),

    -- Preserve original field JSON; add/refresh enrichment keys.
    enriched_fields AS (
        SELECT
            f.RECORD_ID,
            f.SQL_KEY,
            CASE
                WHEN COALESCE(IS_ARRAY(f.FIELD_VALUE:"GroupList"), FALSE)
                 AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"GroupList")), 0) > 0
                 AND rg.ITEMS IS NOT NULL
                 AND rg.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"GroupList"))
                 AND COALESCE(rg.BLOCKING_MEMBERS, 0) = 0
                    THEN TO_VARIANT(
                        OBJECT_INSERT(
                            AS_OBJECT(
                                CASE
                                    WHEN COALESCE(IS_ARRAY(f.FIELD_VALUE:"ValuesListIds"), FALSE)
                                     AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"ValuesListIds")), 0) > 0
                                     AND rv.ITEMS IS NOT NULL
                                     AND rv.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"ValuesListIds"))
                                     AND COALESCE(rv.BLOCKING_MEMBERS, 0) = 0
                                        THEN TO_VARIANT(
                                            OBJECT_INSERT(
                                                AS_OBJECT(
                                                    CASE
                                                        WHEN COALESCE(IS_ARRAY(f.FIELD_VALUE:"UserList"), FALSE)
                                                         AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList")), 0) > 0
                                                         AND ul.ENRICHED_USER_LIST IS NOT NULL
                                                         AND ul.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList"))
                                                         AND COALESCE(ul.BLOCKING_MEMBERS, 0) = 0
                                                            THEN TO_VARIANT(
                                                                OBJECT_INSERT(
                                                                    AS_OBJECT(f.FIELD_VALUE),
                                                                    'UserList',
                                                                    ul.ENRICHED_USER_LIST,
                                                                    TRUE
                                                                )
                                                            )
                                                        ELSE f.FIELD_VALUE
                                                    END
                                                ),
                                                'ResolvedValues',
                                                rv.ITEMS,
                                                TRUE
                                            )
                                        )
                                    ELSE
                                        CASE
                                            WHEN COALESCE(IS_ARRAY(f.FIELD_VALUE:"UserList"), FALSE)
                                             AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList")), 0) > 0
                                             AND ul.ENRICHED_USER_LIST IS NOT NULL
                                             AND ul.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList"))
                                             AND COALESCE(ul.BLOCKING_MEMBERS, 0) = 0
                                                THEN TO_VARIANT(
                                                    OBJECT_INSERT(
                                                        AS_OBJECT(f.FIELD_VALUE),
                                                        'UserList',
                                                        ul.ENRICHED_USER_LIST,
                                                        TRUE
                                                    )
                                                )
                                            ELSE f.FIELD_VALUE
                                        END
                                END
                            ),
                            'ResolvedGroups',
                            rg.ITEMS,
                            TRUE
                        )
                    )
                ELSE
                    CASE
                        WHEN COALESCE(IS_ARRAY(f.FIELD_VALUE:"ValuesListIds"), FALSE)
                         AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"ValuesListIds")), 0) > 0
                         AND rv.ITEMS IS NOT NULL
                         AND rv.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"ValuesListIds"))
                         AND COALESCE(rv.BLOCKING_MEMBERS, 0) = 0
                            THEN TO_VARIANT(
                                OBJECT_INSERT(
                                    AS_OBJECT(
                                        CASE
                                            WHEN COALESCE(IS_ARRAY(f.FIELD_VALUE:"UserList"), FALSE)
                                             AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList")), 0) > 0
                                             AND ul.ENRICHED_USER_LIST IS NOT NULL
                                             AND ul.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList"))
                                             AND COALESCE(ul.BLOCKING_MEMBERS, 0) = 0
                                                THEN TO_VARIANT(
                                                    OBJECT_INSERT(
                                                        AS_OBJECT(f.FIELD_VALUE),
                                                        'UserList',
                                                        ul.ENRICHED_USER_LIST,
                                                        TRUE
                                                    )
                                                )
                                            ELSE f.FIELD_VALUE
                                        END
                                    ),
                                    'ResolvedValues',
                                    rv.ITEMS,
                                    TRUE
                                )
                            )
                        ELSE
                            CASE
                                WHEN COALESCE(IS_ARRAY(f.FIELD_VALUE:"UserList"), FALSE)
                                 AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList")), 0) > 0
                                 AND ul.ENRICHED_USER_LIST IS NOT NULL
                                 AND ul.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList"))
                                 AND COALESCE(ul.BLOCKING_MEMBERS, 0) = 0
                                    THEN TO_VARIANT(
                                        OBJECT_INSERT(
                                            AS_OBJECT(f.FIELD_VALUE),
                                            'UserList',
                                            ul.ENRICHED_USER_LIST,
                                            TRUE
                                        )
                                    )
                                ELSE f.FIELD_VALUE
                            END
                    END
            END AS FIELD_VALUE,
            f.INVALID_USERLIST_SHAPE
              + f.INVALID_VALUESLIST_SHAPE
              + f.INVALID_GROUPLIST_SHAPE
              + IFF(
                    COALESCE(IS_ARRAY(f.FIELD_VALUE:"UserList"), FALSE)
                    AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList")), 0) > 0
                    AND (
                        ul.ENRICHED_USER_LIST IS NULL
                        OR ul.MEMBER_COUNT <> ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList"))
                        OR COALESCE(ul.BLOCKING_MEMBERS, 0) > 0
                    ),
                    1, 0
                )
              + IFF(
                    COALESCE(IS_ARRAY(f.FIELD_VALUE:"ValuesListIds"), FALSE)
                    AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"ValuesListIds")), 0) > 0
                    AND (
                        rv.ITEMS IS NULL
                        OR rv.MEMBER_COUNT <> ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"ValuesListIds"))
                        OR COALESCE(rv.BLOCKING_MEMBERS, 0) > 0
                    ),
                    1, 0
                )
              + IFF(
                    COALESCE(IS_ARRAY(f.FIELD_VALUE:"GroupList"), FALSE)
                    AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"GroupList")), 0) > 0
                    AND (
                        rg.ITEMS IS NULL
                        OR rg.MEMBER_COUNT <> ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"GroupList"))
                        OR COALESCE(rg.BLOCKING_MEMBERS, 0) > 0
                    ),
                    1, 0
                ) AS BLOCKED_FIELD
        FROM fields f
        LEFT JOIN user_lists ul
          ON ul.RECORD_ID = f.RECORD_ID
         AND ul.SQL_KEY   = f.SQL_KEY
        LEFT JOIN resolved_values rv
          ON rv.RECORD_ID = f.RECORD_ID
         AND rv.SQL_KEY   = f.SQL_KEY
        LEFT JOIN resolved_groups rg
          ON rg.RECORD_ID = f.RECORD_ID
         AND rg.SQL_KEY   = f.SQL_KEY
    ),
    rebuilt AS (
        SELECT
            RECORD_ID,
            OBJECT_AGG(
                SQL_KEY,
                COALESCE(FIELD_VALUE, PARSE_JSON('null'))
            ) AS ENRICHED_CURATED_JSON,
            SUM(BLOCKED_FIELD) AS BLOCKED_FIELDS,
            COUNT_IF(
                COALESCE(IS_ARRAY(FIELD_VALUE:"UserList"), FALSE)
                AND COALESCE(ARRAY_SIZE(AS_ARRAY(FIELD_VALUE:"UserList")), 0) > 0
            ) AS USERLIST_FIELDS,
            COUNT_IF(
                COALESCE(IS_ARRAY(FIELD_VALUE:"ValuesListIds"), FALSE)
                AND COALESCE(ARRAY_SIZE(AS_ARRAY(FIELD_VALUE:"ValuesListIds")), 0) > 0
            ) AS VALUESLIST_FIELDS,
            COUNT_IF(
                COALESCE(IS_ARRAY(FIELD_VALUE:"GroupList"), FALSE)
                AND COALESCE(ARRAY_SIZE(AS_ARRAY(FIELD_VALUE:"GroupList")), 0) > 0
            ) AS GROUPLIST_FIELDS
        FROM enriched_fields
        GROUP BY RECORD_ID
    )
    SELECT
        RECORD_ID,
        ENRICHED_CURATED_JSON
    FROM rebuilt
    WHERE (USERLIST_FIELDS + VALUESLIST_FIELDS + GROUPLIST_FIELDS) > 0
      AND BLOCKED_FIELDS = 0
) AS src
WHERE IFF(
          TYPEOF(tgt.RAW_DATA) = 'ARRAY',
          tgt.RAW_DATA[0],
          tgt.RAW_DATA
      ):"RequestedObject":"Id"::NUMBER = src.RECORD_ID
  AND tgt.CONTENT_ID::VARCHAR = src.RECORD_ID::VARCHAR
  AND TYPEOF(tgt.CURATED_JSON) = 'OBJECT';
