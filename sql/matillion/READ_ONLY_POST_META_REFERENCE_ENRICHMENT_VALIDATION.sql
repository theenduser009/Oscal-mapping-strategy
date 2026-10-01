-- Post-Matillion validation for UserList + ValuesListIds + GroupList enrichment
-- Date: 2026-10-01
-- READ ONLY. No DML / DDL.
--
-- Validates the current Source One Authorization Package RAW table after
-- CANDIDATE_enrich_curated_json_users_values_groups.sql runs.
--
-- Expected enrichment:
--   UserList[].ResolvedUser
--   field.ResolvedValues[] from ARCHER_META_VALUES.VALUEID / VALUENAME
--   field.ResolvedGroups[] from ARCHER_META_GROUP.GROUP_ID / GROUP_NAME / GUID

WITH base AS (
    SELECT
        CONTENT_ID::VARCHAR AS CONTENT_ID,
        CURATED_JSON
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    WHERE TYPEOF(CURATED_JSON) = 'OBJECT'
),
fields AS (
    SELECT
        b.CONTENT_ID,
        f.key::VARCHAR AS SQL_KEY,
        f.value AS FIELD_VALUE
    FROM base b,
         LATERAL FLATTEN(INPUT => AS_OBJECT(b.CURATED_JSON)) f
),
user_members AS (
    SELECT
        f.CONTENT_ID,
        f.SQL_KEY,
        u.value AS MEMBER_VALUE
    FROM fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_VALUE:"UserList")) u
    WHERE COALESCE(IS_ARRAY(f.FIELD_VALUE:"UserList"), FALSE)
),
value_members AS (
    SELECT
        f.CONTENT_ID,
        f.SQL_KEY,
        v.index AS MEMBER_INDEX,
        TRIM(v.value::VARCHAR) AS VALUE_ID
    FROM fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_VALUE:"ValuesListIds")) v
    WHERE COALESCE(IS_ARRAY(f.FIELD_VALUE:"ValuesListIds"), FALSE)
),
resolved_values AS (
    SELECT
        f.CONTENT_ID,
        f.SQL_KEY,
        rv.index AS MEMBER_INDEX,
        rv.value:"ValueId"::VARCHAR AS VALUE_ID,
        rv.value:"ValueName"::VARCHAR AS VALUE_NAME,
        rv.value:"LookupStatus"::VARCHAR AS LOOKUP_STATUS
    FROM fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_VALUE:"ResolvedValues")) rv
    WHERE COALESCE(IS_ARRAY(f.FIELD_VALUE:"ResolvedValues"), FALSE)
),
group_members AS (
    SELECT
        f.CONTENT_ID,
        f.SQL_KEY,
        g.index AS MEMBER_INDEX,
        CASE
            WHEN TYPEOF(g.value) = 'OBJECT' THEN
                COALESCE(
                    g.value:"Id"::VARCHAR,
                    g.value:"GroupId"::VARCHAR,
                    g.value:"GROUP_ID"::VARCHAR
                )
            ELSE g.value::VARCHAR
        END AS GROUP_ID
    FROM fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_VALUE:"GroupList")) g
    WHERE COALESCE(IS_ARRAY(f.FIELD_VALUE:"GroupList"), FALSE)
),
resolved_groups AS (
    SELECT
        f.CONTENT_ID,
        f.SQL_KEY,
        rg.index AS MEMBER_INDEX,
        rg.value:"GroupId"::VARCHAR AS GROUP_ID,
        rg.value:"GroupName"::VARCHAR AS GROUP_NAME,
        rg.value:"Guid"::VARCHAR AS GUID,
        rg.value:"LookupStatus"::VARCHAR AS LOOKUP_STATUS
    FROM fields f,
         LATERAL FLATTEN(INPUT => AS_ARRAY(f.FIELD_VALUE:"ResolvedGroups")) rg
    WHERE COALESCE(IS_ARRAY(f.FIELD_VALUE:"ResolvedGroups"), FALSE)
),
summary AS (
    SELECT
        (SELECT COUNT(*) FROM user_members) AS USER_MEMBER_OCCURRENCES,
        (SELECT COUNT(*) FROM user_members
          WHERE MEMBER_VALUE:"ResolvedUser" IS NOT NULL) AS USER_MEMBERS_RESOLVED,

        (SELECT COUNT(*) FROM value_members) AS VALUE_ID_OCCURRENCES,
        (SELECT COUNT(*) FROM resolved_values) AS RESOLVED_VALUE_OCCURRENCES,
        (SELECT COUNT(*) FROM resolved_values
          WHERE LOOKUP_STATUS = 'MATCHED') AS MATCHED_VALUE_OCCURRENCES,
        (SELECT COUNT(*) FROM resolved_values
          WHERE LOOKUP_STATUS = 'VALUE_NOT_FOUND') AS VALUE_NOT_FOUND_OCCURRENCES,
        (SELECT COUNT(*) FROM resolved_values
          WHERE LOOKUP_STATUS IS NULL
             OR LOOKUP_STATUS NOT IN ('MATCHED','VALUE_NOT_FOUND')) AS BAD_VALUE_STATUS_OCCURRENCES,
        (SELECT COUNT(*) FROM value_members v
          LEFT JOIN resolved_values r
            ON r.CONTENT_ID = v.CONTENT_ID
           AND r.SQL_KEY = v.SQL_KEY
           AND r.MEMBER_INDEX = v.MEMBER_INDEX
           AND TRIM(r.VALUE_ID) = TRIM(v.VALUE_ID)
          WHERE r.CONTENT_ID IS NULL) AS VALUE_IDENTITY_MISMATCHES,

        (SELECT COUNT(*) FROM group_members) AS GROUP_ID_OCCURRENCES,
        (SELECT COUNT(*) FROM resolved_groups) AS RESOLVED_GROUP_OCCURRENCES,
        (SELECT COUNT(*) FROM resolved_groups
          WHERE LOOKUP_STATUS = 'MATCHED') AS MATCHED_GROUP_OCCURRENCES,
        (SELECT COUNT(*) FROM resolved_groups
          WHERE LOOKUP_STATUS = 'GROUP_NOT_FOUND') AS GROUP_NOT_FOUND_OCCURRENCES,
        (SELECT COUNT(*) FROM resolved_groups
          WHERE LOOKUP_STATUS IS NULL
             OR LOOKUP_STATUS NOT IN ('MATCHED','GROUP_NOT_FOUND')) AS BAD_GROUP_STATUS_OCCURRENCES,
        (SELECT COUNT(*) FROM group_members g
          LEFT JOIN resolved_groups r
            ON r.CONTENT_ID = g.CONTENT_ID
           AND r.SQL_KEY = g.SQL_KEY
           AND r.MEMBER_INDEX = g.MEMBER_INDEX
           AND TRIM(r.GROUP_ID) = TRIM(g.GROUP_ID)
          WHERE r.CONTENT_ID IS NULL) AS GROUP_IDENTITY_MISMATCHES
)
SELECT
    *,
    CASE
        WHEN USER_MEMBER_OCCURRENCES <> USER_MEMBERS_RESOLVED
          OR VALUE_ID_OCCURRENCES <> RESOLVED_VALUE_OCCURRENCES
          OR VALUE_NOT_FOUND_OCCURRENCES > 0
          OR BAD_VALUE_STATUS_OCCURRENCES > 0
          OR VALUE_IDENTITY_MISMATCHES > 0
          OR GROUP_ID_OCCURRENCES <> RESOLVED_GROUP_OCCURRENCES
          OR GROUP_NOT_FOUND_OCCURRENCES > 0
          OR BAD_GROUP_STATUS_OCCURRENCES > 0
          OR GROUP_IDENTITY_MISMATCHES > 0
        THEN 'REVIEW_BEFORE_OSCAL'
        ELSE 'POST_MATILLION_META_ENRICHMENT_PASSED'
    END AS STATUS
FROM summary;


-- Sample the resolved CIA/FIPS labels after Matillion enrichment.
SELECT
    CONTENT_ID,
    f.key::VARCHAR AS ARCHER_FIELD_NAME,
    f.value:"ValuesListIds" AS VALUES_LIST_IDS,
    f.value:"ResolvedValues" AS RESOLVED_VALUES
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r,
     LATERAL FLATTEN(INPUT => AS_OBJECT(r.CURATED_JSON)) f
WHERE TYPEOF(r.CURATED_JSON) = 'OBJECT'
  AND f.key::VARCHAR IN (
      'RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY',
      'CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',
      'RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',
      'INTEGRITY_CONTROL_CATEGORY_OVERRIDE',
      'AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',
      'RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',
      'PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',
      'PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',
      'CNSS_AVAILABILITY_RATING',
      'CNSS_CONFIDENTIALITY_RATING',
      'CNSS_INTEGRITY_RATING'
  )
  AND COALESCE(ARRAY_SIZE(AS_ARRAY(f.value:"ValuesListIds")), 0) > 0
ORDER BY CONTENT_ID, ARCHER_FIELD_NAME
LIMIT 50;
