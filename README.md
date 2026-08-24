This output is exactly what we needed. It tells us **not to run POA&M through the mapper yet**.

Three important facts:

```text
Authorization Packages       2165
Packages with POAMS            536
POA&M reference occurrences   2563
Distinct POA&M ContentIds     1112
```

So:

1. We should **not create 2,165 POA&M roots**. Only 536 source records actually have POA&M references.
2. More importantly, `2563 references` but only `1112 distinct ContentIds` means **the same POA&M ContentId is referenced by multiple Authorization Packages**.
3. Before deciding the POA&M node identity, we need to understand that reuse. Otherwise we could accidentally duplicate one logical POA&M item many times.

### Next step only — inspect shared POA&M ContentIds

Run this read-only cell:

```python
# ============================================================
# POA&M Cross-Package Reference Check
# READ ONLY
# ============================================================

from collections import defaultdict

poam_usage = defaultdict(set)
poam_occurrences = defaultdict(int)

for record in source_df.to_local_iterator():

    source_record_id = str(record["SOURCE_RECORD_ID"])

    source_obj = _parse_source_json(record)
    value = resolve_json_path(source_obj, "POAMS")

    if value in (None, "", [], {}):
        continue

    items = value if isinstance(value, list) else [value]

    for item in items:

        if isinstance(item, dict):
            content_id = item.get("ContentId")
        else:
            content_id = item

        if content_id is None:
            continue

        content_id = str(content_id)

        poam_usage[content_id].add(source_record_id)
        poam_occurrences[content_id] += 1


shared = [
    (
        content_id,
        len(source_records),
        poam_occurrences[content_id]
    )
    for content_id, source_records in poam_usage.items()
    if len(source_records) > 1
]

shared.sort(
    key=lambda x: x[1],
    reverse=True
)


print("=== POA&M CROSS-PACKAGE REUSE ===")
print("Distinct ContentIds        :", len(poam_usage))
print("Shared by multiple packages:", len(shared))

print("\n=== TOP SHARED POA&M IDs ===")

for content_id, package_count, occurrences in shared[:20]:
    print(
        "ContentId:", content_id,
        "| Packages:", package_count,
        "| Occurrences:", occurrences
    )
```

Why I'm stopping here first: our current generic collection key would effectively be:

```text
AuthorizationPackageID + POAM ContentId
```

If `ContentId 566742` belongs to 10 different Authorization Packages, that would create **10 separate POA&M item nodes**.

That may be correct, or `566742` may actually be **one reusable POA&M entity** that should exist once and be related to several packages. We need the actual data to answer that instead of guessing.

Also, your result confirms another improvement we'll eventually make to the generic mapper: an empty OSCAL root should not be created when neither it nor any descendant has data. That would give POA&M approximately **536 roots rather than 2,165**, assuming the root is package-scoped.

Run this reuse check next. Then we can make the POA&M identity decision correctly.
