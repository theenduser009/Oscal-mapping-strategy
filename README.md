Yes — this passes cleanly. And the 944 is important; we should use the actual result rather than expecting 2,813.

Your validation shows:

system-implementation nodes = 944
Distinct NODE_KEYs          = 944
Null NODE_KEYs              = 0
Edges SSP → implementation  = 944

So the mapper created exactly one unique system-implementation node for each applicable SSP record, and every one has its parent edge. The other SSP records simply didn't produce this element.

Next: validate components[]

This is more important because your registry says:

IS_COLLECTION     = TRUE
INSTANCE_KEY_RULE = CONTENT_ID
ITEM_PATH         = $

Run only this next cell:

from snowflake.snowpark.functions import col

print("=== COMPONENTS GRAPH CHECK ===")

components_path = (
    "system-security-plan.system-implementation.components[]"
)

components_df = final_nodes_df.filter(
    col("NODE_PATH") == components_path
)

print("Total component nodes:")
print(components_df.count())

print("Distinct NODE_KEYs:")
print(
    components_df
    .select("NODE_KEY")
    .distinct()
    .count()
)

print("Null NODE_KEYs:")
print(
    components_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

print("\nEdges into components[]:")
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == components_path)
    .group_by(
        "SOURCE_NODE_PATH",
        "TARGET_NODE_PATH"
    )
    .count()
    .show()
)

Here do not expect 944. components[] is a collection, so there may be multiple component instances underneath each of those 944 system-implementation parents.

The critical result is:

Total component nodes = Distinct NODE_KEYs, Null = 0, and edges should come from system-implementation → components[].