# Check mappings directly owned by system-implementation
# once components[] becomes its own node.

parent_path = "system-security-plan.system-implementation"
child_path  = "system-security-plan.system-implementation.components[]"

rows = (
    canonical_mapping_df
    .filter(col("OSCAL_ELEMENT_PATH").startswith(parent_path + "."))
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH"
    )
    .collect()
)

direct_parent = []
component_child = []

for r in rows:
    path = r["OSCAL_ELEMENT_PATH"]

    if path == child_path or path.startswith(child_path + "."):
        component_child.append(r)
    else:
        direct_parent.append(r)

print("Direct system-implementation mappings:", len(direct_parent))
print("Mappings moving to components[]:", len(component_child))

for r in direct_parent:
    print(
        r["SOURCE_FIELD_NAME"],
        "->",
        r["OSCAL_ELEMENT_PATH"]
    )
