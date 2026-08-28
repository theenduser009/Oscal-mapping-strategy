Good. Let's validate system-ids[] next, but read-only and one thing at a time.

Run this notebook cell:

from snowflake.snowpark.functions import col
import json

node_path = "system-security-plan.system-characteristics.system-ids[]"

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

# Test the known record
test_record = (
    source_df
    .filter(col("SOURCE_RECORD_ID") == "565189")
    .collect()[0]
)

payload = build_element_payload(test_record, mappings)

print("\nSOURCE_RECORD_ID:", test_record["SOURCE_RECORD_ID"])
print("PAYLOAD:")
print(json.dumps(payload, indent=2, default=str))

We expect approximately:

NODE: ...system-ids[]
OWNED MAPPINGS: 1

SAP_ID -> ...system-ids[].id | relative: id

PAYLOAD:
{
  "id": "565189-Information System"
}

For now, don't test counts or change the mapper. First confirm this ownership/payload result. Then we'll check whether system-ids[] being marked as a collection is actually producing the correct DIM node + FACT edge behavior.