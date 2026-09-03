Yep — here is that last SQL again, corrected to compare FIELD_ID values as text, not numbers.

WITH raw_fields AS (
    SELECT
        t.CONTENT_ID,
        f.key::STRING AS FIELD_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW t,
         LATERAL FLATTEN(
             INPUT => t.RAW_DATA:"RequestedObject":"FieldContents"
         ) f
),

expected AS (
    SELECT
        r.CONTENT_ID,
        r.FIELD_ID,
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
        e.FIELD_ID,
        e.EXPECTED_CURATED_KEY,
        COUNT(*) AS RAW_OCCURRENCES,

        COUNT_IF(
            GET(t.CURATED_JSON, e.EXPECTED_CURATED_KEY) IS NOT NULL
        ) AS FOUND_COUNT,

        COUNT_IF(
            GET(t.CURATED_JSON, e.EXPECTED_CURATED_KEY) IS NULL
        ) AS MISSING_COUNT

    FROM expected e

    JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW t
        ON TRIM(t.CONTENT_ID::STRING)
         = TRIM(e.CONTENT_ID::STRING)

    GROUP BY
        e.FIELD_ID,
        e.EXPECTED_CURATED_KEY
)

SELECT
    FIELD_ID,
    EXPECTED_CURATED_KEY,
    RAW_OCCURRENCES,
    FOUND_COUNT,
    MISSING_COUNT
FROM validation
WHERE MISSING_COUNT > 0
ORDER BY MISSING_COUNT DESC;

This is the one we want now.

The key question is: for those 406 FieldIDs, are they truly always missing, or are they found in some rows and missing in others?

Look at FOUND_COUNT and MISSING_COUNT for the first few rows and send me those values.