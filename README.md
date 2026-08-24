Perfect. ✅

Your result proves `CONTENT_ID` is a safe instance key for POA&M:

```text
POA&M references:                 2563
Unique source record + ContentId: 2563
LevelId collisions:                  0
```

So **no Python changes. No Cell 4/5 changes.**

### Next: add POA&M to the registry

Run this SQL:

```sql
MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
USING (
    SELECT
        'POAM' AS OSCAL_MODEL_KEY,
        'plan-of-action-and-milestones' AS NODE_PATH,
        'plan-of-action-and-milestones' AS ELEMENT_TYPE,
        NULL AS PARENT_NODE_PATH,
        FALSE AS IS_COLLECTION,
        'SINGLETON' AS INSTANCE_KEY_RULE,
        1 AS PROCESS_ORDER,
        TRUE AS IS_ACTIVE

    UNION ALL

    SELECT
        'POAM',
        'plan-of-action-and-milestones.poam-items[]',
        'poam-items',
        'plan-of-action-and-milestones',
        TRUE,
        'CONTENT_ID',
        2,
        TRUE
) s
ON  t.OSCAL_MODEL_KEY = s.OSCAL_MODEL_KEY
AND t.NODE_PATH = s.NODE_PATH

WHEN MATCHED THEN UPDATE SET
    t.ELEMENT_TYPE      = s.ELEMENT_TYPE,
    t.PARENT_NODE_PATH  = s.PARENT_NODE_PATH,
    t.IS_COLLECTION     = s.IS_COLLECTION,
    t.INSTANCE_KEY_RULE = s.INSTANCE_KEY_RULE,
    t.PROCESS_ORDER     = s.PROCESS_ORDER,
    t.IS_ACTIVE         = s.IS_ACTIVE

WHEN NOT MATCHED THEN INSERT (
    OSCAL_MODEL_KEY,
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER,
    IS_ACTIVE
)
VALUES (
    s.OSCAL_MODEL_KEY,
    s.NODE_PATH,
    s.ELEMENT_TYPE,
    s.PARENT_NODE_PATH,
    s.IS_COLLECTION,
    s.INSTANCE_KEY_RULE,
    s.PROCESS_ORDER,
    s.IS_ACTIVE
);
```

That gives us:

```text
plan-of-action-and-milestones
        │
        └── poam-items[]  × 2,563 occurrences
```

**Stop after running this.** Next we switch `CONFIG` to POAM and point it at the correct POA&M DIM/FACT tables — without changing the engine.
