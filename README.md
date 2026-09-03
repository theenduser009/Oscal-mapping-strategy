Yes — field ID → field name only. That’s the validation. Forget value transformation for now.

We want to prove:

RAW_DATA FieldId → ARCHER_META_FIELD.FIELD_ID → SQL_FIELD_NAME → key exists in CURATED_JSON on the same row.

Use this SQL:

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
    WHERE f.value:"Value" IS NOT NULL
      AND NOT IS_NULL_VALUE(f.value:"Value")
),

mapped AS (
    SELECT
        r.CONTENT_ID,
        r.FIELD_ID,
        amf.SQL_FIELD_NAME,
        r.CURATED_JSON
    FROM raw_fields r
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
)

SELECT
    FIELD_ID,
    SQL_FIELD_NAME,
    COUNT(*) AS POPULATED_RAW_COUNT,
    COUNT_IF(
        SQL_FIELD_NAME IS NOT NULL
        AND GET(CURATED_JSON, SQL_FIELD_NAME) IS NOT NULL
    ) AS MAPPED_TO_CURATED_COUNT,
    COUNT_IF(
        SQL_FIELD_NAME IS NULL
        OR GET(CURATED_JSON, SQL_FIELD_NAME) IS NULL
    ) AS NOT_MAPPED_COUNT
FROM mapped
GROUP BY
    FIELD_ID,
    SQL_FIELD_NAME
HAVING NOT_MAPPED_COUNT > 0
ORDER BY NOT_MAPPED_COUNT DESC;

If this returns empty, then your FieldID → SQL_FIELD_NAME → CURATED_JSON key mapping is working for every populated top-level field.

That’s the exact thing we’re validating right now.