-- ============================================================
-- SSP VALIDATION 01 — LIVE REGISTRY STRUCTURAL CHECK
-- Date: 2026-09-15
-- READ ONLY. NO DML / NO DDL.
--
-- Repository contract used:
--   Mapping/ARCHER_OSCAL_MAPPINGS.csv is the runtime mapping artifact.
--   RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY is the live registry.
--
-- Purpose of this first executable validation:
--   1) inspect the live SSP registry rows actually present in Snowflake;
--   2) verify duplicate path / process-order conditions;
--   3) verify every active SSP child points to an active SSP parent;
--   4) verify collection identity metadata is present;
--   5) report the currently registered SSP branch inventory.
--
-- IMPORTANT:
--   This does NOT prove OSCAL semantic correctness yet.
--   This does NOT validate the CSV contents inside Snowflake because the runtime
--   mapping CSV is a notebook/repository file, not a proven Snowflake table.
--   CSV-to-registry validation will be done against the actual GitHub CSV plus
--   the read-back produced by this script.
-- ============================================================

-- ------------------------------------------------------------
-- 01A. Live active SSP registry inventory
-- ------------------------------------------------------------
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
WHERE UPPER(OSCAL_MODEL_KEY) = 'SSP'
  AND COALESCE(IS_ACTIVE, TRUE) = TRUE
ORDER BY PROCESS_ORDER, NODE_PATH;


-- ------------------------------------------------------------
-- 01B. Duplicate active NODE_PATH check
-- Expected: zero rows
-- ------------------------------------------------------------
SELECT
    NODE_PATH,
    COUNT(*) AS ROW_COUNT
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(OSCAL_MODEL_KEY) = 'SSP'
  AND COALESCE(IS_ACTIVE, TRUE) = TRUE
GROUP BY NODE_PATH
HAVING COUNT(*) > 1
ORDER BY NODE_PATH;


-- ------------------------------------------------------------
-- 01C. Duplicate active PROCESS_ORDER check
-- Review only: process-order duplicates may be intentional only if the
-- implementation explicitly supports them. Return them for evidence.
-- ------------------------------------------------------------
SELECT
    PROCESS_ORDER,
    COUNT(*) AS ROW_COUNT,
    LISTAGG(NODE_PATH, ' | ') WITHIN GROUP (ORDER BY NODE_PATH) AS NODE_PATHS
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(OSCAL_MODEL_KEY) = 'SSP'
  AND COALESCE(IS_ACTIVE, TRUE) = TRUE
GROUP BY PROCESS_ORDER
HAVING COUNT(*) > 1
ORDER BY PROCESS_ORDER;


-- ------------------------------------------------------------
-- 01D. Orphan parent check
-- Expected: zero rows.
-- Root node is allowed to have PARENT_NODE_PATH = NULL.
-- ------------------------------------------------------------
WITH active_ssp AS (
    SELECT *
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE UPPER(OSCAL_MODEL_KEY) = 'SSP'
      AND COALESCE(IS_ACTIVE, TRUE) = TRUE
)
SELECT
    c.NODE_PATH AS CHILD_NODE_PATH,
    c.PARENT_NODE_PATH
FROM active_ssp c
LEFT JOIN active_ssp p
    ON p.NODE_PATH = c.PARENT_NODE_PATH
WHERE c.PARENT_NODE_PATH IS NOT NULL
  AND p.NODE_PATH IS NULL
ORDER BY c.NODE_PATH;


-- ------------------------------------------------------------
-- 01E. Collection identity completeness check
-- Expected: zero rows for executable collection nodes.
-- A collection needs an instance identity rule; ITEM_PATH may be required
-- depending on the collection/operator, so return it for review as evidence.
-- ------------------------------------------------------------
SELECT
    NODE_PATH,
    ELEMENT_TYPE,
    INSTANCE_KEY_RULE,
    ITEM_PATH,
    OPERATOR
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(OSCAL_MODEL_KEY) = 'SSP'
  AND COALESCE(IS_ACTIVE, TRUE) = TRUE
  AND COALESCE(IS_COLLECTION, FALSE) = TRUE
  AND NULLIF(TRIM(INSTANCE_KEY_RULE), '') IS NULL
