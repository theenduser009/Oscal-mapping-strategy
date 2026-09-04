Yes — the query we used to validate FieldID → SQL_FIELD_NAME mapping and compare RAW vs CURATED was this pattern.

For one CONTENT_ID like 565189:

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
    WHERE TRIM(t.CONTENT_ID::STRING) = '565189'
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
),

mapped AS (
    SELECT
        r.CONTENT_ID,
        r.FIELD_ID,
        r.RAW_VALUE,
        amf.SQL_FIELD_NAME,
        r.CURATED_JSON
    FROM raw_fields r
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
)

SELECT
    CONTENT_ID,
    FIELD_ID,
    SQL_FIELD_NAME,
    RAW_VALUE,

    GET(CURATED_JSON, SQL_FIELD_NAME) AS CURATED_VALUE,

    CASE
        WHEN SQL_FIELD_NAME IS NULL
            THEN 'NO_META_MAPPING'

        WHEN GET(CURATED_JSON, SQL_FIELD_NAME) IS NULL
            THEN 'KEY_NOT_PRESENT'

        WHEN IS_NULL_VALUE(GET(CURATED_JSON, SQL_FIELD_NAME))
            THEN 'KEY_PRESENT_JSON_NULL'

        ELSE 'KEY_PRESENT_WITH_VALUE'
    END AS CURATED_KEY_STATUS

FROM mapped
ORDER BY TRY_TO_NUMBER(FIELD_ID);

This checks exactly:

RAW FieldID → ARCHER_META_FIELD.SQL_FIELD_NAME → same key in CURATED_JSON

And it also shows RAW_VALUE beside CURATED_VALUE, so you can visually validate cases like Type 4 where RAW had:

{
  "OtherText": null,
  "ValuesListIds": [84046]
}

but old CURATED had only:

[84046]

After your updated SQL, that should now preserve the whole object.