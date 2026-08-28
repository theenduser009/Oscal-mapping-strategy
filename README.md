Perfect — that confirms the system-ids[] payload itself is correct.

Now the next important check is whether the graph builder is treating system-ids[] correctly as a collection node and creating the expected DIM node and FACT edge.

Run this read-only cell:

from snowflake.snowpark.functions import col

system_ids_path = (
    "system-security-plan.system-characteristics.system-ids[]"
)

print("=== SYSTEM IDS GRAPH CHECK ===")

# Node count
(
    final_nodes_df
    .filter(col("NODE_PATH") == system_ids_path)
    .group_by("NODE_PATH", "ELEMENT_TYPE")
    .count()
    .show()
)

# Edge count into system-ids[]
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == system_ids_path)
    .group_by("SOURCE_NODE_PATH", "TARGET_NODE_PATH")
    .count()
    .show()
)

What I want to verify next is:

system-characteristics
→ system-ids[]

and that the node count and edge count make sense relative to how many source records actually have SAP_ID.

If that looks good, then system-ids[] is fully validated and we can move to props[], which is the more interesting collection because it owns multiple Archer extension properties.