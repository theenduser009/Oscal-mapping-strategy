Start with a read-only branch audit of the SSP component path.

We already know the notebook baseline is healthy and the graph validates. The open question is specifically why the relationship tree stops at:

system-implementation → components

instead of continuing through:

components → component → props / links / responsible-roles / protocols

So the next step is not to change Cells 1–7. Add one temporary diagnostic cell after Cell 7 and inspect what the graph builder actually produced for that branch.

Use this:

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
    col("SOURCE_NODE_PATH").contains(
        "system-security-plan.system-implementation.components"
    )
    |
    col("TARGET_NODE_PATH").contains(
        "system-security-plan.system-implementation.components"
    )
).group_by(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).count().sort(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).show()

Keep EXECUTE_WRITES = False.

This will tell us exactly whether the problem is:

the deeper nodes are not being created, or

the nodes exist but Cell 5 is not creating their parent→child edges.


Run only this and send me the output. Then we’ll know the exact next code change.