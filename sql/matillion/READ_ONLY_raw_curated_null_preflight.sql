-- READ ONLY: original Matillion extraction/typing on its existing pending cohort.
-- ${jv_raw_table_name} is the EXISTING Matillion job variable. In a Snowflake
-- worksheet, substitute its actual fully qualified table name; do not guess it.
-- No UPDATE/DDL. No raw IDs or field values are returned. Duplicate checks include
-- SQL-null values, since retaining them can expose previously ignored duplicate keys.
-- Existing nested extraction/type errors intentionally remain visible, not hidden.
-- NO_PENDING_ROWS is NOT a pass; already-curated rows need a separately scoped check.

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
preflight AS (
    SELECT
        (SELECT COUNT(*) FROM norm) AS PENDING_RAW_ROWS,
        (SELECT COUNT(DISTINCT REQ_OBJ_ID) FROM flat) AS EXTRACTED_RECORDS,
        (SELECT COUNT(*) FROM norm n WHERE
            n.obj:"RequestedObject":"Id" IS NULL) AS MISSING_REQUESTED_OBJECT_IDS,
        (SELECT COUNT(*) FROM combined) AS COMBINED_FIELD_ROWS,
        (SELECT COUNT(*) FROM combined WHERE SQL_KEY IS NULL) AS NULL_NAME_ROWS,
        (SELECT COUNT(*) FROM combined WHERE SQL_KEY = '') AS EMPTY_NAME_ROWS,
        (SELECT COUNT(*) FROM combined
            WHERE SQL_KEY IS NOT NULL AND TYPED_VALUE IS NULL) AS SQL_NULL_FIELD_ROWS,
        (SELECT COUNT(*) FROM (
            SELECT REQ_OBJ_ID, SQL_KEY FROM combined
            GROUP BY REQ_OBJ_ID, SQL_KEY HAVING COUNT(*) > 1
        )) AS DUPLICATE_KEY_GROUPS,
        (SELECT COUNT(*) FROM typed WHERE LEFT(SQL_KEY, 6) = 'FIELD_') AS FALLBACK_STYLE_NAME_ROWS,
        (SELECT COUNT(*) FROM flat) AS RAW_TOP_LEVEL_FIELD_ROWS,
        (SELECT COUNT(*) FROM mapped WHERE rn = 1) AS SELECTED_TOP_LEVEL_FIELD_ROWS,
        (SELECT COUNT(*) FROM mapped m JOIN typed t
            ON m.REQ_OBJ_ID=t.REQ_OBJ_ID AND m.SQL_KEY=t.SQL_KEY
            WHERE m.rn=1 AND m.TYPE_ID IN (2,3,6,20,21,22)
              AND m.V IS NOT NULL AND NOT COALESCE(IS_NULL_VALUE(m.V), FALSE)
              AND NULLIF(m.V::STRING, '') IS NOT NULL
              AND t.TYPED_VALUE IS NULL) AS POPULATED_VALUES_CONVERTED_TO_SQL_NULL
)
SELECT *,
    CASE
        WHEN PENDING_RAW_ROWS = 0 THEN 'NO_PENDING_ROWS_NOT_A_VERIFICATION'
        WHEN MISSING_REQUESTED_OBJECT_IDS > 0 OR NULL_NAME_ROWS > 0
          OR EMPTY_NAME_ROWS > 0 OR DUPLICATE_KEY_GROUPS > 0
          THEN 'BLOCKED_REVIEW_SOURCE_OR_KEY_COLLISIONS'
        WHEN EXTRACTED_RECORDS = 0 THEN 'NO_EXTRACTED_RECORDS_NOT_A_VERIFICATION'
        ELSE 'PREFLIGHT_ONLY_COMPARE_PENDING_RECORD_BEFORE_DEPLOY'
    END AS STATUS
FROM preflight;
