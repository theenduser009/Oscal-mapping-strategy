Yes — the confusing part is that you are seeing two different kinds of “null” representations, and Snowflake/UI can display them differently.

In your result:

RAW_VALUE = null means the Archer JSON contains an explicit JSON null at "Value".

CURATED_VALUE = None usually means GET(CURATED_JSON, SQL_FIELD_NAME) returned SQL NULL because the key is not present.

CURATED_VALUE = null means the key is present in CURATED_JSON, but its value is explicit JSON null.


So these are not the same:

"FISMA_REPORTABLE" key missing entirely
→ GET(...) returns SQL NULL
→ UI may show None

"FISMA_REPORTABLE": null
→ key exists
→ GET(...) returns VARIANT JSON null
→ UI may show null

That explains exactly what you are seeing.

And the 578 rows makes sense too: for CONTENT_ID = 565189, there are 578 field entries in RAW_DATA:"RequestedObject":"FieldContents". That does not mean 578 populated values. It means 578 field definitions/slots exist for that record, many with "Value": null.

The most useful query now is one that distinguishes all three states clearly:

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
        r.*,
        amf.SQL_FIELD_NAME
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

This will remove the ambiguity.

The important distinction for changing the UPDATE is:

KEY_NOT_PRESENT
vs
KEY_PRESENT_JSON_NULL

Right now your current update is producing a mix of both. That is exactly what we need to normalize in the next change.