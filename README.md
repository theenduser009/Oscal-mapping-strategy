Yes! This result isolates the problem nicely. 🔎

After the fresh run, the component branch contains only:

ELEMENT_TYPE    COUNT
components      4792

So build_oscal_graph() is not creating:

component
props
links
responsible-roles
protocols

That means the registry itself is no longer our main suspect. The issue is inside the graph builder's collection → child handling. This also fits the code you showed earlier: Cell 5 has explicit restrictions around nested collection lineage and parent instances.

Next step only

Before changing the whole Cell 5 function, I want to inspect the metadata values the builder is actually receiving for these six registry rows.

Run this read-only cell:

from snowflake.snowpark.functions import col

(
    element_registry_df
    .filter(
        col("NODE_PATH").like(
            "system-security-plan.system-implementation.components%"
        )
    )
    .select(
        "NODE_PATH",
        "ELEMENT_TYPE",
        "PARENT_NODE_PATH",
        "IS_COLLECTION",
        "INSTANCE_KEY_RULE",
        "ITEM_PATH",
        "PROCESS_ORDER",
        "IS_ACTIVE"
    )
    .sort("PROCESS_ORDER", "NODE_PATH")
    .show(50)
)

Send me that output.

Don't change Cell 5 yet. Once I see IS_ACTIVE, PROCESS_ORDER, ITEM_PATH, and INSTANCE_KEY_RULE for all six, we can determine exactly why the builder stops at components[] and then I'll give you the corrected whole Cell 5 function, not little patches.