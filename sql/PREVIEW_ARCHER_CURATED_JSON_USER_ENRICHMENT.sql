-- OSCAL: build proposed user-enriched CURATED_JSON for ONE eligible Dev record.
-- Date: 2026-09-29. Baseline: ca77c8648c74fbc87806c34ecd671797d1755119.
-- READ ONLY: one SELECT. No UPDATE, temporary tables, or notebook execution.
-- This is actual JSON enrichment logic, not another column-discovery query.
--
-- Verified source member path: <field>.UserList[].Id (case-sensitive).
-- Lookup: ARCHER_META_USER.ARCHER_USER_ID. GroupList[].Id is a separate namespace.
-- New proposed member key: ResolvedUser. Original Id, flags and arrays are retained.
-- ResolvedUser contains a version marker, lookup status, EEID and approved name fields.
-- No Meta Group lookup is assumed; all group content remains unchanged.
-- Existing field-name and select-value representations remain unchanged.
--
-- Automatically selects the lowest text RequestedObject.Id with a populated UserList,
-- one source row, object CURATED_JSON, and matching stored CONTENT_ID.
-- Multi-object RAW_DATA arrays, duplicate records, and differing Content IDs are NOT
-- eligible for this bounded preview. It does not certify excluded rows or nested paths.
-- No source/user IDs or personal values are embedded in the published SQL.
-- Keep output private: it contains source payloads and resolved person attributes.
-- Current lookup snapshot only; this does not reconstruct historical identities.
-- Do not turn this into a whole-table UPDATE before reviewing the result and scope.

