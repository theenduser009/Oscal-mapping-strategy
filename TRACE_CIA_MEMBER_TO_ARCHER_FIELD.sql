-- TRACE ONE CIA MEMBER TO ITS ARCHER SOURCE FIELD(S)
-- Date: 2026-10-02
-- READ ONLY.
--
-- Change only these two values.
SET TEST_CONTENT_ID = '866211';
SET TEST_MEMBER = 'security-objective-availability';
-- Other valid TEST_MEMBER values:
--   security-objective-confidentiality
--   security-objective-integrity
--   security-objective-availability

WITH field_map AS (
    SELECT *
    FROM VALUES
        ('RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY', 'security-objective-confidentiality'),
        ('CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',    'security-objective-confidentiality'),
        ('RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',       'security-objective-integrity'),
        ('INTEGRITY_CONTROL_CATEGORY_OVERRIDE',          'security-objective-integrity'),
        ('AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',       'security-objective-availability'),
        ('RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',    'security-objective-availability'),
        ('PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',       'security-objective-integrity'),
        ('PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',    'security-objective-availability'),
        ('CNSS_AVAILABILITY_RATING',                     'security-objective-availability'),
        ('CNSS_CONFIDENTIALITY_RATING',                  'security-objective-confidentiality'),
        ('CNSS_INTEGRITY_RATING',                        'security-objective-integrity')
    AS m(SOURCE_FIELD_NAME, OSCAL_MEMBER)
),
impact AS (
    SELECT
        PK_OSCAL_SSP_ELEMENT_HASH AS IMPACT_KEY,
        SOURCE_RECORD_ID::VARCHAR AS SOURCE_RECORD_ID,
        GET(
            TRY_PARSE_JSON(METADATA_JSON::STRING),
            $TEST_MEMBER
        )::VARCHAR AS OSCAL_VALUE,
        METADATA_JSON AS SECURITY_IMPACT_PAYLOAD
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE TRIM(SOURCE_RECORD_ID::VARCHAR) = $TEST_CONTENT_ID
      AND ELEMENT_TYPE = 'security-impact-level'
),
system_characteristics_parent AS (
    SELECT
        i.SOURCE_RECORD_ID,
        i.OSCAL_VALUE,
        i.SECURITY_IMPACT_PAYLOAD,
        p.PK_OSCAL_SSP_ELEMENT_HASH AS SYSTEM_CHARACTERISTICS_KEY
    FROM impact i
    JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f
      ON f.FK_TARGET_ELEMENT_HASH = i.IMPACT_KEY
    JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT p
      ON p.PK_OSCAL_SSP_ELEMENT_HASH = f.FK_SOURCE_ELEMENT_HASH
     AND p.ELEMENT_TYPE = 'system-characteristics'
),
lineage_props AS (
    SELECT
        p.SOURCE_RECORD_ID,
        p.OSCAL_VALUE,
        p.SECURITY_IMPACT_PAYLOAD,
        TRY_PARSE_JSON(c.METADATA_JSON::STRING):"value"::VARCHAR AS SOURCE_FIELD_NAME
    FROM system_characteristics_parent p
    JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f
      ON f.FK_SOURCE_ELEMENT_HASH = p.SYSTEM_CHARACTERISTICS_KEY
    JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT c
      ON c.PK_OSCAL_SSP_ELEMENT_HASH = f.FK_TARGET_ELEMENT_HASH
    WHERE c.ELEMENT_TYPE = 'props'
      AND TRY_PARSE_JSON(c.METADATA_JSON::STRING):"name"::VARCHAR = 'source-field'
)
SELECT
    l.SOURCE_RECORD_ID,
    $TEST_MEMBER AS OSCAL_MEMBER,
    l.OSCAL_VALUE,
    l.SOURCE_FIELD_NAME AS ARCHER_SOURCE_FIELD,
    l.SECURITY_IMPACT_PAYLOAD
FROM lineage_props l
JOIN field_map m
  ON m.SOURCE_FIELD_NAME = l.SOURCE_FIELD_NAME
 AND m.OSCAL_MEMBER = $TEST_MEMBER
ORDER BY l.SOURCE_FIELD_NAME;
