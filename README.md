# Cell 8B — Inspect ALL component source fields

component_fields = [
    m["SOURCE_FIELD_NAME"]
    for m in component_mappings
]

stats = {
    field: {"count": 0, "samples": []}
    for field in component_fields
}

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

    for field in component_fields:

        value = resolve_json_path(
            source_obj,
            field
        )

        if value not in (None, "", [], {}):

            stats[field]["count"] += 1

            if len(stats[field]["samples"]) < 2:
                stats[field]["samples"].append(value)


for field, info in stats.items():

    print("\nFIELD:", field)
    print("Records with value:", info["count"])

    for sample in info["samples"]:
        print("Sample:", str(sample)[:500])
