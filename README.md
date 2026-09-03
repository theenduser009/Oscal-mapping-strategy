Yes — let’s do that next.

We want to compare populated keys in CURATED_JSON against the mapping CSV’s SOURCE_FIELD_NAME. Since your mapping is already loaded as canonical_mapping_df, we can do this safely in the notebook without needing another physical mapping table.

Run this read-only temporary cell:

from collections import Counter

# 1) Count populated keys that actually exist in CURATED_JSON
curated_counts = Counter()

for record in source_df.to_local_iterator():
    source_obj = _parse_source_json(record)

    if not isinstance(source_obj, dict):
        continue

    for key, value in source_obj.items():
        if value not in (None, "", [], {}):
            curated_counts[key] += 1


# 2) Get all mapped Archer source field names
mapped_fields = {
    row["SOURCE_FIELD_NAME"]
    for row in canonical_mapping_df
        .select("SOURCE_FIELD_NAME")
        .distinct()
        .collect()
    if row["SOURCE_FIELD_NAME"]
}


# 3) Show populated curated fields that have NO OSCAL mapping
gaps = [
    (field, count)
    for field, count in curated_counts.items()
    if field not in mapped_fields
]

gaps.sort(key=lambda x: x[1], reverse=True)

print("=== POPULATED CURATED FIELDS WITH NO OSCAL MAPPING ===")
print("Total unmapped populated fields:", len(gaps))

for field, count in gaps[:200]:
    print(field, "=", count)

This is the report we actually need for your manager.

If it returns something like:

FIELD_A = 2813
FIELD_B = 2740
FIELD_C = 1900

those are fields with real data that currently have no row in the Archer→OSCAL mapping. Those deserve business review.

Fields with 0 populated rows are a separate retirement/data-quality discussion with Josh.

Run this and send me the output. Then we’ll split it into: high-value unmapped, sparse/problem, and already mapped.