# Level-355 direct package join evidence — 2026-09-24

## Owner-provided live Snowflake evidence
The owner ran a direct join between:
- ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW s
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW p
- ON p.CONTENT_ID = s.CONTENT_ID

The query returned 1,895 distinct matched CONTENT_ID values in the earlier grouped view.

A 20-row detail sample for one matched CONTENT_ID showed:
- the same package CONTENT_ID repeated across multiple control rows;
- CONTROL_NUMBER varies per row (for example 03.08.01, 03.08.02, ...);
- CONTROL_NAME varies per row and contains the control title;
- ALLOCATED_CONTROL_ID varies per row and contains a package/control-set-specific identifier;
- AUTHORIZATION_PACKAGE contains the same package identifier;
- IMPLEMENTATION_DETAILS and IMPLEMENTATION_STATUS were null in the displayed sample.

## Interpretation
This is strong current-runtime evidence that:
- top-level CONTROL_RAW.CONTENT_ID is package-grain lineage, not the per-control identity;
- one Authorization Package can own many Level-355 control rows;
- ALLOCATED_CONTROL_ID is a strong candidate for per-control row identity, pending uniqueness/null verification;
- CONTROL_NUMBER is the leading candidate for OSCAL implemented-requirement.control-id, pending catalog/profile identifier compatibility;
- CONTROL_NAME should not be used as the control identity;
- implementation description/status mapping must be based on actual population across the full matched dataset, not the displayed null sample.

## Next action
Published:
`sql/validation/2026-09-24_level355_control_identity_and_field_profile.sql`

Run it to establish:
1. row/package/allocated-control cardinality;
2. ALLOCATED_CONTROL_ID uniqueness;
3. population counts for implementation fields;
4. reverse AUTHORIZATION_PACKAGE consistency;
5. sample rows where implementation-related fields are actually populated.

No mapper change should be made until this identity/profile check returns.
