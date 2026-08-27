Good — Samples found: 0 means the problem is simply that COMPONENTS is not the Archer source-field name in source_df. We shouldn't guess it.

Since the graph already contains system-implementation → components, let's ask the mapping itself which Archer field(s) created that node.

Run this next — READ ONLY

# ============================================================
# SSP — Find mappings that created components[]
# READ ONLY
# ============================================================

component_mappings = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH").contains(
            "system-implementation.components"
        )
    )
)

component_mappings.select(
    "SOURCE_FIELD_NAME",
    "OSCAL_ELEMENT_PATH",
    "MAPPING_TYPE"
).show(100, truncate=False)

This should tell us something like:

SOURCE_FIELD_NAME       OSCAL_ELEMENT_PATH
---------------------   --------------------------------------------
<actual Archer field>   ...system-implementation.components[]

Don't change anything else.

Once we know the actual source field name, we'll inspect that field's raw value and continue:

system-implementation
        ↓
components[]
        ↓
component
        ↓
props[] / links[] / ...

That gets us back onto the real SSP data instead of guessing field names.