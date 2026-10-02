-- SSP System Characteristics — one field at a time
-- Date: 2026-10-02
-- READ ONLY. No DML / DDL / MERGE / INSERT / UPDATE / DELETE.
--
-- Purpose:
--   1) FIPS/CIA: Archer field -> Archer metadata -> ValuesListIds/ResolvedValues
--      -> exact OSCAL security-impact-level member.
--   2) Generic prop: Archer field -> exact named system-characteristics prop.
--
-- Current SSP PREVIEW is unchanged vs target (0 DIM/FACT inserts/updates), so the
-- persisted SSP DIM/FACT can be used for these spot checks.
--
-- Change ONLY the SET values in the section you want to inspect.


-- ============================================================================
-- SECTION 1 — FIPS / CIA ONE FIELD
-- Example proven in current data:
--   CONTENT_ID 866211
--   AVAILABILITY_CONTROL_CATEGORY_OVERRIDE
--   ValueId 80654 -> Low -> security-objective-availability = low
-- ============================================================================

SET TEST_CONTENT_ID = '866211';
SET TEST_FIPS_SOURCE_FIELD = 'AVAILABILITY_CONTROL_CATEGORY_OVERRIDE';
SET TEST_FIPS_TARGET_MEMBER = 'security-objective-availability';

WITH raw_row AS (
    SELECT
        CONTENT_ID::VARCHAR AS CONTENT_ID,
        IFF(TYPEOF(RAW_DATA) = 'ARRAY', RAW_DATA[0], RAW_DATA)
            :"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID,
        CURATED_JSON
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    WHERE TRIM(CONTENT_ID::VARCHAR) = $TEST_CONTENT_ID
),
source_value AS (
    SELECT
        CONTENT_ID,
        LEVEL_ID,
        GET(CURATED_JSON, $TEST_FIPS_SOURCE_FIELD) AS SOURCE_RAW,
        GET(GET(CURATED_JSON, $TEST_FIPS_SOURCE_FIELD), 'ValuesListIds')
            AS VALUES_LIST_IDS,
        GET(GET(CURATED_JSON, $TEST_FIPS_SOURCE_FIELD), 'ResolvedValues')
            AS RESOLVED_VALUES
    FROM raw_row
),
meta AS (
    SELECT
        UPPER(SQL_FIELD_NAME) AS SQL_FIELD_NAME,
        LEVEL_ID,
        ARRAY_AGG(DISTINCT FIELD_ID) AS FIELD_IDS,
        ARRAY_AGG(DISTINCT FIELD_TYPE_ID) AS FIELD_TYPE_IDS,
        ARRAY_AGG(DISTINCT FIELD_NAME) AS ARCHER_FIELD_NAMES,
        COUNT(DISTINCT FIELD_ID) AS FIELD_ID_CANDIDATES
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
    WHERE UPPER(SQL_FIELD_NAME) = UPPER($TEST_FIPS_SOURCE_FIELD)
    GROUP BY UPPER(SQL_FIELD_NAME), LEVEL_ID
),
impact AS (
    SELECT
        SOURCE_RECORD_ID::VARCHAR AS CONTENT_ID,
        METADATA_JSON AS SECURITY_IMPACT_PAYLOAD,
        GET(METADATA_JSON, $TEST_FIPS_TARGET_MEMBER)::VARCHAR
            AS OSCAL_VALUE
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE TRIM(SOURCE_RECORD_ID::VARCHAR) = $TEST_CONTENT_ID
      AND ELEMENT_TYPE = 'security-impact-level'
)
SELECT
    s.CONTENT_ID,
    $TEST_FIPS_SOURCE_FIELD AS SQL_FIELD_NAME,
    m.ARCHER_FIELD_NAMES,
    m.FIELD_IDS AS ARCHER_FIELD_IDS,
    m.FIELD_TYPE_IDS AS ARCHER_FIELD_TYPE_IDS,
    s.LEVEL_ID AS ARCHER_LEVEL_ID,
    m.FIELD_ID_CANDIDATES AS META_FIELD_ID_CANDIDATES,
    s.SOURCE_RAW,
    s.VALUES_LIST_IDS,
    s.RESOLVED_VALUES,
    'system-security-plan.system-characteristics.security-impact-level'
        AS OSCAL_ELEMENT_PATH,
    $TEST_FIPS_TARGET_MEMBER AS OSCAL_MEMBER,
    i.OSCAL_VALUE,
    i.SECURITY_IMPACT_PAYLOAD
