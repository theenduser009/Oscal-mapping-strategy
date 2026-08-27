Excellent — the new Cell 5 runs cleanly. 🎯

And there is an important change:

Before the Cell 5 replacement:

Nodes : 59,232
Edges : 56,013

After:

Nodes : 59,232
Edges : 56,419
                     +406 edges

Nodes stayed exactly the same, while 406 additional valid relationships were created. And all integrity checks remain zero.

That means the new lineage logic is doing something useful, but we still need to confirm it is the relationship we intended rather than assume.

Next: inspect only our branch

Run this after Cell 7:

from snowflake.snowpark.functions import col

print("=== COMPONENT BRANCH NODES ===")

final_nodes_df.filter(
    col("ELEMENT_TYPE").isin(
        "components",
        "component",
        "props",
        "links",
        "responsible-roles",
        "protocols"
    )
).group_by(
    "ELEMENT_TYPE"
).count().sort(
    "ELEMENT_TYPE"
).show()


print("=== COMPONENT BRANCH EDGES ===")

final_edges_df.filter(
    col("SOURCE_NODE_PATH").like(
        "%system-security-plan.system-implementation.components%"
    )
    |
    col("TARGET_NODE_PATH").like(
        "%system-security-plan.system-implementation.components%"
    )
).group_by(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).count().sort(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).show()

The crucial result is whether we now have:

components[] → component
component    → props[]

and their counts.

Still don't enable writes. Once we see those edges, we'll know whether this branch is genuinely fixed or whether Cell 5 needs one more adjustment.