ORDER BY NODE_PATH;


-- ------------------------------------------------------------
-- 01F. Root check
-- Expected: exactly one active SSP root row.
-- ------------------------------------------------------------
SELECT
    COUNT(*) AS SSP_ROOT_COUNT,
    MIN(NODE_PATH) AS ROOT_NODE_PATH
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(OSCAL_MODEL_KEY) = 'SSP'
  AND COALESCE(IS_ACTIVE, TRUE) = TRUE
  AND PARENT_NODE_PATH IS NULL;


-- ------------------------------------------------------------
-- 01G. Branch inventory summary
-- This is evidence, not a conformance claim.
-- ------------------------------------------------------------
SELECT
    CASE
        WHEN NODE_PATH = 'system-security-plan' THEN 'ROOT'
        WHEN NODE_PATH LIKE 'system-security-plan.metadata%' THEN 'METADATA'
        WHEN NODE_PATH LIKE 'system-security-plan.system-characteristics%' THEN 'SYSTEM_CHARACTERISTICS'
        WHEN NODE_PATH LIKE 'system-security-plan.system-implementation%' THEN 'SYSTEM_IMPLEMENTATION'
        WHEN NODE_PATH LIKE 'system-security-plan.control-implementation%' THEN 'CONTROL_IMPLEMENTATION'
        WHEN NODE_PATH LIKE 'system-security-plan.import-profile%' THEN 'IMPORT_PROFILE'
        WHEN NODE_PATH LIKE 'system-security-plan.back-matter%' THEN 'BACK_MATTER'
        ELSE 'OTHER'
    END AS SSP_BRANCH,
    COUNT(*) AS ACTIVE_REGISTRY_ROWS
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(OSCAL_MODEL_KEY) = 'SSP'
  AND COALESCE(IS_ACTIVE, TRUE) = TRUE
GROUP BY SSP_BRANCH
ORDER BY SSP_BRANCH;


-- ------------------------------------------------------------
-- 01H. Compact PASS/FAIL mechanical summary
-- Note: PROCESS_ORDER duplicates are reported separately and intentionally
-- excluded from automatic FAIL until their semantics are reviewed.
-- ------------------------------------------------------------
WITH active_ssp AS (
    SELECT *
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE UPPER(OSCAL_MODEL_KEY) = 'SSP'
      AND COALESCE(IS_ACTIVE, TRUE) = TRUE
),
duplicate_paths AS (
    SELECT NODE_PATH
    FROM active_ssp
    GROUP BY NODE_PATH
    HAVING COUNT(*) > 1
),
orphans AS (
    SELECT c.NODE_PATH
    FROM active_ssp c
    LEFT JOIN active_ssp p
      ON p.NODE_PATH = c.PARENT_NODE_PATH
    WHERE c.PARENT_NODE_PATH IS NOT NULL
      AND p.NODE_PATH IS NULL
),
bad_collections AS (
    SELECT NODE_PATH
    FROM active_ssp
    WHERE COALESCE(IS_COLLECTION, FALSE) = TRUE
      AND NULLIF(TRIM(INSTANCE_KEY_RULE), '') IS NULL
),
root_count AS (
    SELECT COUNT(*) AS CNT
    FROM active_ssp
    WHERE PARENT_NODE_PATH IS NULL
)
SELECT
    (SELECT COUNT(*) FROM active_ssp) AS ACTIVE_SSP_REGISTRY_ROWS,
    (SELECT COUNT(*) FROM duplicate_paths) AS DUPLICATE_NODE_PATHS,
    (SELECT COUNT(*) FROM orphans) AS ORPHAN_PARENT_PATHS,
    (SELECT COUNT(*) FROM bad_collections) AS COLLECTIONS_WITHOUT_KEY_RULE,
    (SELECT CNT FROM root_count) AS ROOT_COUNT,
    CASE
        WHEN (SELECT COUNT(*) FROM duplicate_paths) = 0
         AND (SELECT COUNT(*) FROM orphans) = 0
         AND (SELECT COUNT(*) FROM bad_collections) = 0
         AND (SELECT CNT FROM root_count) = 1
        THEN 'PASS'
        ELSE 'FAIL'
    END AS SSP_REGISTRY_MECHANICAL_STATUS;
