Yep. **Next we stop changing the engine. Cells 3–7 are now the reusable engine.** ✅

Now prove reuse with the **next OSCAL structure using metadata only**. I’d use **POA&M** next because your CSV already contains:

```text
OSCAL_MODEL        = POA&M
OSCAL_ELEMENT_PATH = plan-of-action-and-milestones.poam-items[]
```

### Next step only: inspect POA&M mappings

Add a new temporary read-only cell:

```python
# ============================================================
# Next Test — Inspect POA&M mappings
# READ ONLY
# ============================================================

poam_rows = (
    mapping_df
    .filter(
        col("OSCAL_MODEL") == "POA&M"
    )
    .select(
        "ARCHER_FIELD_NAME",
        "OSCAL_ELEMENT_PATH"
    )
    .collect()
)

print("POA&M mapping rows:", len(poam_rows))

for r in poam_rows:
    print(
        r["ARCHER_FIELD_NAME"],
        "->",
        r["OSCAL_ELEMENT_PATH"]
    )
```

Run **only this** and show me the output.

We are **not writing POA&M Python**. The goal now is to add POA&M registry metadata and run the **same engine**. If we find ourselves rewriting Cells 3–7 for POA&M, then the design has failed.
