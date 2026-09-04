Next: do a read-only validation across the whole table to prove the proposed Type 4 behavior would preserve the full object everywhere.

Run this on ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_RAW:

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
        r.*,
        amf.SQL_FIELD_NAME,
        GET(r.CURATED_JSON, amf.SQL_FIELD_NAME) AS CURRENT_CURATED_VALUE
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
        TYPE_ID,
        RAW_VALUE,
        CURRENT_CURATED_VALUE,

        /* proposed new Type 4 behavior */
        TO_VARIANT(RAW_VALUE) AS EXPECTED_CURATED_VALUE,

        CASE
            WHEN TYPE_ID = 4
             AND TYPEOF(RAW_VALUE) = 'OBJECT'
             AND TYPEOF(CURRENT_CURATED_VALUE) = 'ARRAY'
                THEN 'OLD_TYPE4_LOGIC_FOUND'

            WHEN TYPE_ID = 4
             AND RAW_VALUE = CURRENT_CURATED_VALUE
                THEN 'ALREADY_CORRECT'

            ELSE 'REVIEW'
        END AS STATUS
    FROM mapped
    WHERE TYPE_ID = 4
      AND RAW_VALUE IS NOT NULL
      AND NOT IS_NULL_VALUE(RAW_VALUE)
)

SELECT
    STATUS,
    COUNT(*) AS ROW_COUNT,
    COUNT(DISTINCT FIELD_ID) AS DISTINCT_FIELDS
FROM validated
GROUP BY STATUS
ORDER BY STATUS;

What I expect from the table you just showed is a large count under:

OLD_TYPE4_LOGIC_FOUND

because current curated values are arrays while RAW values are objects.

If REVIEW = 0, then we have very strong evidence that the Type 4 fix is safe across this whole table. Then the next step is the controlled update using the new generic SQL.