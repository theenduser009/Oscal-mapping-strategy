Yes — after you run the updated Matillion SQL, use this direct validation SQL against the table to check the Type 4 fix.

WITH norm AS (
    SELECT
        t.CONTENT_ID,
        IFF(
            TYPEOF(t.RAW_DATA) = 'ARRAY',
            t.RAW_DATA[0],
            t.RAW_DATA
        ) AS OBJ,
        t.CURATED_JSON
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_RAW t
),

raw_fields AS (
    SELECT
        n.CONTENT_ID,
        f.key::STRING AS FIELD_ID,
        f.value:"Type"::NUMBER AS TYPE_ID,
        f.value:"Value" AS RAW_VALUE,
        n.CURATED_JSON
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => n.OBJ:"RequestedObject":"FieldContents"
         ) f
    WHERE f.value:"Type"::NUMBER = 4
),

mapped AS (
    SELECT
        r.*,
        amf.SQL_FIELD_NAME,
        GET(r.CURATED_JSON, amf.SQL_FIELD_NAME) AS CURATED_VALUE
    FROM raw_fields r
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
),

validated AS (
    SELECT
        CONTENT_ID,
        FIELD_ID,
        SQL_FIELD_NAME,
        RAW_VALUE,
        CURATED_VALUE,

        CASE
            WHEN SQL_FIELD_NAME IS NULL
                THEN 'NO_META_MAPPING'

            WHEN RAW_VALUE IS NULL
              OR IS_NULL_VALUE(RAW_VALUE)
                THEN 'SOURCE_NULL'

            WHEN CURATED_VALUE IS NULL
                THEN 'KEY_MISSING'

            WHEN RAW_VALUE = CURATED_VALUE
                THEN 'PASS'

            ELSE 'VALUE_MISMATCH'
        END AS STATUS

    FROM mapped
)

SELECT
    STATUS,
    COUNT(*) AS ROW_COUNT,
    COUNT(DISTINCT FIELD_ID) AS DISTINCT_FIELDS
FROM validated
GROUP BY STATUS
ORDER BY STATUS;

What we want after the fix

For the populated Type 4 rows, ideally:

PASS              138481    7
VALUE_MISMATCH          0    0
KEY_MISSING             0    0

There will also be SOURCE_NULL rows — that's fine.

And if you want to see only failures, change the final SELECT to:

SELECT
    CONTENT_ID,
    FIELD_ID,
    SQL_FIELD_NAME,
    RAW_VALUE,
    CURATED_VALUE,
    STATUS
FROM validated
WHERE STATUS IN (
    'VALUE_MISMATCH',
    'KEY_MISSING',
    'NO_META_MAPPING'
)
ORDER BY CONTENT_ID, FIELD_ID;

If that second query returns empty, the Type 4 mapping fix passed.