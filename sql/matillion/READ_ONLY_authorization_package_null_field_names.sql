-- READ ONLY: one-step list of MAPPED FIELD NAMES whose proposed values are null.
-- Raw table is explicitly the authorization-package table from repository Cell 1:
-- RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
-- This is the configured DEV location, not an assertion about your production target.
-- Replace REPLACE_WITH_REQUESTED_OBJECT_ID below with one raw RequestedObject.Id.
-- Keep its quotes. Do not use the derived CONTENT_ID unless it is actually the same ID.
-- Run the complete file in one Snowflake SQL cell. No prior query is required.
-- No writes. Already-curated rows are inspected, not repaired.
-- Field conversions and nested extraction match the candidate, including existing
-- strict casts. Retained nulls may come from raw nulls, blanks, or failed conversions.
-- Keep sensitive result details in Snowflake. Not live-verified.

WITH preview_input AS (
    SELECT 'REPLACE_WITH_REQUESTED_OBJECT_ID' AS REQUESTED_OBJECT_ID
),
preview_source AS (
    SELECT
        IFF(TYPEOF(r.RAW_DATA) = 'ARRAY', r.RAW_DATA[0], r.RAW_DATA) AS obj,
        r.CURATED_JSON,
        r.CONTENT_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r
    WHERE TYPEOF(r.RAW_DATA) IN ('ARRAY', 'OBJECT')
      AND IFF(TYPEOF(r.RAW_DATA) = 'ARRAY', r.RAW_DATA[0], r.RAW_DATA)
          :"RequestedObject":"Id"::STRING =
          (SELECT REQUESTED_OBJECT_ID FROM preview_input)
),
preview_source_count AS (
    SELECT COUNT(*) AS MATCHING_RAW_ROWS FROM preview_source
),
norm AS (
    SELECT obj
    FROM preview_source
    WHERE (SELECT MATCHING_RAW_ROWS FROM preview_source_count) = 1
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
                TO_NUMBER(f.FIELD_ID)
        ) AS rn
    FROM flat f
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TO_NUMBER(amf.FIELD_ID) = TO_NUMBER(f.FIELD_ID)
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
        ON TO_NUMBER(amf.FIELD_ID) = TO_NUMBER(nf.FIELD_ID)
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
preview_key_check AS (
    SELECT
        COUNT(*) AS COMBINED_FIELD_ROWS,
        COALESCE(COUNT_IF(SQL_KEY IS NULL OR SQL_KEY = ''), 0) AS INVALID_KEY_ROWS,
        COALESCE(COUNT_IF(TYPED_VALUE IS NULL), 0) AS SQL_NULL_FIELD_ROWS,
        (SELECT COUNT(*) FROM (
            SELECT REQ_OBJ_ID, SQL_KEY
            FROM combined
            GROUP BY REQ_OBJ_ID, SQL_KEY
            HAVING COUNT(*) > 1
        )) AS DUPLICATE_KEY_GROUPS
    FROM combined
),
preview_json AS (
    SELECT
        c.REQ_OBJ_ID,
        OBJECT_AGG(c.SQL_KEY, COALESCE(c.TYPED_VALUE, PARSE_JSON('null')))
            AS PROPOSED_CURATED_JSON,
        OBJECT_AGG(c.SQL_KEY, c.TYPED_VALUE) AS ID_SOURCE_JSON
    FROM combined c
    CROSS JOIN preview_key_check k
    WHERE k.INVALID_KEY_ROWS = 0
      AND k.DUPLICATE_KEY_GROUPS = 0
    GROUP BY c.REQ_OBJ_ID
),
preview_result AS (
    SELECT
        REQ_OBJ_ID,
        PROPOSED_CURATED_JSON,
        COALESCE(
            ID_SOURCE_JSON:"ssp_uuid"::string,
            ID_SOURCE_JSON:"AUTH_PKG_TRACKING_ID"::string,
            ID_SOURCE_JSON:"HRTN_ID"::string,
            ID_SOURCE_JSON:"TRACKING_ID"::string,
            ID_SOURCE_JSON:"CONTENT_ID"::string,
            REQ_OBJ_ID::string
        ) AS PROPOSED_CONTENT_ID
    FROM preview_json
),
preview_document AS (
SELECT
    CASE
        WHEN NOT REGEXP_LIKE(i.REQUESTED_OBJECT_ID, '^[0-9]+$')
            THEN 'INPUT_REQUIRED'
        WHEN sc.MATCHING_RAW_ROWS = 0 THEN 'NO_MATCHING_RAW_RECORD'
        WHEN sc.MATCHING_RAW_ROWS <> 1 THEN 'BLOCKED_MULTIPLE_RAW_ROWS_FOR_ID'
        WHEN k.INVALID_KEY_ROWS > 0 THEN 'BLOCKED_NULL_OR_EMPTY_FIELD_NAMES'
        WHEN k.DUPLICATE_KEY_GROUPS > 0 THEN 'BLOCKED_DUPLICATE_FIELD_NAMES'
        WHEN k.COMBINED_FIELD_ROWS = 0 THEN 'NO_FIELDS_EXTRACTED_NOT_A_PASS'
        WHEN c.REQ_OBJ_ID IS NULL THEN 'NO_PROPOSED_JSON_NOT_A_PASS'
        ELSE 'PREVIEW_READY_NOT_WRITTEN'
    END AS PREVIEW_STATUS,
    sc.MATCHING_RAW_ROWS,
    k.COMBINED_FIELD_ROWS,
    k.INVALID_KEY_ROWS,
    k.DUPLICATE_KEY_GROUPS,
    k.SQL_NULL_FIELD_ROWS,
    CASE WHEN sc.MATCHING_RAW_ROWS = 1
         THEN p.CURATED_JSON IS NULL ELSE NULL END
        AS IS_PENDING_UNDER_ORIGINAL_UPDATE_FILTER,
    p.obj:"RequestedObject":"FieldContents" AS RAW_FIELD_CONTENTS,
    p.CURATED_JSON AS CURRENT_CURATED_JSON,
    c.PROPOSED_CURATED_JSON,
    p.CONTENT_ID AS CURRENT_CONTENT_ID,
    c.PROPOSED_CONTENT_ID,
    CASE WHEN c.REQ_OBJ_ID IS NOT NULL
         THEN EQUAL_NULL(p.CONTENT_ID::STRING, c.PROPOSED_CONTENT_ID)
         ELSE NULL END AS CONTENT_ID_MATCHES_STORED,
    CASE WHEN TYPEOF(p.CURATED_JSON) = 'OBJECT'
         THEN ARRAY_SIZE(OBJECT_KEYS(p.CURATED_JSON)) ELSE NULL END
        AS CURRENT_KEY_COUNT,
    ARRAY_SIZE(OBJECT_KEYS(c.PROPOSED_CURATED_JSON)) AS PROPOSED_KEY_COUNT
FROM preview_input i
CROSS JOIN preview_source_count sc
CROSS JOIN preview_key_check k
LEFT JOIN preview_source p ON sc.MATCHING_RAW_ROWS = 1
LEFT JOIN preview_result c ON sc.MATCHING_RAW_ROWS = 1
),
null_fields AS (
    SELECT f.KEY::STRING AS FIELD_NAME, f.VALUE AS MAPPED_VALUE
    FROM preview_document p,
         LATERAL FLATTEN(INPUT => p.PROPOSED_CURATED_JSON) f
    WHERE IS_NULL_VALUE(f.VALUE)
)
SELECT
    CASE
        WHEN p.PREVIEW_STATUS <> 'PREVIEW_READY_NOT_WRITTEN'
            THEN p.PREVIEW_STATUS
        WHEN f.FIELD_NAME IS NULL
            THEN 'NO_NULL_VALUED_FIELDS_IN_PROPOSED_JSON'
        ELSE 'NULL_VALUED_FIELD'
    END AS STATUS,
    f.FIELD_NAME,
    f.MAPPED_VALUE,
    p.MATCHING_RAW_ROWS,
    p.COMBINED_FIELD_ROWS,
    p.DUPLICATE_KEY_GROUPS,
    p.INVALID_KEY_ROWS
FROM preview_document p
LEFT JOIN null_fields f ON TRUE
ORDER BY f.FIELD_NAME;
