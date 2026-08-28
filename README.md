Perfect. Run this read-only check for the system-characteristics parent itself:

from snowflake.snowpark.functions import col

sc_path = "system-security-plan.system-characteristics"

print("=== SYSTEM CHARACTERISTICS GRAPH CHECK ===")

sc_df = final_nodes_df.filter(
    col("NODE_PATH") == sc_path
)

print("Total system-characteristics nodes:")
print(sc_df.count())

print("Distinct NODE_KEYs:")
print(
    sc_df
    .select("NODE_KEY")
    .distinct()
    .count()
)

print("Null NODE_KEYs:")
print(
    sc_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

print("\nEdges into system-characteristics:")
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == sc_path)
    .group_by("SOURCE_NODE_PATH", "TARGET_NODE_PATH")
    .count()
    .show()
)

I expect something close to:

Total nodes:        2813
Distinct NODE_KEYs: 2813
Null NODE_KEYs:        0

system-security-plan
→ system-characteristics
Edges: 2813

If that matches, we can consider the system-characteristics branch structurally closed out and move to the next SSP branch.