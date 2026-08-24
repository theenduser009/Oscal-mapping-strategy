# Cell 8C — Inspect component reference identities
# READ ONLY

component_fields = [
    "SOFTWARE",
    "HARDWARE",
    "INTERCONNECTIONS",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM"
]

samples = 0

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

            print(
                "PARENT:", record["SOURCE_RECORD_ID"],
                "| FIELD:", field,
                "| CONTENT_ID:", content_id,
                "| LEVEL_ID:", level_id
            )

            samples += 1

            if samples >= 20:
                break

        if samples >= 20:
            break

    if samples >= 20:
        break
