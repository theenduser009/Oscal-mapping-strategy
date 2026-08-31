Yes — it does look like METADATA_JSON is just repeating SOURCE_RECORD_ID, and that is suspicious. We should not mark document-ids[].identifier Done yet.

The next thing is to find exactly which Archer source field is mapped to that OSCAL path.

Run this in the notebook:

(
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH")
        == "system-security-plan.metadata.document-ids[].identifier"
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE"
    )
    .show(truncate=False)
)

That will tell us the actual Archer field feeding identifier.

Then we take one SOURCE_RECORD_ID from your screenshot, for example 8167163, and compare:

Raw Archer value from that mapped source field
vs.
DIM METADATA_JSON = 8167163

If the raw field is also 8167163, then this mapping is correct.

If the raw field is something else, then we found a bug in how document-ids[] is being constructed.

So right now: document-ids = not verified yet. Run the mapping lookup above first.