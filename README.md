Excellent — this is exactly what we needed.

For CONTENT_ID 866211, we can see:

CNSS_CONFIDENTIALITY_RATING = null
CNSS_INTEGRITY_RATING       = null
CNSS_AVAILABILITY_RATING    = null

CONF_OVERRIDE  = [80654]
INT_OVERRIDE   = [80654]
AVAIL_OVERRIDE = [80654]

So security-impact-level absolutely has source data. Let's test 866211.

Run this notebook cell:

from snowflake.snowpark.functions import col
import json

# Test a record with populated security-impact source fields
test_record = (
    source_df
    .filter(col("SOURCE_RECORD_ID") == "866211")
    .collect()[0]
)

node_path = (
    "system-security-plan.system-characteristics.security-impact-level"
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

What we're testing

We already know this node has 12 owned mappings.

Therefore for 866211, I do not expect {} anymore. Some payload should be generated from those override values.

If it still returns:

{}

then we've found an actual mapper/mapping-path problem.

If it produces fields under security-impact-level, then this branch is functioning too.

Run exactly that and show me the result.