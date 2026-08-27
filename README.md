Yes. That's the best way to do it. One branch, all the way to the end, validate it, then repeat the pattern.

Let's take this branch because we already know where your current graph stops:

system-security-plan
    ↓
system-implementation
    ↓
components
    ↓
???

We will finish only this branch first.

Step 1 — find what data actually exists under components

Before changing the registry, CSV, or notebook, let's inspect the SSP DIM rows that were created for components.

Run:

SELECT
    ELEMENT_TYPE,
    SOURCE_RECORD_ID,
    OSCAL_UUID,
    METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE ELEMENT_TYPE = 'components'
LIMIT 20;

I specifically want to see what METADATA_JSON contains for those components nodes.

Then we'll determine whether the next node should be:

components
   ↓
component

and what is actually inside each component — title, description, purpose, props, links, etc.

Don't change anything yet. Run only this query and show me the result. Then we'll take this single branch to its true endpoint.