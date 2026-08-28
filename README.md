Excellent. ✅ system-characteristics is structurally validated.

We now have:

system-security-plan
└── system-characteristics          2,813 ✅
    ├── authorization-boundary          ✅ payload
    ├── security-impact-level           ✅ payload
    ├── status                       2,813 ✅
    ├── system-ids[]                 2,813 ✅
    └── props[]                     15,120 ✅

And the parent itself is clean: 2,813 nodes = 2,813 distinct keys = 0 null keys = 2,813 incoming edges.

So I would stop testing this branch now rather than over-validating it.

Next

Let's identify the next active direct child of system-security-plan from your registry instead of guessing from OSCAL.

Run:

SELECT
    NODE_PATH,
    ELEMENT_TYPE,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND PARENT_NODE_PATH = 'system-security-plan'
  AND IS_ACTIVE = TRUE
ORDER BY PROCESS_ORDER, NODE_PATH;

Send me that result. Then we'll pick the next SSP branch from what your mapper is actually configured to process.