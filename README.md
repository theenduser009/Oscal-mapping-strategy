Yes — that’s exactly the right logic to inspect, and your breakdown is correct.

The key point is this: the blank FIELD_RELATIVE_PATH in responsible-parties[] is not automatically a bug, because this collection is not being built by build_element_payload() in the same way as document-ids[]. For collection nodes, build_oscal_graph() routes through _get_collection_instances(), and that function uses ITEM_PATH = UserList[] plus INSTANCE_KEY_RULE = SOURCE_FIELD_NAME+ID to create separate instances.

So now we should stop testing responsible-parties[] with build_element_payload() alone. That test is misleading for this branch.

The next validation should inspect the actual collection instances produced by _get_collection_instances() for record 565189.

Run this read-only cell:

import json
from snowflake.snowpark.functions import col

# ================================================================
# READ ONLY - responsible-parties[] collection expansion test
# ================================================================

node_path = "system-security-plan.metadata.responsible-parties[]"

test_record = (
    source_df
    .filter(col("SOURCE_RECORD_ID") == "565189")
    .collect()[0]
)

mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    CONFIG["OSCAL_MODEL"]
)

registry_row = (
    element_registry_df
    .filter(col("NODE_PATH") == node_path)
    .collect()[0]
)

instance_key_rule = registry_row["INSTANCE_KEY_RULE"]
item_path = registry_row["ITEM_PATH"] or "$"

instances = _get_collection_instances(
    test_record,
    mappings,
    instance_key_rule,
    item_path
)

print("NODE:", node_path)
print("SOURCE_RECORD_ID:", test_record["SOURCE_RECORD_ID"])
print("INSTANCE_KEY_RULE:", instance_key_rule)
print("ITEM_PATH:", item_path)
print("INSTANCE COUNT:", len(instances))

print("\n=== INSTANCES ===")

for i, instance in enumerate(instances, start=1):
    print("\nINSTANCE", i)
    print("INSTANCE_KEY:", instance.get("INSTANCE_KEY"))
    print("PAYLOAD:")
    print(json.dumps(instance.get("PAYLOAD"), indent=2, default=str))

What I expect to see is something like:

INSTANCE_KEY: INFORMATION_SYSTEM_OWNER_ISO|111016

INSTANCE_KEY: AUTHORIZING_OFFICIAL_AO|217958

INSTANCE_KEY: INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO|218665

INSTANCE_KEY: INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE|111034

Each should be a separate collection instance.

If that happens, then the collection expansion logic is correct, and only then we validate the resulting responsible-parties[] node count, uniqueness, and edges.