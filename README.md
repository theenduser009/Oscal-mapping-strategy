Next: run Cell 4 once so the new transform functions are loaded.

Then do not run Cells 5–7 yet. First prove the responsible-party transform on one real record.

Add a temporary test cell:

import json

node_path = "system-security-plan.metadata.responsible-parties[]"

# Get responsible-party mappings
mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    CONFIG["OSCAL_MODEL"]
)

# Find one real record having a System Owner
test_record = None

for record in source_df.collect():

    source_obj = _parse_source_json(record)

    value = resolve_json_path(
        source_obj,
        "INFORMATION_SYSTEM_OWNER_ISO"
    )

    if value not in (None, "", [], {}):
        test_record = record
        break


print(
    "SOURCE_RECORD_ID:",
    test_record["SOURCE_RECORD_ID"]
)

payload = build_element_payload(
    test_record,
    mappings
)

print("\nRESPONSIBLE PARTY PAYLOAD:")
print(
    json.dumps(
        payload,
        indent=2,
        default=str
    )
)

We want to see something roughly like:

{
  "role-id": "system-owner",
  "party-ids": [
    "115290"
  ]
}

—or multiple responsible-party entries if that record has several populated role fields.

Run Cell 4 → this test cell → show me the output. Then we'll know whether the reusable handler is wired correctly before rebuilding all 61K+ nodes.