-- Source 2 / Source -> Catalog Metadata: exact RAW-source read-only discovery.
-- Corrected: 2026-09-17 after owner clarification that the physical source is the
-- same Archer content name with _RAW appended, and mapped fields are in CURATED_JSON.
-- No DDL/DML. Do not run the seven cells yet.

-- Expected physical source for the Source level:
-- RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW

-- 1) Confirm the exact RAW object and the columns the seven-cell framework needs.
SELECT
    CURRENT_TIMESTAMP() AS INSPECTED_AT,
    TABLE_CATALOG AS DATABASE_NAME,
    TABLE_SCHEMA AS SCHEMA_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    ORDINAL_POSITION,
    IS_NULLABLE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME = 'ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW'
ORDER BY ORDINAL_POSITION;

-- 2) Read only a very small sample from the RAW CURATED_JSON payload.
-- This checks the first two clear Catalog Metadata pilot fields without using
-- the non-RAW/wide table as the mapping source.
SELECT
    CONTENT_ID,
    TYPEOF(CURATED_JSON) AS CURATED_JSON_TYPE,
    CURATED_JSON:"SOURCE_NAME"::STRING AS SOURCE_NAME,
    CURATED_JSON:"SOURCE_VERSION"::STRING AS SOURCE_VERSION
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW
WHERE CURATED_JSON IS NOT NULL
LIMIT 5;
