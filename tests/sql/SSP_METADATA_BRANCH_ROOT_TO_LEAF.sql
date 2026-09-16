-- SSP Metadata branch drill-down for one SOURCE_RECORD_ID.
-- Replace 565279 with the source/content ID you want to inspect.
-- Walks the persisted SSP graph from the system-security-plan root through the
-- Metadata branch and returns each node's payload and parent relationship.

WITH RECURSIVE METADATA_TREE
(
    LEVEL_NO,
    NODE_PK,
    PARENT_PK,
    ELEMENT_TYPE,
    SOURCE_RECORD_ID,
    OSCAL_UUID,
    METADATA_JSON
) AS
(
    /* Level 1: SSP root */
    SELECT
        1,
        R.PK_OSCAL_SSP_ELEMENT_HASH,
        NULL,
        R.ELEMENT_TYPE,
        R.SOURCE_RECORD_ID,
        R.OSCAL_UUID,
        R.METADATA_JSON
    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT R
    WHERE R.SOURCE_RECORD_ID = '565279'
      AND R.ELEMENT_TYPE = 'system-security-plan'

    UNION ALL

    /* Walk parent -> child through FACT */
    SELECT
        T.LEVEL_NO + 1,
        C.PK_OSCAL_SSP_ELEMENT_HASH,
        T.NODE_PK,
        C.ELEMENT_TYPE,
        C.SOURCE_RECORD_ID,
        C.OSCAL_UUID,
        C.METADATA_JSON
    FROM METADATA_TREE T
    JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY F
      ON F.FK_SOURCE_ELEMENT_HASH = T.NODE_PK
    JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT C
      ON C.PK_OSCAL_SSP_ELEMENT_HASH = F.FK_TARGET_ELEMENT_HASH
    WHERE C.SOURCE_RECORD_ID = '565279'
)

SELECT
    LEVEL_NO,
    ELEMENT_TYPE,
    NODE_PK,
    PARENT_PK,
    OSCAL_UUID,
    METADATA_JSON
FROM METADATA_TREE
WHERE ELEMENT_TYPE IN (
    'system-security-plan',
    'metadata',
    'document-ids',
    'roles',
    'parties',
    'responsible-parties'
)
ORDER BY
    LEVEL_NO,
    ELEMENT_TYPE,
    NODE_PK;
