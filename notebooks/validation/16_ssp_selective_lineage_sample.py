# %% Read-only SSP selective-lineage sample
# Run after Cells 1-7 PREVIEW. Uses the graph already held in MODEL_GRAPHS.
from snowflake.snowpark.functions import col

lineage = MODEL_GRAPHS[("source-one", "SSP")]["nodes"].filter(
    col("METADATA_JSON").contains("urn:company:oscal:lineage:v1")
)

print("CANDIDATE LINEAGE NODES =", lineage.count())

lineage.select(
    "SOURCE_RECORD_ID",
    "ELEMENT_PATH",
    "METADATA_JSON",
).show(20, truncate=False)
