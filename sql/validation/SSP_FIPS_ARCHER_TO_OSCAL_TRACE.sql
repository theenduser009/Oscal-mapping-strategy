-- SSP FIPS / security-impact trace
-- READ ONLY. No DML.
-- Purpose:
--   1) See the Archer FIPS candidate values for one CONTENT_ID.
--   2) Show exactly which Archer field maps to which OSCAL member.
--   3) Compare the Archer source field with the committed OSCAL value.
--
-- Change only TEST_CONTENT_ID.

SET TEST_CONTENT_ID = '867022';

-- ============================================================
-- 1. QUICK SOURCE VIEW: the 11 Archer FIPS/security-objective fields
-- ============================================================

SELECT
    CONTENT_ID::STRING AS ARCHER_CONTENT_ID,
    GET(CURATED_JSON, 'RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY')
        AS RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY,
    GET(CURATED_JSON, 'CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE')
        AS CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE,
    GET(CURATED_JSON, 'RECOMMENDED_INTEGRITY_CONTROL_CATEGORY')
        AS RECOMMENDED_INTEGRITY_CONTROL_CATEGORY,
    GET(CURATED_JSON, 'INTEGRITY_CONTROL_CATEGORY_OVERRIDE')
        AS INTEGRITY_CONTROL_CATEGORY_OVERRIDE,
    GET(CURATED_JSON, 'AVAILABILITY_CONTROL_CATEGORY_OVERRIDE')
        AS AVAILABILITY_CONTROL_CATEGORY_OVERRIDE,
    GET(CURATED_JSON, 'RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY')
        AS RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY,
    GET(CURATED_JSON, 'PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY')
        AS PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY,
    GET(CURATED_JSON, 'PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY')
        AS PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY,
    GET(CURATED_JSON, 'CNSS_AVAILABILITY_RATING')
        AS CNSS_AVAILABILITY_RATING,
    GET(CURATED_JSON, 'CNSS_CONFIDENTIALITY_RATING')
        AS CNSS_CONFIDENTIALITY_RATING,
    GET(CURATED_JSON, 'CNSS_INTEGRITY_RATING')
        AS CNSS_INTEGRITY_RATING
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
WHERE TRIM(CONTENT_ID::STRING) = $TEST_CONTENT_ID
ORDER BY ARCHER_CONTENT_ID;


-- ============================================================
-- 2. MAPPING VIEW: Archer field -> exact OSCAL target path
--    ARCHER_RAW_VALUE comes directly from CURATED_JSON.
-- ============================================================

