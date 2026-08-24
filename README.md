Yes. Since you are back in the **development/reference notebook**, do **not change any existing SSP cells**. Add **one new temporary cell at the very bottom**.

Call it something like:

```text
POA&M Prep — Reference Graph
```

Paste this:

```python
# ============================================================
# POA&M Prep — Reference Graph
# DEV / READ ONLY
# ============================================================

from snowflake.snowpark.functions import col


# ------------------------------------------------------------
# 1. Find Authorization Packages that actually contain POAMS
# ------------------------------------------------------------

poam_source_ids = []

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)
    poams = resolve_json_path(source_obj, "POAMS")

    if poams not in (None, "", [], {}):
        poam_source_ids.append(
            str(record["SOURCE_RECORD_ID"])
        )


# ------------------------------------------------------------
# 2. Filter source to only packages containing POA&M refs
# ------------------------------------------------------------

poam_source_df = (
    source_df
    .filter(
        col("SOURCE_RECORD_ID").isin(
            *poam_source_ids
        )
    )
)


# ------------------------------------------------------------
# 3. POA&M mappings only
# ------------------------------------------------------------

poam_mapping_df = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH").startswith(
            "plan-of-action-and-milestones"
        )
    )
)


# ------------------------------------------------------------
# 4. Active POA&M registry only
# ------------------------------------------------------------

poam_registry_df = (
    session.table(CONFIG["REGISTRY_TABLE"])
    .filter(
        (col("OSCAL_MODEL_KEY") == "POAM")
        & (col("IS_ACTIVE") == True)
    )
)


# ------------------------------------------------------------
# 5. Verify
# ------------------------------------------------------------

print("=== POA&M DEV INPUTS ===")
print("Source packages with POAMS :", poam_source_df.count())
print("POA&M mapping rows         :", poam_mapping_df.count())
print("POA&M registry rows        :", poam_registry_df.count())
```

We expect exactly:

```text
Source packages with POAMS : 536
POA&M mapping rows         : 1
POA&M registry rows        : 2
```

### What we are doing

We are **not changing SSP** and not writing anything yet.

We're preparing:

```text
536 Authorization Packages containing POAMS
            ↓
plan-of-action-and-milestones
            ↓
poam-items[]
            ↓
{"ContentId": ..., "LevelId": 346}
```

And importantly, the other **1,629 Authorization Packages will not get empty POA&M roots**.

Run this one cell and show me the three counts. Then we'll feed these three dataframes into the same generic graph builder — no separate POA&M mapping code.
