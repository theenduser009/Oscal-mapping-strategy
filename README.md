Yes — this is a different raw table, ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_RAW, and the screenshot shows the same general symptom:

RAW contains something like:

{
  "OtherText": null,
  "ValuesListIds": [175168]
}

but CURATED currently has only:

[175168]

So if this table is using the same shared Matillion update logic, then this strongly suggests its field is also Archer Type 4 and the old logic is still doing:

WHEN 4 THEN TO_VARIANT(V:"ValuesListIds")

instead of preserving the whole object.

I would not assume the type though. Let’s prove it for this table first with one SQL. Run this against the Authoritative Sources Section raw table:

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
        f.key::STRING        AS FIELD_ID,
        f.value:"Type"       AS TYPE_ID,
        f.value:"Value"      AS RAW_VALUE,
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
        r.RAW_VALUE,
        amf.SQL_FIELD_NAME,
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
WHERE RAW_VALUE IS NOT NULL
  AND TYPEOF(RAW_VALUE) = 'OBJECT'
  AND RAW_VALUE:"ValuesListIds" IS NOT NULL
ORDER BY CONTENT_ID, FIELD_ID;

This will tell us definitively whether that field is TYPE_ID = 4.

If it is, then yes: the same fix applies to this table too, and that is actually good news because your Matillion SQL is variable-driven with ${jv_raw_table_name}. One corrected generic update can handle all these Archer raw tables consistently.