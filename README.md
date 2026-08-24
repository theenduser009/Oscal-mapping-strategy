Excellent — **the backward-compatibility test passed exactly.** ✅

```text
Before ITEM_PATH enhancement:
Nodes = 66,118
Edges = 63,953

After ITEM_PATH enhancement:
Nodes = 66,118
Edges = 63,953
```

So we did **not break any existing SSP behavior**. The generic engine now understands the new metadata contract.

### Next step: register `responsible-parties[]`

Use one SQL cell:

```sql
MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
USING (
    SELECT
        'SSP' AS OSCAL_MODEL_KEY,
        'system-security-plan.metadata.responsible-parties[]' AS NODE_PATH,
        'responsible-parties' AS ELEMENT_TYPE,
        'system-security-plan.metadata' AS PARENT_NODE_PATH,
        TRUE AS IS_COLLECTION,
        'SOURCE_FIELD_NAME+ID' AS INSTANCE_KEY_RULE,
        3 AS PROCESS_ORDER,
        TRUE AS IS_ACTIVE,
        'UserList[]' AS ITEM_PATH
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

This tells the engine generically:

```text
Source role field
    ↓
UserList[]
    ↓
each User object becomes an instance
    ↓
identity = SOURCE_FIELD_NAME + User.Id
```

That preserves those **286 cases where the same user serves multiple roles** instead of incorrectly collapsing them.

Run only this SQL next. After it inserts the row, we'll refresh Cell 3 and run Cell 5 unchanged to see the exact number of new responsible-party nodes.
