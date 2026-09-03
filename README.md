Exactly — 426 distinct fields in CURATED_JSON is a very useful baseline.

Now we need the SQL equivalent of the comparison we were trying to do in Python:

> Of those 426 populated curated fields, which ones have a mapping to OSCAL, and which do not?



Since your mapping CSV is not a Snowflake table, the cleanest SQL-only way is to load the CSV into a temporary/staging table first, then compare.

If you already loaded the mapping CSV into Snowflake somewhere, tell me that table name and I’ll give you the exact query immediately.

If not, the quickest path is to create a temporary mapping table from the CSV and then run:

WITH curated_fields AS (
    SELECT
        f.key::STRING AS FIELD_NAME,
        COUNT(*) AS ROW_COUNT,
        COUNT_IF(
            f.value IS NOT NULL
            AND f.value::STRING NOT IN ('', 'null', '[]', '{}')
        ) AS POPULATED_COUNT
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW t,
         LATERAL FLATTEN(INPUT => t.CURATED_JSON) f
    GROUP BY f.key::STRING
)

SELECT
    c.FIELD_NAME,
    c.ROW_COUNT,
    c.POPULATED_COUNT,
    ROUND(
        100.0 * c.POPULATED_COUNT / NULLIF(c.ROW_COUNT, 0),
        2
    ) AS POPULATED_PCT,
    m.OSCAL_ELEMENT_PATH,
    m.MAPPING_TYPE,
    CASE
        WHEN m.SOURCE_FIELD_NAME IS NULL
            THEN 'UNMAPPED'
        ELSE 'MAPPED'
    END AS MAPPING_STATUS
FROM curated_fields c
LEFT JOIN <YOUR_MAPPING_TABLE> m
    ON UPPER(TRIM(c.FIELD_NAME))
     = UPPER(TRIM(m.SOURCE_FIELD_NAME))
ORDER BY
    MAPPING_STATUS DESC,
    c.POPULATED_COUNT DESC,
    c.FIELD_NAME;

That gives you exactly what management is asking for:

FIELD_NAME
POPULATED_COUNT
POPULATED_PCT
OSCAL_ELEMENT_PATH
MAPPING_TYPE
MAPPED / UNMAPPED

And then the most important subset is:

...
WHERE m.SOURCE_FIELD_NAME IS NULL
  AND c.POPULATED_COUNT > 0

That is your “fields with real data but no OSCAL mapping” report.

So the next thing I need from you is just the name of the Snowflake table where the mapping CSV is loaded. If there isn’t one yet, we can create a temporary table from the CSV and keep the whole validation SQL-based.