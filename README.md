Perfect — now we’ve found the next real level. ✅

Your registry shows:

system-security-plan.system-implementation.components[]
    └── component

And component is not a collection (IS_COLLECTION = FALSE). That makes sense: components[] is the collection container, and each individual item beneath it is represented by the singleton component node.

Next step

Now query the children of that component node:

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
      'system-security-plan.system-implementation.components[].component'
  AND IS_ACTIVE = TRUE
ORDER BY PROCESS_ORDER, NODE_PATH;

Based on what we saw earlier, I expect things like:

props[]
links[]
responsible-roles[]
protocols[]

Run just that and show me the result. Then we’ll continue one level deeper without changing the mapper.