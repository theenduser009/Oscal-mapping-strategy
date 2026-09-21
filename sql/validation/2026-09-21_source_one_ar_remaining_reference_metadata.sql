-- Source One Assessment Results — Archer metadata discovery for remaining reference fields
-- Date: 2026-09-21
-- READ ONLY. No DIM/FACT/registry/mapping DML.
--
-- Context from live shape checks:
-- * RISK_ACCEPTANCE_RBDS = one populated Archer cross-reference object {ContentId, LevelId}
-- * RISK_ASSESSMENT_REPORT = 316 populated numeric arrays, 742 total members, all 742 numeric tokens unique
-- * WORKFLOW_JOB_STATUS = 615 Archer select objects {OtherText, ValuesListIds}, cardinality one
--
-- Purpose:
-- Inspect Archer field metadata before the final bulk mapping correction.
-- In particular, determine whether RISK_ASSESSMENT_REPORT is declared as a
-- cross-reference/reference field versus a value-list/select field.
--
-- Result set 1: show the available metadata columns so we do not guess field-type column names.
SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME IN ('ARCHER_META_FIELD', 'ARCHER_META_VALUE')
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- Result set 2: exact Archer metadata rows for the three fields.
-- Metadata only; this does not print source payload values or referenced IDs.
SELECT *
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(TRIM(SQL_FIELD_NAME)) IN (
    'RISK_ACCEPTANCE_RBDS',
    'RISK_ASSESSMENT_REPORT',
    'WORKFLOW_JOB_STATUS'
)
ORDER BY LEVEL_ID, FIELD_ID, SQL_FIELD_NAME;

-- Result set 3: confirm metadata-row uniqueness by field name.
SELECT
    UPPER(TRIM(SQL_FIELD_NAME)) AS SQL_FIELD_NAME,
    COUNT(*) AS META_FIELD_ROWS,
    COUNT(DISTINCT LEVEL_ID) AS DISTINCT_LEVEL_IDS,
    COUNT(DISTINCT FIELD_ID) AS DISTINCT_FIELD_IDS
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(TRIM(SQL_FIELD_NAME)) IN (
    'RISK_ACCEPTANCE_RBDS',
    'RISK_ASSESSMENT_REPORT',
    'WORKFLOW_JOB_STATUS'
)
GROUP BY 1
ORDER BY 1;
