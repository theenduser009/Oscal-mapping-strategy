Great. 0 rows from both checks is good. It means we have not found evidence that populated Archer fields are being lost because of the ARCHER_META_FIELD lookup.

Now the next validation should answer the manager's actual question:

> Which fields have data in CURATED_JSON, and how populated are they?



Since RAW and CURATED_JSON are columns in the same table, we can do this entirely in Snowflake SQL.

Run this:

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
    FIELD_NAME,
    ROW_COUNT,
    POPULATED_COUNT,
    ROUND(
        100.0 * POPULATED_COUNT / NULLIF(ROW_COUNT, 0),
        2
    ) AS POPULATED_PCT
FROM curated_fields
ORDER BY POPULATED_COUNT DESC, FIELD_NAME;

This gives us the actual CURATED_JSON field inventory, for example:

FIELD_NAME              ROW_COUNT   POPULATED_COUNT   POPULATED_PCT
PACKAGE_TYPE             3514        3514              100.00
...

This is important because then we can split the fields into exactly what the team discussed:

high-population fields → must ensure they have OSCAL mappings
very sparse fields → candidate list to discuss with Josh
zero-data fields → retirement/problem-field discussion

After you run this, don't manually inspect hundreds of rows. Show me the result/count. The next SQL will compare this inventory against the mapping coverage.