# Cell 2 - Sample populated candidate props

Run this after Cell 1. It prints up to ten SSP source records containing at least one populated candidate property field.

> This cell calls the read-only guard before accessing records.

```python
_assert_read_only()

shown = 0

for record in source_df.to_local_iterator():
    source_obj = _parse_source_json(record)
    populated = {}

    for field in PROP_FIELDS:
        value = resolve_json_path(source_obj, field)

        if _has_source_value(value):
            populated[field] = value

    if populated:
        print("\nSOURCE_RECORD_ID:", record["SOURCE_RECORD_ID"])

        for field, value in populated.items():
            print(field, "=", value)

        shown += 1

    if shown >= 10:
        break
```

[Previous: Cell 1](01-configuration-and-safety.md) · [Back to the cell library](README.md) · [Next: Cell 3](03-count-populated-props.md)