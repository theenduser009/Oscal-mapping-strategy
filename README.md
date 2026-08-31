Yes — the rows in your screenshot are worth checking next, and I agree: the timestamp transformation should be straightforward.

From the screenshot, the main unfinished group is:

metadata.published and metadata.last-modified
→ Mapping_Type = Transform
→ Convert timestamp to OSCAL DateTimeWithTimezoneDatatype

We should not mark them Done yet. We can test one real SSP record first, exactly like we did with the FIPS-199 fields.

Next step only

Let's inspect what the actual source values look like before changing any function.

In a new Python cell, run:

# Check actual source values for OSCAL metadata timestamps

node_path = "system-security-plan.metadata"

mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    CONFIG["OSCAL_MODEL"]
)

(
    mappings
    .filter(col("MAPPING_TYPE") == "Transform")
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "OSCAL_DATA_TYPE",
        "TRANSFORMATION_LOGIC"
    )
    .show()
)

Send me the output.

Then we'll pick one published / last-modified source field, inspect its real value, and determine whether our existing builder already handles it or whether we need one small timestamp-transform function. No changes yet.