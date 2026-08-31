Great — freeze security-impact-level now. That branch is done for this phase. ✅

Next, we should stay in the Direct/Transform bucket and find the next OSCAL path instead of jumping to Reference yet.

Run this in a new Python cell:

print("=== REMAINING DIRECT/TRANSFORM PATHS ===")

(
    canonical_mapping_df
    .filter(
        col("MAPPING_TYPE") == "Direct/Transform"
    )
    .select(
        "OSCAL_ELEMENT_PATH",
        "SOURCE_FIELD_NAME"
    )
    .distinct()
    .sort("OSCAL_ELEMENT_PATH")
    .show(200, truncate=False)
)

We already finished the paths ending in:

security-objective-confidentiality
security-objective-integrity
security-objective-availability

So show me the output from that cell. We’ll pick the next Direct/Transform path and finish it, one branch at a time. No more touching this security-impact code.