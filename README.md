Perfect. ✅ The compatibility check passed again:

```text
Nodes: 76,083
Edges: 73,918
```

So the new `SOURCE_FIELD_NAME+VALUE` logic did **not** affect anything already working.

### Next step: register `props[]`

Use this SQL cell:

```sql
MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
USING (
    SELECT
        'SSP' AS OSCAL_MODEL_KEY,
        'system-security-plan.system-characteristics.props[]' AS NODE_PATH,
        'props' AS ELEMENT_TYPE,
        'system-security-plan.system-characteristics' AS PARENT_NODE_PATH,
        TRUE AS IS_COLLECTION,
        'SOURCE_FIELD_NAME+VALUE' AS INSTANCE_KEY_RULE,
        3 AS PROCESS_ORDER,
        TRUE AS IS_ACTIVE,
        '$' AS ITEM_PATH
) s

ON  t.OSCAL_MODEL_KEY = s.OSCAL_MODEL_KEY
AND t.NODE_PATH = s.NODE_PATH

WHEN MATCHED THEN UPDATE SET
    t.ELEMENT_TYPE      = s.ELEMENT_TYPE,
    t.PARENT_NODE_PATH  = s.PARENT_NODE_PATH,
    t.IS_COLLECTION     = s.IS_COLLECTION,
    t.INSTANCE_KEY_RULE = s.INSTANCE_KEY_RULE,
    t.PROCESS_ORDER     = s.PROCESS_ORDER,
    t.IS_ACTIVE         = s.IS_ACTIVE,
    t.ITEM_PATH         = s.ITEM_PATH

WHEN NOT MATCHED THEN INSERT (
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
VALUES (
    s.OSCAL_MODEL_KEY,
    s.NODE_PATH,
    s.ELEMENT_TYPE,
    s.PARENT_NODE_PATH,
    s.IS_COLLECTION,
    s.INSTANCE_KEY_RULE,
    s.PROCESS_ORDER,
    s.IS_ACTIVE,
    s.ITEM_PATH
);
```

This means:

```text
FINANCIAL_SYSTEM | 80647
MISSION_CRITICAL | 80651
INFORMATION_CLASSIFICATION | 162484
INFORMATION_CLASSIFICATION | 162486
...
```

Each becomes a distinct `props[]` instance.

And importantly, we're **following the mapping exactly as provided**. We are not inventing OSCAL `name`, `value`, or transformation semantics.

Run only this registry MERGE. Then refresh **Cell 3** and run **Cell 5 unchanged**. The prop scan found 12,028 source occurrences; Cell 5 will tell us the authoritative node count after its deterministic de-duplication.
