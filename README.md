Yes — this is a clean pass. 🎯

Your result shows:

system-ids[] nodes = 2813
system-characteristics → system-ids[] edges = 2813

That is especially strong because your Authorization Package source has 2,813 records. So structurally:

2813 source records
      ↓
2813 system-characteristics
      ↓
2813 system-ids[] nodes
      ↓
2813 parent → child edges

So we can mark system-ids[] as validated: payload ownership works, node generation works, and parent-child edge generation works.

Next: props[]

This one is more important because it's a true extension-property collection. Your mapping showed roughly 10 Archer fields owned by props[], including PACKAGE_TYPE, FISMA_REPORTABLE, MISSION_CRITICAL, etc.

Before changing anything, let's inspect what the graph currently generated.

Run only:

from snowflake.snowpark.functions import col

props_path = "system-security-plan.system-characteristics.props[]"

print("=== PROPS GRAPH CHECK ===")

(
    final_nodes_df
    .filter(col("NODE_PATH") == props_path)
    .group_by("NODE_PATH", "ELEMENT_TYPE")
    .count()
    .show()
)

(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == props_path)
    .group_by("SOURCE_NODE_PATH", "TARGET_NODE_PATH")
    .count()
    .show()
)

Don't change the mapper yet.

This result is going to be interesting: if we get only 2813 props[] nodes despite potentially multiple populated extension properties per Authorization Package, we need to examine whether we're incorrectly collapsing multiple OSCAL prop objects into one node.