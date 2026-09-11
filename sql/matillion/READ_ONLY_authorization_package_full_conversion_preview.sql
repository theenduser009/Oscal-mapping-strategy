-- READ ONLY: COMPLETE RAW-TO-CURATED CONVERSION PREVIEW, NOT A NULL-ONLY REPORT.
-- Copy the WHOLE file into ONE Snowflake SQL cell and run. No edits or inputs.
-- Table is the exact authorization-package DEV table configured in Cell 1.
-- Shows CURRENT and PROPOSED JSON with populated values AND retained null keys.
-- No UPDATE, MERGE, DDL, Matillion change or previous-query dependency.
-- Includes pending and already-curated records for inspection only.
-- Published without running tests at owner request; NOT live-verified in Snowflake.
-- Full-table processing consumes warehouse compute. Keep real values in Snowflake.
-- Duplicate raw IDs, duplicate output keys and unsupported root shapes are reported
-- as blocked, rather than selecting a winner or presenting partial JSON as complete.
-- The original field conversion, metadata lookup and nested extraction remain.
-- Existing strict-cast/extraction errors can still stop this SELECT.
-- This previews the candidate behavior; it does not prove every raw field is covered.

WITH preview_raw AS (
    SELECT
        IFF(TYPEOF(r.RAW_DATA) = 'ARRAY', r.RAW_DATA[0], r.RAW_DATA) AS obj,
        TYPEOF(r.RAW_DATA) AS RAW_TYPE,
        CASE WHEN TYPEOF(r.RAW_DATA) = 'ARRAY'
             THEN ARRAY_SIZE(r.RAW_DATA) ELSE 1 END AS ROOT_ITEM_COUNT,
        r.CURATED_JSON,
        r.CONTENT_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r
),
preview_source AS (
    SELECT
        obj, RAW_TYPE, ROOT_ITEM_COUNT, CURATED_JSON, CONTENT_ID,
        TRY_TO_NUMBER(obj:"RequestedObject":"Id"::STRING) AS REQ_OBJ_ID
    FROM preview_raw
),
preview_source_counts AS (
    SELECT
        REQ_OBJ_ID,
        COUNT(*) AS MATCHING_RAW_ROWS,
        SUM(CASE WHEN RAW_TYPE IN ('OBJECT', 'ARRAY')
                      AND ROOT_ITEM_COUNT = 1
                 THEN 0 ELSE 1 END) AS UNSUPPORTED_ROOT_ROWS
    FROM preview_source
    GROUP BY REQ_OBJ_ID
),
norm AS (
    SELECT p.obj
    FROM preview_source p
    JOIN preview_source_counts sc ON p.REQ_OBJ_ID = sc.REQ_OBJ_ID
    WHERE sc.REQ_OBJ_ID IS NOT NULL
      AND sc.MATCHING_RAW_ROWS = 1
      AND sc.UNSUPPORTED_ROOT_ROWS = 0
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
preview_key_counts AS (
    SELECT
        REQ_OBJ_ID,
        COUNT(*) AS COMBINED_FIELD_ROWS,
        COALESCE(COUNT_IF(SQL_KEY IS NULL OR SQL_KEY = ''), 0) AS INVALID_KEY_ROWS,
        COALESCE(COUNT_IF(TYPED_VALUE IS NULL), 0) AS SQL_NULL_FIELD_ROWS
    FROM combined
    GROUP BY REQ_OBJ_ID
),
preview_duplicate_keys AS (
    SELECT REQ_OBJ_ID, SQL_KEY
    FROM combined
    GROUP BY REQ_OBJ_ID, SQL_KEY
    HAVING COUNT(*) > 1
),
preview_duplicate_counts AS (
    SELECT REQ_OBJ_ID, COUNT(*) AS DUPLICATE_KEY_GROUPS
    FROM preview_duplicate_keys
    GROUP BY REQ_OBJ_ID
),
preview_json AS (
    SELECT
        c.REQ_OBJ_ID,
        OBJECT_AGG(c.SQL_KEY, COALESCE(c.TYPED_VALUE, PARSE_JSON('null')))
            AS PROPOSED_CURATED_JSON,
        OBJECT_AGG(c.SQL_KEY, c.TYPED_VALUE) AS ID_SOURCE_JSON
    FROM combined c
    JOIN preview_key_counts k ON c.REQ_OBJ_ID = k.REQ_OBJ_ID
    LEFT JOIN preview_duplicate_counts d ON c.REQ_OBJ_ID = d.REQ_OBJ_ID
    WHERE k.INVALID_KEY_ROWS = 0
      AND COALESCE(d.DUPLICATE_KEY_GROUPS, 0) = 0
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
)
SELECT
    sc.REQ_OBJ_ID AS REQUESTED_OBJECT_ID,
    CASE
        WHEN sc.REQ_OBJ_ID IS NULL THEN 'BLOCKED_MISSING_OR_INVALID_RAW_RECORD_ID'
        WHEN sc.MATCHING_RAW_ROWS <> 1 THEN 'BLOCKED_MULTIPLE_RAW_ROWS_FOR_ID'
        WHEN sc.UNSUPPORTED_ROOT_ROWS > 0 THEN 'BLOCKED_UNSUPPORTED_ROOT_SHAPE'
        WHEN COALESCE(k.COMBINED_FIELD_ROWS, 0) = 0 THEN 'NO_FIELDS_EXTRACTED_NOT_A_PASS'
        WHEN k.INVALID_KEY_ROWS > 0 THEN 'BLOCKED_NULL_OR_EMPTY_FIELD_NAMES'
        WHEN COALESCE(d.DUPLICATE_KEY_GROUPS, 0) > 0 THEN 'BLOCKED_DUPLICATE_FIELD_NAMES'
        WHEN c.REQ_OBJ_ID IS NULL THEN 'NO_PROPOSED_JSON_NOT_A_PASS'
        ELSE 'PREVIEW_READY_NOT_WRITTEN'
    END AS PREVIEW_STATUS,
    p.CURATED_JSON AS CURRENT_CURATED_JSON,
    c.PROPOSED_CURATED_JSON,
    p.CONTENT_ID AS CURRENT_CONTENT_ID,
    c.PROPOSED_CONTENT_ID,
    p.obj:"RequestedObject":"FieldContents" AS RAW_FIELD_CONTENTS,
    CASE WHEN sc.MATCHING_RAW_ROWS = 1
         THEN p.CURATED_JSON IS NULL ELSE NULL END
        AS IS_PENDING_UNDER_ORIGINAL_UPDATE_FILTER,
    CASE WHEN c.REQ_OBJ_ID IS NOT NULL
         THEN EQUAL_NULL(p.CONTENT_ID::STRING, c.PROPOSED_CONTENT_ID)
         ELSE NULL END AS CONTENT_ID_MATCHES_STORED,
    CASE WHEN TYPEOF(p.CURATED_JSON) = 'OBJECT'
         THEN ARRAY_SIZE(OBJECT_KEYS(p.CURATED_JSON)) ELSE NULL END
        AS CURRENT_KEY_COUNT,
    ARRAY_SIZE(OBJECT_KEYS(c.PROPOSED_CURATED_JSON)) AS PROPOSED_KEY_COUNT,
    sc.MATCHING_RAW_ROWS,
    sc.UNSUPPORTED_ROOT_ROWS,
    COALESCE(k.COMBINED_FIELD_ROWS, 0) AS COMBINED_FIELD_ROWS,
    COALESCE(k.INVALID_KEY_ROWS, 0) AS INVALID_KEY_ROWS,
    COALESCE(d.DUPLICATE_KEY_GROUPS, 0) AS DUPLICATE_KEY_GROUPS,
    COALESCE(k.SQL_NULL_FIELD_ROWS, 0) AS SQL_NULL_FIELD_ROWS
FROM preview_source_counts sc
LEFT JOIN preview_source p
    ON EQUAL_NULL(p.REQ_OBJ_ID, sc.REQ_OBJ_ID) AND sc.MATCHING_RAW_ROWS = 1
LEFT JOIN preview_key_counts k ON sc.REQ_OBJ_ID = k.REQ_OBJ_ID
LEFT JOIN preview_duplicate_counts d ON sc.REQ_OBJ_ID = d.REQ_OBJ_ID
LEFT JOIN preview_result c ON sc.REQ_OBJ_ID = c.REQ_OBJ_ID
ORDER BY sc.REQ_OBJ_ID;
