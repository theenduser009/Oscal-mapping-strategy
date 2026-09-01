Next target: finish the remaining SSP Transform mappings before touching Reference again.

We have already verified these areas in actual Snowflake data:

metadata.published / last-modified ✅

metadata.document-ids[].identifier ✅

FIPS-199 security-impact-level ✅

5 approved metadata.responsible-parties[] transforms ✅

4 responsible-party rows marked TBD stay parked

Reference traversal (components[], etc.) is Phase 2 and partially explored, but not finished


So now we need one clean inventory of what Transform mappings remain that are neither Done nor TBD.

Run this read-only notebook cell:

from snowflake.snowpark.functions import col

(
    canonical_mapping_df
    .filter(
        col("MAPPING_TYPE") == "Transform"
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE"
    )
    .distinct()
    .sort(
        "OSCAL_ELEMENT_PATH",
        "SOURCE_FIELD_NAME"
    )
    .show(200, 250)
)

Then we will cross out the ones already completed:

metadata.published
metadata.last-modified
metadata.responsible-parties[]

and whatever remains becomes our exact next build list.

I would not go back to components/reference yet. First close the remaining non-TBD Transform mappings, mark them Done in your Excel, then move into Reference Phase 2 with a clean boundary.