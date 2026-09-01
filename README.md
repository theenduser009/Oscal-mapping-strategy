from snowflake.snowpark.functions import col

(
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH")
        .startswith("system-security-plan.system-characteristics")
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