FROM source_value s
LEFT JOIN meta m
    ON m.SQL_FIELD_NAME = UPPER($TEST_FIPS_SOURCE_FIELD)
   AND m.LEVEL_ID = s.LEVEL_ID
LEFT JOIN impact i
    ON i.CONTENT_ID = s.CONTENT_ID;


-- ============================================================================
-- SECTION 2 — GENERIC SYSTEM-CHARACTERISTICS PROP, ONE FIELD
-- Example:
--   ALLOCATED_CONTROLS -> prop name allocated-controls
--
-- Change these three SET values only.
-- ============================================================================

SET TEST_PROP_CONTENT_ID = '866499';
SET TEST_PROP_SOURCE_FIELD = 'ALLOCATED_CONTROLS';
SET TEST_PROP_NAME = 'allocated-controls';

WITH RECURSIVE
raw_row AS (
    SELECT
        CONTENT_ID::VARCHAR AS CONTENT_ID,
        IFF(TYPEOF(RAW_DATA) = 'ARRAY', RAW_DATA[0], RAW_DATA)
            :"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID,
        GET(CURATED_JSON, $TEST_PROP_SOURCE_FIELD) AS SOURCE_RAW,
        GET(GET(CURATED_JSON, $TEST_PROP_SOURCE_FIELD), 'ResolvedValues')
            AS RESOLVED_VALUES
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    WHERE TRIM(CONTENT_ID::VARCHAR) = $TEST_PROP_CONTENT_ID
),
meta AS (
    SELECT
        UPPER(SQL_FIELD_NAME) AS SQL_FIELD_NAME,
        LEVEL_ID,
        ARRAY_AGG(DISTINCT FIELD_ID) AS FIELD_IDS,
        ARRAY_AGG(DISTINCT FIELD_TYPE_ID) AS FIELD_TYPE_IDS,
        ARRAY_AGG(DISTINCT FIELD_NAME) AS ARCHER_FIELD_NAMES,
        COUNT(DISTINCT FIELD_ID) AS FIELD_ID_CANDIDATES
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
    WHERE UPPER(SQL_FIELD_NAME) = UPPER($TEST_PROP_SOURCE_FIELD)
    GROUP BY UPPER(SQL_FIELD_NAME), LEVEL_ID
),
nodes AS (
    SELECT
        PK_OSCAL_SSP_ELEMENT_HASH AS NODE_KEY,
        SOURCE_RECORD_ID::VARCHAR AS SOURCE_RECORD_ID,
        ELEMENT_TYPE,
        OSCAL_UUID,
        METADATA_JSON
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE TRIM(SOURCE_RECORD_ID::VARCHAR) = $TEST_PROP_CONTENT_ID
),
edges AS (
    SELECT
        FK_SOURCE_ELEMENT_HASH AS PARENT_NODE_KEY,
        FK_TARGET_ELEMENT_HASH AS CHILD_NODE_KEY,
        DEPENDENCY_TYPE
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY
),
graph (
    SOURCE_RECORD_ID,
    NODE_KEY,
    ELEMENT_TYPE,
    OSCAL_UUID,
    OSCAL_PATH,
    METADATA_JSON,
    DEPTH
) AS (
    SELECT
        n.SOURCE_RECORD_ID,
        n.NODE_KEY,
        n.ELEMENT_TYPE,
        n.OSCAL_UUID,
        CAST(n.ELEMENT_TYPE AS VARCHAR(2000)) AS OSCAL_PATH,
        n.METADATA_JSON,
        0 AS DEPTH
    FROM nodes n
    WHERE n.ELEMENT_TYPE = 'system-security-plan'

    UNION ALL

    SELECT
        child.SOURCE_RECORD_ID,
        child.NODE_KEY,
        child.ELEMENT_TYPE,
        child.OSCAL_UUID,
        CAST(parent.OSCAL_PATH || '.' || child.ELEMENT_TYPE AS VARCHAR(2000)),
        child.METADATA_JSON,
        parent.DEPTH + 1
    FROM graph parent
    JOIN edges e
      ON e.PARENT_NODE_KEY = parent.NODE_KEY
    JOIN nodes child
      ON child.NODE_KEY = e.CHILD_NODE_KEY
    WHERE parent.DEPTH < 30
),
target_prop AS (
    SELECT
        SOURCE_RECORD_ID AS CONTENT_ID,
        OSCAL_PATH,
        METADATA_JSON:"name"::VARCHAR AS PROP_NAME,
        METADATA_JSON:"value" AS PROP_VALUE,
        METADATA_JSON AS PROP_PAYLOAD
    FROM graph
    WHERE OSCAL_PATH = 'system-security-plan.system-characteristics.props'
      AND METADATA_JSON:"name"::VARCHAR = $TEST_PROP_NAME
)
SELECT
    r.CONTENT_ID,
    $TEST_PROP_SOURCE_FIELD AS SQL_FIELD_NAME,
    m.ARCHER_FIELD_NAMES,
    m.FIELD_IDS AS ARCHER_FIELD_IDS,
    m.FIELD_TYPE_IDS AS ARCHER_FIELD_TYPE_IDS,
    r.LEVEL_ID AS ARCHER_LEVEL_ID,
    m.FIELD_ID_CANDIDATES AS META_FIELD_ID_CANDIDATES,
    r.SOURCE_RAW,
    r.RESOLVED_VALUES,
    'system-security-plan.system-characteristics.props[]' AS OSCAL_ELEMENT_PATH,
    $TEST_PROP_NAME AS EXPECTED_PROP_NAME,
    p.PROP_NAME AS ACTUAL_PROP_NAME,
    p.PROP_VALUE AS ACTUAL_PROP_VALUE,
    p.PROP_PAYLOAD
