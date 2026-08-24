Yes. **Next step: update the registry metadata contract only. No Python changes yet.**

Use a new **SQL cell**:

```sql
-- ============================================================
-- Add generic collection extraction metadata
-- ============================================================

ALTER TABLE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
ADD COLUMN IF NOT EXISTS ITEM_PATH VARCHAR;


-- Existing collections whose items come directly
-- from the mapped source value
UPDATE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
SET ITEM_PATH = '$'
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND NODE_PATH IN (
      'system-security-plan.system-implementation.components[]',
      'system-security-plan.metadata.document-ids[]',
      'system-security-plan.system-characteristics.system-ids[]'
  );


-- Verify
SELECT
    OSCAL_MODEL_KEY,
    NODE_PATH,
    IS_COLLECTION,
    ITEM_PATH,
    INSTANCE_KEY_RULE
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'SSP'
ORDER BY PROCESS_ORDER, NODE_PATH;
```

For now we expect:

```text
components[]      ITEM_PATH = $   INSTANCE_KEY_RULE = CONTENT_ID
document-ids[]    ITEM_PATH = $   INSTANCE_KEY_RULE = VALUE
system-ids[]      ITEM_PATH = $   INSTANCE_KEY_RULE = VALUE
```

We are **not registering `responsible-parties[]` yet**.

Later its metadata will look conceptually like:

```text
ITEM_PATH         = UserList[]
INSTANCE_KEY_RULE = SOURCE_FIELD_NAME+ID
```

but first we'll teach the generic engine to understand `ITEM_PATH`.

Run this SQL and show me the result. Then the next change will be **one generic helper enhancement**, not SSP-specific code.
