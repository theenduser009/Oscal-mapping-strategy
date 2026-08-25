Yes — this is the important result. We have **45 Assessment Results mappings**, but one path is visibly ambiguous/truncated:

```text
assessment-results.results[].findings[]        1
assessment-results.results[].observations[]   19
assessment-results.results[].observations[] or ...   18
assessment-results.results[].props[]           7
```

So **do not add anything to the registry yet**. We first need the exact text of that third path. It may contain an alternate mapping such as `observations[] or risks[]`, and we cannot let the engine interpret that as a real OSCAL path.

### Next step only

Run this read-only cell:

```python
# ============================================================
# Assessment Results — Exact Paths
# READ ONLY
# ============================================================

rows = (
    assessment_results_paths
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_MODEL",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE"
    )
    .sort(
        "OSCAL_ELEMENT_PATH",
        "SOURCE_FIELD_NAME"
    )
    .collect()
)

print("=== ASSESSMENT RESULTS EXACT MAPPINGS ===")

for r in rows:
    print(
        "\nSOURCE_FIELD_NAME :", r["SOURCE_FIELD_NAME"],
        "\nOSCAL_MODEL       :", r["OSCAL_MODEL"],
        "\nOSCAL_ELEMENT_PATH:", repr(r["OSCAL_ELEMENT_PATH"]),
        "\nMAPPING_TYPE      :", r["MAPPING_TYPE"]
    )
```

`repr()` is intentional — it will show the **complete path exactly as stored in the CSV**, without Snowpark `.show()` truncating it.

The bigger issue we're investigating is:

```text
assessment-results
    ↓
results[]                 ← we still need to determine its instance identity
       ↓
       findings[]
       observations[]
       props[]
```

That is our first **collection-under-collection** case, so we will establish the actual hierarchy from the data before touching the generic mapper.

Run this and show me the exact paths, especially those 18 ambiguous rows.
