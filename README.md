Yep — the screenshot confirms it. All six component-branch registry rows are active now, including props[], links[], responsible-roles[], and protocols[].

So we can stop touching IS_ACTIVE. That is not the problem.

The next thing to prove is whether the mapper actually has data available to create those deeper children. Your CSV inspection already showed mappings for components[] / components[].component, but not mappings owned by props[], links[], etc.

Next step only: inspect one component payload

Run this read-only cell after Cell 7:

from snowflake.snowpark.functions import col

(
    final_nodes_df
    .filter(
        col("NODE_PATH") ==
        "system-security-plan.system-implementation.components[].component"
    )
    .select(
        "SOURCE_RECORD_ID",
        "ELEMENT_TYPE",
        "NODE_PATH",
        "ELEMENT_JSON"
    )
    .show(5, truncate=False)
)

I want to see what is actually inside ELEMENT_JSON for a component.

That will answer the key question:

Are props, links, responsible-roles, and protocols physically present inside the component payload, or do we need to obtain them from another Archer source/reference?

Don't change Cell 5 or the registry again yet. Send me that output and we'll make the next decision from evidence.