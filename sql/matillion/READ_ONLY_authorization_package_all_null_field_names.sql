-- READ ONLY. COPY THE WHOLE FILE INTO ONE SNOWFLAKE SQL CELL AND RUN.
-- No inputs, placeholders, previous query, notebook setup or Matillion variable.
-- Full-table inventory using the configured authorization-package DEV raw table.
-- Published without a test run at owner request. Not live-verified in Snowflake.
-- No data is written. May scan the full table and consume warehouse compute.
-- Returns one row per field NAME whose selected, converted value is null in
-- at least one record, plus affected-record counts. Not one row per raw record.
-- Includes both pending and already-curated records for inspection only.
-- Existing extraction, type conversions, ROW_NUMBER precedence and nested
-- strict casts are preserved. A null after conversion is not always a raw null.
-- Existing first-array-item handling remains. This is NOT proof all raw field
-- IDs are covered, and does not approve a production UPDATE or repair.

WITH norm AS (
    SELECT
        IFF(TYPEOF(r.RAW_DATA) = 'ARRAY', r.RAW_DATA[0], r.RAW_DATA) AS obj
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r
    WHERE TYPEOF(r.RAW_DATA) IN ('ARRAY', 'OBJECT')
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
key_occurrences AS (
    SELECT REQ_OBJ_ID, SQL_KEY, COUNT(*) AS KEY_OCCURRENCES
    FROM combined
    GROUP BY REQ_OBJ_ID, SQL_KEY
),
null_field_summary AS (
    SELECT
        c.SQL_KEY AS FIELD_NAME,
        COUNT(*) AS NULL_VALUE_OCCURRENCES,
        COUNT(DISTINCT c.REQ_OBJ_ID) AS AFFECTED_RECORDS,
        COALESCE(COUNT_IF(c.TYPED_VALUE IS NULL), 0) AS SQL_NULL_OCCURRENCES,
        COALESCE(COUNT_IF(IS_NULL_VALUE(c.TYPED_VALUE)), 0) AS JSON_NULL_OCCURRENCES,
        COUNT(DISTINCT CASE WHEN k.KEY_OCCURRENCES > 1 THEN c.REQ_OBJ_ID END)
            AS AFFECTED_RECORDS_WITH_DUPLICATE_KEY
    FROM combined c
    JOIN key_occurrences k
      ON EQUAL_NULL(c.REQ_OBJ_ID, k.REQ_OBJ_ID)
     AND EQUAL_NULL(c.SQL_KEY, k.SQL_KEY)
    WHERE c.TYPED_VALUE IS NULL OR IS_NULL_VALUE(c.TYPED_VALUE)
    GROUP BY c.SQL_KEY
)
SELECT
    FIELD_NAME,
    PARSE_JSON('null') AS MAPPED_VALUE,
    AFFECTED_RECORDS,
    NULL_VALUE_OCCURRENCES,
    SQL_NULL_OCCURRENCES,
    JSON_NULL_OCCURRENCES,
    AFFECTED_RECORDS_WITH_DUPLICATE_KEY,
    CASE
        WHEN FIELD_NAME IS NULL OR FIELD_NAME = '' THEN 'MISSING_FIELD_NAME_REVIEW'
        WHEN AFFECTED_RECORDS_WITH_DUPLICATE_KEY > 0 THEN 'DUPLICATE_KEY_REVIEW'
        WHEN LEFT(FIELD_NAME, 6) = 'FIELD_' THEN 'FALLBACK_STYLE_NAME_REVIEW'
        ELSE 'NAMED_NULL_AFTER_CONVERSION'
    END AS STATUS
FROM null_field_summary
ORDER BY FIELD_NAME;
