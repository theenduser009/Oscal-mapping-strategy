Yes — these screenshots explain what is happening.

The 406 “missing” fields are mostly a false alarm from our previous validation. Look at rows like:

RAW_OCCURRENCES = 2813
FOUND_COUNT     = 0
MISSING_COUNT   = 2813

and then later:

RAW_OCCURRENCES = 2813
FOUND_COUNT     = 1
MISSING_COUNT   = 2812

That strongly indicates FieldContents contains the field structurally on essentially every Archer record, even when its value is NULL/empty. Your CURATED conversion doesn't necessarily create a key for an empty value, so our previous query incorrectly called those cases “missing.”

What we actually need to ask is:

> When RAW_DATA has a real populated value for a FieldID, does its mapped SQL field appear in CURATED_JSON on that same record?



Run this corrected validation:

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

raw_populated AS (
    SELECT
        n.CONTENT_ID,
        f.key::STRING AS FIELD_ID,
        f.value AS RAW_VALUE,
        n.CURATED_JSON
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => n.OBJ:"RequestedObject":"FieldContents"
         ) f
    WHERE f.key IS NOT NULL

      /* ONLY fields that actually contain data */
      AND f.value IS NOT NULL
      AND NOT IS_NULL_VALUE(f.value)

      AND COALESCE(
            NULLIF(TRIM(TO_JSON(f.value)), ''),
            'null'
          ) NOT IN ('null', '""', '[]', '{}')
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

    FROM raw_populated r

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
ORDER BY
    MISSING_COUNT DESC,
    FIELD_ID;

This is the meaningful test.

Your screenshot already gives us a clue: a field showing 2813 / 1 / 2812 may simply have one actual populated record out of 2,813, not 2,812 mappings being lost.

So ignore the earlier 406 missing number for now. Run this corrected query. If it returns 0 rows, then populated top-level RAW fields are successfully reaching CURATED_JSON. If it still returns rows, those are the ones we investigate as genuine conversion gaps.