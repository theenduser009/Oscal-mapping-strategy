-- Extension Properties population check
-- Date: 2026-09-15
-- READ ONLY. No writes.
--
-- Purpose:
-- Profile the seven fields currently proposed in the review workbook as
-- assessment-results.results[].props[].
-- IMPORTANT: this workbook target is not yet treated as approved source/model truth.
-- Grady/source-owner guidance indicates workflow/helper fields may be transient and
-- should not automatically be mapped to OSCAL. This query only checks population.
--
-- If the physical Assessment Results RAW table has a different name, change ONLY
-- the FROM table below after confirming the actual table name.

WITH src AS (
    SELECT TRY_PARSE_JSON(TO_VARCHAR(CURATED_JSON)) AS payload
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ASSESSMENT_RESULTS_RAW
)
SELECT
    COUNT(*) AS TOTAL_ROWS,
    COUNT_IF(payload:WORKFLOW_CURRENT_NODE IS NOT NULL)      AS WORKFLOW_CURRENT_NODE_CNT,
    COUNT_IF(payload:WORKFLOW_PROCESS_VERSION IS NOT NULL)   AS WORKFLOW_PROCESS_VERSION_CNT,
    COUNT_IF(payload:WORKFLOW_JOB_STATUS IS NOT NULL)        AS WORKFLOW_JOB_STATUS_CNT,
    COUNT_IF(payload:WORKFLOW_STATUS IS NOT NULL)            AS WORKFLOW_STATUS_CNT,
    COUNT_IF(payload:DUE_DATE IS NOT NULL)                   AS DUE_DATE_CNT,
    COUNT_IF(payload:WORKFLOW_CURRENT_NODE_HRTN IS NOT NULL) AS WORKFLOW_CURRENT_NODE_HRTN_CNT,
    COUNT_IF(payload:WORKFLOW_STATUS_CHANGED IS NOT NULL)    AS WORKFLOW_STATUS_CHANGED_CNT
FROM src;
