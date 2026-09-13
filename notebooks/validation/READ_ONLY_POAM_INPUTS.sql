-- POA&M discovery: run all three SELECT statements in a Snowflake SQL worksheet.
-- No notebook variables, DDL, DML or target payload reads.
-- Post the three result grids, including empty grids.
-- Searches cover the configured DEV schemas and objects visible to your role;
-- no result does not establish that a table is absent elsewhere.
-- Reference-shape counts below include all physical source rows, not a load batch.

-- 1. Candidate OSCAL destinations and their columns.
-- This inventory does not itself verify the writer's exact physical contract.
SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME,
       DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE,
       IS_NULLABLE, COLUMN_DEFAULT
FROM RTX_ENTERPRISESERVICES_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC_CURATED'
  AND TABLE_NAME ILIKE '%OSCAL%'
  AND TABLE_NAME ILIKE ANY ('%POAM%', '%POA_M%', '%PLAN%ACTION%', '%MILESTONE%')
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- 2. Existing hierarchy and identity rules, including inactive rows.
SELECT *
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE NODE_PATH LIKE 'plan-of-action-and-milestones%'
   OR UPPER(OSCAL_MODEL_KEY) IN ('POAM', 'POA&M', 'PLAN_OF_ACTION_AND_MILESTONES')
ORDER BY PROCESS_ORDER, NODE_PATH;

-- 3. POAMS container/item shapes only: no source IDs or business values.
-- Empty arrays produce one null outer slot. Null/missing/malformed JSON is
-- visible in JSON_TYPE/POAMS_TYPE and must not be treated as a resolved item.
WITH source_json AS (
    SELECT TRY_PARSE_JSON(TO_VARCHAR(CURATED_JSON)) AS J
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
), reference_shapes AS (
    SELECT COALESCE(TYPEOF(J), 'SQL_NULL_OR_INVALID_JSON') AS JSON_TYPE,
           COALESCE(TYPEOF(J:POAMS), 'MISSING_OR_SQL_NULL') AS POAMS_TYPE,
           J:POAMS AS REFS
    FROM source_json
)
SELECT S.JSON_TYPE, S.POAMS_TYPE,
       COALESCE(TYPEOF(F.VALUE), 'NO_ITEM') AS ITEM_TYPE,
       CASE WHEN TYPEOF(F.VALUE) = 'OBJECT'
            THEN TO_JSON(ARRAY_SORT(OBJECT_KEYS(F.VALUE))) END AS ITEM_KEYS,
       COUNT(*) AS PHYSICAL_REFERENCE_SLOTS
FROM reference_shapes S,
     LATERAL FLATTEN(
         INPUT => CASE WHEN S.POAMS_TYPE = 'ARRAY' THEN S.REFS
                       ELSE ARRAY_CONSTRUCT(S.REFS) END,
         OUTER => TRUE
     ) F
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4;
