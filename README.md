Ah — **from the actual Archer data**, not just from the mapping file. Then I need to correct the statement:

**We have not yet proven that every relevant SSP field present in the raw data is mapped.**

What we proved is:

```text
Current mapping CSV
        ↓
all SSP paths in that CSV
        ↓
all required structural nodes registered
        ↓
DIM + FACT built and verified
```

But there could still be fields in `CURATED_JSON` that contain data and **are missing from the mapping CSV** — exactly like the case you noticed earlier.

So before calling SSP truly complete **from the data**, we should do one final raw-data coverage audit.

### Next step — actual data vs mapping

Run this read-only audit in the **reference notebook**, not the clean production mapper:

```python
# ============================================================
# RAW DATA vs MAPPING COVERAGE AUDIT
# READ ONLY
# ============================================================

from collections import Counter

# All mapped Archer source fields
mapped_fields = {
    str(r["SOURCE_FIELD_NAME"]).strip()
    for r in canonical_mapping_df.select("SOURCE_FIELD_NAME").collect()
    if r["SOURCE_FIELD_NAME"]
}

# Count every populated top-level field actually present
# across all Archer Authorization Package records
raw_field_counts = Counter()

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)

    if not isinstance(source_obj, dict):
        continue

    for field_name, value in source_obj.items():

        if value in (None, "", [], {}):
            continue

        raw_field_counts[str(field_name).strip()] += 1


raw_fields = set(raw_field_counts.keys())

unmapped_fields = sorted(
    raw_fields - mapped_fields,
    key=lambda x: raw_field_counts[x],
    reverse=True
)

mapped_and_present = raw_fields & mapped_fields


print("=== RAW DATA vs MAPPING COVERAGE ===")

print("Populated fields found in raw :", len(raw_fields))
print("Mapped fields present in raw  :", len(mapped_and_present))
print("Populated but NOT mapped      :", len(unmapped_fields))

print("\n=== POPULATED UNMAPPED FIELDS ===")

for field in unmapped_fields:
    print(
        f"{field:60} "
        f"records={raw_field_counts[field]}"
    )
```

This answers the question you are really asking:

> **“What data actually exists in Archer that our mapping does not currently account for?”**

If this produces fields like:

```text
NAS
SOME_OTHER_FIELD
...
```

then we know SSP is **not yet complete from the source-data perspective**, and you can update the mapping before we move to another OSCAL model.

So: **mapping-side SSP = complete. Raw-data-side coverage = this is the final check we still need.**
