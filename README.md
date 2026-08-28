Run this read-only notebook cell:

import json

node_path = "system-security-plan.metadata.responsible-parties[]"

# Get mappings owned by responsible-parties[]
mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    CONFIG["OSCAL_MODEL"]
)

print("NODE:", node_path)
print("OWNED MAPPINGS:", len(mappings))

for m in mappings:
    print(
        m["SOURCE_FIELD_NAME"],
        "->",
        m["OSCAL_ELEMENT_PATH"],
        "| relative:",
        m["FIELD_RELATIVE_PATH"]
    )

# Use the same test_record currently in memory
payload = build_element_payload(
    test_record,
    mappings
)

print("\nSOURCE_RECORD_ID:", test_record["SOURCE_RECORD_ID"])
print("PAYLOAD:")
print(json.dumps(payload, indent=2, default=str))

Run exactly that and send me the output. Then we’ll check whether responsible-parties[] is producing the right multi-value structure before validating its node and edge counts.