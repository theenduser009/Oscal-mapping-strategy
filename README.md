Excellent — **76,083 DIM and 73,918 FACT is now our new verified SSP baseline.** ✅

We have only one unresolved SSP branch from the current mapping inventory:

```text
system-security-plan.system-characteristics.props[]
```

Before registering it, we need one very specific check: **can one Archer source field produce multiple prop values for the same SSP?**

That determines whether the generic identity can simply be:

```text
SOURCE_FIELD_NAME
```

or must be:

```text
SOURCE_FIELD_NAME + VALUE
```

### Next cell — props identity check only

```python
# ============================================================
# Validate props[] instance identity
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

NODE_PATH = "system-security-plan.system-characteristics.props[]"

prop_fields = [
    r["SOURCE_FIELD_NAME"]
    for r in (
        canonical_mapping_df
        .filter(col("OSCAL_ELEMENT_PATH") == NODE_PATH)
        .select("SOURCE_FIELD_NAME")
        .distinct()
        .collect()
    )
]

total_instances = 0
multi_value_cases = []
max_items = 0

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)
    source_record_id = str(record["SOURCE_RECORD_ID"])

    for source_field in prop_fields:

        value = resolve_json_path(source_obj, source_field)

        if value in (None, "", [], {}):
            continue

        values = value if isinstance(value, list) else [value]

        total_instances += len(values)
        max_items = max(max_items, len(values))

        if len(values) > 1:
            multi_value_cases.append(
                (
                    source_record_id,
                    source_field,
                    values
                )
            )


print("=== props[] Identity Check ===")
print("Mapped prop fields:", len(prop_fields))
print("Total prop instances:", total_instances)
print("Maximum items from one field:", max_items)
print("Multi-value field occurrences:", len(multi_value_cases))

if multi_value_cases:
    print("\n=== Sample Multi-Value Cases ===")

    for record_id, field, values in multi_value_cases[:10]:
        print(
            "SOURCE_RECORD_ID:", record_id,
            "| FIELD:", field,
            "| VALUES:", values
        )
```

The key output is:

```text
Maximum items from one field: ?
Multi-value field occurrences: ?
```

If max is `1`, we can safely make each mapped Archer field one `props[]` instance using `SOURCE_FIELD_NAME` as its deterministic identity.

Run this only, then send me the result.
