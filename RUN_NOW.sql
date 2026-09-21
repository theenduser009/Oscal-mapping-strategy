-- RUN NOW — Source One Assessment Results: find the REAL Archer attachment identifier/store
-- Date: 2026-09-21
-- READ ONLY. No target DML.
--
-- Correction:
-- Do NOT join RISK_ASSESSMENT_REPORT attachment IDs to
-- ARCHER_CONTENT_DOCUMENT_REPOSITORY.DOCUMENT_ID and do NOT treat DOCUMENT_URL
-- as the attachment identifier. The Document Repository is a business content
-- application/table, not proven Archer attachment storage.
--
-- Confirmed live metadata:
--   RISK_ASSESSMENT_REPORT -> FIELD_TYPE_ID = 11 (Attachment)
--   Source payload -> arrays of numeric attachment IDs
--
-- Goal:
-- Find the actual warehouse table/column that stores Archer attachment/file IDs
-- and determine the correct key before changing the OSCAL mapping.

-- 1) Re-read the exact Archer field metadata row.
SELECT
    FIELD_ID,
    FIELD_TYPE_ID,
    FIELD_GUID,
    LEVEL_ID,
    MODULE_ID,
    FIELD_NAME,
    SELECT_ID,
    SQL_FIELD_NAME,
    KEY_FIELD
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(TRIM(SQL_FIELD_NAME)) = 'RISK_ASSESSMENT_REPORT';

-- 2) Find candidate tables/views whose NAMES suggest Archer attachment/file storage.
SELECT
    TABLE_NAME,
    TABLE_TYPE,
    ROW_COUNT
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND (
       UPPER(TABLE_NAME) LIKE '%ATTACH%'
    OR UPPER(TABLE_NAME) LIKE '%FILE%'
    OR UPPER(TABLE_NAME) LIKE '%BINARY%'
  )
ORDER BY TABLE_NAME;

-- 3) Find candidate attachment/file identifier columns anywhere in the Archer schema.
-- This is metadata-only discovery; no source values are printed.
SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND (
       UPPER(COLUMN_NAME) LIKE '%ATTACH%'
    OR UPPER(COLUMN_NAME) LIKE '%FILE_ID%'
    OR UPPER(COLUMN_NAME) LIKE '%FILEID%'
    OR UPPER(COLUMN_NAME) LIKE '%ATTACHMENT_ID%'
    OR UPPER(COLUMN_NAME) LIKE '%ATTACHMENTID%'
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- 4) Inventory Archer metadata tables that may resolve MODULE_ID / LEVEL_ID / FIELD_ID
-- to the physical application/source. This tells us what metadata is available
-- before guessing a backing table.
SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND UPPER(TABLE_NAME) LIKE 'ARCHER_META_%'
  AND UPPER(COLUMN_NAME) IN (
      'MODULE_ID',
      'LEVEL_ID',
      'FIELD_ID',
      'FIELD_TYPE_ID',
      'MODULE_NAME',
      'LEVEL_NAME',
      'APPLICATION_ID',
      'APPLICATION_NAME',
      'TABLE_NAME',
      'SQL_TABLE_NAME'
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;
