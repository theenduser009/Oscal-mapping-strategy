Perfect — status payload is working too. ✅

Now do the same structural validation we used for system-ids[] and props[]: count the status nodes, count incoming edges, and verify uniqueness.

from snowflake.snowpark.functions import col

status_path = "system-security-plan.system-characteristics.status"

print("=== STATUS GRAPH CHECK ===")

status_df = final_nodes_df.filter(
    col("NODE_PATH") == status_path
)

print("Total status nodes:")
print(status_df.count())

print("Distinct NODE_KEYs:")
print(
    status_df
    .select("NODE_KEY")
    .distinct()
    .count()
)

print("Null NODE_KEYs:")
print(
    status_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

print("\nEdges into status:")
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == status_path)
    .group_by("SOURCE_NODE_PATH", "TARGET_NODE_PATH")
    .count()
    .show()
)

What I expect is a clean result: total nodes = distinct keys, null keys = 0, and the edge count should line up with the status nodes that actually exist.

Run that next and send me the numbers.