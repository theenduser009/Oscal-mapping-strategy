Yep — I see the issue. Your query returned 1 row: components[] itself, not children beneath components[].

That happened because the WHERE clause in the screenshot uses an OR, so it includes the node itself.

Run this exact query instead:

SELECT
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    ITEM_PATH,
    PROCESS_ORDER
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND PARENT_NODE_PATH =
      'system-security-plan.system-implementation.components[]'
  AND IS_ACTIVE = TRUE
ORDER BY PROCESS_ORDER, NODE_PATH;

No OR NODE_PATH = ... this time.

If this returns 0 rows, that's meaningful: your registry currently has no registered children below components[], so the mapper cannot traverse any deeper on this branch yet.

Run it and show me the result.