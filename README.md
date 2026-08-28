Good. Next, only validate one real components[] instance. We want to prove that CONTENT_ID is actually becoming the collection instance identity.

Run this Python cell:

import json

components_path = (
    "system-security-plan.system-implementation.components[]"
)

# Get registry configuration
component_registry = [
    r for r in registry_rows
    if r["NODE_PATH"] == components_path
][0]

instance_key_rule = component_registry["INSTANCE_KEY_RULE"]
item_path = component_registry["ITEM_PATH"] or "$"

# Get mappings owned by components[]
mappings = mappings_by_node.get(components_path, [])

print("NODE:", components_path)
print("INSTANCE_KEY_RULE:", instance_key_rule)
print("ITEM_PATH:", item_path)
print("OWNED MAPPINGS:", len(mappings))

# Find first source record that actually produces component instances
for source_record in source_records:

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

What we're looking for

Because the registry says:

INSTANCE_KEY_RULE = CONTENT_ID

the output should show a real component identity, not NULL, not a generated sequence, and not the parent SSP ID.

Send me the output from this cell. Then we'll know whether the 4,792 component nodes are not only unique structurally, but are being identified correctly.