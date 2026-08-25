Yes — next we add the **clean `observations[]` branch only**. Your 19 exact mappings are confirmed, and the ambiguous `observations[] or props[]` rows will remain untouched.

Run this registry insert:

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
    'assessment-results.results[].observations[]',
    'observations',
    'assessment-results.results[]',
    TRUE,
    'SOURCE_FIELD_NAME',
    3,
    TRUE,
    NULL
);
```

Then verify:

```sql
SELECT *
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'ASSESSMENT_RESULTS'
ORDER BY PROCESS_ORDER, NODE_PATH;
```

You should now have:

```text
1  assessment-results
2  assessment-results.results[]
3  assessment-results.results[].observations[]
3  assessment-results.results[].props[]
```

Once that is correct, **rerun the existing Assessment Results Graph Test exactly as-is**. Don’t change the graph code and don’t write to DIM/FACT yet.

Send me the new **Nodes / Edges / element counts**.
