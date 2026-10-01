# %% Read-only SSP selective-lineage sample
# Run after Cells 1-7 PREVIEW. Uses the graph already held in MODEL_GRAPHS.
from snowflake.snowpark.functions import col, lit

lineage = MODEL_GRAPHS[("source-one", "SSP")]["nodes"].filter(
    col("METADATA_JSON").contains(lit("urn:company:oscal:lineage:v1"))
)

print("CANDIDATE LINEAGE NODES =", lineage.count())

sample = lineage.select(
    "SOURCE_RECORD_ID",
    "ELEMENT_PATH",
    "METADATA_JSON",
).limit(20).collect()

for row in sample:
    print(row.as_dict(recursive=True) if hasattr(row, "as_dict") else row)
