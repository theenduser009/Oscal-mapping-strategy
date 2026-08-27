Yes — let’s move.

Since Cells 1–7 stay frozen, we’ll extend the SSP registry template without breaking the current mapper. Because components[] is a collection and our current engine does not yet hydrate a child element beneath a collection parent, add the component row as inactive structural metadata first.

Run this SQL:

INSERT INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
(
    OSCAL_MODEL_KEY,
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER,
    IS_ACTIVE,
    ITEM_PATH
)
SELECT
    'SSP',
    'system-security-plan.system-implementation.components[].component',
    'component',
    'system-security-plan.system-implementation.components[]',
    FALSE,
    'CONTENT_ID',
    4,
    FALSE,          -- template only for now; do NOT let mapper process it yet
    '$'
WHERE NOT EXISTS (
    SELECT 1
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE OSCAL_MODEL_KEY = 'SSP'
      AND NODE_PATH =
          'system-security-plan.system-implementation.components[].component'
);

Then verify:

SELECT
    OSCAL_MODEL_KEY,
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER,
    IS_ACTIVE,
    ITEM_PATH
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND NODE_PATH ILIKE '%system-implementation%component%'
ORDER BY PROCESS_ORDER, NODE_PATH;

We want to see conceptually:

system-implementation
        ↓
components[]               ACTIVE
        ↓
component                  INACTIVE/template

The FALSE is intentional. Do not turn component active yet, because otherwise our existing mapper can hit the nested-collection relationship problem again.

Once this row is there, we immediately go one level below Component and register its OSCAL structure (props, links, responsible-roles, protocols, etc.). We can build the complete SSP template first and then solve hydration separately.