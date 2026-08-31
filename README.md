Yes — run this single read-only Python cell in Snowflake. It reads the attached mapping CSV into a DataFrame, reads the registry table, and compares Direct mappings vs active registry ownership.

# ================================================================
# PHASE 1 - DIRECT MAPPING VS REGISTRY COVERAGE
# READ ONLY
# ================================================================

import pandas as pd
from snowflake.snowpark.functions import col

# ------------------------------------------------
# 1. Load attached mapping CSV
# ------------------------------------------------

mapping_pdf = pd.read_csv(
    "archer_to_oscal_mapping (4).csv",
    encoding="cp1252",
    dtype=str
)

mapping_df = session.create_dataframe(mapping_pdf)

# ------------------------------------------------
# 2. Canonical mapping
# ------------------------------------------------

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

# ------------------------------------------------
# 3. Load registry
# ------------------------------------------------

registry_df = (
    session.table(
        "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY"
    )
)

# ------------------------------------------------
# 4. Active SSP registry paths
# ------------------------------------------------

active_registry_rows = (
    registry_df
    .filter(
        (col("OSCAL_MODEL_KEY") == "SSP")
        & (col("IS_ACTIVE") == True)
    )
    .select(
        "NODE_PATH",
        "ELEMENT_TYPE",
        "PARENT_NODE_PATH"
    )
    .collect()
)

active_paths = {
    r["NODE_PATH"]
    for r in active_registry_rows
}

# ------------------------------------------------
# 5. Direct SSP mappings
# ------------------------------------------------

direct_rows = (
    canonical_mapping_df
    .filter(
        (col("OSCAL_MODEL") == "SSP")
        & (col("MAPPING_TYPE") == "Direct")
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH"
    )
    .collect()
)

# ------------------------------------------------
# 6. Find registry owner for each Direct mapping
# ------------------------------------------------

covered = []
missing = []

for row in direct_rows:

    source_field = row["SOURCE_FIELD_NAME"]
    mapping_path = row["OSCAL_ELEMENT_PATH"]

    candidates = [
        p
        for p in active_paths
        if (
            mapping_path == p
            or mapping_path.startswith(p + ".")
        )
    ]

    if candidates:
        owner = max(candidates, key=len)

        covered.append({
            "SOURCE_FIELD_NAME": source_field,
            "OSCAL_ELEMENT_PATH": mapping_path,
            "OWNER_NODE_PATH": owner
        })

    else:
        missing.append({
            "SOURCE_FIELD_NAME": source_field,
            "OSCAL_ELEMENT_PATH": mapping_path
        })

# ------------------------------------------------
# 7. Results
# ------------------------------------------------

print("=== SSP DIRECT MAPPING COVERAGE ===")
print("Direct mappings          :", len(direct_rows))
print("Covered by registry      :", len(covered))
print("Missing registry owner   :", len(missing))

print("\n=== MISSING DIRECT MAPPINGS ===")

if not missing:
    print("NONE")
else:
    for r in missing:
        print(
            r["SOURCE_FIELD_NAME"],
            "->",
            r["OSCAL_ELEMENT_PATH"]
        )

print("\n=== COVERED DIRECT MAPPINGS ===")

for r in covered:
    print(
        r["SOURCE_FIELD_NAME"],
        "->",
        r["OSCAL_ELEMENT_PATH"],
        "| OWNER:",
        r["OWNER_NODE_PATH"]
    )

The result I care about most is:

Direct mappings:
Covered by registry:
Missing registry owner:

and then whatever appears under MISSING DIRECT MAPPINGS.

Send me that output and we’ll use it as the actual remaining Phase-1 build list.