Yes — we can validate the proposed fix against the existing table without updating anything. I can’t execute against your Snowflake session from here, but this read-only query will simulate the new conversion and compare it with the current CURATED_JSON.

Run this against ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_RAW:

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
        n.CURATED_JSON,
        f.key::STRING          AS FIELD_ID,
        f.value:"Type"::NUMBER AS TYPE_ID,
        f.value:"Value"        AS V
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => n.OBJ:"RequestedObject":"FieldContents"
         ) f
),

mapped AS (
    SELECT
        r.*,
        amf.SQL_FIELD_NAME
    FROM raw_fields r
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
),

expected AS (
    SELECT
        CONTENT_ID,
        FIELD_ID,
        SQL_FIELD_NAME,
        TYPE_ID,
        V AS RAW_VALUE,

        CASE
            WHEN V IS NULL OR IS_NULL_VALUE(V)
                THEN PARSE_JSON('null')

            ELSE CASE TYPE_ID
                WHEN 1 THEN TO_VARIANT(NULLIF(V::STRING, ''))

                WHEN 2 THEN TO_VARIANT(
                    TRY_TO_NUMBER(NULLIF(V::STRING, ''))
                )

                WHEN 3 THEN TO_VARIANT(
                    TRY_TO_DATE(NULLIF(V::STRING, ''))
                )

                /* NEW FIX */
                WHEN 4 THEN TO_VARIANT(V)

                WHEN 6 THEN TO_VARIANT(
                    TRY_TO_NUMBER(NULLIF(V::STRING, ''))
                )

                WHEN 8 THEN TO_VARIANT(V)
                WHEN 9 THEN TO_VARIANT(V)
                WHEN 11 THEN TO_VARIANT(V)

                WHEN 20 THEN TO_VARIANT(
                    TRY_TO_NUMBER(NULLIF(V::STRING, ''))
                )

                WHEN 21 THEN TO_VARIANT(
                    TRY_TO_TIMESTAMP_NTZ(NULLIF(V::STRING, ''))
                )

                WHEN 22 THEN TO_VARIANT(
                    TRY_TO_TIMESTAMP_NTZ(NULLIF(V::STRING, ''))
                )

                WHEN 23 THEN TO_VARIANT(V)

                ELSE TO_VARIANT(V)
            END
        END AS EXPECTED_CURATED_VALUE,

        GET(CURATED_JSON, SQL_FIELD_NAME) AS CURRENT_CURATED_VALUE

    FROM mapped
    WHERE SQL_FIELD_NAME IS NOT NULL
)

SELECT
    TYPE_ID,
    FIELD_ID,
    SQL_FIELD_NAME,
    RAW_VALUE,
    CURRENT_CURATED_VALUE,
    EXPECTED_CURATED_VALUE,

    CASE
        WHEN TYPE_ID = 4
         AND TYPEOF(RAW_VALUE) = 'OBJECT'
         AND TYPEOF(CURRENT_CURATED_VALUE) = 'ARRAY'
            THEN 'TYPE_4_FIX_REQUIRED'

        WHEN EXPECTED_CURATED_VALUE = CURRENT_CURATED_VALUE
            THEN 'MATCH'

        WHEN IS_NULL_VALUE(EXPECTED_CURATED_VALUE)
         AND IS_NULL_VALUE(CURRENT_CURATED_VALUE)
            THEN 'MATCH'

        ELSE 'REVIEW'
    END AS VALIDATION_STATUS

FROM expected
ORDER BY
    VALIDATION_STATUS DESC,
    TYPE_ID,
    CONTENT_ID,
    FIELD_ID;

For your Type 4 example, you should see:

RAW:
{"OtherText":null,"ValuesListIds":[175168]}

CURRENT:
[175168]

EXPECTED:
{"OtherText":null,"ValuesListIds":[175168]}

STATUS:
TYPE_4_FIX_REQUIRED

That proves the proposed update before we touch the table.

Even better: after running it, tell me the counts for MATCH, TYPE_4_FIX_REQUIRED, and REVIEW. Then we’ll know whether Type 4 is the only change needed or whether another type needs attention too.