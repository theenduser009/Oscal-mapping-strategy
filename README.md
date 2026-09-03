Yes — that is exactly the intent. We should stay entirely inside the RAW → CURATED_JSON conversion and validate only that mapping.

So the flow we are checking is:

RAW_DATA contains Archer FieldContents objects keyed by FieldID

→ join FieldID to ARCHER_META_FIELD.FIELD_ID

→ take ARCHER_META_FIELD.SQL_FIELD_NAME

→ write that field name and converted value into the same row's CURATED_JSON

So the validation question is simply:

> For every populated RAW_DATA field, did the correct SQL_FIELD_NAME appear in CURATED_JSON, and did the value match after the expected type conversion?



The empty result from the last query tells us the key/name mapping is working for populated top-level fields. Now the next validation should check the value, not OSCAL or any canonical mapping.

Run this SQL next. It shows RAW value and CURATED value side-by-side for populated fields:

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
    WHERE t.RAW_DATA IS NOT NULL
),

raw_fields AS (
    SELECT
        n.CONTENT_ID,
        f.key::STRING AS FIELD_ID,
        f.value:"Type" AS ARCHER_TYPE,
        f.value:"Value" AS RAW_VALUE,
        n.CURATED_JSON
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => n.OBJ:"RequestedObject":"FieldContents"
         ) f
    WHERE f.value:"Value" IS NOT NULL
      AND NOT IS_NULL_VALUE(f.value:"Value")
),

mapped AS (
    SELECT
        r.CONTENT_ID,
        r.FIELD_ID,
        r.ARCHER_TYPE,
        amf.SQL_FIELD_NAME,
        r.RAW_VALUE,
        GET(r.CURATED_JSON, amf.SQL_FIELD_NAME) AS CURATED_VALUE
    FROM raw_fields r
    JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
    WHERE amf.SQL_FIELD_NAME IS NOT NULL
)

SELECT
    CONTENT_ID,
    FIELD_ID,
    SQL_FIELD_NAME,
    ARCHER_TYPE,
    RAW_VALUE,
    CURATED_VALUE,
    TYPEOF(RAW_VALUE) AS RAW_TYPE,
    TYPEOF(CURATED_VALUE) AS CURATED_TYPE
FROM mapped
ORDER BY CONTENT_ID, FIELD_ID
LIMIT 200;

This is now the right direction: no OSCAL, no CSV, no canonical mapping. We are validating only that your UPDATE correctly transforms RAW_DATA into CURATED_JSON.