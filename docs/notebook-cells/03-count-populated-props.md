# Cell 3 - Count populated candidate props

Run this after Cells 1 and 2. It counts how many SSP source records populate each candidate property field.

> This cell calls the read-only guard before accessing records.

```python
_assert_read_only()

counts = Counter()

for record in source_df.to_local_iterator():
    source_obj = _parse_source_json(record)

    for field in PROP_FIELDS:
        value = resolve_json_path(source_obj, field)

        if _has_source_value(value):
            counts[field] += 1

print("=== POPULATED PROP FIELD COUNTS ===")

for field in PROP_FIELDS:
    print(field, "=", counts[field])
```

After running it, copy the output beginning with:

```text
=== POPULATED PROP FIELD COUNTS ===
```

[Previous: Cell 2](02-sample-populated-props.md) · [Back to the cell library](README.md)