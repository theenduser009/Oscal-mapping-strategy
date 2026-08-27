Yep — now the error tells us exactly what's wrong. The column is quoted/case-sensitive.

Snowflake says the actual identifiers are:

"SOURCE_FIELD_NAME", "OSCAL_ELEMENT_PATH", "OSCAL_MODEL", "MAPPING_TYPE", "TRANSFORMATION_LOGIC"

So Snowpark's col("OSCAL_ELEMENT_PATH") is resolving incorrectly against this quoted dataframe.

Use this instead — only change this test cell:

# READ ONLY — test SSP component mappings

component_mappings = canonical_mapping_df.filter(
    canonical_mapping_df['"OSCAL_ELEMENT_PATH"'].contains(
        "system-implementation.components"
    )
)

component_mappings.show()

Do not change anything else yet.

Also, important correction from my last response: SOURCE_FIELD_NAME does exist. The error itself confirms it. The issue is the quoted identifier, not a missing column.

Run this and show me the result. If it returns 0, that's actually useful—we'll then inspect the exact SSP paths present in the canonical mapping rather than guessing another path.