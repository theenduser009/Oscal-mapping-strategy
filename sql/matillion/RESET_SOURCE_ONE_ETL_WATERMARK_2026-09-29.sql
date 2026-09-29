-- Source One ETL watermark rewind for DEV reload
-- Date: 2026-09-29
-- Control table contract previously used in this project:
--   RTX_RAW_DEV.ES_ESC_GRC.ETL_WATERMARK
--   SOURCE_SYSTEM, OBJECT_NAME, LAST_LOADED_DATE
--
-- Purpose:
--   Rewind only the Source One content objects we have actually used so the
--   Matillion source load can re-pull them before the updated raw->CURATED_JSON step.
--
-- IMPORTANT:
--   ETL_WATERMARK stores Archer OBJECT_NAME values without the physical _RAW suffix.
--   This script updates existing rows only; it does not INSERT missing watermark rows.
--   Meta lookup tables are intentionally excluded because their watermark contract
--   has not been established here.
--
-- Current reload date: previous day, so the 2026-09-29 daily load can be replayed.
SET RESET_TO_DATE = '2026-09-28';

-- 1) PRECHECK: confirm the exact watermark rows and current values before changing them.
SELECT
    SOURCE_SYSTEM,
    OBJECT_NAME,
    LAST_LOADED_DATE
FROM RTX_RAW_DEV.ES_ESC_GRC.ETL_WATERMARK
WHERE UPPER(SOURCE_SYSTEM) = 'ARCHER'
  AND UPPER(OBJECT_NAME) IN (
      'ARCHER_CONTENT_AUTHORIZATION_PACKAGE',
      'ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL',
      'ARCHER_CONTENT_SOFTWARE',
      'ARCHER_CONTENT_INTERCONNECTIONS'
  )
ORDER BY OBJECT_NAME;

-- 2) REWIND ONLY THESE SOURCE ONE OBJECTS.
UPDATE RTX_RAW_DEV.ES_ESC_GRC.ETL_WATERMARK
SET LAST_LOADED_DATE = TO_DATE($RESET_TO_DATE)
WHERE UPPER(SOURCE_SYSTEM) = 'ARCHER'
  AND UPPER(OBJECT_NAME) IN (
      'ARCHER_CONTENT_AUTHORIZATION_PACKAGE',
      'ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL',
      'ARCHER_CONTENT_SOFTWARE',
      'ARCHER_CONTENT_INTERCONNECTIONS'
  );

-- 3) READ BACK: verify the watermark after the update.
SELECT
    SOURCE_SYSTEM,
    OBJECT_NAME,
    LAST_LOADED_DATE
FROM RTX_RAW_DEV.ES_ESC_GRC.ETL_WATERMARK
WHERE UPPER(SOURCE_SYSTEM) = 'ARCHER'
  AND UPPER(OBJECT_NAME) IN (
      'ARCHER_CONTENT_AUTHORIZATION_PACKAGE',
      'ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL',
      'ARCHER_CONTENT_SOFTWARE',
      'ARCHER_CONTENT_INTERCONNECTIONS'
  )
ORDER BY OBJECT_NAME;
