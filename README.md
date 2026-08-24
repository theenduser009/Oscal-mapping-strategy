Perfect. ✅ Cell 8 tells us:

```text
POAMS -> plan-of-action-and-milestones.poam-items[]
```

So the CSV already gives us the POA&M hierarchy. Now we only need to inspect **what `POAMS` actually contains** so we know the collection instance key.

### Cell 9 — inspect POAMS source value

```python
# ============================================================
# Cell 9 — Inspect POA&M Collection Source
# READ ONLY
# ============================================================

samples = 0

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)

    value = resolve_json_path(
        source_obj,
        "POAMS"
    )

    if value in (None, "", [], {}):
        continue

    print("\nSOURCE_RECORD_ID:", record["SOURCE_RECORD_ID"])
    print("TYPE:", type(value).__name__)
    print("VALUE:", str(value)[:1000])

    samples += 1

    if samples >= 5:
        break

print("\nSamples found:", samples)
```

Run **only Cell 9** and show me the output.

We are not changing Cells 3–7. We are proving that POA&M can be onboarded through mapping + registry metadata using the same engine.
