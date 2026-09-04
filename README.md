Yes — here’s the SELECT-only dry run for ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_RAW. It simulates the proposed new curated value for Type 4 without updating anything.

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
),

mapped AS (
    SELECT
        r.CONTENT_ID,
        r.FIELD_ID,
        r.TYPE_ID,
        r.RAW_VALUE,
        amf.SQL_FIELD_NAME,
        GET(r.CURATED_JSON, amf.SQL_FIELD_NAME) AS CURRENT_CURATED_VALUE
    FROM raw_fields r
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
),

simulated AS (
    SELECT
        CONTENT_ID,
        FIELD_ID,
        SQL_FIELD_NAME,
        TYPE_ID,
        RAW_VALUE,
        CURRENT_CURATED_VALUE,

        CASE
            WHEN RAW_VALUE IS NULL
              OR IS_NULL_VALUE(RAW_VALUE)
                THEN PARSE_JSON('null')

            WHEN TYPE_ID = 4
                THEN TO_VARIANT(RAW_VALUE)

            ELSE CURRENT_CURATED_VALUE
        END AS PROPOSED_CURATED_VALUE
    FROM mapped
    WHERE SQL_FIELD_NAME IS NOT NULL
)

SELECT
    CONTENT_ID,
    FIELD_ID,
    SQL_FIELD_NAME,
    TYPE_ID,
    RAW_VALUE,
    CURRENT_CURATED_VALUE,
    PROPOSED_CURATED_VALUE,

    CASE
        WHEN TYPE_ID = 4
         AND TYPEOF(RAW_VALUE) = 'OBJECT'
         AND PROPOSED_CURATED_VALUE = RAW_VALUE
            THEN 'TYPE_4_FIX_OK'

        WHEN TYPE_ID <> 4
         AND PROPOSED_CURATED_VALUE = CURRENT_CURATED_VALUE
            THEN 'UNCHANGED'

        WHEN RAW_VALUE IS NULL
          OR IS_NULL_VALUE(RAW_VALUE)
            THEN 'SOURCE_NULL'

        ELSE 'REVIEW'
    END AS VALIDATION_STATUS

FROM simulated
ORDER BY
    TYPE_ID,
    CONTENT_ID,
    FIELD_ID;

What you want to see:

TYPE_4_FIX_OK

for those 7 Type 4 fields, and mostly:

UNCHANGED

for the other types.

That gives us a clean proof that the change fixes Type 4 without altering the rest of the existing curated behavior.