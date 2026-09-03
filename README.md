Yep — I can read the result. And this tells us something important.

The output is still showing lots of rows like:

FIELD_ID   EXPECTED_CURATED_KEY                 POPULATED_RAW_COUNT  FOUND  MISSING
23260      PIA_REQUIRED                         2813                 0      2813
23261      SECURITY_CATEGORY_VERSION_COMBO      2813                 0      2813
...

So my previous “populated” filter is still wrong for Archer's FieldContents structure. f.value itself is apparently an Archer field-content object, so the object exists on every record even when its actual inner value is empty. That's why we're still getting 2813.

We should not trust these missing counts yet.

The right next step is much smaller: inspect the actual RAW structure for one field, PIA_REQUIRED (FIELD_ID 23260), before writing another generalized query.

Run:

SELECT
    t.CONTENT_ID,
    f.key::STRING AS FIELD_ID,
    f.value AS FIELD_CONTENT,
    TYPEOF(f.value) AS FIELD_CONTENT_TYPE,
    GET(t.CURATED_JSON, 'PIA_REQUIRED') AS CURATED_VALUE
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW t,
     LATERAL FLATTEN(
         INPUT => IFF(
             TYPEOF(t.RAW_DATA) = 'ARRAY',
             t.RAW_DATA[0],
             t.RAW_DATA
         ):"RequestedObject":"FieldContents"
     ) f
WHERE TRIM(f.key::STRING) = '23260'
LIMIT 10;

Just run this. I want to see what FIELD_CONTENT actually looks like — e.g. whether Archer stores the real value under Value, Values, FieldValue, value, etc.

Once we see that structure, I'll correct the validation query based on the actual Archer value, rather than guessing again.