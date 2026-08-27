Yes — I see it. 👍

After rerunning, the result is still:

Nodes : 59,232
Edges : 56,419

Null node keys      : 0
Duplicate node keys : 0
Null edge keys      : 0
Duplicate edge keys : 0
Missing parents     : 0
Missing children    : 0

Validation PASSED
Writes: False

So refreshing the registry did not change the graph. That tells us the issue is not stale element_registry_df.

Next step — one diagnostic only

Now we need to determine whether those deeper component paths are actually being processed by build_oscal_graph().

Add one temporary Python cell after Cell 7:

from snowflake.snowpark.functions import col

print("=== COMPONENT BRANCH AFTER FRESH RUN ===")

(
    final_nodes_df
    .filter(
        col("NODE_PATH").like(
            "system-security-plan.system-implementation.components%"
        )
    )
    .group_by("NODE_PATH", "ELEMENT_TYPE")
    .count()
    .sort("NODE_PATH")
    .show(50)
)

This is read-only.

I expect this to tell us immediately whether the fresh graph contains:

components[]
components[].component
components[].component.props[]
components[].component.links[]
components[].component.responsible-roles[]
components[].component.protocols[]

Send me that output. Don't modify Cell 5 yet. We're narrowing this down properly now. 🔎