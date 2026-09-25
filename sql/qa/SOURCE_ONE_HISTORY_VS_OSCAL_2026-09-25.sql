-- SOURCE ONE: HISTORICAL TABLE -> CURRENT RAW -> OSCAL TARGET VALUE QA
-- Date: 2026-09-25
-- READ ONLY. No DML.
--
-- Historical Authorization Package comparison source:
--   RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE
-- Current RAW:
--   RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
--
-- IMPORTANT CORRECTION 2026-09-25:
-- Do NOT assume every RAW object has a historical object with "_RAW" removed.
-- The guessed object ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL does not exist
-- or is not authorized in the owner's Snowflake session. Level-355 historical
-- discovery is therefore separated from the executable comparison below.
--
-- This file intentionally does not assume every historical column still exists.
-- Missing historical columns are reported, not treated as mapping failures.


-- =====================================================================
-- H00. AUTHORIZATION PACKAGE HISTORICAL / RAW BASIC COUNTS
-- Expected: both objects are readable. Differences are reported, not hidden.
-- =====================================================================
SELECT 'HIST_AUTHORIZATION_PACKAGE' OBJECT_NAME, COUNT(*) ROWS,
       COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) DISTINCT_CONTENT_IDS
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE
UNION ALL
SELECT 'RAW_AUTHORIZATION_PACKAGE', COUNT(*),
       COUNT(DISTINCT TRIM(CONTENT_ID::STRING))
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
ORDER BY OBJECT_NAME;


-- H00B. Discover the ACTUAL historical Level-355 object, if one exists.
-- This is discovery only; it prevents another guessed object-name failure.
SELECT TABLE_NAME AS OBJECT_NAME, TABLE_TYPE AS OBJECT_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA='ES_ESC_GRC'
  AND TABLE_NAME ILIKE '%ALLOCATED%CONTROL%'
  AND TABLE_NAME NOT ILIKE '%_RAW'
UNION ALL
SELECT TABLE_NAME, 'VIEW'
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA='ES_ESC_GRC'
  AND TABLE_NAME ILIKE '%ALLOCATED%CONTROL%'
  AND TABLE_NAME NOT ILIKE '%_RAW'
ORDER BY OBJECT_NAME;


-- =====================================================================
-- H01. HISTORICAL vs CURRENT RAW CONTENT_ID SET
-- Shows old-only/current-only/common IDs and duplicate IDs.
-- =====================================================================
WITH h AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID, COUNT(*) N
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE
  GROUP BY 1
),
r AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID, COUNT(*) N
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  GROUP BY 1
),
x AS (
  SELECT COALESCE(h.CONTENT_ID,r.CONTENT_ID) CONTENT_ID,
         h.N HIST_ROWS, r.N RAW_ROWS
  FROM h FULL OUTER JOIN r USING(CONTENT_ID)
)
SELECT
  COUNT(*) UNION_CONTENT_IDS,
  COUNT_IF(HIST_ROWS IS NOT NULL AND RAW_ROWS IS NOT NULL) COMMON_CONTENT_IDS,
  COUNT_IF(HIST_ROWS IS NOT NULL AND RAW_ROWS IS NULL) HIST_ONLY_CONTENT_IDS,
  COUNT_IF(HIST_ROWS IS NULL AND RAW_ROWS IS NOT NULL) RAW_ONLY_CONTENT_IDS,
  COUNT_IF(COALESCE(HIST_ROWS,0)>1) HIST_DUPLICATE_CONTENT_IDS,
  COUNT_IF(COALESCE(RAW_ROWS,0)>1) RAW_DUPLICATE_CONTENT_IDS
FROM x;


-- H01B. Detail only if H01 reports differences. Expected ideally zero rows
-- for current overlapping business population; historical retention may explain old-only IDs.
WITH h AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID, COUNT(*) N
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE GROUP BY 1
),
r AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID, COUNT(*) N
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW GROUP BY 1
)
SELECT COALESCE(h.CONTENT_ID,r.CONTENT_ID) CONTENT_ID,
       COALESCE(h.N,0) HIST_ROWS, COALESCE(r.N,0) RAW_ROWS,
       CASE WHEN h.CONTENT_ID IS NULL THEN 'RAW_ONLY'
            WHEN r.CONTENT_ID IS NULL THEN 'HIST_ONLY'
            WHEN h.N<>1 OR r.N<>1 THEN 'DUPLICATE_GRAIN'
       END DEFECT
FROM h FULL OUTER JOIN r USING(CONTENT_ID)
WHERE h.CONTENT_ID IS NULL OR r.CONTENT_ID IS NULL OR h.N<>1 OR r.N<>1
ORDER BY DEFECT, CONTENT_ID
LIMIT 500;


