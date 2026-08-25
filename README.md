Yep — next we prove the `findings[]` source before touching the registry.

Add **one new READ ONLY cell** after your reconciliation cell:

```python
# ============================================================
# Assessment Results — Findings Source Check
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

findings_mapping_df = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH")
        == "assessment-results.results[].findings[]"
    )
)

findings_rows = findings_mapping_df.collect()

print("=== ASSESSMENT RESULTS FINDINGS CHECK ===")
print("Mapping rows:", len(findings_rows))

for mapping in findings_rows:

    field = mapping["SOURCE_FIELD_NAME"]

    populated = 0
    types_seen = set()
    max_list_length = 0
    samples = []

    for record in source_df.to_local_iterator():

        source_obj = _parse_source_json(record)

        value = resolve_json_path(
            source_obj,
            field
        )

        if value in (None, "", [], {}):
            continue

        populated += 1
        types_seen.add(type(value).__name__)

        if isinstance(value, list):
            max_list_length = max(
                max_list_length,
                len(value)
            )

        if len(samples) < 5:
            samples.append(value)

    print("\nFIELD       :", field)
    print("POPULATED   :", populated)
    print("TYPES       :", sorted(types_seen))
    print("MAX LIST    :", max_list_length)

    for sample in samples:
        print("SAMPLE      :", sample)
```

I expect it may show:

```text
FIELD     : FINDINGS
POPULATED : 0
```

If that is what we get, **we do not add `findings[]` to the registry yet**. That tells us the Authorization Package raw table cannot currently construct that branch, and then we’ll identify which Archer raw table actually owns the Finding records.
