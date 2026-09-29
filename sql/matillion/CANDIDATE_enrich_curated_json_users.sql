-- OSCAL / Archer CURATED_JSON Meta User enrichment
-- Date: 2026-09-29
-- CANDIDATE ONLY: writes CURATED_JSON when executed. Review in DEV before use.
--
-- Intended Matillion placement:
--   1) Existing raw -> CURATED_JSON conversion runs first.
--   2) This enrichment runs next, before OSCAL mapping.
--
-- UserList[].Id -> ARCHER_META_USER.ARCHER_USER_ID
-- Original Id and permission flags are preserved.
-- GroupList is NOT changed until an authoritative Meta Group lookup is available.
-- Unmatched users are preserved with LookupStatus = USER_NOT_FOUND.
-- Existing ResolvedUser values from another contract block that record from update.

UPDATE ${jv_raw_table_name} AS tgt
SET tgt.CURATED_JSON = src.ENRICHED_CURATED_JSON
FROM (
    WITH source_rows AS (
        SELECT
            IFF(
                TYPEOF(r.RAW_DATA) = 'ARRAY',
                r.RAW_DATA[0],
                r.RAW_DATA
            ):"RequestedObject":"Id"::NUMBER AS RECORD_ID,
            r.CURATED_JSON
        FROM ${jv_raw_table_name} r
        WHERE TYPEOF(r.CURATED_JSON) = 'OBJECT'
    ),
    fields AS (
        SELECT
            s.RECORD_ID,
            f.key::STRING AS SQL_KEY,
            f.value       AS FIELD_VALUE
        FROM source_rows s,
             LATERAL FLATTEN(INPUT => AS_OBJECT(s.CURATED_JSON)) f
        WHERE s.RECORD_ID IS NOT NULL
    ),
    user_members AS (
        SELECT
            f.RECORD_ID,
            f.SQL_KEY,
            u.index AS MEMBER_INDEX,
            u.value AS MEMBER_VALUE,
            CASE
                WHEN TYPEOF(u.value:"Id") IN ('INTEGER', 'DECIMAL', 'VARCHAR')
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
    resolved_members AS (
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
    enriched_members AS (
        SELECT
            r.*,
            CASE
                WHEN LOOKUP_STATUS IN ('INVALID_MEMBER_OBJECT', 'ENRICHMENT_KEY_COLLISION')
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
                LOOKUP_STATUS IN ('INVALID_MEMBER_OBJECT', 'ENRICHMENT_KEY_COLLISION'),
                1, 0
            ) AS BLOCKING_MEMBER
        FROM resolved_members r
    ),
    user_lists AS (
        SELECT
            RECORD_ID,
            SQL_KEY,
            ARRAY_AGG(
                COALESCE(ENRICHED_MEMBER_VALUE, PARSE_JSON('null'))
            ) WITHIN GROUP (ORDER BY MEMBER_INDEX) AS ENRICHED_USER_LIST,
            SUM(BLOCKING_MEMBER) AS BLOCKING_MEMBERS
        FROM enriched_members
        GROUP BY RECORD_ID, SQL_KEY
    ),
    enriched_fields AS (
        SELECT
            f.RECORD_ID,
            f.SQL_KEY,
            CASE
                WHEN COALESCE(IS_ARRAY(f.FIELD_VALUE:"UserList"), FALSE)
                 AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.FIELD_VALUE:"UserList")), 0) > 0
                 AND ul.ENRICHED_USER_LIST IS NOT NULL
                    THEN TO_VARIANT(
                        OBJECT_INSERT(
                            AS_OBJECT(f.FIELD_VALUE),
                            'UserList',
                            ul.ENRICHED_USER_LIST,
                            TRUE
                        )
                    )
                ELSE f.FIELD_VALUE
            END AS FIELD_VALUE,
            COALESCE(ul.BLOCKING_MEMBERS, 0) AS BLOCKING_MEMBERS
        FROM fields f
        LEFT JOIN user_lists ul
            ON ul.RECORD_ID = f.RECORD_ID
           AND ul.SQL_KEY   = f.SQL_KEY
    ),
    rebuilt AS (
        SELECT
            RECORD_ID,
            OBJECT_AGG(
                SQL_KEY,
                COALESCE(FIELD_VALUE, PARSE_JSON('null'))
            ) AS ENRICHED_CURATED_JSON,
            SUM(BLOCKING_MEMBERS) AS BLOCKING_MEMBERS,
            COUNT_IF(
                COALESCE(IS_ARRAY(FIELD_VALUE:"UserList"), FALSE)
                AND COALESCE(ARRAY_SIZE(AS_ARRAY(FIELD_VALUE:"UserList")), 0) > 0
            ) AS USERLIST_FIELDS
        FROM enriched_fields
        GROUP BY RECORD_ID
    )
    SELECT
        RECORD_ID,
        ENRICHED_CURATED_JSON
    FROM rebuilt
    WHERE USERLIST_FIELDS > 0
      AND BLOCKING_MEMBERS = 0
) AS src
WHERE IFF(
          TYPEOF(tgt.RAW_DATA) = 'ARRAY',
          tgt.RAW_DATA[0],
          tgt.RAW_DATA
      ):"RequestedObject":"Id"::NUMBER = src.RECORD_ID
  AND TYPEOF(tgt.CURATED_JSON) = 'OBJECT';
