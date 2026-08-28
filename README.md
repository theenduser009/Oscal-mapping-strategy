Perfect — now we have the next active level clearly. ✅

Under:

system-security-plan.system-implementation.components[].component

you have four active collection children:

props[]
links[]
responsible-roles[]
protocols[]

This matches what we expected from the earlier registry work.

The best next move is to validate component itself first, because it is the structural parent of all four collections. We should make sure its node count, uniqueness, and edges from components[] are correct before going into the children.

Run this read-only cell:

from snowflake.snowpark.functions import col

print("=== COMPONENT NODE GRAPH CHECK ===")

component_path = (
    "system-security-plan.system-implementation.components[].component"
)

component_df = final_nodes_df.filter(
    col("NODE_PATH") == component_path
)

print("Total component nodes:")
print(component_df.count())

print("Distinct NODE_KEYs:")
print(
    component_df
    .select("NODE_KEY")
    .distinct()
    .count()
)

print("Null NODE_KEYs:")
print(
    component_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

print("\nEdges into component:")
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == component_path)
    .group_by(
        "SOURCE_NODE_PATH",
        "TARGET_NODE_PATH"
    )
    .count()
    .show()
)

I expect the relationship to be:

components[]
    →
component

and likely the node count will align with the 4,792 component collection instances, but don’t assume it — let the output prove it.

If that passes, then we’ll test the four child collections one at a time, starting with component.props[].