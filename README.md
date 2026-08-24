# ============================================================
# Cell 8 — Inspect First Collection Node
# READ ONLY
# ============================================================

collection_path = (
    "system-security-plan.system-implementation.components[]"
)

# Find mapping rows targeting components[]
component_mappings = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH") == collection_path
    )
    .collect()
)

print("Mappings found:", len(component_mappings))

for m in component_mappings:
    print(
        "SOURCE_FIELD_NAME:",
        m["SOURCE_FIELD_NAME"],
        "| CARDINALITY:",
        m["CARDINALITY"],
        "| MAPPING_TYPE:",
        m["MAPPING_TYPE"]
    )


# Inspect actual source values
if component_mappings:

    source_field = component_mappings[0]["SOURCE_FIELD_NAME"]

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

        value = resolve_json_path(
            source_obj,
            source_field
        )

        if value not in (None, "", [], {}):

            print("\nSOURCE_RECORD_ID:", record["SOURCE_RECORD_ID"])
            print("VALUE TYPE:", type(value).__name__)
            print("VALUE:", str(value)[:1000])

            samples += 1

        if samples >= 5:
            break

print("\nInspection complete.")
