# Cell 8F — Expected component node count
# READ ONLY

unique_parent_component = {
    (parent_id, content_id)
    for parent_id, field, content_id, level_id in refs
}

print("Reference occurrences:", len(refs))
print("Unique SSP + ContentId:", len(unique_parent_component))
print(
    "Duplicate references within same SSP:",
    len(refs) - len(unique_parent_component)
)
