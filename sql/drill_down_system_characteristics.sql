-- Standalone, read-only drill-down for system-characteristics.
-- This does not depend on RESULT_SCAN or another notebook cell.
-- Change only this test CONTENT_ID.

SET TEST_CONTENT_ID = '565189';

WITH RECURSIVE
nodes AS (
    SELECT
        PK_OSCAL_SSP_ELEMENT_HASH AS NODE_KEY,
        SOURCE_RECORD_ID,
        ELEMENT_TYPE,
        OSCAL_UUID,
        METADATA_JSON
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
    WHERE TRIM(SOURCE_RECORD_ID::STRING) = $TEST_CONTENT_ID
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
    PARENT_OSCAL_UUID,
    DEPENDENCY_TYPE,
    OSCAL_PATH,
    WRITTEN_PAYLOAD,
    DEPTH
) AS (
    SELECT
        n.SOURCE_RECORD_ID,
        n.NODE_KEY,
        n.ELEMENT_TYPE,
        n.OSCAL_UUID,
        CAST(NULL AS VARCHAR) AS PARENT_OSCAL_UUID,
        CAST(NULL AS VARCHAR) AS DEPENDENCY_TYPE,
        CAST(n.ELEMENT_TYPE AS VARCHAR(2000)) AS OSCAL_PATH,
        n.METADATA_JSON AS WRITTEN_PAYLOAD,
        0 AS DEPTH
    FROM nodes n
    WHERE n.ELEMENT_TYPE = 'system-security-plan'

    UNION ALL

    SELECT
        child.SOURCE_RECORD_ID,
        child.NODE_KEY,
        child.ELEMENT_TYPE,
        child.OSCAL_UUID,
        parent.OSCAL_UUID AS PARENT_OSCAL_UUID,
        edge.DEPENDENCY_TYPE,
        CAST(
            parent.OSCAL_PATH || '.' || child.ELEMENT_TYPE
            AS VARCHAR(2000)
        ) AS OSCAL_PATH,
        child.METADATA_JSON AS WRITTEN_PAYLOAD,
        parent.DEPTH + 1 AS DEPTH
    FROM graph parent
    JOIN edges edge
        ON edge.PARENT_NODE_KEY = parent.NODE_KEY
    JOIN nodes child
        ON child.NODE_KEY = edge.CHILD_NODE_KEY
    WHERE parent.DEPTH < 30
)
SELECT
    SOURCE_RECORD_ID,
    OSCAL_PATH,
    ELEMENT_TYPE,
    OSCAL_UUID,
    WRITTEN_PAYLOAD,
    PARENT_OSCAL_UUID,
    DEPENDENCY_TYPE
FROM graph
WHERE
    OSCAL_PATH = 'system-security-plan.system-characteristics'
    OR OSCAL_PATH LIKE 'system-security-plan.system-characteristics.%'
ORDER BY
    DEPTH,
    OSCAL_PATH,
    OSCAL_UUID;

