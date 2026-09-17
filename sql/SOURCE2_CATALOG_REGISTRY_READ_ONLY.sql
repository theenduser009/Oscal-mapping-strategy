-- Source 2 / Catalog registry pre-insert inspection.
-- Prepared: 2026-09-17 after live readiness results showed:
--   148 RAW rows, 0 missing CONTENT_ID, 148 distinct CONTENT_IDs,
--   0 NULL CURATED_JSON rows, Catalog DIM/FACT tables present,
--   and 0 existing Catalog registry rows.
-- READ ONLY. NO DDL / NO DML.

-- 1) Confirm the live registry table's current column contract.
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    ORDINAL_POSITION,
    IS_NULLABLE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY'
ORDER BY ORDINAL_POSITION;

-- 2) Read representative active rows from already-working models so the new
-- Catalog hierarchy follows the current live conventions instead of an old setup script.
SELECT
    OSCAL_MODEL_KEY,
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER,
    IS_ACTIVE,
    ITEM_PATH,
    OPERATOR,
    UUID_POLICY,
    REQUIRED_MEMBERS
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE COALESCE(IS_ACTIVE, TRUE) = TRUE
  AND (
       PARENT_NODE_PATH IS NULL
       OR LOWER(NODE_PATH) LIKE '%metadata%'
       OR LOWER(NODE_PATH) LIKE '%props[]'
      )
ORDER BY OSCAL_MODEL_KEY, PROCESS_ORDER, NODE_PATH;

-- 3) Double-check that no active or inactive Catalog rows already exist.
-- Expected from the prior read-back: zero rows.
SELECT
    OSCAL_MODEL_KEY,
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER,
    IS_ACTIVE,
    ITEM_PATH,
    OPERATOR,
    UUID_POLICY,
    REQUIRED_MEMBERS
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(COALESCE(OSCAL_MODEL_KEY, '')) = 'CATALOG'
   OR LOWER(COALESCE(NODE_PATH, '')) LIKE 'catalog%'
ORDER BY PROCESS_ORDER, NODE_PATH;

-- Return all three result sets.
-- After review, the next step will be a separate guarded Catalog registry setup script.
-- Do not insert registry rows manually and do not run the seven-cell mapper yet.
