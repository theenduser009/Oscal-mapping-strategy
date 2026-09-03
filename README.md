Exactly. We are validating only this:

Same row, same table

RAW_DATA FieldID → ARCHER_META_FIELD.SQL_FIELD_NAME → that field name exists as a key in CURATED_JSON

Run this read-only SQL:

WITH raw_fields AS (
    SELECT
        t.CONTENT_ID,
        t.RAW_DATA:"RequestedObject":"Id"::NUMBER AS REQUESTED_OBJECT_ID,
        t.RAW_DATA:"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID,
        f.key::STRING AS FIELD_ID,
        f.value AS RAW_VALUE
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW t,
         LATERAL FLATTEN(
             INPUT => t.RAW_DATA:"RequestedObject":"FieldContents"
         ) f
    WHERE t.RAW_DATA IS NOT NULL
),

expected_mapping AS (
    SELECT
        r.CONTENT_ID,
        r.REQUESTED_OBJECT_ID,
        r.LEVEL_ID,
        r.FIELD_ID,
        r.RAW_VALUE,

        /* This is the expected CURATED_JSON key */
        COALESCE(
            amf.SQL_FIELD_NAME,
            'FIELD_' || r.FIELD_ID
        ) AS EXPECTED_CURATED_KEY

    FROM raw_fields r

    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
        ON TRY_TO_NUMBER(amf.FIELD_ID)
         = TRY_TO_NUMBER(r.FIELD_ID)
),

curated_keys AS (
    SELECT
        t.CONTENT_ID,
        k.key::STRING AS CURATED_KEY
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW t,
         LATERAL FLATTEN(INPUT => t.CURATED_JSON) k
),

validation AS (
    SELECT
        e.CONTENT_ID,
        e.REQUESTED_OBJECT_ID,
        e.LEVEL_ID,
        e.FIELD_ID,
        e.EXPECTED_CURATED_KEY,
        e.RAW_VALUE,

        CASE
            WHEN c.CURATED_KEY IS NOT NULL
                THEN 'FOUND_IN_CURATED'
            ELSE 'MISSING_FROM_CURATED'
        END AS VALIDATION_STATUS

    FROM expected_mapping e

    LEFT JOIN curated_keys c
        ON c.CONTENT_ID = e.CONTENT_ID
       AND UPPER(c.CURATED_KEY)
         = UPPER(e.EXPECTED_CURATED_KEY)
)

SELECT
    VALIDATION_STATUS,
    COUNT(*) AS FIELD_OCCURRENCES,
    COUNT(DISTINCT FIELD_ID) AS DISTINCT_FIELD_IDS
FROM validation
GROUP BY VALIDATION_STATUS
ORDER BY VALIDATION_STATUS;

What we want

Ideally:

FOUND_IN_CURATED      xxxxx     426
MISSING_FROM_CURATED      0       0

This is much closer to the actual question than our earlier queries because we're validating the conversion itself record-by-record, rather than bringing OSCAL/canonical mapping into it.

Run this one and give me just the result counts. If MISSING_FROM_CURATED is greater than 0, our next SQL will show exactly which FieldIDs/SQL field names are missing and on which records.