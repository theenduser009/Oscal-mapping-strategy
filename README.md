Good — Cell 4 is updated successfully. ✅

Now add **only the two Assessment Results registry rows**. Run this SQL:

```sql
INSERT INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
(
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
VALUES
(
    'ASSESSMENT_RESULTS',
    'assessment-results',
    'assessment-results',
    NULL,
    FALSE,
    'SINGLETON',
    1,
    TRUE,
    NULL
),
(
    'ASSESSMENT_RESULTS',
    'assessment-results.results[]',
    'results',
    'assessment-results',
    TRUE,
    'SOURCE_RECORD_ID',
    2,
    TRUE,
    NULL
);
```

Then verify only:

```sql
SELECT *
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'ASSESSMENT_RESULTS'
ORDER BY PROCESS_ORDER;
```

You should see exactly **2 rows**:

```text
assessment-results
    ↓
assessment-results.results[]
```

Send me that result. **Do not run the graph builder yet.**
