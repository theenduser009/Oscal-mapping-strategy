Run just this read-only notebook cell. It picks CONTENT_ID = 565422 and tests only the authorization-boundary payload.

from snowflake.snowpark.functions import col
import json

test_record = (
    source_df
    .filter(col("SOURCE_RECORD_ID") == "565422")
    .collect()[0]
)

node_path = (
    "system-security-plan.system-characteristics.authorization-boundary"
)

mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    CONFIG["OSCAL_MODEL"]
)

payload = build_element_payload(
    test_record,
    mappings
)

print("SOURCE_RECORD_ID:", test_record["SOURCE_RECORD_ID"])
print("NODE:", node_path)
print("OWNED MAPPINGS:", len(mappings))
print("PAYLOAD:")
print(json.dumps(payload, indent=2, default=str))

Expected result should be roughly:

OWNED MAPPINGS: 1

PAYLOAD:
{
  "description": "Corporate network DT ..."
}

Run that and send me the output.