-- OSCAL / Archer metadata lookup discovery
-- Date: 2026-09-29
-- Purpose: identify available Meta User / Meta Group tables and exact columns
-- before adding user/group enrichment to the Matillion CURATED_JSON UPDATE.
-- Also includes the existing Meta Field and Meta Value column definitions.
--
-- READ ONLY: one SELECT; no data changes, temporary tables, or pipeline reruns.
-- Run this file in Snowflake Dev and return the column-definition result.
-- This returns schema metadata, not user/group business records.
-- Only objects accessible to the current role in ES_ESC_GRC are returned.
-- A missing table in this result does not establish its absence elsewhere.
--
-- Publication baseline: simplify-metadata-boundary
-- 9217ad6746a08177450d0230b01bbc966039d72e
-- This is the same discovery SELECT supplied in the QA conversation.
-- It is not the revised enrichment UPDATE and has not been run in Snowflake here.

SELECT
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME ILIKE 'ARCHER%META%'
  AND (
       TABLE_NAME ILIKE '%USER%'
    OR TABLE_NAME ILIKE '%GROUP%'
    OR TABLE_NAME IN ('ARCHER_META_FIELD', 'ARCHER_META_VALUE')
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;
