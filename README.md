Good — that tells us the currently loaded SSP graph stops at those five nodes.

So right now:

system-characteristics
├── authorization-boundary   ← leaf in current graph
├── props                    ← leaf in current graph
├── security-impact-level    ← leaf in current graph
├── status                   ← leaf in current graph
└── system-ids               ← leaf in current graph

That does not necessarily mean OSCAL ends there. It only means the loaded DIM/FACT graph has no deeper edges from those nodes.

Next, instead of picking blindly, let’s compare these current leaves against the registry. Run:

SELECT
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    IS_ACTIVE
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND (
       NODE_PATH ILIKE '%authorization-boundary%'
    OR NODE_PATH ILIKE '%security-impact-level%'
    OR NODE_PATH ILIKE '%status%'
    OR NODE_PATH ILIKE '%system-ids%'
    OR NODE_PATH ILIKE '%system-characteristics%props%'
  )
ORDER BY PROCESS_ORDER, NODE_PATH;

This tells us which of those are true terminal registry nodes versus nodes that have deeper registered structure we haven’t generated yet.

That’s the clean next step.