-- Source One Assessment Results — post-preview verification
-- Date: 2026-09-21
-- READ ONLY. No target DML.
--
-- Context:
-- Source One = Archer Authorization Package.
-- This check follows the 2026-09-21 bulk Assessment Results mapping update.
-- PREVIEW evidence supplied by owner: Source One 2,813 records / 90,016 nodes /
-- 87,203 edges, validation passed, storage verified, writes false, target DML false.
--
-- Purpose:
-- Confirm the 12 newly approved Source One Assessment Results mappings are the
-- metadata currently visible to Snowflake before investigating population/routing.
--
-- Expected:
-- 12 rows, all APPROVED, with the transforms and runtime paths committed in
-- Mapping/ARCHER_OSCAL_MAPPINGS.csv.
--
-- NOTE:
-- If the runtime mapping metadata is not materialized as
-- RTX_RAW_DEV.ES_ESC_GRC.ARCHER_OSCAL_MAPPINGS in this environment, do not create
-- or replace anything. Use the notebook's Cell 2 loaded mapping dataframe/check
-- instead and preserve the same 12-field filter.

SELECT
    SOURCE_FIELD_NAME,
    EXECUTION_STATUS,
    TRANSFORM_ID,
    RUNTIME_TARGET_PATH
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_OSCAL_MAPPINGS
WHERE SOURCE_FIELD_NAME IN (
    'AVG_SECURITY_COMPLIANCE_REPORTING_SCORE',
    'AVG_SECURITY_COMPLIANCE_SCORE',
    'TOTAL_PACKAGE_INHERENT_RISK',
    'RISK_ACCEPTANCE_RBDS',
    'RISK_ASSESSMENT_REPORT',
    'WORKFLOW_CURRENT_NODE',
    'WORKFLOW_PROCESS_VERSION',
    'WORKFLOW_JOB_STATUS',
    'WORKFLOW_STATUS',
    'DUE_DATE',
    'WORKFLOW_CURRENT_NODE_HRTN',
    'WORKFLOW_STATUS_CHANGED'
)
ORDER BY SOURCE_FIELD_NAME;
