Yes — exactly. Before choosing status or anything else, let’s first see which current SSP children themselves have children.

Run this read-only SQL:

SELECT DISTINCT
    p.ELEMENT_TYPE AS PARENT,
    c.ELEMENT_TYPE AS CHILD
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT p
    ON f.FK_SOURCE_ELEMENT_HASH = p.PK_OSCAL_SSP_ELEMENT_HASH

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT c
    ON f.FK_TARGET_ELEMENT_HASH = c.PK_OSCAL_SSP_ELEMENT_HASH

WHERE p.ELEMENT_TYPE IN (
    'authorization-boundary',
    'props',
    'security-impact-level',
    'status',
    'system-ids'
)

ORDER BY
    PARENT,
    CHILD;

If this returns rows, those are the branches that continue deeper.

If it returns nothing for one of those element types, that element is currently a leaf in your loaded SSP graph.

Run this first and send me the result. Then we’ll pick only a branch that actually goes deeper.