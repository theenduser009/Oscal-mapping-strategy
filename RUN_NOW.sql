-- RUN NOW — Source One Assessment Results attachment discovery
-- Date: 2026-09-21
-- READ ONLY. No target DML.
--
-- Current resolved metadata:
--   WORKFLOW_JOB_STATUS   FIELD_TYPE_ID=4  -> Archer Values List
--   RISK_ACCEPTANCE_RBDS  FIELD_TYPE_ID=9  -> Archer Cross-Reference
--   RISK_ASSESSMENT_REPORT FIELD_TYPE_ID=11 -> Archer Attachment
--
-- Purpose of this query:
-- Find the warehouse table(s) that expose Archer attachment metadata/content so
-- RISK_ASSESSMENT_REPORT can be mapped to OSCAL without inventing URLs or dropping
-- multi-valued attachment IDs.

-- 1) Candidate attachment-related tables/views in the Archer raw schema.
SELECT
    TABLE_NAME,
    TABLE_TYPE,
    ROW_COUNT
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND (
      UPPER(TABLE_NAME) LIKE '%ATTACH%'
      OR UPPER(TABLE_NAME) LIKE '%DOCUMENT%'
      OR UPPER(TABLE_NAME) LIKE '%FILE%'
  )
ORDER BY TABLE_NAME;

-- 2) Columns on those candidate tables/views.
SELECT
    C.TABLE_NAME,
    C.ORDINAL_POSITION,
    C.COLUMN_NAME,
    C.DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS C
WHERE C.TABLE_SCHEMA = 'ES_ESC_GRC'
  AND C.TABLE_NAME IN (
      SELECT TABLE_NAME
      FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
      WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
        AND (
            UPPER(TABLE_NAME) LIKE '%ATTACH%'
            OR UPPER(TABLE_NAME) LIKE '%DOCUMENT%'
            OR UPPER(TABLE_NAME) LIKE '%FILE%'
        )
  )
ORDER BY C.TABLE_NAME, C.ORDINAL_POSITION;
