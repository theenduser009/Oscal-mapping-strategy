Yeah — we’ve confirmed the real problem now. The fresh Cell 7 run still gives exactly:

Nodes : 59232
Edges : 56419
Validation PASSED

So we should stop rerunning Cell 7. Activating the registry rows did not change the graph.

The important clue from our earlier diagnostic was this:

props[]               Mapping count: 0
links[]               Mapping count: 0
responsible-roles[]   Mapping count: 0
protocols[]           Mapping count: 0

That matters because Cell 5 calls _get_collection_instances(...). For these collection nodes, it needs mappings to find the source values. No owned mappings → no collection instances → no nodes → no new edges.

So the next step is not changing Cell 5 yet. We first need to see what component-related paths actually exist in your canonical mapping CSV.

Run this one read-only diagnostic cell:

# ================================================================
# READ ONLY - Find component mappings in canonical mapping
# ================================================================

from snowflake.snowpark.functions import col

print("=== COMPONENT MAPPINGS IN CSV ===")

(
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH")
        .like("%system-implementation%component%")
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE",
        "TRANSFORMATION_LOGIC"
    )
    .sort("OSCAL_ELEMENT_PATH")
    .show(200)
)

What we're looking for

We need to see whether your CSV actually contains paths resembling:

system-security-plan.system-implementation.components[].component.props[]
system-security-plan.system-implementation.components[].component.links[]
system-security-plan.system-implementation.components[].component.responsible-roles[]
system-security-plan.system-implementation.components[].component.protocols[]

If that cell returns nothing or the paths are slightly different, we’ve found the bottleneck.

Do only this now and send me the output. No more Cell 7 reruns and no changes to the production functions until we see this result.