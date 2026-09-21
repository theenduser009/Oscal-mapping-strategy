# Source-system boundary clarification — 2026-09-21

## Owner-confirmed architecture boundary

The owner clarified the role of the Archer structured/STG tables during Source One
Assessment Results investigation.

Confirmed for current OSCAL work:

- `*_STG` tables are historical-system/staging artifacts and are not part of the
  future OSCAL runtime source contract.
- Historical structured Archer tables such as
  `ARCHER_CONTENT_AUTHORIZATION_PACKAGE` may be inspected for discovery or
  historical context only.
- They must not be treated as the authoritative production input for the OSCAL
  mapper simply because a convenient typed column exists there.
- Source One runtime remains the current raw/curated-json route:
  `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`.
- The mapper continues to build the curated OSCAL graph into the configured OSCAL
  DIM/FACT targets; historical Archer tables are not future OSCAL target tables.
- Archer metadata tables (for example `ARCHER_META_FIELD`,
  `ARCHER_META_LEVEL`, `ARCHER_META_VALUE`) remain valid discovery/reference
  metadata when needed to interpret source semantics.

## Current Assessment Results implication

For `RISK_ASSESSMENT_REPORT`, historical structured/STG columns can help explain
legacy field semantics, but final runtime mapping must be based on the current
Source One raw payload plus authoritative Archer metadata and the OSCAL model
contract. Do not add a dependency on the historical structured/STG tables.

This clarification supersedes any prior suggestion to use
`ARCHER_CONTENT_AUTHORIZATION_PACKAGE_STG` as part of the runtime mapping path.

No Snowflake data or mapper code was changed by this checkpoint.