WITH FIPS_MAPPING AS (
    SELECT COLUMN1 AS ARCHER_FIELD_NAME, COLUMN2 AS OSCAL_ELEMENT_PATH
    FROM VALUES
      ('RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('INTEGRITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('CNSS_AVAILABILITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('CNSS_CONFIDENTIALITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('CNSS_INTEGRITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity')
),
SRC AS (
    SELECT
        CONTENT_ID::STRING AS ARCHER_CONTENT_ID,
        CURATED_JSON
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    WHERE TRIM(CONTENT_ID::STRING) = $TEST_CONTENT_ID
)
SELECT
    S.ARCHER_CONTENT_ID,
    M.ARCHER_FIELD_NAME,
    GET(S.CURATED_JSON, M.ARCHER_FIELD_NAME) AS ARCHER_RAW_VALUE,
    M.OSCAL_ELEMENT_PATH
FROM SRC S
CROSS JOIN FIPS_MAPPING M
WHERE GET(S.CURATED_JSON, M.ARCHER_FIELD_NAME) IS NOT NULL
ORDER BY M.OSCAL_ELEMENT_PATH, M.ARCHER_FIELD_NAME;


-- ============================================================
-- 3. END-TO-END TRACE:
-- NOTE:
-- The persisted DIM table does NOT contain ELEMENT_PATH.
-- ELEMENT_PATH exists in the in-memory candidate graph only.
-- Persisted rows are identified here by ELEMENT_TYPE + METADATA_JSON shape.
--    Archer CONTENT_ID + Archer field -> committed OSCAL member/value.
--
--    The lineage prop stores only:
--      {"name":"source-field","value":"<ARCHER_FIELD_NAME>"}
--
--    SOURCE_RECORD_ID is the Archer CONTENT_ID.
-- ============================================================

WITH FIPS_MAPPING AS (
    SELECT COLUMN1 AS ARCHER_FIELD_NAME, COLUMN2 AS OSCAL_ELEMENT_PATH
    FROM VALUES
      ('RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('INTEGRITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('CNSS_AVAILABILITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('CNSS_CONFIDENTIALITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('CNSS_INTEGRITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity')
),
SRC AS (
    SELECT
        CONTENT_ID::STRING AS ARCHER_CONTENT_ID,
        CURATED_JSON
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    WHERE TRIM(CONTENT_ID::STRING) = $TEST_CONTENT_ID
),
LINEAGE AS (
    SELECT
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
        METADATA_JSON:"security-objective-confidentiality"::STRING AS OSCAL_CONFIDENTIALITY,
        METADATA_JSON:"security-objective-integrity"::STRING AS OSCAL_INTEGRITY,
        METADATA_JSON:"security-objective-availability"::STRING AS OSCAL_AVAILABILITY
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE TRIM(SOURCE_RECORD_ID::STRING) = $TEST_CONTENT_ID
      AND ELEMENT_TYPE = 'security-impact-level'
)
SELECT
    S.ARCHER_CONTENT_ID,
    L.ARCHER_FIELD_NAME,
    GET(S.CURATED_JSON, L.ARCHER_FIELD_NAME) AS ARCHER_RAW_VALUE,
    M.OSCAL_ELEMENT_PATH,
    CASE
        WHEN M.OSCAL_ELEMENT_PATH LIKE '%security-objective-confidentiality'
            THEN I.OSCAL_CONFIDENTIALITY
        WHEN M.OSCAL_ELEMENT_PATH LIKE '%security-objective-integrity'
            THEN I.OSCAL_INTEGRITY
        WHEN M.OSCAL_ELEMENT_PATH LIKE '%security-objective-availability'
            THEN I.OSCAL_AVAILABILITY
    END AS COMMITTED_OSCAL_VALUE
FROM LINEAGE L
JOIN FIPS_MAPPING M
  ON M.ARCHER_FIELD_NAME = L.ARCHER_FIELD_NAME
JOIN SRC S
  ON S.ARCHER_CONTENT_ID = L.ARCHER_CONTENT_ID
LEFT JOIN IMPACT I
  ON I.ARCHER_CONTENT_ID = L.ARCHER_CONTENT_ID
ORDER BY M.OSCAL_ELEMENT_PATH, L.ARCHER_FIELD_NAME;


-- ============================================================
-- 4. OPTIONAL: show the Archer select-value labels used by the mapper
--    for canonical FIPS 199 values.
-- ============================================================

SELECT
    SELECT_VALUE_ID,
    SELECT_VALUE_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE
WHERE LOWER(TRIM(SELECT_VALUE_NAME)) IN ('low', 'moderate', 'high')
ORDER BY LOWER(TRIM(SELECT_VALUE_NAME)), SELECT_VALUE_ID;

-- ============================================================
-- 5. FIND A REAL "HIGH" FIPS EXAMPLE END TO END
--    Step A: resolve Archer meta value(s) whose label is High.
--    Step B: find Source One records whose FIPS candidate field contains that ID.
--    Step C: show the committed OSCAL value for the matching objective.
--    READ ONLY.
-- ============================================================

WITH HIGH_IDS AS (
    SELECT
        TRIM(SELECT_VALUE_ID::STRING) AS SELECT_VALUE_ID,
        TRIM(SELECT_VALUE_NAME::STRING) AS SELECT_VALUE_NAME
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE
    WHERE LOWER(TRIM(SELECT_VALUE_NAME::STRING)) = 'high'
),
FIPS_MAPPING AS (
    SELECT COLUMN1 AS ARCHER_FIELD_NAME, COLUMN2 AS OSCAL_ELEMENT_PATH
    FROM VALUES
      ('RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('INTEGRITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity'),
      ('PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('CNSS_AVAILABILITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-availability'),
      ('CNSS_CONFIDENTIALITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality'),
      ('CNSS_INTEGRITY_RATING',
       'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity')
),
SOURCE_HIGH AS (
    SELECT DISTINCT
        R.CONTENT_ID::STRING AS ARCHER_CONTENT_ID,
        M.ARCHER_FIELD_NAME,
        M.OSCAL_ELEMENT_PATH,
        V.VALUE::STRING AS SELECT_VALUE_ID,
        H.SELECT_VALUE_NAME,
        GET(R.CURATED_JSON, M.ARCHER_FIELD_NAME) AS ARCHER_RAW_VALUE
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW R
    CROSS JOIN FIPS_MAPPING M,
         LATERAL FLATTEN(
             INPUT => GET(GET(R.CURATED_JSON, M.ARCHER_FIELD_NAME), 'ValuesListIds')
         ) V
    JOIN HIGH_IDS H
      ON TRIM(V.VALUE::STRING) = H.SELECT_VALUE_ID
),
IMPACT AS (
    SELECT
        SOURCE_RECORD_ID::STRING AS ARCHER_CONTENT_ID,
        METADATA_JSON:"security-objective-confidentiality"::STRING AS OSCAL_CONFIDENTIALITY,
        METADATA_JSON:"security-objective-integrity"::STRING AS OSCAL_INTEGRITY,
        METADATA_JSON:"security-objective-availability"::STRING AS OSCAL_AVAILABILITY
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE ELEMENT_TYPE = 'security-impact-level'
)
SELECT
    S.ARCHER_CONTENT_ID,
    S.ARCHER_FIELD_NAME,
    S.SELECT_VALUE_ID,
    S.SELECT_VALUE_NAME AS ARCHER_RESOLVED_LABEL,
    S.ARCHER_RAW_VALUE,
    S.OSCAL_ELEMENT_PATH,
    CASE
        WHEN S.OSCAL_ELEMENT_PATH LIKE '%security-objective-confidentiality'
            THEN I.OSCAL_CONFIDENTIALITY
        WHEN S.OSCAL_ELEMENT_PATH LIKE '%security-objective-integrity'
            THEN I.OSCAL_INTEGRITY
        WHEN S.OSCAL_ELEMENT_PATH LIKE '%security-objective-availability'
            THEN I.OSCAL_AVAILABILITY
    END AS COMMITTED_OSCAL_VALUE
FROM SOURCE_HIGH S
LEFT JOIN IMPACT I
  ON I.ARCHER_CONTENT_ID = S.ARCHER_CONTENT_ID
ORDER BY S.ARCHER_CONTENT_ID, S.ARCHER_FIELD_NAME
LIMIT 50;

-- ============================================================
-- 5A. SHOW LOW / MODERATE / HIGH META IDS
--     This proves which Archer select IDs represent the three
--     canonical FIPS labels, independent of source usage.
-- ============================================================

SELECT
    TRIM(SELECT_VALUE_ID::STRING) AS SELECT_VALUE_ID,
    TRIM(SELECT_VALUE_NAME::STRING) AS SELECT_VALUE_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE
WHERE LOWER(TRIM(SELECT_VALUE_NAME::STRING)) IN ('low', 'moderate', 'high')
ORDER BY
    CASE LOWER(TRIM(SELECT_VALUE_NAME::STRING))
        WHEN 'low' THEN 1
        WHEN 'moderate' THEN 2
        WHEN 'high' THEN 3
        ELSE 4
    END,
    SELECT_VALUE_ID;


-- ============================================================
-- 5B. COUNT ACTUAL SOURCE USAGE OF LOW / MODERATE / HIGH
--     across the 11 reviewed SSP FIPS/security-objective fields.
--
--     If HIGH has zero rows here, Section 5 being empty is expected:
--     the current Source One snapshot simply has no HIGH value in
--     those 11 mapped fields.
-- ============================================================

WITH SOURCE_FIPS AS (
    SELECT CONTENT_ID::STRING AS ARCHER_CONTENT_ID,
           'RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY' AS ARCHER_FIELD_NAME,
           GET(CURATED_JSON, 'RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY') AS ARCHER_RAW_VALUE
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',
           GET(CURATED_JSON, 'CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',
           GET(CURATED_JSON, 'RECOMMENDED_INTEGRITY_CONTROL_CATEGORY')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'INTEGRITY_CONTROL_CATEGORY_OVERRIDE',
           GET(CURATED_JSON, 'INTEGRITY_CONTROL_CATEGORY_OVERRIDE')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',
           GET(CURATED_JSON, 'AVAILABILITY_CONTROL_CATEGORY_OVERRIDE')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',
           GET(CURATED_JSON, 'RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',
           GET(CURATED_JSON, 'PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',
           GET(CURATED_JSON, 'PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'CNSS_AVAILABILITY_RATING',
           GET(CURATED_JSON, 'CNSS_AVAILABILITY_RATING')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'CNSS_CONFIDENTIALITY_RATING',
           GET(CURATED_JSON, 'CNSS_CONFIDENTIALITY_RATING')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'CNSS_INTEGRITY_RATING',
           GET(CURATED_JSON, 'CNSS_INTEGRITY_RATING')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
),
EXPLODED AS (
    SELECT
        S.ARCHER_CONTENT_ID,
        S.ARCHER_FIELD_NAME,
        S.ARCHER_RAW_VALUE,
        V.VALUE::STRING AS SELECT_VALUE_ID
    FROM SOURCE_FIPS S,
         LATERAL FLATTEN(
             INPUT => GET(S.ARCHER_RAW_VALUE, 'ValuesListIds')
         ) V
),
RESOLVED AS (
    SELECT
        E.ARCHER_CONTENT_ID,
        E.ARCHER_FIELD_NAME,
        E.ARCHER_RAW_VALUE,
        E.SELECT_VALUE_ID,
        TRIM(M.SELECT_VALUE_NAME::STRING) AS SELECT_VALUE_NAME
    FROM EXPLODED E
    JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE M
      ON TRIM(M.SELECT_VALUE_ID::STRING) = TRIM(E.SELECT_VALUE_ID)
    WHERE LOWER(TRIM(M.SELECT_VALUE_NAME::STRING)) IN ('low', 'moderate', 'high')
)
SELECT
    LOWER(SELECT_VALUE_NAME) AS FIPS_LABEL,
    SELECT_VALUE_ID,
    ARCHER_FIELD_NAME,
    COUNT(*) AS SOURCE_OCCURRENCES,
    COUNT(DISTINCT ARCHER_CONTENT_ID) AS DISTINCT_CONTENT_IDS
FROM RESOLVED
GROUP BY 1, 2, 3
ORDER BY 1, 3;


-- ============================================================
-- 5C. SHOW SAMPLE HIGH ROWS, IF ANY EXIST
-- ============================================================

WITH SOURCE_FIPS AS (
    SELECT CONTENT_ID::STRING AS ARCHER_CONTENT_ID,
           'RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY' AS ARCHER_FIELD_NAME,
           GET(CURATED_JSON, 'RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY') AS ARCHER_RAW_VALUE
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',
           GET(CURATED_JSON, 'CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',
           GET(CURATED_JSON, 'RECOMMENDED_INTEGRITY_CONTROL_CATEGORY')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'INTEGRITY_CONTROL_CATEGORY_OVERRIDE',
           GET(CURATED_JSON, 'INTEGRITY_CONTROL_CATEGORY_OVERRIDE')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',
           GET(CURATED_JSON, 'AVAILABILITY_CONTROL_CATEGORY_OVERRIDE')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',
           GET(CURATED_JSON, 'RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',
           GET(CURATED_JSON, 'PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',
           GET(CURATED_JSON, 'PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'CNSS_AVAILABILITY_RATING',
           GET(CURATED_JSON, 'CNSS_AVAILABILITY_RATING')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'CNSS_CONFIDENTIALITY_RATING',
           GET(CURATED_JSON, 'CNSS_CONFIDENTIALITY_RATING')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    UNION ALL
    SELECT CONTENT_ID::STRING,
           'CNSS_INTEGRITY_RATING',
           GET(CURATED_JSON, 'CNSS_INTEGRITY_RATING')
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
),
EXPLODED AS (
    SELECT
        S.ARCHER_CONTENT_ID,
        S.ARCHER_FIELD_NAME,
        S.ARCHER_RAW_VALUE,
        V.VALUE::STRING AS SELECT_VALUE_ID
    FROM SOURCE_FIPS S,
         LATERAL FLATTEN(
             INPUT => GET(S.ARCHER_RAW_VALUE, 'ValuesListIds')
         ) V
)
SELECT
    E.ARCHER_CONTENT_ID,
    E.ARCHER_FIELD_NAME,
    E.SELECT_VALUE_ID,
    TRIM(M.SELECT_VALUE_NAME::STRING) AS ARCHER_RESOLVED_LABEL,
    E.ARCHER_RAW_VALUE
FROM EXPLODED E
JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE M
  ON TRIM(M.SELECT_VALUE_ID::STRING) = TRIM(E.SELECT_VALUE_ID)
WHERE LOWER(TRIM(M.SELECT_VALUE_NAME::STRING)) = 'high'
ORDER BY E.ARCHER_CONTENT_ID, E.ARCHER_FIELD_NAME
LIMIT 50;
