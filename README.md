Yes — this answers our Reference question. Tim is recommending that we resolve the Archer references, not merely store the LevelId/ContentId pair.

His intended flow is:

SSP → System Implementation → Archer FK → referenced Archer record → continue resolving FKs recursively → leaf node → map back into OSCAL Component elements.

And importantly, he says to keep the component associated with the SSP, using a UUID/link, rather than resolving it independently upstream where we could lose the relationship back to the originating SSP.

So our design for Reference should be:

SSP record
   ↓
components[] reference
   ↓
LevelId + ContentId
   ↓
determine referenced Archer table
   ↓
retrieve ContentId record
   ↓
does that record contain another FK?
   ├─ YES → resolve next LevelId + ContentId
   └─ NO  → leaf reached
                ↓
        build OSCAL component
                ↓
        create DIM nodes + FACT relationships
                ↓
        retain relationship to originating SSP

One important change from what we were considering

Do not create a fake components[] payload just from LevelId/ContentId.

Those are traversal information. The real OSCAL component should be built from the resolved Archer data. We should preserve LevelId/ContentId as lineage/source metadata, but they aren't the OSCAL component themselves.

And Tim specifically says one layer at a time until the leaf, which fits beautifully with the generic registry/graph approach we've already built.

Next step — inspection only

Before writing the resolver, let's see exactly what our six Reference mappings contain.

Run one new cell:

from snowflake.snowpark.functions import col

print("=== REFERENCE MAPPINGS ===")

(
    canonical_mapping_df
    .filter(col("MAPPING_TYPE") == "Reference")
    .select(
        "OSCAL_ELEMENT_PATH",
        "SOURCE_FIELD_NAME",
        "SOURCE_FIELD_ID"
    )
    .distinct()
    .sort("OSCAL_ELEMENT_PATH", "SOURCE_FIELD_NAME")
    .show(100, truncate=False)
)

Don't change Cells 1–7 yet. Show me that output. Then we'll determine exactly which Archer fields provide the LevelId and ContentId and build the resolver from there.