WITH source_objects AS (
    SELECT CONTENT_ID::VARCHAR AS STORED_CONTENT_ID, CURATED_JSON,
           CASE WHEN TYPEOF(RAW_DATA) = 'OBJECT' THEN RAW_DATA
                WHEN TYPEOF(RAW_DATA) = 'ARRAY' AND ARRAY_SIZE(RAW_DATA) = 1
                    THEN RAW_DATA[0]
           END AS RAW_OBJECT
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
), source_records AS (
    SELECT STORED_CONTENT_ID, CURATED_JSON,
           RAW_OBJECT:"RequestedObject":"Id"::VARCHAR AS SOURCE_CONTENT_ID
    FROM source_objects
), counted_records AS (
    SELECT *, COUNT(*) OVER (PARTITION BY SOURCE_CONTENT_ID) AS SOURCE_ROWS
    FROM source_records
), sample_choice AS (
    SELECT MIN(r.SOURCE_CONTENT_ID) AS SOURCE_CONTENT_ID
    FROM counted_records r, LATERAL FLATTEN(INPUT => AS_OBJECT(r.CURATED_JSON)) f
    WHERE r.SOURCE_ROWS = 1
      AND r.SOURCE_CONTENT_ID = r.STORED_CONTENT_ID
      AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.VALUE:"UserList")), 0) > 0
), sample_record AS (
    SELECT r.*
    FROM counted_records r
    JOIN sample_choice s ON s.SOURCE_CONTENT_ID = r.SOURCE_CONTENT_ID
), fields AS (
    SELECT r.SOURCE_CONTENT_ID, f.KEY::VARCHAR AS SOURCE_FIELD_NAME,
           f.VALUE AS BEFORE_FIELD,
           ARRAY_SIZE(AS_ARRAY(f.VALUE:"UserList")) AS USER_ARRAY_SIZE,
           ARRAY_SIZE(AS_ARRAY(f.VALUE:"GroupList")) AS GROUP_ARRAY_SIZE
    FROM sample_record r, LATERAL FLATTEN(INPUT => AS_OBJECT(r.CURATED_JSON)) f
), user_members AS (
    SELECT f.SOURCE_CONTENT_ID, f.SOURCE_FIELD_NAME, u.INDEX AS MEMBER_INDEX,
           u.VALUE AS BEFORE_MEMBER,
           CASE WHEN TYPEOF(u.VALUE:"Id") IN ('INTEGER', 'DECIMAL', 'VARCHAR')
                     AND REGEXP_LIKE(u.VALUE:"Id"::VARCHAR, '^[0-9]+$')
                THEN TRY_TO_NUMBER(u.VALUE:"Id"::VARCHAR, 38, 0)
           END AS LOOKUP_USER_ID
    FROM fields f, LATERAL FLATTEN(INPUT => AS_ARRAY(f.BEFORE_FIELD:"UserList")) u
), user_lookup AS (
    -- MAX is used only for a singleton match; duplicate IDs never choose a winner.
    SELECT ARCHER_USER_ID, COUNT(*) AS MATCH_COUNT,
           IFF(COUNT(*) = 1, MAX(EEID), NULL) AS EEID,
           IFF(COUNT(*) = 1, MAX(FIRST_NAME), NULL) AS FIRST_NAME,
           IFF(COUNT(*) = 1, MAX(MIDDLE_NAME), NULL) AS MIDDLE_NAME,
           IFF(COUNT(*) = 1, MAX(LAST_NAME), NULL) AS LAST_NAME
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER
    WHERE ARCHER_USER_ID IN (SELECT LOOKUP_USER_ID FROM user_members)
    GROUP BY ARCHER_USER_ID
), resolved AS (
    SELECT m.*, u.EEID, u.FIRST_NAME, u.MIDDLE_NAME, u.LAST_NAME,
           CASE
             WHEN NOT COALESCE(IS_OBJECT(m.BEFORE_MEMBER), FALSE)
                 THEN 'INVALID_MEMBER_OBJECT'
             WHEN m.BEFORE_MEMBER:"ResolvedUser" IS NOT NULL
                  AND NOT COALESCE(
                      m.BEFORE_MEMBER:"ResolvedUser":"ContractVersion"::VARCHAR
                          = 'archer-meta-user-v1', FALSE)
                 THEN 'ENRICHMENT_KEY_COLLISION'
             WHEN m.LOOKUP_USER_ID IS NULL THEN 'INVALID_USER_ID'
             WHEN u.MATCH_COUNT > 1 THEN 'DUPLICATE_LOOKUP_ID'
             WHEN u.ARCHER_USER_ID IS NULL THEN 'USER_NOT_FOUND'
             WHEN NULLIF(TRIM(u.EEID), '') IS NULL THEN 'MATCHED_MISSING_EEID'
             ELSE 'MATCHED'
           END AS LOOKUP_STATUS
    FROM user_members m
    LEFT JOIN user_lookup u ON u.ARCHER_USER_ID = m.LOOKUP_USER_ID
), enriched_members AS (
    SELECT r.*,
           CASE WHEN LOOKUP_STATUS IN
                          ('INVALID_MEMBER_OBJECT', 'ENRICHMENT_KEY_COLLISION',
                           'INVALID_USER_ID', 'DUPLICATE_LOOKUP_ID')
                THEN BEFORE_MEMBER
                ELSE TO_VARIANT(OBJECT_INSERT(
                    AS_OBJECT(BEFORE_MEMBER), 'ResolvedUser',
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'ContractVersion', 'archer-meta-user-v1',
                        'LookupStatus', LOOKUP_STATUS,
                        'EEID', EEID,
                        'FIRST_NAME', FIRST_NAME,
                        'MIDDLE_NAME', MIDDLE_NAME,
                        'LAST_NAME', LAST_NAME
                    ), TRUE))
           END AS AFTER_MEMBER
    FROM resolved r
), user_arrays AS (
    SELECT SOURCE_CONTENT_ID, SOURCE_FIELD_NAME,
           COUNT(*) AS MEMBER_COUNT,
           ARRAY_AGG(COALESCE(AFTER_MEMBER, PARSE_JSON('null')))
               WITHIN GROUP (ORDER BY MEMBER_INDEX) AS AFTER_USER_LIST,
           SUM(IFF(LOOKUP_STATUS IN ('MATCHED', 'MATCHED_MISSING_EEID'), 1, 0))
               AS MATCHED_USERS,
           SUM(IFF(LOOKUP_STATUS = 'USER_NOT_FOUND', 1, 0)) AS UNMATCHED_USERS,
           SUM(IFF(LOOKUP_STATUS = 'MATCHED_MISSING_EEID', 1, 0)) AS MISSING_EEID_USERS,
           SUM(IFF(LOOKUP_STATUS IN
               ('INVALID_MEMBER_OBJECT', 'ENRICHMENT_KEY_COLLISION',
                'INVALID_USER_ID', 'DUPLICATE_LOOKUP_ID'), 1, 0)) AS BLOCKING_MEMBERS,
           ARRAY_AGG(OBJECT_CONSTRUCT_KEEP_NULL(
               'Index', MEMBER_INDEX, 'Id', BEFORE_MEMBER:"Id", 'Status', LOOKUP_STATUS
           )) WITHIN GROUP (ORDER BY MEMBER_INDEX) AS MEMBER_RESULTS
    FROM enriched_members
    GROUP BY SOURCE_CONTENT_ID, SOURCE_FIELD_NAME
), field_checks AS (
    SELECT f.*, a.AFTER_USER_LIST, a.MEMBER_RESULTS,
           COALESCE(a.MATCHED_USERS, 0) AS MATCHED_USERS,
           COALESCE(a.UNMATCHED_USERS, 0) AS UNMATCHED_USERS,
           COALESCE(a.MISSING_EEID_USERS, 0) AS MISSING_EEID_USERS,
           CASE WHEN f.BEFORE_FIELD:"UserList" IS NOT NULL
                     AND NOT COALESCE(IS_NULL_VALUE(f.BEFORE_FIELD:"UserList"), FALSE)
                     AND NOT COALESCE(IS_ARRAY(f.BEFORE_FIELD:"UserList"), FALSE)
                THEN 1
                WHEN COALESCE(f.USER_ARRAY_SIZE, 0) > 0
                     AND (COALESCE(a.MEMBER_COUNT, 0) <> f.USER_ARRAY_SIZE
                          OR COALESCE(a.BLOCKING_MEMBERS, 0) > 0)
                THEN 1 ELSE 0 END AS BLOCKED_FIELD
    FROM fields f
    LEFT JOIN user_arrays a
      ON a.SOURCE_CONTENT_ID = f.SOURCE_CONTENT_ID
     AND a.SOURCE_FIELD_NAME = f.SOURCE_FIELD_NAME
), enriched_fields AS (
    SELECT f.*,
           CASE WHEN COALESCE(USER_ARRAY_SIZE, 0) > 0 AND BLOCKED_FIELD = 0
                THEN TO_VARIANT(OBJECT_INSERT(
                    AS_OBJECT(BEFORE_FIELD), 'UserList', AFTER_USER_LIST, TRUE))
                ELSE BEFORE_FIELD
           END AS AFTER_FIELD
    FROM field_checks f
), document_preview AS (
    SELECT SOURCE_CONTENT_ID,
           OBJECT_AGG(SOURCE_FIELD_NAME, COALESCE(AFTER_FIELD, PARSE_JSON('null')))
               AS CANDIDATE_JSON,
           SUM(COALESCE(USER_ARRAY_SIZE, 0)) AS USER_MEMBERS,
           SUM(MATCHED_USERS) AS MATCHED_USERS,
           SUM(UNMATCHED_USERS) AS UNMATCHED_USERS,
           SUM(MISSING_EEID_USERS) AS MISSING_EEID_USERS,
           SUM(BLOCKED_FIELD) AS BLOCKED_FIELDS,
           SUM(COALESCE(GROUP_ARRAY_SIZE, 0)) AS GROUP_MEMBERS_UNCHANGED,
           SUM(IFF(BEFORE_FIELD:"GroupList" IS DISTINCT FROM AFTER_FIELD:"GroupList",
                   1, 0)) AS GROUP_FIELDS_CHANGED,
           ARRAY_AGG(IFF(USER_ARRAY_SIZE IS NOT NULL OR GROUP_ARRAY_SIZE IS NOT NULL
                         OR BLOCKED_FIELD > 0,
               OBJECT_CONSTRUCT_KEEP_NULL(
                   'SourceFieldName', SOURCE_FIELD_NAME,
                   'Blocked', BLOCKED_FIELD,
                   'MemberResults', MEMBER_RESULTS,
                   'Before', BEFORE_FIELD, 'After', AFTER_FIELD
               ), NULL)) WITHIN GROUP (ORDER BY SOURCE_FIELD_NAME) AS FIELD_PREVIEW
    FROM enriched_fields
    GROUP BY SOURCE_CONTENT_ID
)
SELECT
    CASE WHEN s.SOURCE_CONTENT_ID IS NULL THEN 'NO_ELIGIBLE_SOURCE_RECORD'
         WHEN p.BLOCKED_FIELDS > 0 OR p.GROUP_FIELDS_CHANGED > 0
             THEN 'BLOCKED_REVIEW_FIELD_PREVIEW'
         WHEN p.UNMATCHED_USERS > 0 OR p.MISSING_EEID_USERS > 0
             THEN 'PREVIEW_HAS_UNRESOLVED_USERS'
         ELSE 'PREVIEW_BUILT_USER_LOOKUPS_MATCHED'
    END AS PREVIEW_STATUS,
    s.SOURCE_CONTENT_ID, r.STORED_CONTENT_ID,
    p.USER_MEMBERS, p.MATCHED_USERS, p.UNMATCHED_USERS, p.MISSING_EEID_USERS,
    p.BLOCKED_FIELDS, p.GROUP_MEMBERS_UNCHANGED, p.GROUP_FIELDS_CHANGED,
    r.CURATED_JSON AS BEFORE_CURATED_JSON,
    IFF(p.BLOCKED_FIELDS = 0 AND p.GROUP_FIELDS_CHANGED = 0,
        p.CANDIDATE_JSON, NULL) AS AFTER_CURATED_JSON,
    p.FIELD_PREVIEW
FROM sample_choice s
LEFT JOIN sample_record r ON r.SOURCE_CONTENT_ID = s.SOURCE_CONTENT_ID
LEFT JOIN document_preview p ON p.SOURCE_CONTENT_ID = s.SOURCE_CONTENT_ID;
