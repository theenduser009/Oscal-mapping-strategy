(
    canonical_mapping_df
    .filter(col("OSCAL_ELEMENT_PATH") ==
            "system-security-plan.system-characteristics.props[]")
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE"
    )
    .distinct()
    .sort("SOURCE_FIELD_NAME")
    .show(100, 250)
)