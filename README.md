Good — this run is structurally healthy. ✅

From the screenshot:

Nodes              ≈ 59,232
Edges              ≈ 56,013

Null node keys       0
Duplicate node keys  0
Null edge keys       0
Duplicate edge keys  0
Missing parents      0
Missing children     0

Validation PASSED
EXECUTE_WRITES = False

So activating component did not break the graph.

One thing I do not want to ignore: these totals are materially different from the earlier 92,880 / 90,715 run. We should not guess why yet.

Next — check only our component branch

Run this temporary read-only cell:

from snowflake.snowpark.functions import col

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

What we want now is:

components
component       ← this MUST appear now
props
links
responsible-roles
protocols

Don't change Cells 1–7 and keep EXECUTE_WRITES = False.

Run just this and show me the output. Then we know whether the component layer is actually being built now.