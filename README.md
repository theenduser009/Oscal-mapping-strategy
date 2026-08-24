Exactly — registry is confirmed. ✅

Before we run POA&M through the mapper, there is **one important semantic check** I want to make first.

Our generic mapper currently creates the **root node once per source record**. That made perfect sense for SSP because each Authorization Package row represented an SSP root.

For POA&M, `POAMS` is a **reference collection**, so we need to know:

> Does every Authorization Package actually have POA&M data, or only some of them?

Run this **read-only** check:

```python
# ============================================================
# POA&M Source Coverage Check
# READ ONLY
# ============================================================

records_total = 0
records_with_poams = 0
records_without_poams = 0
total_poam_refs = 0

distinct_content_ids = set()
max_refs_per_record = 0

for record in source_df.to_local_iterator():

    records_total += 1

    source_obj = _parse_source_json(record)
    value = resolve_json_path(source_obj, "POAMS")

    if value in (None, "", [], {}):
        records_without_poams += 1
        continue

    records_with_poams += 1

    items = value if isinstance(value, list) else [value]

    max_refs_per_record = max(
        max_refs_per_record,
        len(items)
    )

    for item in items:

        total_poam_refs += 1

        if isinstance(item, dict):
            cid = (
                item.get("ContentId")
                or item.get("CONTENT_ID")
                or item.get("content_id")
            )

            if cid is not None:
                distinct_content_ids.add(str(cid))

        else:
            distinct_content_ids.add(str(item))


print("=== POA&M SOURCE COVERAGE ===")
print("Authorization Package records :", records_total)
print("Records WITH POAMS            :", records_with_poams)
print("Records WITHOUT POAMS         :", records_without_poams)
print("Total POA&M references        :", total_poam_refs)
print("Distinct referenced ContentIds:", len(distinct_content_ids))
print("Maximum refs in one record    :", max_refs_per_record)
```

### Why this matters

Suppose the output is:

```text
2165 total Authorization Packages
800 have POAMS
1365 have no POAMS
```

Then we probably **should not create 2,165 empty `plan-of-action-and-milestones` roots**.

We would want something more like:

```text
Authorization Package with POAMS
        ↓
plan-of-action-and-milestones
        ↓
poam-items[]
```

only where POA&M references actually exist.

So run this first. **Don't modify the mapper or registry yet.** This result will tell us whether our current generic root-creation rule is correct for POA&M or needs a generic metadata rule.
