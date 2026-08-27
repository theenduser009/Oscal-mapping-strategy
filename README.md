Perfect. This confirms the registry is already built for this branch. Don’t insert anything else yet.

I can see these 6 registered nodes:

system-security-plan.system-implementation.components[]
    │
    └── component
          ├── props[]
          ├── links[]
          ├── responsible-roles[]
          └── protocols[]

And importantly, your PARENT_NODE_PATH relationships look correct.

So now we need to answer only one question:

> Did the mapper actually create these six element types in DIM, or is the registry ahead of the loaded graph?



Run this next:

SELECT
    ELEMENT_TYPE,
    COUNT(*) AS ROW_COUNT
FROM RTX_ENTERPRISESERVICES_DEV.ES_ES_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE ELEMENT_TYPE IN (
    'components',
    'component',
    'props',
    'links',
    'responsible-roles',
    'protocols'
)
GROUP BY ELEMENT_TYPE
ORDER BY ELEMENT_TYPE;

How we'll interpret it

If you get:

components          50,000
component           0 / missing
props               0 / missing
links               0 / missing
responsible-roles   0 / missing
protocols           0 / missing

then we've found the exact break: the mapper stops at components[] even though the deeper hierarchy exists in the registry.

If component, props, links, etc. already have rows, then they're being created and we'll inspect the FACT edges instead.

Run only this now and show me the result. Then we'll follow the branch exactly one level at a time.