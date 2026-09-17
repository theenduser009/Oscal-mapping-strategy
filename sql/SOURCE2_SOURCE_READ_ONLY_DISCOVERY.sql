-- Source 2 / Source -> Catalog Metadata: physical-source discovery only.
-- Prepared: 2026-09-17. Reviewed repository base: 5379fcf4e3fadcd1cfb1fddc8f1f636e82aa70c2.
-- Run this SELECT in a Snowflake SQL worksheet; do not run the seven cells yet.
-- The initial pilot fields are SOURCE_NAME and SOURCE_VERSION. Doubtful mappings stay pending.
-- Search starts in the existing RAW schema; Source 2 location is not assumed proven.
-- This query reads object/column metadata only: no source payloads, DDL or DML.
-- Names are candidates, not approved bindings; do not pick a RAW object by name alone.
-- Empty results mean no matching object is visible in this schema to your current role,
-- not proof that the Source table does not exist elsewhere or under another name.
-- Return this result for review. The single-record JSON check follows after binding review.

WITH candidate_objects AS (
    SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
    FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
      AND POSITION('AUTHORITATIVE_SOURCES_SOURCE' IN UPPER(TABLE_NAME)) > 0
)
SELECT
    CURRENT_TIMESTAMP() AS INSPECTED_AT,
    t.TABLE_CATALOG AS DATABASE_NAME,
    t.TABLE_SCHEMA AS SCHEMA_NAME,
    t.TABLE_NAME,
    t.TABLE_TYPE,
    c.ORDINAL_POSITION,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.NUMERIC_PRECISION,
    c.NUMERIC_SCALE,
    c.DATETIME_PRECISION,
    c.IS_NULLABLE
FROM candidate_objects AS t
LEFT JOIN RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS AS c
    ON c.TABLE_CATALOG = t.TABLE_CATALOG
   AND c.TABLE_SCHEMA = t.TABLE_SCHEMA
   AND c.TABLE_NAME = t.TABLE_NAME
ORDER BY t.TABLE_CATALOG, t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION;
