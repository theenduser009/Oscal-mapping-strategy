Excellent — **SSP is now fully verified for every path currently materialized from the mapping file.** ✅

```text
DIM  : 88,111 / 88,111
FACT : 85,946 / 85,946
LOAD VERIFIED
```

There is now **one cleanup item before we call SSP complete**: `control-implementation` exists in the registry, but Cell 5 produced **zero `control-implementation` nodes**.

We should not guess why. Let's ask the mapping file directly.

### Next step only — check control-implementation mappings

Run this read-only cell:

```python
from snowflake.snowpark.functions import col

control_paths = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH").startswith(
            "system-security-plan.control-implementation"
        )
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH"
    )
    .distinct()
)

print("Control-implementation mapping rows:", control_paths.count())
control_paths.show(100, truncate=False)
```

There are only two possible outcomes:

```text
> 0 rows
→ mappings exist; we inspect why they aren't materializing.

0 rows
→ the mapping file currently has no control-implementation mapping,
  so we should not manufacture it in Python.
```

After this, we can say whether the **current SSP mapping cycle is complete**, and then move to packaging the production mapper instead of adding more exploratory logic.
