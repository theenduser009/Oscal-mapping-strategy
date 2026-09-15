-- Read-only discovery: trace the Archer metadata relationship for ALLOCATED_CONTROLS.
-- Goal: resolve the source field to its cross-reference / related-record target application/level.
-- No target writes.

-- Step 1: identify the ALLOCATED_CONTROLS field metadata.
SELECT
    FIELD_ID,
    LEVEL_ID,
    SQL_FIELD_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(SQL_FIELD_NAME) = 'ALLOCATED_CONTROLS';

-- Step 2: confirm whether a metadata relationship table exists in this schema.
SHOW TABLES LIKE '%RELATION%' IN SCHEMA RTX_RAW_DEV.ES_ESC_GRC;

-- If a relationship table is returned, use the FIELD_ID from Step 1 as CR_FIELD_ID.
-- Example shape only; adjust the physical table/column names to the Step 2 result before running:
-- SELECT *
-- FROM RTX_RAW_DEV.ES_ESC_GRC.<ARCHER_META_FIELD_RELATIONSHIP_TABLE>
-- WHERE CR_FIELD_ID = <FIELD_ID_FROM_STEP_1>;
