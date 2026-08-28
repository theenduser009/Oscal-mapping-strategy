Right — don’t rely on registry_rows. We already have element_registry_df, which is safer anyway.

Use this corrected read-only cell:

import json
from snowflake.snowpark.functions import col

components_path = (
    "system-security-plan.system-implementation.components[]"
)

# Pull registry row directly from element_registry_df
component_registry = (
    element_registry_df
    .filter(col("NODE_PATH") == components_path)
    .collect()[0]
)

instance_key_rule = component_registry["INSTANCE_KEY_RULE"]
item_path = component_registry["ITEM_PATH"] or "$"

# Get mappings directly
mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    components_path,
    CONFIG["OSCAL_MODEL"]
)

print("NODE:", components_path)
print("INSTANCE_KEY_RULE:", instance_key_rule)
print("ITEM_PATH:", item_path)
print("OWNED MAPPINGS:", len(mappings))

# Find first source record that actually produces component instances
for source_record in source_df.to_local_iterator():

    instances = _get_collection_instances(
        source_record,
        mappings,
        instance_key_rule,
        item_path
    )

    if instances:
        print("\nSOURCE_RECORD_ID:", source_record["SOURCE_RECORD_ID"])
        print("INSTANCE COUNT:", len(instances))

        print("\n=== FIRST COMPONENT INSTANCE ===")

        instance = instances[0]

        print("INSTANCE_KEY:", instance.get("INSTANCE_KEY"))
        print("PAYLOAD:")
        print(
            json.dumps(
                instance.get("PAYLOAD"),
                indent=2,
                default=str
            )
        )

        break

This avoids registry_rows and source_records completely.

Run this one. The key thing I want to see next is the INSTANCE_KEY for that first component.