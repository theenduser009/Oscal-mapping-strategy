Yes — you found a real loss of information in the current RAW → CURATED SQL.

For those fields, the RAW "Value" is an object like:

{
  "OtherText": null,
  "ValuesListIds": [84046]
}

But your typed CTE currently has:

WHEN 4 THEN TO_VARIANT(V:"ValuesListIds")

So you are explicitly throwing away everything except ValuesListIds. That is why CURATED becomes only:

[84046]

and OtherText disappears.

If the goal of CURATED_JSON is to map FieldID → SQL field name without losing the source information, then I would change Type 4 to preserve the complete object:

WHEN 4 THEN TO_VARIANT(V)

Before changing the UPDATE, test that behavior for CONTENT_ID = 565189:

WITH norm AS (
    SELECT
        t.CONTENT_ID,
        IFF(
            TYPEOF(t.RAW_DATA) = 'ARRAY',
            t.RAW_DATA[0],
            t.RAW_DATA
        ) AS OBJ
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW t
    WHERE TRIM(t.CONTENT_ID::STRING) = '565189'
),

raw_fields AS (
    SELECT
        n.CONTENT_ID,
        f.key::STRING AS FIELD_ID,
        f.value:"Type"::NUMBER AS TYPE_ID,
        f.value:"Value" AS V
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
    FIELD_ID,
    SQL_FIELD_NAME,
    TYPE_ID,
    V AS RAW_VALUE,

    /* CURRENT behavior */
    V:"ValuesListIds" AS CURRENT_CURATED_LOGIC,

    /* PROPOSED behavior */
    V AS PROPOSED_CURATED_LOGIC

FROM mapped
WHERE TYPE_ID = 4
  AND V IS NOT NULL
ORDER BY FIELD_ID;

For something like HELPER_DEFINED_IMP_DETAILS, you should then see:

RAW_VALUE:
{"OtherText":null,"ValuesListIds":[84046]}

CURRENT_CURATED_LOGIC:
[84046]

PROPOSED_CURATED_LOGIC:
{"OtherText":null,"ValuesListIds":[84046]}

So yes: this one needs fixing.

And importantly, I would not change every type blindly. We found a specific issue: Type 4 is intentionally stripping part of the Archer value. Let's validate all Type 4 records first, then make that one precise change to the Matillion UPDATE.