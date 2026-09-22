-- SOURCE ONE END-TO-END QA PACK
-- Date: 2026-09-22
-- Repository branch: simplify-metadata-boundary
-- Repository basis before creation: 75db443a91c3151f3430a717b84aa4df3f8f74d5
--
-- READ ONLY. No target DML / no registry DML / no source DML.
--
-- Source One runtime source:
--   RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
--
-- Current runtime model routes from Cell 1:
--   SSP, ASSESSMENT_RESULTS, POAM, SECURITY_ASSESSMENT_PLAN
--
-- IMPORTANT SCOPE:
-- * Catalog is Source Two, NOT Source One.
-- * Profile is not a current Source One runtime route in Cell 1.
-- * Core SSP Control Implementation implemented-requirements[] is not expected
--   until ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW (Level 355 CONTROL) is ingested.
-- * AUTHORIZATION_DECISION was PREVIEW-reconciled on 2026-09-21 but its new
--   2,308-row target COMMIT/read-back has not yet been supplied.
-- * RISK_ASSESSMENT_REPORT remains deferred.
-- * FINDINGS destination is known; current reviewed Source One value was null.
--
-- HOW TO USE:
-- 1) Run section 01A and pick a candidate CONTENT_ID with broad coverage.
-- 2) Set QA_CONTENT_ID below to that value.
-- 3) Run sections 01B through 10 and save the result grids/screenshots.
--
-- Replace this after running 01A:
SET QA_CONTENT_ID = 'REPLACE_WITH_CONTENT_ID';


-- =====================================================================
-- 01A. FIND A REPRESENTATIVE SOURCE RECORD
-- Prefer MODEL_GROUPS_WITH_DATA = 4.
-- If no one record covers all four routes, use the best primary record and
-- choose a second record for the missing route.
-- =====================================================================
WITH representative_fields(MODEL_GROUP, SOURCE_FIELD) AS (
  SELECT COLUMN1, COLUMN2 FROM VALUES
    ('SSP', 'AUTHORIZATION_PACKAGE_NAME'),
    ('SSP', 'SAP_ID'),
    ('SSP', 'OPERATIONAL_STATUS'),
    ('SSP', 'AUTHORIZATION_BOUNDARY_DESCRIPTION'),
    ('SSP', 'INFORMATION_SYSTEM_OWNER_ISO'),
    ('SSP', 'INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO'),
    ('SSP', 'SUBSYSTEMS'),
    ('SSP', 'SOFTWARE'),
    ('SSP', 'HARDWARE'),
    ('SSP', 'INTERCONNECTIONS'),
    ('ASSESSMENT_RESULTS', 'VULNERABILITY_SCORE'),
    ('ASSESSMENT_RESULTS', 'AVG_SECURITY_COMPLIANCE_SCORE'),
    ('ASSESSMENT_RESULTS', 'TOTAL_PACKAGE_INHERENT_RISK'),
    ('ASSESSMENT_RESULTS', 'WORKFLOW_STATUS'),
    ('POAM', 'POAMS'),
    ('SECURITY_ASSESSMENT_PLAN', 'REQUEST_TO_BEGIN_ASSESSMENT'),
    ('SECURITY_ASSESSMENT_PLAN', 'APPROVAL_TO_BEGIN_ASSESSMENT'),
    ('SECURITY_ASSESSMENT_PLAN', 'PREASSESSMENT_REVIEW_COMMENTS')
),
source_flat AS (
  SELECT
    TRIM(s.CONTENT_ID::STRING) AS CONTENT_ID,
    f.KEY::STRING AS SOURCE_FIELD,
    f.VALUE AS SOURCE_VALUE
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW s,
       LATERAL FLATTEN(INPUT => s.CURATED_JSON) f
),
hits AS (
  SELECT
    sf.CONTENT_ID,
    rf.MODEL_GROUP,
    rf.SOURCE_FIELD,
    CASE
      WHEN TYPEOF(sf.SOURCE_VALUE) = 'NULL_VALUE' THEN 0
      WHEN TYPEOF(sf.SOURCE_VALUE) = 'VARCHAR'
           AND NULLIF(TRIM(sf.SOURCE_VALUE::STRING), '') IS NULL THEN 0
      WHEN TYPEOF(sf.SOURCE_VALUE) = 'ARRAY'
           AND ARRAY_SIZE(sf.SOURCE_VALUE) = 0 THEN 0
      WHEN TYPEOF(sf.SOURCE_VALUE) = 'OBJECT'
           AND ARRAY_SIZE(OBJECT_KEYS(sf.SOURCE_VALUE)) = 0 THEN 0
      ELSE 1
    END AS HAS_VALUE
  FROM source_flat sf
  JOIN representative_fields rf
    ON UPPER(sf.SOURCE_FIELD) = UPPER(rf.SOURCE_FIELD)
)
SELECT
  CONTENT_ID,
  COUNT_IF(HAS_VALUE = 1) AS REPRESENTATIVE_FIELDS_POPULATED,
  COUNT(DISTINCT IFF(HAS_VALUE = 1, MODEL_GROUP, NULL)) AS MODEL_GROUPS_WITH_DATA,
  MAX(IFF(MODEL_GROUP='SSP' AND HAS_VALUE=1,1,0)) AS HAS_SSP,
  MAX(IFF(MODEL_GROUP='ASSESSMENT_RESULTS' AND HAS_VALUE=1,1,0)) AS HAS_ASSESSMENT_RESULTS,
  MAX(IFF(MODEL_GROUP='POAM' AND HAS_VALUE=1,1,0)) AS HAS_POAM,
  MAX(IFF(MODEL_GROUP='SECURITY_ASSESSMENT_PLAN' AND HAS_VALUE=1,1,0)) AS HAS_ASSESSMENT_PLAN
FROM hits
GROUP BY CONTENT_ID
ORDER BY MODEL_GROUPS_WITH_DATA DESC, REPRESENTATIVE_FIELDS_POPULATED DESC, CONTENT_ID
LIMIT 20;


-- =====================================================================
-- 01B. SOURCE RECORD UNIQUENESS / BASIC SANITY
-- Expected for QA_CONTENT_ID: 1 row, 1 distinct CONTENT_ID.
-- =====================================================================
SELECT
  $QA_CONTENT_ID AS QA_CONTENT_ID,
  COUNT(*) AS SOURCE_ROWS,
  COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) AS DISTINCT_CONTENT_IDS,
  CASE WHEN COUNT(*)=1 AND COUNT(DISTINCT TRIM(CONTENT_ID::STRING))=1
       THEN 'PASS' ELSE 'REVIEW' END AS SOURCE_RECORD_STATUS
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
WHERE TRIM(CONTENT_ID::STRING) = $QA_CONTENT_ID;


