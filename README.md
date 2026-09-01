prop_fields = [
    "FISMA_REPORTABLE",
    "FINANCIAL_SYSTEM",
    "MISSION_CRITICAL",
    "CRITICAL_INFRASTRUCTURE",
    "PACKAGE_TYPE",
    "HELPER_PTA_CALC",
    "PACKAGE_TYPE_HELPER_CALC",
    "PIA_REQUIRED"
]

for field in prop_fields:
    print("\n===", field, "===")
    (
        raw_df
        .select("CONTENT_ID", "CURATED_JSON")
        .filter(col("CURATED_JSON").is_not_null())
        .limit(10)
        .show()
    )