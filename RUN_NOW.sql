-- RUN NOW — Source One Assessment Results: locate RISK_ASSESSMENT_REPORT in the actual Authorization Package tables
-- Date: 2026-09-21
-- READ ONLY. No target DML.
--
-- What the previous discovery proved:
-- * RISK_ASSESSMENT_REPORT = Archer FIELD_TYPE_ID 11 (Attachment), LEVEL_ID 353, MODULE_ID 547.
-- * There is no dedicated table/view whose NAME contains ATTACH/FILE/BINARY in ES_ESC_GRC.
-- * Attachment-related fields are instead present as columns on many Archer content tables.
--
-- Therefore stop looking for a global attachment table. Resolve the owning Archer
-- level/module and inspect the exact Authorization Package column(s).

-- 1) Resolve Archer Level 353 / Module 547 to their business names.
SELECT
    LEVEL_ID,
    LEVEL_NAME,
    MODULE_ID,
    MODULE_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_LEVEL
WHERE LEVEL_ID = 353
   OR MODULE_ID = 547
ORDER BY LEVEL_ID;

-- 2) Find the exact structured/STG column for RISK_ASSESSMENT_REPORT anywhere in ES_ESC_GRC.
SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND (
       UPPER(COLUMN_NAME) = 'RISK_ASSESSMENT_REPORT'
    OR UPPER(COLUMN_NAME) LIKE '%RISK%ASSESSMENT%REPORT%'
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- 3) On the Authorization Package structured/STG tables, show only attachment/report-related columns.
SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME IN (
      'ARCHER_CONTENT_AUTHORIZATION_PACKAGE',
      'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_STG'
  )
  AND (
       UPPER(COLUMN_NAME) LIKE '%ATTACH%'
    OR UPPER(COLUMN_NAME) LIKE '%RISK%ASSESSMENT%REPORT%'
    OR UPPER(COLUMN_NAME) LIKE '%REPORT%'
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- Stop after these three result sets.
-- Do not join attachment IDs to DOCUMENT_ID / DOCUMENT_URL and do not change the mapping yet.