-- =====================================================================
-- 02. CURRENT APPROVED/GUARDED SOURCE-ONE MAPPING FIELDS FOR THIS RECORD
-- This CTE is generated from the current repository runtime CSV.
-- It shows the source value, transform and runtime target path.
-- CONFIG rows are reported separately in 02B.
-- =====================================================================
WITH mappings(
  OSCAL_MODEL_LABEL, SOURCE_FIELD, RUNTIME_TARGET_PATH, TRANSFORM_ID,
  EXECUTION_STATUS, VALUE_SOURCE, NULL_POLICY, PROPERTY_NAME, ROLE_ID, REFERENCE_TYPE
) AS (
  SELECT COLUMN1,COLUMN2,COLUMN3,COLUMN4,COLUMN5,COLUMN6,COLUMN7,COLUMN8,COLUMN9,COLUMN10
  FROM VALUES
    ('SSP - Metadata', 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED', 'system-security-plan.metadata.published', 'timestamp', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - Metadata', 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED', 'system-security-plan.metadata.last-modified', 'timestamp', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - Metadata', 'TRACKING_ID', 'system-security-plan.metadata.document-ids[].identifier', 'identifier', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - Metadata', 'FIRST_PUBLISHED', 'system-security-plan.metadata.published', 'timestamp', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - Metadata', 'LAST_UPDATED', 'system-security-plan.metadata.last-modified', 'timestamp', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - Metadata', 'INFORMATION_OWNER_IO', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'information-owner', ''),
    ('SSP - Metadata', 'INFORMATION_SYSTEM_OWNER_ISO', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'system-owner', ''),
    ('SSP - Metadata', 'SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'senior-information-systems-security-officer', ''),
    ('SSP - Metadata', 'AUTHORIZING_OFFICIAL_AO', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'authorizing-official', ''),
    ('SSP - Metadata', 'INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'system-security-officer', ''),
    ('SSP - Metadata', 'INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'information-system-security-engineer', ''),
    ('SSP - Metadata', 'INFORMATION_SYSTEM_ADMINISTRATOR_ISA', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'information-system-administrator', ''),
    ('SSP - Metadata', 'AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'authorizing-official-designated-representative', ''),
    ('SSP - Metadata', 'PRIVACY_OFFICER_PO', 'system-security-plan.metadata.responsible-parties[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', 'privacy-officer', ''),
    ('SSP - System Characteristics', 'SAP_ID', 'system-security-plan.system-characteristics.system-ids[].id', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'AUTHORIZATION_PACKAGE_NAME', 'system-security-plan.system-characteristics.system-name', 'text', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'ACRONYM', 'system-security-plan.system-characteristics.system-name-short', 'text', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'OPERATIONAL_STATUS', 'system-security-plan.system-characteristics.status.state', 'status-crosswalk', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'INFORMATION_SYSTEM_TYPE', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'FISMA_REPORTABLE', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'FINANCIAL_SYSTEM', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'MISSION_CRITICAL', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'CRITICAL_INFRASTRUCTURE', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'MISSION_PURPOSE', 'system-security-plan.system-characteristics.description', 'text', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'PACKAGE_TYPE', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'AUTHORIZATION_BOUNDARY_DESCRIPTION', 'system-security-plan.system-characteristics.authorization-boundary.description', 'text', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'AUTHORIZATION_DECISION', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'AUTHORIZATION_COMMENTS', 'system-security-plan.system-characteristics.status.remarks', 'text', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'PIA_REQUIRED', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'ATOIATO_DATE', 'system-security-plan.system-characteristics.date-authorized', 'date', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY', 'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE', 'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'RECOMMENDED_INTEGRITY_CONTROL_CATEGORY', 'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'INTEGRITY_CONTROL_CATEGORY_OVERRIDE', 'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'AVAILABILITY_CONTROL_CATEGORY_OVERRIDE', 'system-security-plan.system-characteristics.security-impact-level.security-objective-availability', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY', 'system-security-plan.system-characteristics.security-impact-level.security-objective-availability', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'SECURITY_CATEGORY', 'system-security-plan.system-characteristics.security-sensitivity-level', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY', 'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY', 'system-security-plan.system-characteristics.security-impact-level.security-objective-availability', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'CNSS_AVAILABILITY_RATING', 'system-security-plan.system-characteristics.security-impact-level.security-objective-availability', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'CNSS_CONFIDENTIALITY_RATING', 'system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Characteristics', 'CNSS_INTEGRITY_RATING', 'system-security-plan.system-characteristics.security-impact-level.security-objective-integrity', 'security-objective', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - System Implementation', 'SUBSYSTEMS', 'system-security-plan.system-implementation.components[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', 'system'),
    ('SSP - System Implementation', 'SOFTWARE', 'system-security-plan.system-implementation.components[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', 'software'),
    ('SSP - System Implementation', 'HARDWARE', 'system-security-plan.system-implementation.components[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', 'hardware'),
    ('SSP - System Implementation', 'INTERCONNECTIONS', 'system-security-plan.system-implementation.components[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', 'interconnection'),
    ('SSP - System Implementation', 'INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM', 'system-security-plan.system-implementation.components[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', 'interconnection'),
    ('SSP - System Implementation', 'SAP_INTAKE_FORM_INTERCONNECTIONS', 'system-security-plan.system-implementation.components[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', 'interconnection'),
    ('System Security Plan', 'INFORMATION_CLASSIFICATION', 'system-security-plan.system-characteristics.props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('System Security Plan', 'DAILY_LOSS_AMOUNT_FROM_OUTAGE', 'system-security-plan.system-characteristics.props[]', 'direct', 'APPROVED', 'FIELD', 'preserve', '', '', ''),
    ('Assessment Results', 'RISK_ACCEPTANCE_RBDS', 'assessment-results.results[].props[]', 'reference-ids', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'VULNERABILITY_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'ANTIVIRUS_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'PATCH_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'SECURITY_COMPLIANCE_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'STANDARD_OPERATING_ENVIRONMENT_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'COMPUTER_PASSWORD_AGE_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'VULNERABILITY_REPORTING_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'SECURITY_COMPLIANCE_REPORTING_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_AUTHORIZATION_PACKAGE_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'RISK_SCORE_GRADE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_VULNERABILITY_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_PATCH_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_SECURITY_COMPLIANCE_REPORTING_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_ANTIVIRUS_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_COMPUTER_PASSWORD_AGE_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_VULNERABILITY_REPORTING_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'AVG_SECURITY_COMPLIANCE_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'TOTAL_PACKAGE_INHERENT_RISK', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'TOTAL_PACKAGE_RESIDUAL_RISK', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'ADJUSTED_TOTAL_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'ADJUSTED_AVERAGE_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'CURRENT_HIGHEST_DEVICE_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'CURRENT_AVERAGE_DEVICE_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'CURRENT_CONTROL_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'BASELINE_HIGHEST_DEVICE_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'BASELINE_AVERAGE_DEVICE_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'BASELINE_CONTROL_RISK_SCORE', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'RISK_ASSESSMENT', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', '_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', '_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'INITIAL_RISK_ASSESSMENT', 'assessment-results.results[].observations[]', 'scalar-score', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'WORKFLOW_CURRENT_NODE', 'assessment-results.results[].props[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'WORKFLOW_PROCESS_VERSION', 'assessment-results.results[].props[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'WORKFLOW_JOB_STATUS', 'assessment-results.results[].props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'WORKFLOW_STATUS', 'assessment-results.results[].props[]', 'archer-select', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'DUE_DATE', 'assessment-results.results[].props[]', 'date', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'WORKFLOW_CURRENT_NODE_HRTN', 'assessment-results.results[].props[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Assessment Results', 'WORKFLOW_STATUS_CHANGED', 'assessment-results.results[].props[]', 'date', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('POA&M', 'POAMS', 'plan-of-action-and-milestones.poam-items[]', 'direct', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('Security Assessment Plan', 'REQUEST_TO_BEGIN_ASSESSMENT', 'assessment-plan.tasks[].props[]', 'archer-select', 'APPROVED', 'FIELD', 'preserve', '', '', ''),
    ('Security Assessment Plan', 'APPROVAL_TO_BEGIN_ASSESSMENT', 'assessment-plan.tasks[].props[]', 'archer-select', 'APPROVED', 'FIELD', 'preserve', '', '', ''),
    ('Security Assessment Plan', 'PREASSESSMENT_REVIEW_COMMENTS', 'assessment-plan.tasks[].remarks', 'text', 'APPROVED', 'FIELD', 'preserve', '', '', ''),
    ('SSP', 'RECOMMENDED_SECURITY_CATEGORY', 'system-security-plan.system-characteristics.security-impact-level', 'reject-populated', 'BLOCKED_IF_POPULATED', 'FIELD', 'omit', '', '', ''),
    ('SSP - Metadata', 'AUTHORIZATION_PACKAGE_NAME', 'system-security-plan.metadata.title', 'text', 'APPROVED', 'FIELD', 'omit', '', '', ''),
    ('SSP - Metadata', 'OSCAL_VERSION', 'system-security-plan.metadata.oscal-version', 'text', 'APPROVED', 'CONFIG', 'omit', '', '', ''),
    ('SSP - Metadata', 'SSP_DOCUMENT_VERSION', 'system-security-plan.metadata.version', 'canonical-text', 'APPROVED', 'CONFIG', 'omit', '', '', ''),
    ('Security Assessment Plan', 'ASSESSMENT_TASK_TITLE', 'assessment-plan.tasks[].title', 'text', 'APPROVED', 'CONFIG', 'omit', '', '', ''),
    ('Security Assessment Plan', 'ASSESSMENT_TASK_TYPE', 'assessment-plan.tasks[].type', 'text', 'APPROVED', 'CONFIG', 'omit', '', '', '')
),
src AS (
  SELECT CURATED_JSON
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  WHERE TRIM(CONTENT_ID::STRING) = $QA_CONTENT_ID
),
flat AS (
  SELECT f.KEY::STRING AS SOURCE_FIELD, f.VALUE AS SOURCE_VALUE
  FROM src, LATERAL FLATTEN(INPUT => src.CURATED_JSON) f
)
SELECT
  m.OSCAL_MODEL_LABEL,
  m.SOURCE_FIELD,
  m.EXECUTION_STATUS,
  m.TRANSFORM_ID,
  m.RUNTIME_TARGET_PATH,
  m.NULL_POLICY,
  m.ROLE_ID,
  m.REFERENCE_TYPE,
  CASE
    WHEN f.SOURCE_FIELD IS NULL THEN 'ABSENT'
    WHEN TYPEOF(f.SOURCE_VALUE) = 'NULL_VALUE' THEN 'EXPLICIT_JSON_NULL'
    WHEN TYPEOF(f.SOURCE_VALUE) = 'VARCHAR'
         AND NULLIF(TRIM(f.SOURCE_VALUE::STRING), '') IS NULL THEN 'EMPTY_STRING'
    WHEN TYPEOF(f.SOURCE_VALUE) = 'ARRAY'
         AND ARRAY_SIZE(f.SOURCE_VALUE) = 0 THEN 'EMPTY_ARRAY'
    WHEN TYPEOF(f.SOURCE_VALUE) = 'OBJECT'
         AND ARRAY_SIZE(OBJECT_KEYS(f.SOURCE_VALUE)) = 0 THEN 'EMPTY_OBJECT'
    ELSE 'POPULATED'
  END AS SOURCE_STATE,
  TYPEOF(f.SOURCE_VALUE) AS SOURCE_TYPE,
  f.SOURCE_VALUE
FROM mappings m
LEFT JOIN flat f
  ON UPPER(f.SOURCE_FIELD) = UPPER(m.SOURCE_FIELD)
WHERE m.VALUE_SOURCE <> 'CONFIG'
ORDER BY m.OSCAL_MODEL_LABEL, m.RUNTIME_TARGET_PATH, m.SOURCE_FIELD;


-- 02B. CONFIG-SOURCED VALUES (not Archer JSON keys)
WITH config_rows(OSCAL_MODEL_LABEL, CONFIG_KEY, RUNTIME_TARGET_PATH) AS (
  SELECT COLUMN1,COLUMN2,COLUMN3 FROM VALUES
    ('SSP - Metadata', 'OSCAL_VERSION', 'system-security-plan.metadata.oscal-version'),
    ('SSP - Metadata', 'SSP_DOCUMENT_VERSION', 'system-security-plan.metadata.version'),
    ('Security Assessment Plan', 'ASSESSMENT_TASK_TITLE', 'assessment-plan.tasks[].title'),
    ('Security Assessment Plan', 'ASSESSMENT_TASK_TYPE', 'assessment-plan.tasks[].type')
)
SELECT
  OSCAL_MODEL_LABEL,
  CONFIG_KEY,
  RUNTIME_TARGET_PATH,
  CASE CONFIG_KEY
    WHEN 'OSCAL_VERSION' THEN '1.2.3'
    WHEN 'SSP_DOCUMENT_VERSION' THEN '1.0'
    WHEN 'ASSESSMENT_TASK_TITLE' THEN 'Preassessment review'
    WHEN 'ASSESSMENT_TASK_TYPE' THEN 'action'
  END AS EXPECTED_CONFIG_VALUE
FROM config_rows
ORDER BY OSCAL_MODEL_LABEL, CONFIG_KEY;


-- =====================================================================
-- 03. LIVE REGISTRY / RULES FOR THE FOUR SOURCE-ONE ROUTES
-- Expected mechanical properties:
-- * one root per model
-- * no duplicate active NODE_PATH
-- * every non-root child has an active parent
-- =====================================================================
SELECT
  OSCAL_MODEL_KEY,
  NODE_PATH,
  ELEMENT_TYPE,
  PARENT_NODE_PATH,
  IS_COLLECTION,
  INSTANCE_KEY_RULE,
  PROCESS_ORDER,
  ITEM_PATH,
  OPERATOR,
  UUID_POLICY,
  REQUIRED_MEMBERS
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) IN
      ('SSP','ASSESSMENT_RESULTS','POAM','SECURITY_ASSESSMENT_PLAN')
  AND COALESCE(IS_ACTIVE, TRUE) = TRUE
ORDER BY OSCAL_MODEL_KEY, PROCESS_ORDER, NODE_PATH;


-- 03B. Registry structural defects. Expected: zero rows.
WITH r AS (
  SELECT *
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) IN
        ('SSP','ASSESSMENT_RESULTS','POAM','SECURITY_ASSESSMENT_PLAN')
    AND COALESCE(IS_ACTIVE, TRUE) = TRUE
),
duplicate_paths AS (
  SELECT OSCAL_MODEL_KEY, NODE_PATH, COUNT(*) AS N
  FROM r
  GROUP BY OSCAL_MODEL_KEY, NODE_PATH
  HAVING COUNT(*) > 1
),
orphans AS (
  SELECT c.OSCAL_MODEL_KEY, c.NODE_PATH, c.PARENT_NODE_PATH
  FROM r c
  LEFT JOIN r p
    ON UPPER(TRIM(p.OSCAL_MODEL_KEY)) = UPPER(TRIM(c.OSCAL_MODEL_KEY))
   AND p.NODE_PATH = c.PARENT_NODE_PATH
  WHERE c.PARENT_NODE_PATH IS NOT NULL
    AND p.NODE_PATH IS NULL
)
SELECT 'DUPLICATE_PATH' AS DEFECT, OSCAL_MODEL_KEY, NODE_PATH, NULL AS DETAIL
FROM duplicate_paths
UNION ALL
SELECT 'ORPHAN_PARENT', OSCAL_MODEL_KEY, NODE_PATH, PARENT_NODE_PATH
FROM orphans
ORDER BY DEFECT, OSCAL_MODEL_KEY, NODE_PATH;


-- =====================================================================
-- 04. TARGET NODE COUNTS FOR THE SELECTED SOURCE RECORD
-- A formal PASS requires the corresponding route to have been committed in
-- the QA environment. Zero rows before a route is loaded = NOT READY, not a
-- transformation defect.
-- =====================================================================
SELECT 'SSP' AS MODEL,
       COUNT(*) AS NODE_COUNT,
       COUNT(DISTINCT ELEMENT_TYPE) AS ELEMENT_TYPES,
       COUNT_IF(ELEMENT_TYPE='system-security-plan') AS ROOT_COUNT
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
UNION ALL
SELECT 'ASSESSMENT_RESULTS',
       COUNT(*), COUNT(DISTINCT ELEMENT_TYPE),
       COUNT_IF(ELEMENT_TYPE='assessment-results')
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
UNION ALL
SELECT 'POAM',
       COUNT(*), COUNT(DISTINCT ELEMENT_TYPE),
       COUNT_IF(ELEMENT_TYPE='plan-of-action-and-milestones')
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
UNION ALL
SELECT 'SECURITY_ASSESSMENT_PLAN',
       COUNT(*), COUNT(DISTINCT ELEMENT_TYPE),
       COUNT_IF(ELEMENT_TYPE='assessment-plan')
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
ORDER BY MODEL;


-- 04B. Target element inventory for this record
SELECT 'SSP' MODEL, ELEMENT_TYPE, COUNT(*) N
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
GROUP BY ELEMENT_TYPE
UNION ALL
SELECT 'ASSESSMENT_RESULTS', ELEMENT_TYPE, COUNT(*)
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
GROUP BY ELEMENT_TYPE
UNION ALL
SELECT 'POAM', ELEMENT_TYPE, COUNT(*)
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
GROUP BY ELEMENT_TYPE
UNION ALL
SELECT 'SECURITY_ASSESSMENT_PLAN', ELEMENT_TYPE, COUNT(*)
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
GROUP BY ELEMENT_TYPE
ORDER BY MODEL, ELEMENT_TYPE;


-- =====================================================================
-- 05. SSP DIRECT FIELD EXAMPLES
-- These are easy source-to-target checks for a QA tester.
-- =====================================================================
WITH src AS (
  SELECT CURATED_JSON
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  WHERE TRIM(CONTENT_ID::STRING)=$QA_CONTENT_ID
),
metadata_node AS (
  SELECT METADATA_JSON
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
    AND ELEMENT_TYPE='metadata'
),
sc_node AS (
  SELECT METADATA_JSON
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
    AND ELEMENT_TYPE='system-characteristics'
),
boundary_node AS (
  SELECT METADATA_JSON
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
    AND ELEMENT_TYPE='authorization-boundary'
)
SELECT
  'AUTHORIZATION_PACKAGE_NAME -> metadata.title' AS CHECK_NAME,
  src.CURATED_JSON:AUTHORIZATION_PACKAGE_NAME::STRING AS SOURCE_VALUE,
  metadata_node.METADATA_JSON:title::STRING AS TARGET_VALUE,
  IFF(src.CURATED_JSON:AUTHORIZATION_PACKAGE_NAME::STRING
      = metadata_node.METADATA_JSON:title::STRING,'PASS','REVIEW') AS STATUS
FROM src, metadata_node
UNION ALL
SELECT
  'AUTHORIZATION_PACKAGE_NAME -> system-characteristics.system-name',
  src.CURATED_JSON:AUTHORIZATION_PACKAGE_NAME::STRING,
  sc_node.METADATA_JSON:"system-name"::STRING,
  IFF(src.CURATED_JSON:AUTHORIZATION_PACKAGE_NAME::STRING
      = sc_node.METADATA_JSON:"system-name"::STRING,'PASS','REVIEW')
FROM src, sc_node
UNION ALL
SELECT
  'ACRONYM -> system-characteristics.system-name-short',
  src.CURATED_JSON:ACRONYM::STRING,
  sc_node.METADATA_JSON:"system-name-short"::STRING,
  IFF(src.CURATED_JSON:ACRONYM::STRING
      = sc_node.METADATA_JSON:"system-name-short"::STRING,'PASS','REVIEW')
FROM src, sc_node
UNION ALL
SELECT
  'MISSION_PURPOSE -> system-characteristics.description',
  src.CURATED_JSON:MISSION_PURPOSE::STRING,
  sc_node.METADATA_JSON:description::STRING,
  IFF(src.CURATED_JSON:MISSION_PURPOSE::STRING
      = sc_node.METADATA_JSON:description::STRING,'PASS','REVIEW')
FROM src, sc_node
UNION ALL
SELECT
  'AUTHORIZATION_BOUNDARY_DESCRIPTION -> authorization-boundary.description',
  src.CURATED_JSON:AUTHORIZATION_BOUNDARY_DESCRIPTION::STRING,
  boundary_node.METADATA_JSON:description::STRING,
  IFF(src.CURATED_JSON:AUTHORIZATION_BOUNDARY_DESCRIPTION::STRING
      = boundary_node.METADATA_JSON:description::STRING,'PASS','REVIEW')
FROM src, boundary_node;


-- 05B. SSP system IDs and current system-characteristics payload
SELECT
  ELEMENT_TYPE,
  OSCAL_UUID,
  METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
  AND ELEMENT_TYPE IN ('system-characteristics','system-ids','status','security-impact-level',
                       'authorization-boundary','props')
ORDER BY ELEMENT_TYPE, OSCAL_UUID;


-- =====================================================================
-- 06. SSP RESPONSIBLE PARTIES
-- Compare source Users/Groups population to generated responsible-party payloads.
-- Do not share the raw UserList/GroupList IDs outside the authorized QA team.
-- =====================================================================
WITH role_map(SOURCE_FIELD, ROLE_ID, ROLE_TITLE) AS (
  SELECT COLUMN1,COLUMN2,COLUMN3 FROM VALUES
    ('INFORMATION_OWNER_IO', 'information-owner', 'Information Owner'),
    ('INFORMATION_SYSTEM_OWNER_ISO', 'system-owner', 'Information System Owner'),
    ('SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO', 'senior-information-systems-security-officer', 'Senior Information Systems Security Officer'),
    ('AUTHORIZING_OFFICIAL_AO', 'authorizing-official', 'Authorizing Official'),
    ('INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO', 'system-security-officer', 'Information System Security Officer'),
    ('INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE', 'information-system-security-engineer', 'Information System Security Engineer'),
    ('INFORMATION_SYSTEM_ADMINISTRATOR_ISA', 'information-system-administrator', 'Information System Administrator'),
    ('AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR', 'authorizing-official-designated-representative', 'Authorizing Official Designated Representative'),
    ('PRIVACY_OFFICER_PO', 'privacy-officer', 'Privacy Officer')
),
src AS (
  SELECT CURATED_JSON
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  WHERE TRIM(CONTENT_ID::STRING)=$QA_CONTENT_ID
),
flat AS (
  SELECT f.KEY::STRING AS SOURCE_FIELD, f.VALUE AS SOURCE_VALUE
  FROM src, LATERAL FLATTEN(INPUT=>src.CURATED_JSON) f
),
source_roles AS (
  SELECT
    rm.ROLE_ID,
    rm.ROLE_TITLE,
    rm.SOURCE_FIELD,
    COALESCE(ARRAY_SIZE(GET(f.SOURCE_VALUE,'UserList')),0)
      + COALESCE(ARRAY_SIZE(GET(f.SOURCE_VALUE,'GroupList')),0) AS SOURCE_SUBJECT_COUNT
  FROM role_map rm
  LEFT JOIN flat f
    ON UPPER(f.SOURCE_FIELD)=UPPER(rm.SOURCE_FIELD)
),
target_roles AS (
  SELECT
    METADATA_JSON:"role-id"::STRING AS ROLE_ID,
    COUNT(*) AS RESPONSIBLE_PARTY_NODES,
    SUM(COALESCE(ARRAY_SIZE(METADATA_JSON:"party-uuids"),0)) AS TARGET_PARTY_UUID_COUNT
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
    AND ELEMENT_TYPE='responsible-parties'
  GROUP BY METADATA_JSON:"role-id"::STRING
)
SELECT
  s.ROLE_ID,
  s.ROLE_TITLE,
  s.SOURCE_FIELD,
  s.SOURCE_SUBJECT_COUNT,
  COALESCE(t.RESPONSIBLE_PARTY_NODES,0) AS RESPONSIBLE_PARTY_NODES,
  COALESCE(t.TARGET_PARTY_UUID_COUNT,0) AS TARGET_PARTY_UUID_COUNT
FROM source_roles s
LEFT JOIN target_roles t USING (ROLE_ID)
ORDER BY s.ROLE_ID;


-- 06B. Read the actual role / party / assignment payloads
SELECT ELEMENT_TYPE, OSCAL_UUID, METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
  AND ELEMENT_TYPE IN ('roles','parties','responsible-parties')
ORDER BY ELEMENT_TYPE, OSCAL_UUID;


-- =====================================================================
-- 07. SSP SYSTEM IMPLEMENTATION / COMPONENTS
-- Source count is DISTINCT ContentId by component type across all approved
-- source fields. Target count is component nodes by METADATA_JSON:type.
-- =====================================================================
WITH component_fields(SOURCE_FIELD, COMPONENT_TYPE) AS (
  SELECT COLUMN1,COLUMN2 FROM VALUES
    ('SUBSYSTEMS', 'system'),
    ('SOFTWARE', 'software'),
    ('HARDWARE', 'hardware'),
    ('INTERCONNECTIONS', 'interconnection'),
    ('INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM', 'interconnection'),
    ('SAP_INTAKE_FORM_INTERCONNECTIONS', 'interconnection')
),
src AS (
  SELECT CURATED_JSON
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  WHERE TRIM(CONTENT_ID::STRING)=$QA_CONTENT_ID
),
flat AS (
  SELECT f.KEY::STRING AS SOURCE_FIELD, f.VALUE AS SOURCE_VALUE
  FROM src, LATERAL FLATTEN(INPUT=>src.CURATED_JSON) f
),
source_refs AS (
  SELECT
    cf.COMPONENT_TYPE,
    x.VALUE:ContentId::STRING AS REF_CONTENT_ID
  FROM component_fields cf
  JOIN flat f
    ON UPPER(f.SOURCE_FIELD)=UPPER(cf.SOURCE_FIELD),
       LATERAL FLATTEN(INPUT=>f.SOURCE_VALUE) x
  WHERE x.VALUE:ContentId IS NOT NULL
),
source_counts AS (
  SELECT COMPONENT_TYPE, COUNT(DISTINCT REF_CONTENT_ID) AS SOURCE_DISTINCT_REFERENCES
  FROM source_refs
  GROUP BY COMPONENT_TYPE
),
target_counts AS (
  SELECT
    METADATA_JSON:type::STRING AS COMPONENT_TYPE,
    COUNT(*) AS TARGET_COMPONENT_NODES
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
    AND ELEMENT_TYPE='components'
  GROUP BY METADATA_JSON:type::STRING
),
types AS (
  SELECT COMPONENT_TYPE FROM source_counts
  UNION
  SELECT COMPONENT_TYPE FROM target_counts
)
SELECT
  t.COMPONENT_TYPE,
  COALESCE(s.SOURCE_DISTINCT_REFERENCES,0) AS SOURCE_DISTINCT_REFERENCES,
  COALESCE(g.TARGET_COMPONENT_NODES,0) AS TARGET_COMPONENT_NODES,
  IFF(COALESCE(s.SOURCE_DISTINCT_REFERENCES,0)=COALESCE(g.TARGET_COMPONENT_NODES,0),
      'PASS','REVIEW') AS COUNT_STATUS
FROM types t
LEFT JOIN source_counts s USING (COMPONENT_TYPE)
LEFT JOIN target_counts g USING (COMPONENT_TYPE)
ORDER BY COMPONENT_TYPE;


-- 07B. Component payloads; software/interconnection may be hydrated from lookups.
SELECT OSCAL_UUID, METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
  AND ELEMENT_TYPE='components'
ORDER BY METADATA_JSON:type::STRING, METADATA_JSON:title::STRING, OSCAL_UUID;


-- =====================================================================
-- 08. ASSESSMENT RESULTS
-- Shows each current approved Source One AR field beside the generated
-- observation/result-property payload value(s).
-- SELECT objects are expected to resolve to labels in the target.
-- =====================================================================
WITH ar_map(SOURCE_FIELD, TARGET_KIND, PROPERTY_NAME, TRANSFORM_ID) AS (
  SELECT COLUMN1,COLUMN2,COLUMN3,COLUMN4 FROM VALUES
    ('RISK_ACCEPTANCE_RBDS', 'result-prop', 'risk-acceptance-rbds', 'reference-ids'),
    ('VULNERABILITY_SCORE', 'observation', 'vulnerability-score', 'scalar-score'),
    ('ANTIVIRUS_SCORE', 'observation', 'antivirus-score', 'scalar-score'),
    ('PATCH_SCORE', 'observation', 'patch-score', 'scalar-score'),
    ('SECURITY_COMPLIANCE_SCORE', 'observation', 'security-compliance-score', 'scalar-score'),
    ('STANDARD_OPERATING_ENVIRONMENT_SCORE', 'observation', 'standard-operating-environment-score', 'scalar-score'),
    ('COMPUTER_PASSWORD_AGE_SCORE', 'observation', 'computer-password-age-score', 'scalar-score'),
    ('VULNERABILITY_REPORTING_SCORE', 'observation', 'vulnerability-reporting-score', 'scalar-score'),
    ('SECURITY_COMPLIANCE_REPORTING_SCORE', 'observation', 'security-compliance-reporting-score', 'scalar-score'),
    ('TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE', 'observation', 'total-authorization-package-risk-score', 'scalar-score'),
    ('AVG_AUTHORIZATION_PACKAGE_RISK_SCORE', 'observation', 'avg-authorization-package-risk-score', 'scalar-score'),
    ('RISK_SCORE_GRADE', 'observation', 'risk-score-grade', 'scalar-score'),
    ('AVG_VULNERABILITY_SCORE', 'observation', 'avg-vulnerability-score', 'scalar-score'),
    ('AVG_PATCH_SCORE', 'observation', 'avg-patch-score', 'scalar-score'),
    ('AVG_SECURITY_COMPLIANCE_REPORTING_SCORE', 'observation', 'avg-security-compliance-reporting-score', 'scalar-score'),
    ('AVG_ANTIVIRUS_SCORE', 'observation', 'avg-antivirus-score', 'scalar-score'),
    ('AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE', 'observation', 'avg-standard-operating-environment-score', 'scalar-score'),
    ('AVG_COMPUTER_PASSWORD_AGE_SCORE', 'observation', 'avg-computer-password-age-score', 'scalar-score'),
    ('AVG_VULNERABILITY_REPORTING_SCORE', 'observation', 'avg-vulnerability-reporting-score', 'scalar-score'),
    ('AVG_SECURITY_COMPLIANCE_SCORE', 'observation', 'avg-security-compliance-score', 'scalar-score'),
    ('TOTAL_PACKAGE_INHERENT_RISK', 'observation', 'total-package-inherent-risk', 'scalar-score'),
    ('TOTAL_PACKAGE_RESIDUAL_RISK', 'observation', 'total-package-residual-risk', 'scalar-score'),
    ('ADJUSTED_TOTAL_RISK_SCORE', 'observation', 'adjusted-total-risk-score', 'scalar-score'),
    ('ADJUSTED_AVERAGE_RISK_SCORE', 'observation', 'adjusted-average-risk-score', 'scalar-score'),
    ('CURRENT_HIGHEST_DEVICE_RISK_SCORE', 'observation', 'current-highest-device-risk-score', 'scalar-score'),
    ('CURRENT_AVERAGE_DEVICE_RISK_SCORE', 'observation', 'current-average-device-risk-score', 'scalar-score'),
    ('CURRENT_CONTROL_RISK_SCORE', 'observation', 'current-control-risk-score', 'scalar-score'),
    ('PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD', 'observation', 'pct-current-highest-device-risk-threshold', 'scalar-score'),
    ('PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD', 'observation', 'pct-current-average-device-risk-threshold', 'scalar-score'),
    ('BASELINE_HIGHEST_DEVICE_RISK_SCORE', 'observation', 'baseline-highest-device-risk-score', 'scalar-score'),
    ('BASELINE_AVERAGE_DEVICE_RISK_SCORE', 'observation', 'baseline-average-device-risk-score', 'scalar-score'),
    ('BASELINE_CONTROL_RISK_SCORE', 'observation', 'baseline-control-risk-score', 'scalar-score'),
    ('RISK_ASSESSMENT', 'observation', 'risk-assessment', 'scalar-score'),
    ('_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD', 'observation', 'current-average-device-risk-threshold', 'scalar-score'),
    ('_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD', 'observation', 'current-highest-device-risk-threshold', 'scalar-score'),
    ('INITIAL_RISK_ASSESSMENT', 'observation', 'initial-risk-assessment', 'scalar-score'),
    ('WORKFLOW_CURRENT_NODE', 'result-prop', 'workflow-current-node', 'direct'),
    ('WORKFLOW_PROCESS_VERSION', 'result-prop', 'workflow-process-version', 'direct'),
    ('WORKFLOW_JOB_STATUS', 'result-prop', 'workflow-job-status', 'archer-select'),
    ('WORKFLOW_STATUS', 'result-prop', 'workflow-status', 'archer-select'),
    ('DUE_DATE', 'result-prop', 'due-date', 'date'),
    ('WORKFLOW_CURRENT_NODE_HRTN', 'result-prop', 'workflow-current-node-hrtn', 'direct'),
    ('WORKFLOW_STATUS_CHANGED', 'result-prop', 'workflow-status-changed', 'date')
),
src AS (
  SELECT CURATED_JSON
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  WHERE TRIM(CONTENT_ID::STRING)=$QA_CONTENT_ID
),
flat AS (
  SELECT f.KEY::STRING AS SOURCE_FIELD, f.VALUE AS SOURCE_VALUE
  FROM src, LATERAL FLATTEN(INPUT=>src.CURATED_JSON) f
),
target_values AS (
  SELECT
    'observation' AS TARGET_KIND,
    METADATA_JSON:"props"[0]:name::STRING AS PROPERTY_NAME,
    ARRAY_AGG(METADATA_JSON:"props"[0]:value) AS TARGET_VALUES,
    COUNT(*) AS TARGET_NODE_COUNT
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
    AND ELEMENT_TYPE='observations'
  GROUP BY METADATA_JSON:"props"[0]:name::STRING

  UNION ALL

  SELECT
    'result-prop',
    METADATA_JSON:name::STRING,
    ARRAY_AGG(METADATA_JSON:value),
    COUNT(*)
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
    AND ELEMENT_TYPE='props'
  GROUP BY METADATA_JSON:name::STRING
)
SELECT
  m.SOURCE_FIELD,
  m.TRANSFORM_ID,
  m.TARGET_KIND,
  m.PROPERTY_NAME,
  TYPEOF(f.SOURCE_VALUE) AS SOURCE_TYPE,
  f.SOURCE_VALUE,
  COALESCE(t.TARGET_NODE_COUNT,0) AS TARGET_NODE_COUNT,
  t.TARGET_VALUES
FROM ar_map m
LEFT JOIN flat f
  ON UPPER(f.SOURCE_FIELD)=UPPER(m.SOURCE_FIELD)
LEFT JOIN target_values t
  ON t.TARGET_KIND=m.TARGET_KIND
 AND t.PROPERTY_NAME=m.PROPERTY_NAME
ORDER BY m.TARGET_KIND, m.PROPERTY_NAME;


-- =====================================================================
-- 09. POA&M REFERENCE COUNT
-- Current Source One POAM mapping is the Authorization Package POAMS reference.
-- =====================================================================
WITH src AS (
  SELECT CURATED_JSON
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  WHERE TRIM(CONTENT_ID::STRING)=$QA_CONTENT_ID
),
source_poams AS (
  SELECT COUNT(DISTINCT x.VALUE:ContentId::STRING) AS SOURCE_POAM_REFERENCES
  FROM src, LATERAL FLATTEN(INPUT=>src.CURATED_JSON:POAMS) x
  WHERE x.VALUE:ContentId IS NOT NULL
),
target_poams AS (
  SELECT COUNT(*) AS TARGET_POAM_ITEMS
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
    AND ELEMENT_TYPE='poam-items'
)
SELECT
  SOURCE_POAM_REFERENCES,
  TARGET_POAM_ITEMS,
  IFF(SOURCE_POAM_REFERENCES=TARGET_POAM_ITEMS,'PASS','REVIEW_OR_NOT_LOADED') AS STATUS
FROM source_poams, target_poams;


SELECT ELEMENT_TYPE, OSCAL_UUID, METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
ORDER BY ELEMENT_TYPE, OSCAL_UUID;


-- =====================================================================
-- 10. SECURITY ASSESSMENT PLAN
-- One preassessment task per source record when the route is loaded.
-- The two select fields become task props; comments become task remarks.
-- =====================================================================
WITH src AS (
  SELECT CURATED_JSON
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
  WHERE TRIM(CONTENT_ID::STRING)=$QA_CONTENT_ID
)
SELECT
  src.CURATED_JSON:REQUEST_TO_BEGIN_ASSESSMENT AS SOURCE_REQUEST_TO_BEGIN_ASSESSMENT,
  src.CURATED_JSON:APPROVAL_TO_BEGIN_ASSESSMENT AS SOURCE_APPROVAL_TO_BEGIN_ASSESSMENT,
  src.CURATED_JSON:PREASSESSMENT_REVIEW_COMMENTS AS SOURCE_PREASSESSMENT_REVIEW_COMMENTS
FROM src;

SELECT ELEMENT_TYPE, OSCAL_UUID, METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT
WHERE SOURCE_SYSTEM_NAME='ARCHER'
  AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
ORDER BY ELEMENT_TYPE, OSCAL_UUID;


-- =====================================================================
-- 11. GRAPH INTEGRITY FOR THE SELECTED RECORD
-- Expected for a loaded route:
-- * MISSING_PARENT_NODES = 0
-- * MISSING_CHILD_NODES = 0
-- * CROSS_RECORD_EDGES = 0
-- =====================================================================
WITH
ssp_nodes AS (
  SELECT PK_OSCAL_SSP_ELEMENT_HASH NODE_KEY, SOURCE_RECORD_ID
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
),
ssp_check AS (
  SELECT
    'SSP' MODEL,
    COUNT(*) EDGE_COUNT,
    COUNT_IF(p.NODE_KEY IS NULL) MISSING_PARENT_NODES,
    COUNT_IF(c.NODE_KEY IS NULL) MISSING_CHILD_NODES,
    COUNT_IF(p.NODE_KEY IS NOT NULL AND c.NODE_KEY IS NOT NULL
             AND p.SOURCE_RECORD_ID<>c.SOURCE_RECORD_ID) CROSS_RECORD_EDGES
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f
  LEFT JOIN ssp_nodes p ON p.NODE_KEY=f.FK_SOURCE_ELEMENT_HASH
  LEFT JOIN ssp_nodes c ON c.NODE_KEY=f.FK_TARGET_ELEMENT_HASH
  WHERE TRIM(p.SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
     OR TRIM(c.SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
),
ar_nodes AS (
  SELECT PK_DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT_HASH NODE_KEY, SOURCE_RECORD_ID
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
),
ar_check AS (
  SELECT
    'ASSESSMENT_RESULTS' MODEL,
    COUNT(*) EDGE_COUNT,
    COUNT_IF(p.NODE_KEY IS NULL) MISSING_PARENT_NODES,
    COUNT_IF(c.NODE_KEY IS NULL) MISSING_CHILD_NODES,
    COUNT_IF(p.NODE_KEY IS NOT NULL AND c.NODE_KEY IS NOT NULL
             AND p.SOURCE_RECORD_ID<>c.SOURCE_RECORD_ID) CROSS_RECORD_EDGES
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY f
  LEFT JOIN ar_nodes p ON p.NODE_KEY=f.FK_SOURCE_ELEMENT_HASH
  LEFT JOIN ar_nodes c ON c.NODE_KEY=f.FK_TARGET_ELEMENT_HASH
  WHERE TRIM(p.SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
     OR TRIM(c.SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
),
poam_nodes AS (
  SELECT PK_DIM_OSCAL_POAM_ELEMENT_HASH NODE_KEY, SOURCE_RECORD_ID
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
),
poam_check AS (
  SELECT
    'POAM' MODEL,
    COUNT(*) EDGE_COUNT,
    COUNT_IF(p.NODE_KEY IS NULL) MISSING_PARENT_NODES,
    COUNT_IF(c.NODE_KEY IS NULL) MISSING_CHILD_NODES,
    COUNT_IF(p.NODE_KEY IS NOT NULL AND c.NODE_KEY IS NOT NULL
             AND p.SOURCE_RECORD_ID<>c.SOURCE_RECORD_ID) CROSS_RECORD_EDGES
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_POAM_DEPENDENCY f
  LEFT JOIN poam_nodes p ON p.NODE_KEY=f.FK_SOURCE_ELEMENT_HASH
  LEFT JOIN poam_nodes c ON c.NODE_KEY=f.FK_TARGET_ELEMENT_HASH
  WHERE TRIM(p.SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
     OR TRIM(c.SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
),
sap_nodes AS (
  SELECT PK_DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT_HASH NODE_KEY, SOURCE_RECORD_ID
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
),
sap_check AS (
  SELECT
    'SECURITY_ASSESSMENT_PLAN' MODEL,
    COUNT(*) EDGE_COUNT,
    COUNT_IF(p.NODE_KEY IS NULL) MISSING_PARENT_NODES,
    COUNT_IF(c.NODE_KEY IS NULL) MISSING_CHILD_NODES,
    COUNT_IF(p.NODE_KEY IS NOT NULL AND c.NODE_KEY IS NOT NULL
             AND p.SOURCE_RECORD_ID<>c.SOURCE_RECORD_ID) CROSS_RECORD_EDGES
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_ASSESSMENT_PLAN_DEPENDENCY f
  LEFT JOIN sap_nodes p ON p.NODE_KEY=f.FK_SOURCE_ELEMENT_HASH
  LEFT JOIN sap_nodes c ON c.NODE_KEY=f.FK_TARGET_ELEMENT_HASH
  WHERE TRIM(p.SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
     OR TRIM(c.SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
)
SELECT *, IFF(MISSING_PARENT_NODES=0 AND MISSING_CHILD_NODES=0 AND CROSS_RECORD_EDGES=0,
              'PASS','REVIEW') AS INTEGRITY_STATUS
FROM ssp_check
UNION ALL
SELECT *, IFF(MISSING_PARENT_NODES=0 AND MISSING_CHILD_NODES=0 AND CROSS_RECORD_EDGES=0,
              'PASS','REVIEW') FROM ar_check
UNION ALL
SELECT *, IFF(MISSING_PARENT_NODES=0 AND MISSING_CHILD_NODES=0 AND CROSS_RECORD_EDGES=0,
              'PASS','REVIEW') FROM poam_check
UNION ALL
SELECT *, IFF(MISSING_PARENT_NODES=0 AND MISSING_CHILD_NODES=0 AND CROSS_RECORD_EDGES=0,
              'PASS','REVIEW') FROM sap_check
ORDER BY MODEL;


-- =====================================================================
-- 12. OPTIONAL SSP TREE / PATH DEMO FOR THE SELECTED RECORD
-- Reconstructs written parent-child path from DIM+FACT.
-- =====================================================================
WITH RECURSIVE
nodes AS (
  SELECT
    PK_OSCAL_SSP_ELEMENT_HASH AS NODE_KEY,
    SOURCE_RECORD_ID,
    ELEMENT_TYPE,
    OSCAL_UUID,
    METADATA_JSON
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME='ARCHER'
    AND SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND TRIM(SOURCE_RECORD_ID::STRING)=$QA_CONTENT_ID
),
edges AS (
  SELECT FK_SOURCE_ELEMENT_HASH AS PARENT_NODE_KEY,
         FK_TARGET_ELEMENT_HASH AS CHILD_NODE_KEY,
         DEPENDENCY_TYPE
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY
),
graph(
  SOURCE_RECORD_ID,NODE_KEY,PARENT_NODE_KEY,ELEMENT_TYPE,OSCAL_UUID,PARENT_OSCAL_UUID,
  DEPENDENCY_TYPE,STRUCTURAL_PATH,WRITTEN_PAYLOAD,DEPTH
) AS (
  SELECT
    n.SOURCE_RECORD_ID,n.NODE_KEY,CAST(NULL AS BINARY(16)),n.ELEMENT_TYPE,n.OSCAL_UUID,
    CAST(NULL AS VARCHAR),CAST(NULL AS VARCHAR),
    CAST(n.ELEMENT_TYPE AS VARCHAR(2000)),n.METADATA_JSON,0
  FROM nodes n
  WHERE n.ELEMENT_TYPE='system-security-plan'

  UNION ALL

  SELECT
    child.SOURCE_RECORD_ID,child.NODE_KEY,parent.NODE_KEY,child.ELEMENT_TYPE,child.OSCAL_UUID,
    parent.OSCAL_UUID,edge.DEPENDENCY_TYPE,
    CAST(parent.STRUCTURAL_PATH||'.'||child.ELEMENT_TYPE AS VARCHAR(2000)),
    child.METADATA_JSON,parent.DEPTH+1
  FROM graph parent
  JOIN edges edge ON edge.PARENT_NODE_KEY=parent.NODE_KEY
  JOIN nodes child ON child.NODE_KEY=edge.CHILD_NODE_KEY
  WHERE parent.DEPTH<30
)
SELECT SOURCE_RECORD_ID,STRUCTURAL_PATH AS OSCAL_PATH,ELEMENT_TYPE,OSCAL_UUID,
       WRITTEN_PAYLOAD,PARENT_OSCAL_UUID,DEPENDENCY_TYPE
FROM graph
ORDER BY DEPTH,OSCAL_PATH,OSCAL_UUID;
