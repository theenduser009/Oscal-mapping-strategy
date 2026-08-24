Perfect. ✅ Cell 2 is correct.

And one correction from me: **12 active SSP registry rows is the correct count**, not 11. The active SSP structure is now:

```text
1  system-security-plan
2  metadata
3  system-characteristics
4  system-implementation
5  metadata.document-ids[]
6  metadata.responsible-parties[]
7  system-characteristics.props[]
8  system-characteristics.system-ids[]
9  system-characteristics.authorization-boundary
10 system-characteristics.security-impact-level
11 system-characteristics.status
12 system-implementation.components[]
```

`control-implementation` is inactive, so it isn't included.

## Next: Cell 3 — Canonicalize the mapping

This is the clean production version of the mapping normalization we already proved:

```python
# ============================================================
# Cell 3 — Canonical Mapping
# ============================================================

from snowflake.snowpark.functions import col


canonical_mapping_df = (
    mapping_df
    .select(
        col("ARCHER_FIELD_NAME").alias("SOURCE_FIELD_NAME"),
        col("OSCAL_ELEMENT_PATH"),
        col("OSCAL_MODEL"),
        col("MAPPING_TYPE"),
        col("TRANSFORMATION_LOGIC")
    )
    .filter(
        col("SOURCE_FIELD_NAME").is_not_null()
        & col("OSCAL_ELEMENT_PATH").is_not_null()
    )
)


print("=== Canonical Mapping ===")
print("Canonical mapping rows:", canonical_mapping_df.count())
print("Active registry rows   :", element_registry_df.count())

print("\nCell 3 complete - canonical mapping ready")
```

Expected:

```text
Canonical mapping rows: 608
Active registry rows   : 12
```

Run **Cell 3 only**. Then we move the proven generic helper functions into the production notebook.
