Yes — first we should prove the mapping behavior with a SELECT only, no UPDATE yet.

For one CONTENT_ID like 565189, this query shows every FieldID, its SQL_FIELD_NAME, whether the RAW inner value is null, and whether the mapped field name exists in CURATED_JSON:

WITH norm AS (
    SELECT
        t.CONTENT_ID,
        IFF(
            TYPEOF(t.RAW_DATA) = 'ARRAY',
            t.RAW_DATA[0],
            t.RAW_DATA
        ) AS OBJ,
        t.CURATED_JSON
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW t
    WHERE TRIM(t.CONTENT_ID::STRING) = '565189'
),

raw_fields AS (
    SELECT
        n.CONTENT_ID,
        f.key::STRING AS FIELD_ID,
        f.value:"Value" AS RAW_VALUE,
        n.CURATED_JSON
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => n.OBJ:"RequestedObject":"FieldContents"
         ) f
),

mapped AS (
    SELECT
        r.CONTENT_ID,
        r.FIELD_ID,
        r.RAW_VALUE,
        amf.SQL_FIELD_NAME,
        r.CURATED_JSON
    FROM raw_fields r
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
)

SELECT
    CONTENT_ID,
    FIELD_ID,
    SQL_FIELD_NAME,
    RAW_VALUE,
    GET(CURATED_JSON, SQL_FIELD_NAME) AS CURATED_VALUE,

    CASE
        WHEN SQL_FIELD_NAME IS NULL
            THEN 'NO_META_MAPPING'

        WHEN RAW_VALUE IS NULL
             OR IS_NULL_VALUE(RAW_VALUE)
            THEN 'MAPPED_SOURCE_NULL'

        WHEN GET(CURATED_JSON, SQL_FIELD_NAME) IS NOT NULL
            THEN 'MAPPED_AND_FOUND'

        ELSE 'MAPPING_ERROR'
    END AS MAPPING_STATUS

FROM mapped
ORDER BY TRY_TO_NUMBER(FIELD_ID);

What we want to see is mostly:

23235  INFORMATION_SYSTEM_TYPE   MAPPED_AND_FOUND
23236  FISMA_REPORTABLE          MAPPED_SOURCE_NULL

and ideally zero MAPPING_ERROR rows.

Run this first. Then we’ll change the UPDATE only after this baseline is clear.