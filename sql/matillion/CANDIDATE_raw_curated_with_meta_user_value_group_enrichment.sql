-- REVIEW CANDIDATE: ONE UPDATE raw -> CURATED_JSON + User/Value/Group enrichment.
-- Date: 2026-10-01.
-- Supersedes the post-CURATED enrichment file for the raw-load Matillion component.
--
-- IMPORTANT: this is the raw-load statement. It works when CURATED_JSON is NULL.
-- It preserves the previously accepted raw -> curated behavior:
--   * FIELD_ID -> ARCHER_META_FIELD.SQL_FIELD_NAME
--   * source-side TRY_TO_NUMBER FIELD_ID safety
--   * existing type conversion and nested extraction
--   * JSON-null key preservation
--   * RequestedObject.Id -> CONTENT_ID
--   * CURATED_JSON IS NULL pending-row guards
--
-- It then enriches the newly-built candidate CURATED_JSON:
--   * UserList[].Id   -> ARCHER_META_USER.ARCHER_USER_ID
--   * ValuesListIds[] -> ARCHER_META_VALUE.SELECT_VALUE_ID / SELECT_VALUE_NAME
--   * GroupList[]     -> ARCHER_META_GROUP.GROUP_ID / GROUP_NAME
--
-- If enrichment is malformed/ambiguous for one record, that record still gets
-- the un-enriched raw->curated JSON, matching the existing fail-safe behavior.
--
UPDATE ${jv_raw_table_name} AS tgt
SET
    tgt.CURATED_JSON = src.CURATED_JSON,
    tgt.CONTENT_ID   = src.CONTENT_ID
