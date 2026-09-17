-- Source 2 / Source -> Catalog Metadata: read-only pilot readiness checks.
-- Prepared: 2026-09-17 after owner-provided Snowflake read-back confirmed:
--   RAW table: RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW
--   required RAW columns include CONTENT_ID and CURATED_JSON
--   CURATED_JSON is OBJECT and includes SOURCE_NAME / SOURCE_VERSION in sampled rows.
-- No DDL/DML. Do not run the seven-cell mapper yet.

-- 1) Confirm Source-level RAW identity quality for the mapper input contract.
SELECT
    COUNT(*) AS RAW_ROWS,
    COUNT_IF(CONTENT_ID IS NULL OR LENGTH(TRIM(CONTENT_ID)) = 0) AS MISSING_CONTENT_ID_ROWS,
    COUNT(DISTINCT CONTENT_ID) AS DISTINCT_CONTENT_IDS,
    COUNT_IF(CURATED_JSON IS NULL) AS NULL_CURATED_JSON_ROWS,
    COUNT(*) - COUNT(DISTINCT CONTENT_ID) AS DUPLICATE_CONTENT_ID_EXCESS_ROWS
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW;

-- 2) Confirm the committed Catalog target tables are physically present and inspect their columns.
SELECT
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    ORDINAL_POSITION,
    IS_NULLABLE
FROM RTX_ENTERPRISESERVICES_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC_CURATED'
  AND TABLE_NAME IN ('DIM_OSCAL_CATALOG_ELEMENT', 'FACT_OSCAL_CATALOG_DEPENDENCY')
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- 3) Read the live Catalog registry rows exactly as Snowflake stores them.
-- Cell 3 requires OSCAL_MODEL_KEY, NODE_PATH, parent/collection/identity/operator metadata,
-- UUID policy, process order, required members and IS_ACTIVE to compile the model safely.
SELECT *
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(OSCAL_MODEL_KEY) = 'CATALOG'
   OR LOWER(NODE_PATH) LIKE 'catalog%'
ORDER BY PROCESS_ORDER, NODE_PATH;

-- Return all three result sets for review.
-- We will not insert/update registry rows or enable runtime mapping until these results are reviewed.
