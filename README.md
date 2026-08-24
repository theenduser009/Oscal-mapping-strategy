Yep — this one is straightforward. **My Cell 3 used normalized column names, but your new `mapping_df` preserved the exact CSV header casing.** Snowflake is telling us exactly that:

```text
I looked for: ARCHER_FIELD_NAME
Actual:       "Archer_Field_Name"
```

So **replace Cell 3 only** with this. Do not touch Cells 1–2.

```python
# ============================================================
# Cell 3 — Canonical Mapping
# ============================================================

from snowflake.snowpark.functions import col


canonical_mapping_df = (
    mapping_df
    .filter(
        col('"Archer_Field_Name"').is_not_null()
        & col('"OSCAL_Element_Path"').is_not_null()
    )
    .select(
        col('"Archer_Field_Name"').alias("SOURCE_FIELD_NAME"),
        col('"OSCAL_Element_Path"').alias("OSCAL_ELEMENT_PATH"),
        col('"OSCAL_Model"').alias("OSCAL_MODEL"),
        col('"Mapping_Type"').alias("MAPPING_TYPE"),
        col('"Transformation_Logic"').alias("TRANSFORMATION_LOGIC")
    )
)


print("=== Canonical Mapping ===")
print("Canonical mapping rows:", canonical_mapping_df.count())
print("Active registry rows   :", element_registry_df.count())

print("\nCell 3 complete - canonical mapping ready")
```

These names come directly from the error you showed:

```text
"Archer_Field_Name"
"OSCAL_Model"
"OSCAL_Element_Path"
"Mapping_Type"
"Transformation_Logic"
```

We then deliberately alias them into our standard production names:

```text
SOURCE_FIELD_NAME
OSCAL_ELEMENT_PATH
OSCAL_MODEL
MAPPING_TYPE
TRANSFORMATION_LOGIC
```

That way **everything after Cell 3 uses one clean canonical naming convention**, regardless of how the CSV headers are written.

Expected result:

```text
Canonical mapping rows: 608
Active registry rows   : 12
```

Run just this corrected Cell 3.