FROM (
    SELECT
        curated.REQ_OBJ_ID AS RECORD_ID,
        curated.CURATED_JSON,
        curated.REQ_OBJ_ID::string AS CONTENT_ID
    FROM (
        WITH norm AS (
            SELECT
                IFF(
                    TYPEOF(r.RAW_DATA) = 'ARRAY',
                    r.RAW_DATA[0],
                    r.RAW_DATA
                ) AS obj
            FROM ${jv_raw_table_name} r
            WHERE TYPEOF(r.RAW_DATA) IN ('ARRAY', 'OBJECT')
              AND r.CURATED_JSON IS NULL
        ),
        flat AS (
            SELECT
                n.obj:"RequestedObject":"Id"::NUMBER      AS REQ_OBJ_ID,
                n.obj:"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID,
                fc.key::STRING                              AS FIELD_ID,
                fc.value:"Type"::NUMBER                    AS TYPE_ID,
                fc.value:"Value"                           AS V
            FROM norm n,
                 LATERAL FLATTEN(
                     input => n.obj:"RequestedObject":"FieldContents"
                 ) fc
        ),
        mapped AS (
            SELECT
                f.*,
                COALESCE(amf.SQL_FIELD_NAME, 'FIELD_' || f.FIELD_ID) AS SQL_KEY,
                ROW_NUMBER() OVER (
                    PARTITION BY
                        f.REQ_OBJ_ID,
                        COALESCE(amf.SQL_FIELD_NAME, 'FIELD_' || f.FIELD_ID)
                    ORDER BY
                        CASE
                            WHEN COALESCE(amf.KEY_FIELD, 'N') = 'Y' THEN 0
                            ELSE 1
                        END,
                        CASE
                            WHEN amf.LEVEL_ID IS NOT NULL
                             AND amf.LEVEL_ID = f.LEVEL_ID THEN 0
                            ELSE 1
                        END,
                        TRY_TO_NUMBER(f.FIELD_ID)
                ) AS rn
            FROM flat f
            LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
                ON TO_NUMBER(amf.FIELD_ID) = TRY_TO_NUMBER(f.FIELD_ID)
        ),
        typed AS (
            SELECT
                REQ_OBJ_ID,
                LEVEL_ID,
                SQL_KEY,
                CASE TYPE_ID
                    WHEN 1  THEN TO_VARIANT(NULLIF(V::STRING, ''))
                    WHEN 2  THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
                    WHEN 3  THEN TO_VARIANT(TRY_TO_DATE(NULLIF(V::STRING, '')))
                    WHEN 6  THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
                    WHEN 20 THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
                    WHEN 21 THEN TO_VARIANT(TRY_TO_TIMESTAMP_NTZ(NULLIF(V::STRING, '')))
                    WHEN 22 THEN TO_VARIANT(TRY_TO_TIMESTAMP_NTZ(NULLIF(V::STRING, '')))
                    WHEN 4  THEN TO_VARIANT(V)
                    WHEN 8  THEN TO_VARIANT(V)
                    WHEN 9  THEN TO_VARIANT(V)
                    WHEN 11 THEN TO_VARIANT(V)
                    WHEN 23 THEN TO_VARIANT(V)
                    ELSE TO_VARIANT(V)
                END AS TYPED_VALUE
            FROM mapped
            WHERE rn = 1
        ),
        nested_flat AS (
            SELECT
                n.obj:"RequestedObject":"Id"::NUMBER       AS REQ_OBJ_ID,
                n.obj:"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID,
                f.key::STRING                                AS FIELD_ID,
                f.path                                       AS JSON_PATH,
                f.value                                      AS V
            FROM norm n,
                 LATERAL FLATTEN(
                     input     => n.obj:"RequestedObject":"FieldContents",
                     RECURSIVE => TRUE
                 ) f
            WHERE f.key IS NOT NULL
              AND f.path LIKE '%FieldContents%'
              AND f.key NOT LIKE 'FieldContents'  -- skip the container itself
        ),
        nested_mapped AS (
            SELECT
                nf.REQ_OBJ_ID,
                nf.LEVEL_ID,
                COALESCE(amf.SQL_FIELD_NAME, 'FIELD_' || nf.FIELD_ID) AS SQL_KEY,
                nf.V
            FROM nested_flat nf
            LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
                ON TO_NUMBER(amf.FIELD_ID) = TRY_TO_NUMBER(nf.FIELD_ID)
            WHERE amf.SQL_FIELD_NAME IS NOT NULL
        ),
        nested_typed AS (
            SELECT
                REQ_OBJ_ID,
                NULL AS LEVEL_ID,
                SQL_KEY,
                TO_VARIANT(
                    CASE TYPEOF(V)
                        WHEN 'OBJECT' THEN V:"Value"
                        WHEN 'ARRAY'  THEN V
                        ELSE V
                    END
                ) AS TYPED_VALUE
            FROM nested_mapped
        ),
        combined AS (
            SELECT REQ_OBJ_ID, LEVEL_ID, SQL_KEY, TYPED_VALUE
            FROM typed

            UNION ALL

            SELECT REQ_OBJ_ID, NULL, SQL_KEY, TYPED_VALUE
            FROM nested_typed
        ),
        curated AS (
            SELECT
                REQ_OBJ_ID,
                OBJECT_AGG(SQL_KEY, COALESCE(TYPED_VALUE, PARSE_JSON('null'))) AS CURATED_JSON,
                OBJECT_AGG(SQL_KEY, TYPED_VALUE) AS ID_SOURCE_JSON
            FROM combined
            GROUP BY REQ_OBJ_ID
        ),
curated_fields AS (
            SELECT
                c.REQ_OBJ_ID,
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
            FROM curated c,
                 LATERAL FLATTEN(INPUT => AS_OBJECT(c.CURATED_JSON)) f
        ),

        -- UserList[].Id -> ARCHER_META_USER.ARCHER_USER_ID
        user_members AS (
            SELECT
                cf.REQ_OBJ_ID,
                cf.SQL_KEY,
                u.index AS MEMBER_INDEX,
                u.value AS MEMBER_VALUE,
                CASE
                    WHEN TYPEOF(u.value:"Id") IN ('INTEGER', 'DECIMAL', 'VARCHAR')
                     AND REGEXP_LIKE(u.value:"Id"::VARCHAR, '^[0-9]+$')
                        THEN TRY_TO_NUMBER(u.value:"Id"::VARCHAR, 38, 0)
                END AS ARCHER_USER_ID
            FROM curated_fields cf,
                 LATERAL FLATTEN(INPUT => AS_ARRAY(cf.FIELD_VALUE:"UserList")) u
            WHERE COALESCE(IS_ARRAY(cf.FIELD_VALUE:"UserList"), FALSE)
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
                um.*,
                ul.EEID,
                ul.FIRST_NAME,
                ul.MIDDLE_NAME,
                ul.LAST_NAME,
                CASE
                    WHEN NOT COALESCE(IS_OBJECT(um.MEMBER_VALUE), FALSE)
                        THEN 'INVALID_MEMBER_OBJECT'
                    WHEN um.MEMBER_VALUE:"ResolvedUser" IS NOT NULL
                     AND NOT COALESCE(
                         um.MEMBER_VALUE:"ResolvedUser":"ContractVersion"::VARCHAR
                             = 'archer-meta-user-v1',
                         FALSE
                     )
                        THEN 'ENRICHMENT_KEY_COLLISION'
                    WHEN um.ARCHER_USER_ID IS NULL
                        THEN 'INVALID_USER_ID'
                    WHEN ul.MATCH_COUNT > 1
                        THEN 'DUPLICATE_LOOKUP_ID'
                    WHEN ul.ARCHER_USER_ID IS NULL
                        THEN 'USER_NOT_FOUND'
                    WHEN NULLIF(TRIM(ul.EEID), '') IS NULL
                        THEN 'MATCHED_MISSING_EEID'
                    ELSE 'MATCHED'
                END AS LOOKUP_STATUS
            FROM user_members um
            LEFT JOIN user_lookup ul
              ON ul.ARCHER_USER_ID = um.ARCHER_USER_ID
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
        enriched_user_lists AS (
            SELECT
                REQ_OBJ_ID,
                SQL_KEY,
                COUNT(*) AS MEMBER_COUNT,
                ARRAY_AGG(
                    COALESCE(ENRICHED_MEMBER_VALUE, PARSE_JSON('null'))
                ) WITHIN GROUP (ORDER BY MEMBER_INDEX) AS ENRICHED_USER_LIST,
                SUM(BLOCKING_MEMBER) AS BLOCKING_MEMBERS
            FROM enriched_user_members
            GROUP BY REQ_OBJ_ID, SQL_KEY
        ),

        -- ValuesListIds[] -> ARCHER_META_VALUE.SELECT_VALUE_ID / SELECT_VALUE_NAME
        value_members AS (
            SELECT
                cf.REQ_OBJ_ID,
                cf.SQL_KEY,
                v.index AS MEMBER_INDEX,
                CASE
                    WHEN TYPEOF(v.value) IN ('INTEGER', 'DECIMAL', 'VARCHAR')
                     AND REGEXP_LIKE(v.value::VARCHAR, '^[0-9]+$')
                        THEN TRIM(v.value::VARCHAR)
                END AS VALUE_ID
            FROM curated_fields cf,
                 LATERAL FLATTEN(INPUT => AS_ARRAY(cf.FIELD_VALUE:"ValuesListIds")) v
            WHERE COALESCE(IS_ARRAY(cf.FIELD_VALUE:"ValuesListIds"), FALSE)
        ),
        value_lookup AS (
            SELECT
                TRIM(SELECT_VALUE_ID::VARCHAR) AS VALUE_ID,
                COUNT(*) AS MATCH_COUNT,
                IFF(COUNT(*) = 1, MAX(SELECT_VALUE_NAME::VARCHAR), NULL) AS VALUE_NAME
            FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE
            WHERE TRIM(SELECT_VALUE_ID::VARCHAR) IN (
                SELECT VALUE_ID
                FROM value_members
                WHERE VALUE_ID IS NOT NULL
            )
            GROUP BY TRIM(SELECT_VALUE_ID::VARCHAR)
        ),
        resolved_value_members AS (
            SELECT
                vm.*,
                vl.VALUE_NAME,
                CASE
                    WHEN vm.VALUE_ID IS NULL
                        THEN 'INVALID_VALUE_ID'
                    WHEN vl.MATCH_COUNT > 1
                        THEN 'DUPLICATE_LOOKUP_ID'
                    WHEN vl.VALUE_ID IS NULL
                        THEN 'VALUE_NOT_FOUND'
                    ELSE 'MATCHED'
                END AS LOOKUP_STATUS
            FROM value_members vm
            LEFT JOIN value_lookup vl
              ON vl.VALUE_ID = vm.VALUE_ID
        ),
        resolved_values AS (
            SELECT
                REQ_OBJ_ID,
                SQL_KEY,
                COUNT(*) AS MEMBER_COUNT,
                ARRAY_AGG(
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'ValueId', VALUE_ID,
                        'ValueName', VALUE_NAME,
                        'LookupStatus', LOOKUP_STATUS
                    )
                ) WITHIN GROUP (ORDER BY MEMBER_INDEX) AS RESOLVED_VALUES,
                SUM(IFF(
                    LOOKUP_STATUS IN ('INVALID_VALUE_ID', 'DUPLICATE_LOOKUP_ID'),
                    1, 0
                )) AS BLOCKING_MEMBERS
            FROM resolved_value_members
            GROUP BY REQ_OBJ_ID, SQL_KEY
        ),

        -- GroupList[] -> ARCHER_META_GROUP.GROUP_ID / GROUP_NAME
        group_members AS (
            SELECT
                cf.REQ_OBJ_ID,
                cf.SQL_KEY,
                g.index AS MEMBER_INDEX,
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
                    WHEN TYPEOF(g.value) IN ('INTEGER', 'DECIMAL', 'VARCHAR') THEN
                        TRY_TO_NUMBER(g.value::VARCHAR, 38, 0)
                END AS GROUP_ID
            FROM curated_fields cf,
                 LATERAL FLATTEN(INPUT => AS_ARRAY(cf.FIELD_VALUE:"GroupList")) g
            WHERE COALESCE(IS_ARRAY(cf.FIELD_VALUE:"GroupList"), FALSE)
        ),
        group_lookup AS (
            SELECT
                GROUP_ID,
                COUNT(*) AS MATCH_COUNT,
                IFF(COUNT(*) = 1, MAX(GROUP_NAME::VARCHAR), NULL) AS GROUP_NAME
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
                gm.*,
                gl.GROUP_NAME,
                CASE
                    WHEN gm.GROUP_ID IS NULL
                        THEN 'INVALID_GROUP_ID'
                    WHEN gl.MATCH_COUNT > 1
                        THEN 'DUPLICATE_LOOKUP_ID'
                    WHEN gl.GROUP_ID IS NULL
                        THEN 'GROUP_NOT_FOUND'
                    ELSE 'MATCHED'
                END AS LOOKUP_STATUS
            FROM group_members gm
            LEFT JOIN group_lookup gl
              ON gl.GROUP_ID = gm.GROUP_ID
        ),
        resolved_groups AS (
            SELECT
                REQ_OBJ_ID,
                SQL_KEY,
                COUNT(*) AS MEMBER_COUNT,
                ARRAY_AGG(
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'GroupId', GROUP_ID,
                        'GroupName', GROUP_NAME,
                        'LookupStatus', LOOKUP_STATUS
                    )
                ) WITHIN GROUP (ORDER BY MEMBER_INDEX) AS RESOLVED_GROUPS,
                SUM(IFF(
                    LOOKUP_STATUS IN ('INVALID_GROUP_ID', 'DUPLICATE_LOOKUP_ID'),
                    1, 0
                )) AS BLOCKING_MEMBERS
            FROM resolved_group_members
            GROUP BY REQ_OBJ_ID, SQL_KEY
        ),

        -- Stage 1: preserve field JSON and enrich UserList only.
        user_enriched_fields AS (
            SELECT
                cf.REQ_OBJ_ID,
                cf.SQL_KEY,
                CASE
                    WHEN COALESCE(IS_ARRAY(cf.FIELD_VALUE:"UserList"), FALSE)
                     AND COALESCE(ARRAY_SIZE(AS_ARRAY(cf.FIELD_VALUE:"UserList")), 0) > 0
                     AND eul.ENRICHED_USER_LIST IS NOT NULL
                     AND eul.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(cf.FIELD_VALUE:"UserList"))
                     AND COALESCE(eul.BLOCKING_MEMBERS, 0) = 0
                        THEN TO_VARIANT(
                            OBJECT_INSERT(
                                AS_OBJECT(cf.FIELD_VALUE),
                                'UserList',
                                eul.ENRICHED_USER_LIST,
                                TRUE
                            )
                        )
                    ELSE cf.FIELD_VALUE
                END AS FIELD_VALUE,
                cf.INVALID_USERLIST_SHAPE
                + cf.INVALID_VALUESLIST_SHAPE
                + cf.INVALID_GROUPLIST_SHAPE
                + IFF(
                    COALESCE(IS_ARRAY(cf.FIELD_VALUE:"UserList"), FALSE)
                    AND COALESCE(ARRAY_SIZE(AS_ARRAY(cf.FIELD_VALUE:"UserList")), 0) > 0
                    AND (
                        eul.ENRICHED_USER_LIST IS NULL
                        OR eul.MEMBER_COUNT <> ARRAY_SIZE(AS_ARRAY(cf.FIELD_VALUE:"UserList"))
                        OR COALESCE(eul.BLOCKING_MEMBERS, 0) > 0
                    ),
                    1, 0
                ) AS BLOCKED_FIELD
            FROM curated_fields cf
            LEFT JOIN enriched_user_lists eul
              ON eul.REQ_OBJ_ID = cf.REQ_OBJ_ID
             AND eul.SQL_KEY    = cf.SQL_KEY
        ),

        -- Stage 2: add resolved values without replacing ValuesListIds.
        value_enriched_fields AS (
            SELECT
                uf.REQ_OBJ_ID,
                uf.SQL_KEY,
                CASE
                    WHEN COALESCE(IS_ARRAY(uf.FIELD_VALUE:"ValuesListIds"), FALSE)
                     AND COALESCE(ARRAY_SIZE(AS_ARRAY(uf.FIELD_VALUE:"ValuesListIds")), 0) > 0
                     AND rv.RESOLVED_VALUES IS NOT NULL
                     AND rv.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(uf.FIELD_VALUE:"ValuesListIds"))
                     AND COALESCE(rv.BLOCKING_MEMBERS, 0) = 0
                        THEN TO_VARIANT(
                            OBJECT_INSERT(
                                AS_OBJECT(uf.FIELD_VALUE),
                                'ResolvedValues',
                                rv.RESOLVED_VALUES,
                                TRUE
                            )
                        )
                    ELSE uf.FIELD_VALUE
                END AS FIELD_VALUE,
                uf.BLOCKED_FIELD
                + IFF(
                    COALESCE(IS_ARRAY(uf.FIELD_VALUE:"ValuesListIds"), FALSE)
                    AND COALESCE(ARRAY_SIZE(AS_ARRAY(uf.FIELD_VALUE:"ValuesListIds")), 0) > 0
                    AND (
                        rv.RESOLVED_VALUES IS NULL
                        OR rv.MEMBER_COUNT <> ARRAY_SIZE(AS_ARRAY(uf.FIELD_VALUE:"ValuesListIds"))
                        OR COALESCE(rv.BLOCKING_MEMBERS, 0) > 0
                    ),
                    1, 0
                ) AS BLOCKED_FIELD
            FROM user_enriched_fields uf
            LEFT JOIN resolved_values rv
              ON rv.REQ_OBJ_ID = uf.REQ_OBJ_ID
             AND rv.SQL_KEY    = uf.SQL_KEY
        ),

        -- Stage 3: add resolved groups without replacing GroupList.
        enriched_fields AS (
            SELECT
                vf.REQ_OBJ_ID,
                vf.SQL_KEY,
                CASE
                    WHEN COALESCE(IS_ARRAY(vf.FIELD_VALUE:"GroupList"), FALSE)
                     AND COALESCE(ARRAY_SIZE(AS_ARRAY(vf.FIELD_VALUE:"GroupList")), 0) > 0
                     AND rg.RESOLVED_GROUPS IS NOT NULL
                     AND rg.MEMBER_COUNT = ARRAY_SIZE(AS_ARRAY(vf.FIELD_VALUE:"GroupList"))
                     AND COALESCE(rg.BLOCKING_MEMBERS, 0) = 0
                        THEN TO_VARIANT(
                            OBJECT_INSERT(
                                AS_OBJECT(vf.FIELD_VALUE),
                                'ResolvedGroups',
                                rg.RESOLVED_GROUPS,
                                TRUE
                            )
                        )
                    ELSE vf.FIELD_VALUE
                END AS FIELD_VALUE,
                vf.BLOCKED_FIELD
                + IFF(
                    COALESCE(IS_ARRAY(vf.FIELD_VALUE:"GroupList"), FALSE)
                    AND COALESCE(ARRAY_SIZE(AS_ARRAY(vf.FIELD_VALUE:"GroupList")), 0) > 0
                    AND (
                        rg.RESOLVED_GROUPS IS NULL
                        OR rg.MEMBER_COUNT <> ARRAY_SIZE(AS_ARRAY(vf.FIELD_VALUE:"GroupList"))
                        OR COALESCE(rg.BLOCKING_MEMBERS, 0) > 0
                    ),
                    1, 0
                ) AS BLOCKED_FIELD
            FROM value_enriched_fields vf
            LEFT JOIN resolved_groups rg
              ON rg.REQ_OBJ_ID = vf.REQ_OBJ_ID
             AND rg.SQL_KEY    = vf.SQL_KEY
        ),

        rebuilt_curated AS (
            SELECT
                REQ_OBJ_ID,
                OBJECT_AGG(
                    SQL_KEY,
                    COALESCE(FIELD_VALUE, PARSE_JSON('null'))
                ) AS ENRICHED_CURATED_JSON,
                SUM(BLOCKED_FIELD) AS BLOCKED_FIELDS
            FROM enriched_fields
            GROUP BY REQ_OBJ_ID
        ),
        final_curated AS (
            SELECT
                c.REQ_OBJ_ID,
                IFF(
                    COALESCE(rc.BLOCKED_FIELDS, 0) = 0,
                    COALESCE(rc.ENRICHED_CURATED_JSON, c.CURATED_JSON),
                    c.CURATED_JSON
                ) AS CURATED_JSON,
                c.ID_SOURCE_JSON
            FROM curated c
            LEFT JOIN rebuilt_curated rc
              ON rc.REQ_OBJ_ID = c.REQ_OBJ_ID
        )
        SELECT
            fc.REQ_OBJ_ID,
            fc.CURATED_JSON,
            fc.ID_SOURCE_JSON
        FROM final_curated fc
    ) curated
) AS src
WHERE IFF(
          TYPEOF(tgt.RAW_DATA) = 'ARRAY',
          tgt.RAW_DATA[0],
          tgt.RAW_DATA
      ):"RequestedObject":"Id"::NUMBER = src.RECORD_ID
  AND tgt.CURATED_JSON IS NULL;

