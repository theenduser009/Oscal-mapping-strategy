Yep. Next we validate system-implementation, but first only inspect its registry children—no mapper changes yet.

Run this SQL:

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
  AND (
       NODE_PATH = 'system-security-plan.system-implementation'
       OR PARENT_NODE_PATH = 'system-security-plan.system-implementation'
  )
  AND IS_ACTIVE = TRUE
ORDER BY PROCESS_ORDER, NODE_PATH;

This will show us:

system-security-plan
└── system-implementation
    ├── child 1
    ├── child 2
    └── ...

Don't change anything yet. Send me the result/screenshot. Then we'll validate the first child exactly like we did with metadata.