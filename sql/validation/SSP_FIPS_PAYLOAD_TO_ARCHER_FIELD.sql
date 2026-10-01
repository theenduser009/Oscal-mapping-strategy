-- SSP FIPS / security-impact payload -> Archer source-field trace
-- READ ONLY. One clear query.
--
-- Change only TEST_CONTENT_ID.
-- This shows, for one Archer Authorization Package record:
--   1) the committed OSCAL security-impact-level payload,
--   2) each reviewed Archer candidate field,
--   3) its raw ValuesListIds value,
--   4) the resolved Archer label,
--   5) the exact OSCAL objective member/path,
--   6) whether that Archer field actually contributed to the committed OSCAL value.
--
-- NOTE:
-- SECURITY_CATEGORY is intentionally not in this list. In the current mapping it
-- maps to system-security-plan.system-characteristics.security-sensitivity-level,
-- not to security-impact-level.security-objective-*.

SET TEST_CONTENT_ID = '867022';

WITH FIELD_MAP AS (
    SELECT COLUMN1 AS ARCHER_FIELD_NAME, COLUMN2 AS OSCAL_MEMBER
    FROM VALUES
      ('RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY', 'security-objective-confidentiality'),
      ('CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',     'security-objective-confidentiality'),
      ('RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',       'security-objective-integrity'),
      ('INTEGRITY_CONTROL_CATEGORY_OVERRIDE',           'security-objective-integrity'),
      ('PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',        'security-objective-integrity'),
      ('RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',     'security-objective-availability'),
      ('AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',        'security-objective-availability'),
      ('PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',     'security-objective-availability'),
      ('CNSS_CONFIDENTIALITY_RATING',                   'security-objective-confidentiality'),
      ('CNSS_INTEGRITY_RATING',                         'security-objective-integrity'),
      ('CNSS_AVAILABILITY_RATING',                      'security-objective-availability')
),
SRC AS (
    SELECT DISTINCT
        CONTENT_ID::STRING AS ARCHER_CONTENT_ID,
        CURATED_JSON
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    WHERE TRIM(CONTENT_ID::STRING) = $TEST_CONTENT_ID
),
SOURCE_FIELDS AS (
    SELECT
        S.ARCHER_CONTENT_ID,
        M.ARCHER_FIELD_NAME,
        M.OSCAL_MEMBER,
        GET(S.CURATED_JSON, M.ARCHER_FIELD_NAME) AS ARCHER_RAW_VALUE,
        GET(
            GET(GET(S.CURATED_JSON, M.ARCHER_FIELD_NAME), 'ValuesListIds'),
            0
        )::STRING AS ARCHER_SELECT_VALUE_ID
    FROM SRC S
    CROSS JOIN FIELD_MAP M
),
RESOLVED AS (
    SELECT
        F.ARCHER_CONTENT_ID,
        F.ARCHER_FIELD_NAME,
        F.OSCAL_MEMBER,
        F.ARCHER_RAW_VALUE,
        F.ARCHER_SELECT_VALUE_ID,
        V.SELECT_VALUE_NAME::STRING AS ARCHER_RESOLVED_LABEL
    FROM SOURCE_FIELDS F
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE V
      ON TRIM(V.SELECT_VALUE_ID::STRING) = TRIM(F.ARCHER_SELECT_VALUE_ID)
),
LINEAGE AS (
    SELECT DISTINCT
        SOURCE_RECORD_ID::STRING AS ARCHER_CONTENT_ID,
        METADATA_JSON:"value"::STRING AS ARCHER_FIELD_NAME
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE TRIM(SOURCE_RECORD_ID::STRING) = $TEST_CONTENT_ID
      AND ELEMENT_TYPE = 'props'
      AND METADATA_JSON:"name"::STRING = 'source-field'
),
IMPACT AS (
    SELECT
        SOURCE_RECORD_ID::STRING AS ARCHER_CONTENT_ID,
        METADATA_JSON AS OSCAL_SECURITY_IMPACT_PAYLOAD
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE TRIM(SOURCE_RECORD_ID::STRING) = $TEST_CONTENT_ID
      AND ELEMENT_TYPE = 'security-impact-level'
)
SELECT
    R.ARCHER_CONTENT_ID,
    I.OSCAL_SECURITY_IMPACT_PAYLOAD,
    'system-security-plan.system-characteristics.security-impact-level.'
        || R.OSCAL_MEMBER AS OSCAL_ELEMENT_PATH,
    GET(I.OSCAL_SECURITY_IMPACT_PAYLOAD, R.OSCAL_MEMBER)::STRING AS OSCAL_VALUE,
    R.ARCHER_FIELD_NAME,
    R.ARCHER_RAW_VALUE,
    R.ARCHER_SELECT_VALUE_ID,
    R.ARCHER_RESOLVED_LABEL,
    IFF(L.ARCHER_FIELD_NAME IS NOT NULL, 'Y', 'N') AS USED_TO_BUILD_OSCAL
FROM RESOLVED R
LEFT JOIN LINEAGE L
  ON L.ARCHER_CONTENT_ID = R.ARCHER_CONTENT_ID
 AND L.ARCHER_FIELD_NAME = R.ARCHER_FIELD_NAME
LEFT JOIN IMPACT I
  ON I.ARCHER_CONTENT_ID = R.ARCHER_CONTENT_ID
ORDER BY
    R.OSCAL_MEMBER,
    USED_TO_BUILD_OSCAL DESC,
    R.ARCHER_FIELD_NAME;