FROM raw_row r
LEFT JOIN meta m
    ON m.SQL_FIELD_NAME = UPPER($TEST_PROP_SOURCE_FIELD)
   AND m.LEVEL_ID = r.LEVEL_ID
LEFT JOIN target_prop p
    ON p.CONTENT_ID = r.CONTENT_ID;


-- ============================================================================
-- SECTION 3 — SHOW ALL SYSTEM-CHARACTERISTICS PROPS FOR ONE CONTENT_ID
-- Useful when you simply want to inspect every property currently written.
-- ============================================================================

SET TEST_ALL_PROPS_CONTENT_ID = '866499';

WITH RECURSIVE
nodes AS (
    SELECT
        PK_OSCAL_SSP_ELEMENT_HASH AS NODE_KEY,
        SOURCE_RECORD_ID::VARCHAR AS SOURCE_RECORD_ID,
        ELEMENT_TYPE,
        OSCAL_UUID,
        METADATA_JSON
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE TRIM(SOURCE_RECORD_ID::VARCHAR) = $TEST_ALL_PROPS_CONTENT_ID
),
edges AS (
    SELECT
        FK_SOURCE_ELEMENT_HASH AS PARENT_NODE_KEY,
        FK_TARGET_ELEMENT_HASH AS CHILD_NODE_KEY
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY
),
graph (
    SOURCE_RECORD_ID,
    NODE_KEY,
    ELEMENT_TYPE,
    OSCAL_UUID,
    OSCAL_PATH,
    METADATA_JSON,
    DEPTH
) AS (
    SELECT
        n.SOURCE_RECORD_ID,
        n.NODE_KEY,
        n.ELEMENT_TYPE,
        n.OSCAL_UUID,
        CAST(n.ELEMENT_TYPE AS VARCHAR(2000)),
        n.METADATA_JSON,
        0
    FROM nodes n
    WHERE n.ELEMENT_TYPE = 'system-security-plan'

    UNION ALL

    SELECT
        child.SOURCE_RECORD_ID,
        child.NODE_KEY,
        child.ELEMENT_TYPE,
        child.OSCAL_UUID,
        CAST(parent.OSCAL_PATH || '.' || child.ELEMENT_TYPE AS VARCHAR(2000)),
        child.METADATA_JSON,
        parent.DEPTH + 1
    FROM graph parent
    JOIN edges e
      ON e.PARENT_NODE_KEY = parent.NODE_KEY
    JOIN nodes child
      ON child.NODE_KEY = e.CHILD_NODE_KEY
    WHERE parent.DEPTH < 30
)
SELECT
    SOURCE_RECORD_ID AS CONTENT_ID,
    METADATA_JSON:"name"::VARCHAR AS PROP_NAME,
    METADATA_JSON:"value" AS PROP_VALUE,
    METADATA_JSON AS PROP_PAYLOAD
FROM graph
WHERE OSCAL_PATH = 'system-security-plan.system-characteristics.props'
ORDER BY PROP_NAME, PROP_VALUE;
