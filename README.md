Yes — this confirms it. 👍

The canonical graph currently has only one edge in this branch:

system-implementation
        ↓
     components[]

There is no:

components[] → component
component → props[]
component → links[]
component → responsible-roles[]
component → protocols[]

So now we should stop looking at FACT. The problem is upstream in registry-driven graph construction.

And I noticed something important in your earlier registry screenshot: the component registry row may actually be inactive. If that is true, it explains a lot of what we're seeing.

Next — one read-only check

Run this SQL against the registry:

SELECT
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    ITEM_PATH,
    PROCESS_ORDER,
    IS_ACTIVE
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND NODE_PATH ILIKE '%system-implementation%components%'
ORDER BY PROCESS_ORDER, NODE_PATH;

I want to see all 6 rows with IS_ACTIVE clearly visible.

We are specifically checking whether:

components[]                                      ACTIVE?
components[].component                            ACTIVE?
components[].component.props[]                    ACTIVE?
components[].component.links[]                    ACTIVE?
components[].component.responsible-roles[]        ACTIVE?
components[].component.protocols[]                ACTIVE?

If component = FALSE, do not change Cell 4 or Cell 5 yet. That may be the exact reason the tree is breaking.

Send me that result next. We're finally at the exact break point. 😊