Yes — next step is to stop touching the core blindly and prove exactly what the active registry is feeding into the mapper for the SSP component branch.

Run this one read-only check in the notebook:

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

What I want to see is whether the notebook currently has all of these active:

components[]
components[].component
component.props[]
component.links[]
component.responsible-roles[]
component.protocols[]

If the notebook shows only components[] and component, then the immediate fix is registry activation, not Cell 5.

If it shows all six, then we go straight to the next issue: mapping ownership / instance creation below component.

Do only this now and send me the result.