Yes — we **are going further down the tree**. What we just validated was only the first safe layer:

```text
assessment-results
        ↓
results[]
```

I stopped there intentionally because `results[]` was our first collection parent. Now we’ve proven something useful: there is exactly **one `results[]` instance per source record**, so we can continue below it without guessing which parent a child belongs to.

The next safest branch is the **unambiguous `props[]` branch**:

```text
assessment-results
   └── results[]
         └── props[]
```

We already have **7 mappings explicitly pointing to `assessment-results.results[].props[]`**. We will **not touch** the 18 rows saying `observations[] or props[]` yet.

### Next step only

Add this third registry row:

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
    'assessment-results.results[].props[]',
    'props',
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
ORDER BY PROCESS_ORDER;
```

You should now have:

```text
1  assessment-results
2  assessment-results.results[]
3  assessment-results.results[].props[]
```

**Do only that now.** Then we rerun the graph read-only and see whether our existing generic mapper handles `results[] → props[]` correctly before changing any Python.
