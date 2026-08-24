Perfect. This is exactly what we wanted to see. `POAMS` has the same reusable reference shape as `components[]`:

```text
[
  {"ContentId": 566742, "LevelId": 346},
  {"ContentId": 566746, "LevelId": 346},
  ...
]
```

So **no new mapping logic is needed**. The same generic collection engine can handle it. ✅

Before registering POA&M, do one tiny check—same one that proved `ContentId` for components.

### Cell 10 — POA&M identity check

```python
# Cell 10 — Validate POA&M collection identity
# READ ONLY

poam_refs = []

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)
    values = resolve_json_path(source_obj, "POAMS")

    if not values:
        continue

    if not isinstance(values, list):
        values = [values]

    for item in values:

        if not isinstance(item, dict):
            continue

        content_id = item.get("ContentId")
        level_id = item.get("LevelId")

        if content_id is not None:
            poam_refs.append(
                (
                    str(record["SOURCE_RECORD_ID"]),
                    str(content_id),
                    None if level_id is None else str(level_id)
                )
            )


content_levels = {}

for parent_id, content_id, level_id in poam_refs:
    content_levels.setdefault(content_id, set()).add(level_id)


real_collisions = {
    cid: {x for x in levels if x is not None}
    for cid, levels in content_levels.items()
    if len({x for x in levels if x is not None}) > 1
}


unique_instances = {
    (parent_id, content_id)
    for parent_id, content_id, level_id in poam_refs
}

print("POA&M reference occurrences:", len(poam_refs))
print("Unique source record + ContentId:", len(unique_instances))
print("Multiple NON-NULL LevelId collisions:", len(real_collisions))
```

What I care about is the last line.

If it says:

```text
Multiple NON-NULL LevelId collisions: 0
```

then POA&M registry can simply use:

```text
NODE_PATH         = plan-of-action-and-milestones.poam-items[]
INSTANCE_KEY_RULE = CONTENT_ID
```

No new Python. No cardinality logic. No Cell 4/5 changes. **That will be the real proof that our engine is reusable beyond SSP.**