-- =====================================================================
-- H02. ALL CURRENT MAPPED SOURCE FIELDS: HISTORICAL VALUE vs RAW CURATED_JSON
--
-- This is the broad source-parity gate. It uses the CURRENT repository mapping
-- register and compares only fields participating in approved/guarded Source One
-- mappings. It does not guess columns that are not present in the old table.
--
-- MATCH semantics are canonical VARIANT JSON equality.
-- Expected for unchanged common data: MISMATCH_ROWS = 0.
-- =====================================================================
WITH mapped_fields(FIELD_NAME, MODEL_LABELS, TRANSFORMS, STATUSES) AS (
  SELECT COLUMN1,COLUMN2,COLUMN3,COLUMN4 FROM VALUES
    ('_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD','Assessment Results','scalar-score','APPROVED'),
    ('_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD','Assessment Results','scalar-score','APPROVED'),
    ('ACRONYM','SSP - System Characteristics','text','APPROVED'),
    ('ADD_ADDITIONAL_CONTROLS','SSP - Control Implementation','direct','APPROVED'),
    ('ADJUSTED_AVERAGE_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('ADJUSTED_TOTAL_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('ALLOCATED_CONTROLS','SSP - Control Implementation','reference-ids','APPROVED'),
    ('ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE','SSP - Control Implementation','direct','APPROVED'),
    ('ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS','SSP - Control Implementation','reference-ids','APPROVED'),
    ('ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA','SSP - Control Implementation','direct','APPROVED'),
    ('ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA_TEXT','SSP - Control Implementation','direct','APPROVED'),
    ('ANTIVIRUS_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('APPROVAL_TO_BEGIN_ASSESSMENT','Security Assessment Plan','archer-select','APPROVED'),
    ('ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER','SSP - Metadata','direct','APPROVED'),
    ('ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED','SSP - Metadata','timestamp','APPROVED'),
    ('ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED','SSP - Metadata','timestamp','APPROVED'),
    ('ARCHIVED_CONTROLS','SSP - Control Implementation','reference-ids','APPROVED'),
    ('ATOIATO_DATE','SSP - System Characteristics','date','APPROVED'),
    ('AUTHORIZATION_BOUNDARY_DESCRIPTION','SSP - System Characteristics','text','APPROVED'),
    ('AUTHORIZATION_COMMENTS','SSP - System Characteristics','text','APPROVED'),
    ('AUTHORIZATION_DECISION','SSP - System Characteristics','archer-select','APPROVED'),
    ('AUTHORIZATION_PACKAGE_NAME','SSP - System Characteristics|SSP - Metadata','text','APPROVED'),
    ('AUTHORIZING_OFFICIAL_AO','SSP - Metadata','direct','APPROVED'),
    ('AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR','SSP - Metadata','direct','APPROVED'),
    ('AVAILABILITY_CONTROL_CATEGORY_OVERRIDE','SSP - System Characteristics','security-objective','APPROVED'),
    ('AVG_ANTIVIRUS_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('AVG_AUTHORIZATION_PACKAGE_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('AVG_COMPUTER_PASSWORD_AGE_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('AVG_PATCH_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('AVG_SECURITY_COMPLIANCE_REPORTING_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('AVG_SECURITY_COMPLIANCE_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('AVG_VULNERABILITY_REPORTING_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('AVG_VULNERABILITY_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('BASELINE_AVERAGE_DEVICE_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('BASELINE_CONTROL_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('BASELINE_HIGHEST_DEVICE_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('CHANGE_CONTROL','SSP - Control Implementation','direct','APPROVED'),
    ('CNSS_AVAILABILITY_RATING','SSP - System Characteristics','security-objective','APPROVED'),
    ('CNSS_CONFIDENTIALITY_RATING','SSP - System Characteristics','security-objective','APPROVED'),
    ('CNSS_INTEGRITY_RATING','SSP - System Characteristics','security-objective','APPROVED'),
    ('COMPUTER_PASSWORD_AGE_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE','SSP - System Characteristics','security-objective','APPROVED'),
    ('CONTROL_NUMBER','SSP - Control Implementation','text','APPROVED'),
    ('CONTROL_OWNER_CO','SSP - Control Implementation','direct','APPROVED'),
    ('CONTROL_SET_TO_ASSESS','SSP - Control Implementation','direct','APPROVED'),
    ('CONTROL_SET_VERSION_NUMBER','SSP - Control Implementation','archer-select','APPROVED'),
    ('CONTROL_SET_VERSION_NUMBER_HRC','SSP - Control Implementation','archer-select','APPROVED'),
    ('CONTROL_STANDARDS','SSP - Control Implementation','direct','APPROVED'),
    ('COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED','SSP - Control Implementation','direct','APPROVED'),
    ('COUNT_OF_CONTROLS','SSP - Control Implementation','direct','APPROVED'),
    ('COUNT_OF_CONTROLS_MISSING_POAMRBD','SSP - Control Implementation','direct','APPROVED'),
    ('COUNT_OF_CONTROLS_WITH_OPEN_POAMS','SSP - Control Implementation','direct','APPROVED'),
    ('COUNT_OF_CONTROLS_WITH_OPEN_POAMS_ANDOR_RBDS','SSP - Control Implementation','direct','APPROVED'),
    ('COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS','SSP - Control Implementation','direct','APPROVED'),
    ('COUNT_OF_FULLY_IMPLEMENTED_CONTROLS','SSP - Control Implementation','direct','APPROVED'),
    ('COUNT_OF_INHERITED_CONTROLS','SSP - Control Implementation','direct','APPROVED'),
    ('CRITICAL_INFRASTRUCTURE','SSP - System Characteristics','archer-select','APPROVED'),
    ('CURRENT_AVERAGE_DEVICE_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('CURRENT_CONTROL_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('CURRENT_CONTROL_RISK_THRESHOLD','SSP - Control Implementation','direct','APPROVED'),
    ('CURRENT_HIGHEST_DEVICE_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('DAILY_LOSS_AMOUNT_FROM_OUTAGE','System Security Plan','direct','APPROVED'),
    ('DUE_DATE','Assessment Results','date','APPROVED'),
    ('EXPORT_CONTROL_ASSESSOR_ECA_TEXT','SSP - Control Implementation','text','APPROVED'),
    ('EXPORT_CONTROLLED_DATA_ITARAR_IF_APPLICABLE','SSP - Control Implementation','direct','APPROVED'),
    ('FINANCIAL_SYSTEM','SSP - System Characteristics','archer-select','APPROVED'),
    ('FINDINGS','Assessment Results','direct','APPROVED'),
    ('FIRST_PUBLISHED','SSP - Metadata','timestamp','APPROVED'),
    ('FISMA_REPORTABLE','SSP - System Characteristics','archer-select','APPROVED'),
    ('GS_LAB_CONTROL_ENTITY','SSP - Control Implementation','reference-ids','APPROVED'),
    ('HARDWARE','SSP - System Implementation','direct','APPROVED'),
    ('IMPLEMENTATION_DETAILS','SSP - Control Implementation','text','APPROVED'),
    ('INFORMATION_CLASSIFICATION','System Security Plan','archer-select','APPROVED'),
    ('INFORMATION_OWNER_IO','SSP - Metadata','direct','APPROVED'),
    ('INFORMATION_SYSTEM_ADMINISTRATOR_ISA','SSP - Metadata','direct','APPROVED'),
    ('INFORMATION_SYSTEM_OWNER_ISO','SSP - Metadata','direct','APPROVED'),
    ('INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE','SSP - Metadata','direct','APPROVED'),
    ('INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO','SSP - Metadata','direct','APPROVED'),
    ('INFORMATION_SYSTEM_TYPE','SSP - System Characteristics','archer-select','APPROVED'),
    ('INHERITABLE_CONTROLS','SSP - Control Implementation','reference-ids','APPROVED'),
    ('INHERITED_CONTROL_SELECTION','SSP - Control Implementation','direct','APPROVED'),
    ('INITIAL_RISK_ASSESSMENT','Assessment Results','scalar-score','APPROVED'),
    ('INTEGRITY_CONTROL_CATEGORY_OVERRIDE','SSP - System Characteristics','security-objective','APPROVED'),
    ('INTERCONNECTIONS','SSP - System Implementation','direct','APPROVED'),
    ('INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM','SSP - System Implementation','direct','APPROVED'),
    ('LAST_UPDATED','SSP - Metadata','timestamp','APPROVED'),
    ('MASTER_CONTROLS','SSP - Control Implementation','direct','APPROVED'),
    ('MISSION_CRITICAL','SSP - System Characteristics','archer-select','APPROVED'),
    ('MISSION_PURPOSE','SSP - System Characteristics','text','APPROVED'),
    ('NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS','SSP - Control Implementation','direct','APPROVED'),
    ('OF_SATISFIED_CONTROLS','SSP - Control Implementation','direct','APPROVED'),
    ('OPERATIONAL_STATUS','SSP - System Characteristics','status-crosswalk','APPROVED'),
    ('PACKAGE_TYPE','SSP - System Characteristics','archer-select','APPROVED'),
    ('PATCH_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD','Assessment Results','scalar-score','APPROVED'),
    ('PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD','Assessment Results','scalar-score','APPROVED'),
    ('PIA_REQUIRED','SSP - System Characteristics','archer-select','APPROVED'),
    ('POAMS','POA&M','direct','APPROVED'),
    ('PREASSESSMENT_REVIEW_COMMENTS','Security Assessment Plan','text','APPROVED'),
    ('PRIVACY_OFFICER_PO','SSP - Metadata','direct','APPROVED'),
    ('PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY','SSP - System Characteristics','security-objective','APPROVED'),
    ('PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY','SSP - System Characteristics','security-objective','APPROVED'),
    ('RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY','SSP - System Characteristics','security-objective','APPROVED'),
    ('RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY','SSP - System Characteristics','security-objective','APPROVED'),
    ('RECOMMENDED_INTEGRITY_CONTROL_CATEGORY','SSP - System Characteristics','security-objective','APPROVED'),
    ('RECOMMENDED_SECURITY_CATEGORY','SSP','reject-populated','BLOCKED_IF_POPULATED'),
    ('REQUEST_TO_BEGIN_ASSESSMENT','Security Assessment Plan','archer-select','APPROVED'),
    ('RISK_ACCEPTANCE_RBDS','Assessment Results','reference-ids','APPROVED'),
    ('RISK_ASSESSMENT','Assessment Results','scalar-score','APPROVED'),
    ('RISK_ASSESSMENT_REPORT','Assessment Results','json-text','APPROVED'),
    ('RISK_SCORE_GRADE','Assessment Results','scalar-score','APPROVED'),
    ('SAP_ID','SSP - System Characteristics','direct','APPROVED'),
    ('SAP_INTAKE_FORM_INTERCONNECTIONS','SSP - System Implementation','direct','APPROVED'),
    ('SECURITY_CATEGORY','SSP - System Characteristics','direct','APPROVED'),
    ('SECURITY_COMPLIANCE_REPORTING_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('SECURITY_COMPLIANCE_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('SECURITY_CONTROL_ASSESSOR_SCA','SSP - Control Implementation','direct','APPROVED'),
    ('SECURITY_CONTROL_ASSESSOR_SCA_TEXT','SSP - Control Implementation','text','APPROVED'),
    ('SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO','SSP - Metadata','direct','APPROVED'),
    ('SOFTWARE','SSP - System Implementation','direct','APPROVED'),
    ('STANDARD_OPERATING_ENVIRONMENT_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('SUBSYSTEMS','SSP - System Implementation','direct','APPROVED'),
    ('TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('TOTAL_PACKAGE_INHERENT_RISK','Assessment Results','scalar-score','APPROVED'),
    ('TOTAL_PACKAGE_RESIDUAL_RISK','Assessment Results','scalar-score','APPROVED'),
    ('TRACKING_ID','SSP - Metadata','identifier','APPROVED'),
    ('VULNERABILITY_REPORTING_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('VULNERABILITY_SCORE','Assessment Results','scalar-score','APPROVED'),
    ('WORKFLOW_CURRENT_NODE','Assessment Results','direct','APPROVED'),
    ('WORKFLOW_CURRENT_NODE_HRTN','Assessment Results','direct','APPROVED'),
    ('WORKFLOW_JOB_STATUS','Assessment Results','archer-select','APPROVED'),
    ('WORKFLOW_PROCESS_VERSION','Assessment Results','direct','APPROVED'),
    ('WORKFLOW_STATUS','Assessment Results','archer-select','APPROVED'),
    ('WORKFLOW_STATUS_CHANGED','Assessment Results','date','APPROVED')
),
hist_cols AS (
  SELECT UPPER(COLUMN_NAME) FIELD_NAME
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA='ES_ESC_GRC'
    AND TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE'
),
h0 AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID,
         OBJECT_CONSTRUCT_KEEP_NULL(*) HIST_OBJ,
         COUNT(*) OVER (PARTITION BY TRIM(CONTENT_ID::STRING)) GRAIN_N
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE
),
h AS (
  SELECT CONTENT_ID, ANY_VALUE(HIST_OBJ) HIST_OBJ
  FROM h0 WHERE GRAIN_N=1 GROUP BY 1
),
r0 AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID,
         CURATED_JSON RAW_OBJ,
         COUNT(*) OVER (PARTITION BY TRIM(CONTENT_ID::STRING)) GRAIN_N
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
),
r AS (
  SELECT CONTENT_ID, ANY_VALUE(RAW_OBJ) RAW_OBJ
  FROM r0 WHERE GRAIN_N=1 GROUP BY 1
),
cmp AS (
  SELECT
    m.FIELD_NAME, m.MODEL_LABELS, m.TRANSFORMS, m.STATUSES,
    IFF(c.FIELD_NAME IS NOT NULL,1,0) HIST_COLUMN_EXISTS,
    h.CONTENT_ID,
    GET(h.HIST_OBJ,m.FIELD_NAME) HIST_VALUE,
    GET(r.RAW_OBJ,m.FIELD_NAME) RAW_VALUE,
    ARRAY_CONTAINS(TO_VARIANT(m.FIELD_NAME),OBJECT_KEYS(r.RAW_OBJ)) RAW_KEY_EXISTS
  FROM mapped_fields m
  LEFT JOIN hist_cols c ON c.FIELD_NAME=UPPER(m.FIELD_NAME)
  JOIN h ON TRUE
  JOIN r USING(CONTENT_ID)
)
SELECT
  FIELD_NAME, MODEL_LABELS, TRANSFORMS, STATUSES,
  MAX(HIST_COLUMN_EXISTS) HIST_COLUMN_EXISTS,
  COUNT(*) COMMON_UNIQUE_RECORDS,
  COUNT_IF(RAW_KEY_EXISTS) RAW_KEY_PRESENT_ROWS,
  COUNT_IF(
    HIST_COLUMN_EXISTS=1
    AND COALESCE(
      CASE WHEN HIST_VALUE IS NULL THEN '<SQL_NULL>'
           WHEN IS_NULL_VALUE(HIST_VALUE) THEN '<JSON_NULL>'
           ELSE TO_JSON(HIST_VALUE) END,
      '<SQL_NULL>'
    )
    =
    COALESCE(
      CASE WHEN RAW_VALUE IS NULL THEN '<SQL_NULL>'
           WHEN IS_NULL_VALUE(RAW_VALUE) THEN '<JSON_NULL>'
           ELSE TO_JSON(RAW_VALUE) END,
      '<SQL_NULL>'
    )
  ) MATCH_ROWS,
  COUNT_IF(
    HIST_COLUMN_EXISTS=1
    AND COALESCE(
      CASE WHEN HIST_VALUE IS NULL THEN '<SQL_NULL>'
           WHEN IS_NULL_VALUE(HIST_VALUE) THEN '<JSON_NULL>'
           ELSE TO_JSON(HIST_VALUE) END,
      '<SQL_NULL>'
    )
    <>
    COALESCE(
      CASE WHEN RAW_VALUE IS NULL THEN '<SQL_NULL>'
           WHEN IS_NULL_VALUE(RAW_VALUE) THEN '<JSON_NULL>'
           ELSE TO_JSON(RAW_VALUE) END,
      '<SQL_NULL>'
    )
  ) MISMATCH_ROWS,
  IFF(MAX(HIST_COLUMN_EXISTS)=0,'NO_HIST_COLUMN',
      IFF(COUNT_IF(
        HIST_COLUMN_EXISTS=1
        AND COALESCE(CASE WHEN HIST_VALUE IS NULL THEN '<SQL_NULL>' WHEN IS_NULL_VALUE(HIST_VALUE) THEN '<JSON_NULL>' ELSE TO_JSON(HIST_VALUE) END,'<SQL_NULL>')
          <>
            COALESCE(CASE WHEN RAW_VALUE IS NULL THEN '<SQL_NULL>' WHEN IS_NULL_VALUE(RAW_VALUE) THEN '<JSON_NULL>' ELSE TO_JSON(RAW_VALUE) END,'<SQL_NULL>')
      )=0,'PASS','REVIEW')) STATUS
FROM cmp
GROUP BY FIELD_NAME,MODEL_LABELS,TRANSFORMS,STATUSES
ORDER BY STATUS DESC, FIELD_NAME;


-- H02B. Mismatch detail without dumping every value.
-- Run only for fields with H02 STATUS=REVIEW.
-- Change the field name as needed.
SET QA_FIELD = 'AUTHORIZATION_PACKAGE_NAME';

WITH h AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID, OBJECT_CONSTRUCT_KEEP_NULL(*) HIST_OBJ
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE
),
r AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID, CURATED_JSON RAW_OBJ
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
)
SELECT
  h.CONTENT_ID,
  TYPEOF(GET(h.HIST_OBJ,$QA_FIELD)) HIST_TYPE,
  TYPEOF(GET(r.RAW_OBJ,$QA_FIELD)) RAW_TYPE,
  GET(h.HIST_OBJ,$QA_FIELD) HIST_VALUE,
  GET(r.RAW_OBJ,$QA_FIELD) RAW_VALUE
FROM h JOIN r USING(CONTENT_ID)
WHERE COALESCE(
        CASE WHEN GET(h.HIST_OBJ,$QA_FIELD) IS NULL THEN '<SQL_NULL>'
             WHEN IS_NULL_VALUE(GET(h.HIST_OBJ,$QA_FIELD)) THEN '<JSON_NULL>'
             ELSE TO_JSON(GET(h.HIST_OBJ,$QA_FIELD)) END,'<SQL_NULL>')
   <> COALESCE(
        CASE WHEN GET(r.RAW_OBJ,$QA_FIELD) IS NULL THEN '<SQL_NULL>'
             WHEN IS_NULL_VALUE(GET(r.RAW_OBJ,$QA_FIELD)) THEN '<JSON_NULL>'
             ELSE TO_JSON(GET(r.RAW_OBJ,$QA_FIELD)) END,'<SQL_NULL>')
ORDER BY CONTENT_ID
LIMIT 100;


-- =====================================================================
-- H03. HISTORICAL CONTENT_ID -> CURRENT OSCAL ROOT COVERAGE
-- For every historical CONTENT_ID that still exists in CURRENT RAW, require
-- exactly one root in each Source One OSCAL model.
-- Expected all missing/duplicate counts = 0.
-- =====================================================================
WITH current_population AS (
  SELECT DISTINCT h.CONTENT_ID
  FROM (
    SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE
  ) h
  JOIN (
    SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  ) r USING(CONTENT_ID)
),
roots AS (
  SELECT 'SSP' MODEL, TRIM(SOURCE_RECORD_ID::STRING) CONTENT_ID, COUNT(*) N
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER' AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='system-security-plan'
  GROUP BY 1,2
  UNION ALL
  SELECT 'ASSESSMENT_RESULTS', TRIM(SOURCE_RECORD_ID::STRING), COUNT(*)
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER' AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='assessment-results'
  GROUP BY 1,2
  UNION ALL
  SELECT 'POAM', TRIM(SOURCE_RECORD_ID::STRING), COUNT(*)
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER' AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='plan-of-action-and-milestones'
  GROUP BY 1,2
  UNION ALL
  SELECT 'SECURITY_ASSESSMENT_PLAN', TRIM(SOURCE_RECORD_ID::STRING), COUNT(*)
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER' AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='assessment-plan'
  GROUP BY 1,2
),
models AS (
  SELECT COLUMN1 MODEL FROM VALUES ('SSP'),('ASSESSMENT_RESULTS'),('POAM'),('SECURITY_ASSESSMENT_PLAN')
),
matrix AS (
  SELECT m.MODEL,p.CONTENT_ID,COALESCE(r.N,0) ROOTS
  FROM current_population p CROSS JOIN models m
  LEFT JOIN roots r ON r.MODEL=m.MODEL AND r.CONTENT_ID=p.CONTENT_ID
)
SELECT MODEL,
       COUNT(*) COMMON_HIST_CURRENT_CONTENT_IDS,
       COUNT_IF(ROOTS=0) MISSING_ROOTS,
       COUNT_IF(ROOTS>1) DUPLICATE_ROOTS,
       IFF(COUNT_IF(ROOTS<>1)=0,'PASS','FAIL') STATUS
FROM matrix
GROUP BY MODEL
ORDER BY MODEL;


-- =====================================================================
-- H04. HISTORICAL -> OSCAL DIRECT/NATIVE VALUE PARITY (ALL COMMON RECORDS)
-- These fields have simple native destinations and are meaningful to compare
-- directly against the old structured columns.
-- Expected MISMATCH_COUNT = 0 unless the historical table represents a
-- genuinely different point-in-time value.
-- =====================================================================
WITH h AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID, OBJECT_CONSTRUCT_KEEP_NULL(*) O
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE
),
meta AS (
  SELECT TRIM(SOURCE_RECORD_ID::STRING) CONTENT_ID, METADATA_JSON
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER' AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='metadata'
),
sc AS (
  SELECT TRIM(SOURCE_RECORD_ID::STRING) CONTENT_ID, METADATA_JSON
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER' AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='system-characteristics'
),
boundary AS (
  SELECT TRIM(SOURCE_RECORD_ID::STRING) CONTENT_ID, METADATA_JSON
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER' AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='authorization-boundary'
),
checks AS (
  SELECT 'AUTHORIZATION_PACKAGE_NAME -> metadata.title' CHECK_NAME,
         COUNT_IF(NOT EQUAL_NULL(GET(h.O,'AUTHORIZATION_PACKAGE_NAME')::STRING,m.METADATA_JSON:title::STRING)) MISMATCH_COUNT
  FROM h JOIN meta m USING(CONTENT_ID)
  UNION ALL
  SELECT 'AUTHORIZATION_PACKAGE_NAME -> system-name',
         COUNT_IF(NOT EQUAL_NULL(GET(h.O,'AUTHORIZATION_PACKAGE_NAME')::STRING,s.METADATA_JSON:"system-name"::STRING))
  FROM h JOIN sc s USING(CONTENT_ID)
  UNION ALL
  SELECT 'ACRONYM -> system-name-short',
         COUNT_IF(NOT EQUAL_NULL(GET(h.O,'ACRONYM')::STRING,s.METADATA_JSON:"system-name-short"::STRING))
  FROM h JOIN sc s USING(CONTENT_ID)
  UNION ALL
  SELECT 'MISSION_PURPOSE -> description',
         COUNT_IF(NOT EQUAL_NULL(GET(h.O,'MISSION_PURPOSE')::STRING,s.METADATA_JSON:description::STRING))
  FROM h JOIN sc s USING(CONTENT_ID)
  UNION ALL
  SELECT 'AUTHORIZATION_BOUNDARY_DESCRIPTION -> authorization-boundary.description',
         COUNT_IF(NOT EQUAL_NULL(GET(h.O,'AUTHORIZATION_BOUNDARY_DESCRIPTION')::STRING,b.METADATA_JSON:description::STRING))
  FROM h JOIN boundary b USING(CONTENT_ID)
)
SELECT CHECK_NAME,MISMATCH_COUNT,IFF(MISMATCH_COUNT=0,'PASS','REVIEW') STATUS
FROM checks ORDER BY CHECK_NAME;


-- =====================================================================
-- H05. HISTORICAL -> OSCAL ASSESSMENT-RESULT OBSERVATION VALUE PARITY
-- Compares all current scalar-score mapping fields using the historical
-- structured column value and the final observation inline property value.
-- Expected MISMATCH_ROWS = 0 for fields whose historical/current business value
-- has not changed.
-- =====================================================================
WITH ar_fields(FIELD_NAME, PROPERTY_NAME) AS (
  SELECT COLUMN1,COLUMN2 FROM VALUES
    ('VULNERABILITY_SCORE','vulnerability-score'),
    ('ANTIVIRUS_SCORE','antivirus-score'),
    ('PATCH_SCORE','patch-score'),
    ('SECURITY_COMPLIANCE_SCORE','security-compliance-score'),
    ('STANDARD_OPERATING_ENVIRONMENT_SCORE','standard-operating-environment-score'),
    ('COMPUTER_PASSWORD_AGE_SCORE','computer-password-age-score'),
    ('VULNERABILITY_REPORTING_SCORE','vulnerability-reporting-score'),
    ('SECURITY_COMPLIANCE_REPORTING_SCORE','security-compliance-reporting-score'),
    ('TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE','total-authorization-package-risk-score'),
    ('AVG_AUTHORIZATION_PACKAGE_RISK_SCORE','avg-authorization-package-risk-score'),
    ('RISK_SCORE_GRADE','risk-score-grade'),
    ('AVG_VULNERABILITY_SCORE','avg-vulnerability-score'),
    ('AVG_PATCH_SCORE','avg-patch-score'),
    ('AVG_SECURITY_COMPLIANCE_REPORTING_SCORE','avg-security-compliance-reporting-score'),
    ('AVG_ANTIVIRUS_SCORE','avg-antivirus-score'),
    ('AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE','avg-standard-operating-environment-score'),
    ('AVG_COMPUTER_PASSWORD_AGE_SCORE','avg-computer-password-age-score'),
    ('AVG_VULNERABILITY_REPORTING_SCORE','avg-vulnerability-reporting-score'),
    ('AVG_SECURITY_COMPLIANCE_SCORE','avg-security-compliance-score'),
    ('TOTAL_PACKAGE_INHERENT_RISK','total-package-inherent-risk'),
    ('TOTAL_PACKAGE_RESIDUAL_RISK','total-package-residual-risk'),
    ('ADJUSTED_TOTAL_RISK_SCORE','adjusted-total-risk-score'),
    ('ADJUSTED_AVERAGE_RISK_SCORE','adjusted-average-risk-score'),
    ('CURRENT_HIGHEST_DEVICE_RISK_SCORE','current-highest-device-risk-score'),
    ('CURRENT_AVERAGE_DEVICE_RISK_SCORE','current-average-device-risk-score'),
    ('CURRENT_CONTROL_RISK_SCORE','current-control-risk-score'),
    ('PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD','pct-current-highest-device-risk-threshold'),
    ('PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD','pct-current-average-device-risk-threshold'),
    ('BASELINE_HIGHEST_DEVICE_RISK_SCORE','baseline-highest-device-risk-score'),
    ('BASELINE_AVERAGE_DEVICE_RISK_SCORE','baseline-average-device-risk-score'),
    ('BASELINE_CONTROL_RISK_SCORE','baseline-control-risk-score'),
    ('RISK_ASSESSMENT','risk-assessment'),
    ('_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD','current-average-device-risk-threshold'),
    ('_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD','current-highest-device-risk-threshold'),
    ('INITIAL_RISK_ASSESSMENT','initial-risk-assessment')
),
h AS (
  SELECT TRIM(CONTENT_ID::STRING) CONTENT_ID, OBJECT_CONSTRUCT_KEEP_NULL(*) O
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE
),
obs AS (
  SELECT
    TRIM(SOURCE_RECORD_ID::STRING) CONTENT_ID,
    METADATA_JSON:props[0]:name::STRING PROPERTY_NAME,
    METADATA_JSON:props[0]:value AS TARGET_VALUE
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='observations'
),
hist_cols AS (
  SELECT UPPER(COLUMN_NAME) FIELD_NAME
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA='ES_ESC_GRC'
    AND TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE'
),
cmp AS (
  SELECT f.FIELD_NAME,f.PROPERTY_NAME,
         IFF(c.FIELD_NAME IS NOT NULL,1,0) HIST_COLUMN_EXISTS,
         h.CONTENT_ID,GET(h.O,f.FIELD_NAME) HIST_VALUE,o.TARGET_VALUE
  FROM ar_fields f
  LEFT JOIN hist_cols c ON c.FIELD_NAME=UPPER(f.FIELD_NAME)
  JOIN h ON TRUE
  LEFT JOIN obs o
    ON o.CONTENT_ID=h.CONTENT_ID AND o.PROPERTY_NAME=f.PROPERTY_NAME
)
SELECT
  FIELD_NAME, PROPERTY_NAME,
  MAX(HIST_COLUMN_EXISTS) HIST_COLUMN_EXISTS,
  COUNT(*) HIST_RECORDS,
  COUNT_IF(TARGET_VALUE IS NOT NULL OR IS_NULL_VALUE(TARGET_VALUE)) TARGET_OBSERVATIONS,
  COUNT_IF(
    HIST_COLUMN_EXISTS=1
    AND EQUAL_NULL(
      IFF(HIST_VALUE IS NULL OR IS_NULL_VALUE(HIST_VALUE),NULL,TRIM(HIST_VALUE::STRING)),
      IFF(TARGET_VALUE IS NULL OR IS_NULL_VALUE(TARGET_VALUE),NULL,TRIM(TARGET_VALUE::STRING))
    )
  ) MATCH_ROWS,
  COUNT_IF(
    HIST_COLUMN_EXISTS=1
    AND NOT EQUAL_NULL(
      IFF(HIST_VALUE IS NULL OR IS_NULL_VALUE(HIST_VALUE),NULL,TRIM(HIST_VALUE::STRING)),
      IFF(TARGET_VALUE IS NULL OR IS_NULL_VALUE(TARGET_VALUE),NULL,TRIM(TARGET_VALUE::STRING))
    )
  ) MISMATCH_ROWS,
  IFF(MAX(HIST_COLUMN_EXISTS)=0,'NO_HIST_COLUMN',
      IFF(COUNT_IF(
        HIST_COLUMN_EXISTS=1
        AND NOT EQUAL_NULL(
          IFF(HIST_VALUE IS NULL OR IS_NULL_VALUE(HIST_VALUE),NULL,TRIM(HIST_VALUE::STRING)),
          IFF(TARGET_VALUE IS NULL OR IS_NULL_VALUE(TARGET_VALUE),NULL,TRIM(TARGET_VALUE::STRING))
        )
      )=0,'PASS','REVIEW')) STATUS
FROM cmp
GROUP BY FIELD_NAME,PROPERTY_NAME
ORDER BY STATUS DESC,FIELD_NAME;


-- =====================================================================
-- H06. LEVEL-355 CURRENT RAW -> FINAL OSCAL PARITY
--
-- Historical Level-355 structured-table comparison is intentionally NOT
-- hard-coded until H00B identifies the actual readable historical object.
--
-- This current-source test remains valid and production-relevant:
-- valid Level-355 CONTROL_NUMBER rows must match final SSP
-- implemented-requirements control-id multiplicities by package.
-- Expected: zero mismatch rows.
-- =====================================================================
WITH source_controls AS (
  SELECT
    TRIM(s.CONTENT_ID::STRING) CONTENT_ID,
    s.CURATED_JSON:CONTROL_NUMBER::STRING CONTROL_ID,
    COUNT(*) N
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW s
  JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW p
    ON TRIM(p.CONTENT_ID::STRING)=TRIM(s.CONTENT_ID::STRING)
  WHERE s.CURATED_JSON:CONTROL_NUMBER IS NOT NULL
    AND NOT IS_NULL_VALUE(s.CURATED_JSON:CONTROL_NUMBER)
    AND NULLIF(TRIM(s.CURATED_JSON:CONTROL_NUMBER::STRING),'') IS NOT NULL
  GROUP BY 1,2
),
target_controls AS (
  SELECT
    TRIM(SOURCE_RECORD_ID::STRING) CONTENT_ID,
    METADATA_JSON:"control-id"::STRING CONTROL_ID,
    COUNT(*) N
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='implemented-requirements'
  GROUP BY 1,2
)
SELECT
  COALESCE(s.CONTENT_ID,t.CONTENT_ID) CONTENT_ID,
  COALESCE(s.CONTROL_ID,t.CONTROL_ID) CONTROL_ID,
  COALESCE(s.N,0) SOURCE_COUNT,
  COALESCE(t.N,0) TARGET_COUNT,
  CASE WHEN s.CONTENT_ID IS NULL THEN 'EXTRA_TARGET'
       WHEN t.CONTENT_ID IS NULL THEN 'MISSING_TARGET'
       WHEN s.N<>t.N THEN 'COUNT_MISMATCH'
  END DEFECT
FROM source_controls s
FULL OUTER JOIN target_controls t
  ON s.CONTENT_ID=t.CONTENT_ID
 AND s.CONTROL_ID=t.CONTROL_ID
WHERE s.CONTENT_ID IS NULL OR t.CONTENT_ID IS NULL OR s.N<>t.N
ORDER BY CONTENT_ID, CONTROL_ID
LIMIT 500;


-- H06B. Aggregate current Level-355 -> OSCAL parity.
WITH source_controls AS (
  SELECT TRIM(s.CONTENT_ID::STRING) CONTENT_ID,
         s.CURATED_JSON:CONTROL_NUMBER::STRING CONTROL_ID
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW s
  JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW p
    ON TRIM(p.CONTENT_ID::STRING)=TRIM(s.CONTENT_ID::STRING)
  WHERE s.CURATED_JSON:CONTROL_NUMBER IS NOT NULL
    AND NOT IS_NULL_VALUE(s.CURATED_JSON:CONTROL_NUMBER)
    AND NULLIF(TRIM(s.CURATED_JSON:CONTROL_NUMBER::STRING),'') IS NOT NULL
),
target_controls AS (
  SELECT TRIM(SOURCE_RECORD_ID::STRING) CONTENT_ID,
         METADATA_JSON:"control-id"::STRING CONTROL_ID
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE='implemented-requirements'
)
SELECT
  (SELECT COUNT(*) FROM source_controls) SOURCE_VALID_CONTROL_ROWS,
  (SELECT COUNT(*) FROM target_controls) TARGET_IMPLEMENTED_REQUIREMENTS,
  IFF(
    (SELECT COUNT(*) FROM source_controls)=(SELECT COUNT(*) FROM target_controls),
    'PASS','FAIL'
  ) ROW_COUNT_STATUS;


-- =====================================================================
-- H07. ONE REAL CONTENT_ID: HISTORICAL -> RAW -> FINAL OSCAL PAYLOAD
-- Pick one from current raw. Change only QA_CONTENT_ID.
-- =====================================================================
SET QA_CONTENT_ID = (
  SELECT TRIM(CONTENT_ID::STRING)
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  WHERE CURATED_JSON:AUTHORIZATION_PACKAGE_NAME IS NOT NULL
  ORDER BY CONTENT_ID
  LIMIT 1
);

SELECT
  'HISTORICAL' LAYER,
  h.CONTENT_ID::STRING CONTENT_ID,
  OBJECT_CONSTRUCT_KEEP_NULL(
    'AUTHORIZATION_PACKAGE_NAME',h.AUTHORIZATION_PACKAGE_NAME,
    'ACRONYM',h.ACRONYM,
    'MISSION_PURPOSE',h.MISSION_PURPOSE,
    'AUTHORIZATION_BOUNDARY_DESCRIPTION',h.AUTHORIZATION_BOUNDARY_DESCRIPTION
  ) PAYLOAD
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE h
WHERE TRIM(h.CONTENT_ID::STRING)=$QA_CONTENT_ID

UNION ALL

SELECT
  'CURRENT_RAW',
  r.CONTENT_ID::STRING,
  OBJECT_CONSTRUCT_KEEP_NULL(
    'AUTHORIZATION_PACKAGE_NAME',r.CURATED_JSON:AUTHORIZATION_PACKAGE_NAME,
    'ACRONYM',r.CURATED_JSON:ACRONYM,
    'MISSION_PURPOSE',r.CURATED_JSON:MISSION_PURPOSE,
    'AUTHORIZATION_BOUNDARY_DESCRIPTION',r.CURATED_JSON:AUTHORIZATION_BOUNDARY_DESCRIPTION
  )
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r
WHERE TRIM(r.CONTENT_ID::STRING)=$QA_CONTENT_ID

UNION ALL

SELECT
  'OSCAL_SSP_'||UPPER(ELEMENT_TYPE),
  SOURCE_RECORD_ID,
  METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
  AND ELEMENT_TYPE IN ('metadata','system-characteristics','authorization-boundary')
ORDER BY LAYER;


-- =====================================================================
-- INTERPRETATION
--
-- Production sign-off uses BOTH files:
--
-- 1) sql/qa/SOURCE_ONE_PRODUCTION_QA_2026-09-25.sql
--    -> graph integrity, PK/FK, roots, parent-child, cross-model, idempotency
--
-- 2) this file
--    -> historical Authorization Package vs current RAW vs final OSCAL values
--    -> current Level-355 RAW vs final OSCAL values
--    -> historical Level-355 comparison only after H00B proves the real object name
--
-- A historical mismatch is not automatically a mapper defect:
-- historical tables can be a different point-in-time snapshot.
-- First classify whether the historical and current RAW values differ.
-- If historical = RAW but OSCAL differs, that is a mapping defect candidate.
-- If historical != RAW, classify it as source-history drift before changing mapper logic.
-- =====================================================================
