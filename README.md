print("=== EXACT COMPONENT REGISTRY + MAPPING OWNERSHIP ===")

for path in [
    "system-security-plan.system-implementation.components[].component",
    "system-security-plan.system-implementation.components[].component.props[]",
    "system-security-plan.system-implementation.components[].component.links[]",
    "system-security-plan.system-implementation.components[].component.responsible-roles[]",
    "system-security-plan.system-implementation.components[].component.protocols[]"
]:
    print("\nPATH:", path)

    print("REGISTRY:")
    element_registry_df.filter(
        col("NODE_PATH") == path
    ).show()

    print("MAPPINGS:")
    mappings = get_mappings_for_node(
        canonical_mapping_df,
        element_registry_df,
        path,
        MODEL_KEY
    )

    print("Mapping count:", len(mappings))

    for m in mappings[:20]:
        print(m)