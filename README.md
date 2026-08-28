Good catch — stop here. This result is important. The mapper produced:

components[] = 4,792 nodes   ✅

components[].component = 0 nodes   ❌
Edges into component = 0           ❌

So we should not continue to component.props[] yet.

The registry contains components[].component, but build_oscal_graph() is not materializing that registered non-collection child. This may actually be a modeling/registry issue, not necessarily a mapper bug: your components[] instance payload already looked like:

{
  "ContentId": 572500,
  "LevelId": 354
}

That raises the key question: does .component have mappings/data of its own, or is it just an artificial wrapper between components[] and props[]/links[]/...?

Next step only

Run this to see whether the mapping CSV actually owns anything at .component:

component_path = (
    "system-security-plan.system-implementation.components[].component"
)

mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    component_path,
    CONFIG["OSCAL_MODEL"]
)

print("NODE:", component_path)
print("OWNED MAPPINGS:", len(mappings))

for m in mappings:
    print(
        m["SOURCE_FIELD_NAME"],
        "->",
        m["OSCAL_ELEMENT_PATH"],
        "| relative:",
        m["FIELD_RELATIVE_PATH"]
    )

Don't change Cell 4 or Cell 5 yet.

Send me just the output of OWNED MAPPINGS and whatever mappings it prints. That will tell us whether .component should genuinely become 4,792 nodes or whether the registry hierarchy needs correction.