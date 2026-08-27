Good — this is very useful. component is still not being created. We still have only:

components   47,792
props        15,120

So activating the registry row alone did not solve it. That means we now need to check what Cell 5 actually receives in memory before touching any code.

Run only this read-only diagnostic:

from snowflake.snowpark.functions import col

element_registry_df.filter(
    col("NODE_PATH") ==
    "system-security-plan.system-implementation.components[].component"
).select(
    "NODE_PATH",
    "ELEMENT_TYPE",
    "PARENT_NODE_PATH",
    "IS_COLLECTION",
    "INSTANCE_KEY_RULE",
    "ITEM_PATH",
    "IS_ACTIVE"
).show()

I want to see whether the notebook's element_registry_df itself contains:

components[].component
IS_ACTIVE = TRUE

Why this matters: the Snowflake table may now say TRUE, but if Cell 2 was not refreshed after the UPDATE, the notebook can still be holding the old dataframe state.

Don't change Cells 4 or 5 yet. Send me this one output next. If it shows TRUE, then we go directly inside the Cell 5 structural-parent logic — I already see a likely issue there involving is_collection_node() and the [] in the ancestor path.