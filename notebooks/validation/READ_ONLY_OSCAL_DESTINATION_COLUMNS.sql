-- Run in a Snowflake SQL worksheet; no notebook session variables are needed.
-- Returns column definitions for OSCAL tables in the currently used DEV schema.
-- No target data is read or changed. Missing rows are not proof a table is absent
-- from every database: visibility depends on the active role and this schema.
SELECT
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    ORDINAL_POSITION
FROM RTX_ENTERPRISESERVICES_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC_CURATED'
  AND TABLE_NAME ILIKE '%OSCAL%'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
