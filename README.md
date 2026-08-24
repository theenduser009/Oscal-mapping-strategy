Cell 1 is clean. ✅ `SSP`, source, registry, targets, run ID, and `EXECUTE_WRITES=False` are all correct.

Now **Cell 2 only**. Its job is purely to load the three production inputs:

1. Archer raw records
2. Archer→OSCAL mapping CSV
3. Active registry for the configured model

We are reusing the exact mapping-file approach that already worked in the SSP notebook.

```python
# ============================================================
# Cell 2 — Load Production Inputs
# ============================================================

import pandas as pd

from snowflake.snowpark.functions import col


# ------------------------------------------------------------
# A. Load Archer source
# ------------------------------------------------------------

source_df = (
    session.table(CONFIG["RAW_TABLE"])
    .select(
        col("CONTENT_ID").cast("string").alias("SOURCE_RECORD_ID"),
        col("CURATED_JSON")
    )
)


# ------------------------------------------------------------
# B. Load Archer -> OSCAL mapping CSV
# ------------------------------------------------------------

mapping_pdf = pd.read_csv(
    "archer_to_oscal_mapping (4).csv",
    encoding="cp1252",
    dtype=str
)

mapping_df = session.create_dataframe(mapping_pdf)


# ------------------------------------------------------------
# C. Load active registry for configured OSCAL model
# ------------------------------------------------------------

element_registry_df = (
    session.table(CONFIG["REGISTRY_TABLE"])
    .filter(
        (col("OSCAL_MODEL_KEY") == CONFIG["OSCAL_MODEL"])
        & (col("IS_ACTIVE") == True)
    )
)


# ------------------------------------------------------------
# D. Input verification
# ------------------------------------------------------------

print("=== OSCAL Mapper Inputs ===")
print("Source records :", source_df.count())
print("Mapping rows   :", mapping_df.count())
print("Registry rows  :", element_registry_df.count())

print("\nActive model   :", CONFIG["OSCAL_MODEL"])
```

For our known SSP baseline, we expect approximately:

```text
Source records : 2165
Mapping rows   : 608
Registry rows  : 11
```

The registry count may be `11` now because `control-implementation` was deactivated and the confirmed SSP nodes remain active.

**One thing:** if the new notebook doesn't see `"archer_to_oscal_mapping (4).csv"` directly, don't change anything else. Show me that error and we'll reuse the **exact file reference/import mechanism from the old notebook** rather than inventing another loading method.

Run Cell 2 only.
