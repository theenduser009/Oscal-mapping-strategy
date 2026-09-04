# OSCAL Mapping Strategy

## SSP notebook cells

Open the [SSP Notebook Cell Library](docs/notebook-cells/README.md) to copy each verified cell in execution order.

- [Cell 1 - Configuration and safety guard](docs/notebook-cells/01-configuration-and-safety.md)
- [Cell 2 - Sample populated candidate props](docs/notebook-cells/02-sample-populated-props.md)
- [Cell 3 - Count populated candidate props](docs/notebook-cells/03-count-populated-props.md)

## Existing Type 4 SQL reference

Yep — here’s the direct SQL to see the actual RAW source value and the actual CURATED_JSON value side by side for Type 4.

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
        amf.SQL_FIELD_NAME,
        r.RAW_VALUE,
        GET(r.CURATED_JSON, amf.SQL_FIELD_NAME) AS CURATED_VALUE
    FROM raw_fields r
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
)

SELECT
    CONTENT_ID,
    FIELD_ID,
    SQL_FIELD_NAME,
    TYPE_ID,
    RAW_VALUE,
    CURATED_VALUE
FROM mapped
WHERE TYPE_ID = 4
  AND RAW_VALUE IS NOT NULL
  AND NOT IS_NULL_VALUE(RAW_VALUE)
ORDER BY CONTENT_ID, FIELD_ID;

You should literally see:

RAW_VALUE
{"OtherText":null,"ValuesListIds":[175168]}

CURATED_VALUE
[175168]

After you rerun the corrected Matillion update on fresh/null-curated rows, you want to see:

RAW_VALUE
{"OtherText":null,"ValuesListIds":[175168]}

CURATED_VALUE
{"OtherText":null,"ValuesListIds":[175168]}

If you want to check one specific content ID, add this:

AND TRIM(CONTENT_ID::STRING) = '186731'

to the final WHERE.