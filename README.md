Yep. Now run only this read-only validation cell for responsible-parties[]:

from snowflake.snowpark.functions import col

print("=== RESPONSIBLE PARTIES GRAPH CHECK ===")

rp_path = "system-security-plan.metadata.responsible-parties[]"

rp_df = final_nodes_df.filter(
    col("NODE_PATH") == rp_path
)

print("Total responsible-party nodes:")
print(rp_df.count())

print("Distinct NODE_KEYs:")
print(
    rp_df
    .select("NODE_KEY")
    .distinct()
    .count()
)

print("Null NODE_KEYs:")
print(
    rp_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

print("\nEdges into responsible-parties[]:")
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == rp_path)
    .group_by(
        "SOURCE_NODE_PATH",
        "TARGET_NODE_PATH"
    )
    .count()
    .show()
)

What we want

We do not expect 2,813 here because one SSP can produce multiple responsible-party instances.

We want:

Total nodes = Distinct NODE_KEYs
Null NODE_KEYs = 0

And the edge should be:

system-security-plan.metadata
    →
system-security-plan.metadata.responsible-parties[]

with the edge count matching the responsible-party node count.

Run it and show me the numbers.