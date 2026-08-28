Great. Next we validate status.

Run this read-only cell:

from snowflake.snowpark.functions import col
import json

status_path = "system-security-plan.system-characteristics.status"

# Find one record with status-related source data
test_record = (
    source_df
    .filter(col("SOURCE_RECORD_ID") == "565189")
    .collect()[0]
)

mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    status_path,
    CONFIG["OSCAL_MODEL"]
)

payload = build_element_payload(
    test_record,
    mappings
)

print("SOURCE_RECORD_ID:", test_record["SOURCE_RECORD_ID"])
print("NODE:", status_path)
print("OWNED MAPPINGS:", len(mappings))
print("PAYLOAD:")
print(json.dumps(payload, indent=2, default=str))

We already saw 565189 produce a status value earlier, so I expect something like:

OWNED MAPPINGS: 3

PAYLOAD:
{
  "state": [80661]
}

Run that first. If it matches, the next check will be status node count + edge count + uniqueness, just like we did for system-ids[] and props[].