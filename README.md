# Read-only check: why control-implementation produced 0 nodes

control_path = "system-security-plan.control-implementation"

control_mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    control_path,
    CONFIG["OSCAL_MODEL"]
)

records_with_payload = 0

for record in source_df.to_local_iterator():
    payload = build_element_payload(record, control_mappings)

    if payload:
        records_with_payload += 1

print("Control-implementation mappings:", len(control_mappings))
print("Source records with control payload:", records_with_payload)
