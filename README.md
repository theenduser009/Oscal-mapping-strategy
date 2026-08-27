You're right. We don't need to debug Cell 17 right now. That isn't answering the question you actually care about.

Your goal is:

For SSP, prove what has already been mapped end-to-end, identify where the graph currently stops, then identify exactly what still needs to be added.

From what we've already established, your loaded SSP graph currently has at least:

system-security-plan → metadata
→ system-characteristics
→ system-implementation

And the OSCAL model tells us system-implementation continues into things such as:

components[] → component
users[] → system-user
inventory-items[] → inventory-item

Then those elements can themselves continue deeper. So we should inspect the DIM + FACT that you already loaded, not the CSV first. That tells us what the mapper actually produced.

Do this first

Run this in Snowflake SQL — not the notebook:

SELECT DISTINCT
       p.ELEMENT_TYPE AS PARENT,
       c.ELEMENT_TYPE AS CHILD,
       f.DEPENDENCY_TYPE
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT p
  ON f.FK_SOURCE_ELEMENT_HASH = p.PK_OSCAL_SSP_ELEMENT_HASH

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT c
  ON f.FK_TARGET_ELEMENT_HASH = c.PK_OSCAL_SSP_ELEMENT_HASH

ORDER BY PARENT, CHILD;

This is our inventory of what is already mapped.

Don't change the notebook, registry, CSV, or mapper yet.

Send me that result (screenshots are fine). Then share the other details you mentioned. I'll compare actual loaded SSP graph vs expected OSCAL SSP tree and we'll make a simple checklist:

Already mapped → Missing → Need CSV mapping → Registry-only structural node → Next action.