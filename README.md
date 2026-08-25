Yes — I see exactly what happened. **Do not change AR Graph Test again.** The problem is in Cell 4.

When we moved those 10 mappings from:

```text
observations[] or props[]
```

to exact:

```text
observations[]
```

some records now have child observations but the logical `results[]` parent is not being created. Then the builder hits its nested-collection safety check:

```text
Nested collection parent requires instance relationship metadata:
assessment-results.results[]
```

But for Assessment Results we already established that `results[]` is **one logical instance per source record**, keyed by `SOURCE_RECORD_ID`. So it should always exist for every source row.

### Change only this in Cell 4

Find this section inside `_get_collection_instances()`:

```python
if (
    rule
    == _normalize_key_name(
        "SOURCE_RECORD_ID"
    )
):

    record = _row_to_dict(
        source_record
    )

    raw_record_id = record.get(
        "SOURCE_RECORD_ID"
    )

    if raw_record_id is None:
        return []

    instance_key = str(
        raw_record_id
    ).strip()

    if not instance_key:
        return []

    # Create result only when this logical branch
    # actually has mapped source data.
    has_mapped_data = False

    for mapping in mappings:

        source_field = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        if not source_field:
            continue

        value = resolve_json_path(
            source_obj,
            source_field
        )

        if value not in (
            None,
            "",
            [],
            {}
        ):
            has_mapped_data = True
            break

    if not has_mapped_data:
        return []

    return [
        {
            "INSTANCE_KEY": instance_key,
            "PAYLOAD": {}
        }
    ]
```

Replace that entire block with:

```python
if (
    rule
    == _normalize_key_name(
        "SOURCE_RECORD_ID"
    )
):

    record = _row_to_dict(
        source_record
    )

    raw_record_id = record.get(
        "SOURCE_RECORD_ID"
    )

    if raw_record_id is None:
        return []

    instance_key = str(
        raw_record_id
    ).strip()

    if not instance_key:
        return []

    # One logical results[] instance per source record.
    # Child collections such as props[] and observations[]
    # attach to this record-scoped parent.
    return [
        {
            "INSTANCE_KEY": instance_key,
            "PAYLOAD": {}
        }
    ]
```

Then rerun **Cell 4**, then **Cell 10 AR Graph Test**.

Nothing else. This is the correct fix because `results[]` is a structural record-level parent; its existence should **not depend on which child mapping happens to remain owned by it**.
