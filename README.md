Good — since you’ve rerun through Cell 5, stop there. Do not run Cell 6 or 7 yet.

Now we verify only the thing we just changed: security-impact-level.

First, look at the Cell 5 summary and tell me this number:

security-impact-level | ?

Earlier it collapsed to 37; we want to see whether the count changed after the null-preservation/dynamic lookup changes.

Then run this one test cell:

# ================================================================
# TEST DIRECT/TRANSFORM - SECURITY IMPACT LEVEL
# READ ONLY
# ================================================================

import json
from snowflake.snowpark.functions import col

node_path = (
    "system-security-plan."
    "system-characteristics."
    "security-impact-level"
)

mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    CONFIG["OSCAL_MODEL"]
)

test_record = (
    source_df
    .filter(col("SOURCE_RECORD_ID") == "866211")
    .collect()[0]
)

payload = build_element_payload(
    test_record,
    mappings
)

print("SOURCE_RECORD_ID: 866211")
print("PAYLOAD:")
print(
    json.dumps(
        payload,
        indent=2,
        default=str
    )
)

For that known 80654 case, we want something like:

{
  "security-objective-confidentiality": "low",
  "security-objective-integrity": "low",
  "security-objective-availability": "low"
}

If that looks right, then we test one legacy-ID record and one null record. We are not moving anywhere else until those three cases behave correctly.