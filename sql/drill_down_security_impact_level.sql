-- Standalone, read-only security-impact-level drill-down.
-- Change only this test CONTENT_ID.

SET TEST_CONTENT_ID = '565189';

WITH security_impact AS (
    SELECT
        child.SOURCE_RECORD_ID,
        child.ELEMENT_TYPE,
        child.OSCAL_UUID,
        child.METADATA_JSON AS WRITTEN_PAYLOAD,
        TRY_PARSE_JSON(child.METADATA_JSON::STRING) AS PAYLOAD_JSON,
        parent.ELEMENT_TYPE AS PARENT_ELEMENT_TYPE,
        parent.OSCAL_UUID AS PARENT_OSCAL_UUID,
        dependency.DEPENDENCY_TYPE
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT child
    LEFT JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY dependency
        ON dependency.FK_TARGET_ELEMENT_HASH = child.PK_OSCAL_SSP_ELEMENT_HASH
    LEFT JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT parent
        ON parent.PK_OSCAL_SSP_ELEMENT_HASH = dependency.FK_SOURCE_ELEMENT_HASH
    WHERE TRIM(child.SOURCE_RECORD_ID::STRING) = $TEST_CONTENT_ID
      AND child.ELEMENT_TYPE = 'security-impact-level'
)
SELECT
    SOURCE_RECORD_ID,
    'system-security-plan.system-characteristics.security-impact-level' AS OSCAL_PATH,
    ELEMENT_TYPE,
    OSCAL_UUID,
    WRITTEN_PAYLOAD,
    PAYLOAD_JSON:"security-objective-confidentiality"::STRING
        AS CONFIDENTIALITY,
    PAYLOAD_JSON:"security-objective-integrity"::STRING
        AS INTEGRITY,
    PAYLOAD_JSON:"security-objective-availability"::STRING
        AS AVAILABILITY,
    PARENT_ELEMENT_TYPE,
    PARENT_OSCAL_UUID,
    DEPENDENCY_TYPE
FROM security_impact
ORDER BY OSCAL_UUID;

