Yes. We can validate one CONTENT_ID exactly like the spreadsheet.

From your screenshot, 565189 is a good example. This query will show, for that one record, every RAW FieldID, the mapped SQL_FIELD_NAME, and whether that field name exists in CURATED_JSON.

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
            THEN 'NO META FIELD MAPPING'
        WHEN GET(CURATED_JSON, SQL_FIELD_NAME) IS NOT NULL
            THEN 'FOUND'
        ELSE 'NOT FOUND'
    END AS FOUND_IN_CURATED
FROM mapped
ORDER BY TRY_TO_NUMBER(FIELD_ID);

For 565189, this will let you inspect things like:

23235 → INFORMATION_SYSTEM_TYPE → FOUND

23236 → FISMA_REPORTABLE → FOUND/NOT FOUND


One important point: if FISMA_REPORTABLE has RAW_VALUE = NULL, then NOT FOUND may be perfectly valid. So for a fair comparison with your spreadsheet, we should probably also add a second status like RAW_POPULATED = YES/NO.

Run this for 565189 first.