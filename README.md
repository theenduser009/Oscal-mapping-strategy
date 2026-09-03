Perfect — now we know the RAW structure. The actual value is under f.value:"Value".

For PIA_REQUIRED (23260), your screenshot shows "Value": null, so those records should never have been counted as populated. That explains the misleading 2813 missing count.

Now rerun the validation using the actual Value property:

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
        f.value:"Value" AS RAW_VALUE,
        n.CURATED_JSON
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => n.OBJ:"RequestedObject":"FieldContents"
         ) f

    /* ONLY actual populated Archer values */
    WHERE f.value:"Value" IS NOT NULL
      AND NOT IS_NULL_VALUE(f.value:"Value")
),

expected AS (
    SELECT
        r.CONTENT_ID,
        r.FIELD_ID,
        r.RAW_VALUE,
        r.CURATED_JSON,
        COALESCE(
            amf.SQL_FIELD_NAME,
            'FIELD_' || r.FIELD_ID
        ) AS EXPECTED_CURATED_KEY
    FROM raw_fields r

    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
),

validation AS (
    SELECT
        FIELD_ID,
        EXPECTED_CURATED_KEY,
        COUNT(*) AS POPULATED_RAW_COUNT,

        COUNT_IF(
            GET(CURATED_JSON, EXPECTED_CURATED_KEY) IS NOT NULL
        ) AS FOUND_COUNT,

        COUNT_IF(
            GET(CURATED_JSON, EXPECTED_CURATED_KEY) IS NULL
        ) AS MISSING_COUNT

    FROM expected
    GROUP BY
        FIELD_ID,
        EXPECTED_CURATED_KEY
)

SELECT
    FIELD_ID,
    EXPECTED_CURATED_KEY,
    POPULATED_RAW_COUNT,
    FOUND_COUNT,
    MISSING_COUNT
FROM validation
WHERE MISSING_COUNT > 0
ORDER BY MISSING_COUNT DESC;

This is the result I care about now. The earlier 406 missing number is invalid because we were counting the Archer field wrapper object instead of its "Value".

If this returns 0 rows, top-level populated RAW values are making it into CURATED_JSON. If it returns rows, we finally have a credible list of actual conversion gaps.