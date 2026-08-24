# Cell 8D — Validate stable identity for component references
# READ ONLY

component_fields = [
    m["SOURCE_FIELD_NAME"]
    for m in component_mappings
]

refs = []

for record in source_df.to_local_iterator():

    raw_json = record["CURATED_JSON"]

    if isinstance(raw_json, str):
        try:
            source_obj = json.loads(raw_json)
        except Exception:
            continue
    else:
        source_obj = raw_json

    if not isinstance(source_obj, dict):
        continue

    parent_id = str(record["SOURCE_RECORD_ID"])

    for field in component_fields:

        values = resolve_json_path(source_obj, field)

        if not values:
            continue

        if not isinstance(values, list):
            values = [values]

        for ref in values:

            if isinstance(ref, dict):
                content_id = ref.get("ContentId")
                level_id = ref.get("LevelId")
            else:
                content_id = ref
                level_id = None

            if content_id is not None:
                refs.append(
                    (parent_id, field, str(content_id),
                     None if level_id is None else str(level_id))
                )


# Check ContentId reused with different LevelIds
content_levels = {}

for parent_id, field, content_id, level_id in refs:
    content_levels.setdefault(content_id, set()).add(level_id)

multi_level_ids = {
    cid: levels
    for cid, levels in content_levels.items()
    if len(levels) > 1
}

print("Total reference occurrences:", len(refs))
print("Distinct ContentIds:", len(content_levels))
print("References missing LevelId:",
      sum(1 for r in refs if r[3] is None))
print("ContentIds appearing with multiple LevelIds:",
      len(multi_level_ids))

for cid, levels in list(multi_level_ids.items())[:10]:
    print("Collision:", cid, levels)
