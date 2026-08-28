Yes — let’s pick a branch that can be completed entirely from the Authorization Package row, so we can validate the mapper without cross-table references.

I’d start with system-characteristics because we already know that branch is populated and has several children in the loaded graph.

Run this read-only SQL first to see its distinct child relationships:

SELECT DISTINCT
    p.ELEMENT_TYPE AS PARENT,
    c.ELEMENT_TYPE AS CHILD,
    f.DEPENDENCY_TYPE
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT p
  ON f.FK_SOURCE_ELEMENT_HASH = p.PK_OSCAL_SSP_ELEMENT_HASH

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT c
  ON f.FK_TARGET_ELEMENT_HASH = c.PK_OSCAL_SSP_ELEMENT_HASH

WHERE p.ELEMENT_TYPE = 'system-characteristics'

ORDER BY CHILD;

We already expect children like:

authorization-boundary
props
security-impact-level
status
system-ids

From those, I recommend we take status first because it should be a simple same-record branch with scalar payload like state / remarks, not a cross-table reference.

Run that query and send me the child list. Then we’ll pick one child and take it all the way to the end.