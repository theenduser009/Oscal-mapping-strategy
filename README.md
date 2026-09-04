Yes — I think we should stop assuming yesterday’s update was fully correct. What your new table proves is that the old behavior still exists there: Type 4 is being reduced from the full object to only ValuesListIds.

So first, yes, you can filter directly for Type 4 and inspect it:

SELECT
    t.CONTENT_ID,
    f.key::STRING AS FIELD_ID,
    f.value:"Type"::NUMBER AS TYPE_ID,
    f.value:"Value" AS RAW_VALUE
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_RAW t,
     LATERAL FLATTEN(
         INPUT => IFF(
             TYPEOF(t.RAW_DATA) = 'ARRAY',
             t.RAW_DATA[0],
             t.RAW_DATA
         ):"RequestedObject":"FieldContents"
     ) f
WHERE f.value:"Type"::NUMBER = 4
  AND f.value:"Value" IS NOT NULL
LIMIT 100;

From your screenshot, those rows are definitely TYPE_ID = 4.

What I think happened is one of these two things: either the Matillion job for this table is still using the old update SQL, or the new SQL was only tested/applied on the Authorization Package table and not propagated through the variable-driven orchestration.

And yes, I would also check the other types before we declare the generic update done. We already know Type 4 is lossy. The safest next validation is to inventory every TYPE_ID and compare the RAW value shape against the curated shape.

Run this:

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
        r.*,
        amf.SQL_FIELD_NAME,
        GET(r.CURATED_JSON, amf.SQL_FIELD_NAME) AS CURATED_VALUE
    FROM raw_fields r
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRIM(amf.FIELD_ID::STRING)
         = TRIM(r.FIELD_ID::STRING)
)

SELECT
    TYPE_ID,
    TYPEOF(RAW_VALUE) AS RAW_VALUE_TYPE,
    TYPEOF(CURATED_VALUE) AS CURATED_VALUE_TYPE,
    COUNT(*) AS ROW_COUNT
FROM mapped
WHERE RAW_VALUE IS NOT NULL
GROUP BY
    TYPE_ID,
    TYPEOF(RAW_VALUE),
    TYPEOF(CURATED_VALUE)
ORDER BY TYPE_ID, ROW_COUNT DESC;

That will tell us quickly whether Type 4 is the only suspicious transformation or whether other Archer types are also changing shape in ways we need to review.

My recommendation: do not update the Matillion SQL again yet. Run this type inventory first. Then we fix only the types that are actually lossy.