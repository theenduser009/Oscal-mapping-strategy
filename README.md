Perfect — I can read the column lists from your screenshot. This is exactly what we needed.

Your node key is NODE_KEY, and the node dataframe includes ELEMENT_TYPE, NODE_PATH, SOURCE_RECORD_ID, etc. Your edge key is EDGE_KEY.

Now run only this read-only diagnostic cell after Cell 5:

from snowflake.snowpark import functions as F

dup_nodes = (
    canonical_nodes_df
    .group_by("NODE_KEY")
    .agg(
        F.count("*").alias("ROW_COUNT"),
        F.min("ELEMENT_TYPE").alias("ELEMENT_TYPE"),
        F.min("NODE_PATH").alias("NODE_PATH")
    )
    .filter(F.col("ROW_COUNT") > 1)
)

print("=== DUPLICATE NODE KEYS BY ELEMENT TYPE ===")

(
    dup_nodes
    .group_by("ELEMENT_TYPE", "NODE_PATH")
    .agg(
        F.count("*").alias("DUPLICATE_KEYS"),
        F.sum("ROW_COUNT").alias("ROWS_INVOLVED")
    )
    .sort(F.col("DUPLICATE_KEYS").desc())
    .show(50, truncate=False)
)

This will tell us which branch is producing the ~49,650 duplicate node keys.

Don't change Cells 4, 5, or 6 yet. And definitely don't enable writes.

Send me the output table from this cell; then we'll know whether the duplication is coming from props, components, responsible-parties, or somewhere else.