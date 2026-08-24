Yes — **Cell 9 now.** We’ll register only the two collections we have actually confirmed from the mapping and raw values.

Use a **SQL cell**:

```sql
-- ============================================================
-- Cell 9 — Register Confirmed SSP Child Collections
-- ============================================================

MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
USING (

    SELECT
        'SSP' AS OSCAL_MODEL_KEY,
        'system-security-plan.metadata.document-ids[]' AS NODE_PATH,
        'document-ids' AS ELEMENT_TYPE,
        'system-security-plan.metadata' AS PARENT_NODE_PATH,
        TRUE AS IS_COLLECTION,
        'VALUE' AS INSTANCE_KEY_RULE,
        3 AS PROCESS_ORDER,
        TRUE AS IS_ACTIVE

    UNION ALL

    SELECT
        'SSP',
        'system-security-plan.system-characteristics.system-ids[]',
        'system-ids',
        'system-security-plan.system-characteristics',
        TRUE,
        'VALUE',
        3,
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

Why `VALUE`? Because these two source values are scalars:

```text
TRACKING_ID → 565187
SAP_ID      → "565187-Information System"
```

Our existing collection helper already uses the scalar itself as the instance identity. We're **not changing Cell 5**.

After this, SSP registry becomes:

```text
system-security-plan
├── metadata
│   └── document-ids[]          ← NEW
├── system-characteristics
│   └── system-ids[]            ← NEW
└── system-implementation
    └── components[]
```

Run **only Cell 9** and send me the inserted/updated result. Then we'll run the existing engine and see whether these two deeper levels materialize correctly.
