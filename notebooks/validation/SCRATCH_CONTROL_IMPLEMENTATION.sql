-- CONTROL IMPLEMENTATION / ALLOCATED_CONTROLS DISCOVERY
-- Date: 2026-09-15
-- Read-only only. Run each numbered query separately, top to bottom.
--
-- Verified so far:
--   Authorization Package ALLOCATED_CONTROLS contains {ContentId, LevelId} references.
--   Example referenced record: ContentId = 573482, LevelId = 355.
--   ARCHER_META_CONTENT confirms ContentId 573482 belongs to LevelId 355.
--   ARCHER_META_LEVEL resolves LevelId 355 to:
--       LEVEL_NAME = CONTROL
--       MODULE_ID  = 549
--       MODULE_NAME = ALLOCATED CONTROLS
--   The source Authorization Package level is 353.
--   SQL_FIELD_NAME ALLOCATED_CONTROLS occurs on multiple levels, including:
--       FieldId 23429 / LevelId 353 (Authorization Package)
--       FieldId 23190 / LevelId 350 (Subsystems)
--       FieldId 25941 / LevelId 102 (Task Management)
--   No metadata relationship table was found by SHOW TABLES LIKE '%RELATION%'.
--
-- Goal now: identify the physical Archer content table containing LevelId 355 records,
-- then read ContentId 573482 and inspect the actual control payload.


-- ============================================================
-- 1. Reconfirm the ALLOCATED_CONTROLS field definitions
-- ============================================================
SELECT
    FIELD_ID,
    LEVEL_ID,
    SQL_FIELD_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(SQL_FIELD_NAME) = 'ALLOCATED_CONTROLS'
ORDER BY LEVEL_ID, FIELD_ID;


-- ============================================================
-- 2. Resolve the relevant source/target Archer levels
-- Expected:
--   353 = AUTHORIZATION PACKAGE
--   355 = CONTROL / module ALLOCATED CONTROLS
-- ============================================================
SELECT *
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_LEVEL
WHERE LEVEL_ID IN (353, 355, 350, 102)
ORDER BY LEVEL_ID;


-- ============================================================
-- 3. Reconfirm the referenced ContentId -> LevelId
-- Expected: 573482 -> 355
-- ============================================================
SELECT *
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_CONTENT
WHERE CONTENT_ID = 573482;


-- ============================================================
-- 4. List all Archer content tables in the schema
-- Use this result to identify candidate physical source tables.
-- ============================================================
SELECT
    TABLE_NAME
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME ILIKE 'ARCHER_CONTENT%'
ORDER BY TABLE_NAME;


-- ============================================================
-- 5. Narrow to control-related Archer content tables
-- This is discovery only; a name match does NOT prove ownership of LevelId 355.
-- ============================================================
SELECT
    TABLE_NAME
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME ILIKE 'ARCHER_CONTENT%'
  AND TABLE_NAME ILIKE '%CONTROL%'
ORDER BY TABLE_NAME;


-- ============================================================
-- 6. Inspect LevelId 355 field signatures
-- These fields help identify the correct physical source table.
-- ============================================================
SELECT
    FIELD_ID,
    SQL_FIELD_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE LEVEL_ID = 355
ORDER BY FIELD_ID;


-- ============================================================
-- 7. After a candidate RAW table is identified, test ContentId 573482
-- DO NOT run until <CANDIDATE_RAW_TABLE> is replaced with a real table name.
-- ============================================================
-- SELECT *
-- FROM RTX_RAW_DEV.ES_ESC_GRC.<CANDIDATE_RAW_TABLE>
-- WHERE CONTENT_ID = '573482';


-- ============================================================
-- 8. Once the correct table is confirmed, inspect only the JSON keys first
-- to avoid making mapping assumptions from field names alone.
-- Replace <CONFIRMED_RAW_TABLE> before running.
-- ============================================================
-- SELECT DISTINCT
--     f.key::STRING AS FIELD_NAME
-- FROM RTX_RAW_DEV.ES_ESC_GRC.<CONFIRMED_RAW_TABLE> r,
-- LATERAL FLATTEN(INPUT => r.CURATED_JSON) f
-- WHERE r.CONTENT_ID = '573482'
-- ORDER BY FIELD_NAME;
