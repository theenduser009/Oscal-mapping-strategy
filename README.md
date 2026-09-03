Yes. Let’s do one read-only gap query first against the Authorization Package raw table.

This checks: a FieldID exists in RAW_DATA, has actual values, but cannot resolve to ARCHER_META_FIELD.SQL_FIELD_NAME.

WITH norm AS (
    SELECT
        IFF(
            TYPEOF(RAW_DATA) = 'ARRAY',
            RAW_DATA[0],
            RAW_DATA
        ) AS obj
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    WHERE RAW_DATA IS NOT NULL
),

raw_fields AS (
    SELECT
        f.key::STRING AS FIELD_ID,
        COUNT(*) AS OCCURRENCES,
        COUNT_IF(
            f.value IS NOT NULL
            AND f.value::STRING NOT IN ('', 'null', '[]', '{}')
        ) AS POPULATED_COUNT
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => n.obj:"RequestedObject":"FieldContents"
         ) f
    WHERE f.key IS NOT NULL
    GROUP BY f.key::STRING
)

SELECT
    r.FIELD_ID,
    r.OCCURRENCES,
    r.POPULATED_COUNT,
    amf.SQL_FIELD_NAME,
    amf.LEVEL_ID,
    CASE
        WHEN amf.FIELD_ID IS NULL
            THEN 'FIELD_ID NOT IN ARCHER_META_FIELD'
        WHEN amf.SQL_FIELD_NAME IS NULL
            THEN 'META EXISTS BUT SQL_FIELD_NAME IS NULL'
    END AS MAPPING_GAP
FROM raw_fields r
LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
    ON TRY_TO_NUMBER(amf.FIELD_ID) = TRY_TO_NUMBER(r.FIELD_ID)
WHERE r.POPULATED_COUNT > 0
  AND (
      amf.FIELD_ID IS NULL
      OR amf.SQL_FIELD_NAME IS NULL
  )
ORDER BY r.POPULATED_COUNT DESC;

What this tells us

If this returns rows, those are real source fields containing data that may be getting lost before OSCAL mapping even begins.

For example:

FIELD_ID   POPULATED_COUNT   SQL_FIELD_NAME   MAPPING_GAP
123456     1800              NULL             META EXISTS BUT SQL_FIELD_NAME IS NULL

That is exactly the kind of thing your manager was asking about: “fields that have data that we haven't mapped.”

Run only this query first. Send me the result. Then we’ll do the second comparison: fields that successfully reached CURATED_JSON but have no row in your Archer→OSCAL mapping CSV.