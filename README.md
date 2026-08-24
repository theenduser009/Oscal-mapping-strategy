Yes — understood. For POA&M we will use only these target columns.

**DIM_OSCAL_POAM_ELEMENT**

```text
PK_DIM_OSCAL_POAM_ELEMENT_HASH
ELEMENT_TYPE
OSCAL_UUID
METADATA_JSON
SOURCE_SYSTEM_NAME
SOURCE_TABLE_NAME
SOURCE_RECORD_ID
DW_LOAD_TIMESTAMP
DW_PIPELINE_RUN_ID
```

**FACT_OSCAL_POAM_DEPENDENCY**

```text
PK_FACT_OSCAL_POAM_DEPENDENCY_HASH
FK_SOURCE_ELEMENT_HASH
FK_TARGET_ELEMENT_HASH
DEPENDENCY_TYPE
SOURCE_OSCAL_UUID
TARGET_OSCAL_UUID
```

Ignore the other diagram FKs/indexes.

And yes — **before touching the POA&M registry or mapper configuration, we need to discover the POA&M paths from your mapping CSV.** The root we're looking for is:

```text
plan-of-action-and-milestones
```

### Next step only: inventory every POA&M mapping/path

Run this read-only cell in the reference notebook:

```python
# ============================================================
# POA&M Mapping / Path Inventory
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

POAM_ROOT = "plan-of-action-and-milestones"

poam_mapping_df = (
    canonical_mapping_df
    .filter(
        (col("OSCAL_MODEL") == "POA&M")
        |
        col("OSCAL_ELEMENT_PATH").startswith(POAM_ROOT)
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_MODEL",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE"
    )
    .distinct()
    .sort(
        "OSCAL_ELEMENT_PATH",
        "SOURCE_FIELD_NAME"
    )
)

print("=== POA&M MAPPING INVENTORY ===")
print("POA&M mapping rows:", poam_mapping_df.count())

poam_mapping_df.show(200, truncate=False)

print("\n=== DISTINCT POA&M PATHS ===")

(
    poam_mapping_df
    .select("OSCAL_ELEMENT_PATH")
    .distinct()
    .sort("OSCAL_ELEMENT_PATH")
    .show(200, truncate=False)
)
```

This will tell us exactly whether the CSV contains only:

```text
plan-of-action-and-milestones.poam-items[]
```

or whether it goes deeper, for example:

```text
plan-of-action-and-milestones.metadata...
plan-of-action-and-milestones.poam-items[].title
plan-of-action-and-milestones.poam-items[].description
...
```

**Do not create POA&M registry rows yet.** Show me this output first. Then we'll derive the POA&M hierarchy from the actual paths, just like we did for SSP.
