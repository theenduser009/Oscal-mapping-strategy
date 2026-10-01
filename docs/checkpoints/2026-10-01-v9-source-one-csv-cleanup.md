# V9 Source One mapping CSV cleanup — 2026-10-01

Supersedes the CSV shape used by the namespace-free v8 SSP COMMIT, but does not
supersede that commit/read-back evidence for the v8 target state.

Base repository head inspected before change:
da2c44f4725346c64d77117035ce99f37575b5e1

Owner goal:
reduce mapping-sheet clutter without hiding real mapping behavior in Python.

Changes:
- removed SOURCE_KEY from the Source One CSV; the file/profile is already the source boundary
- normalized OSCAL_MODEL to canonical keys: SSP, ASSESSMENT_RESULTS, POAM,
  SECURITY_ASSESSMENT_PLAN, PROFILE
- moved NOTES to the last column; NOTES remains human-only
- blanked default LINEAGE_REQUIRED=N values; only 12 Y values remain visible
- blanked default VALUE_SOURCE=FIELD values; only 4 CONFIG exceptions remain visible
- blanked default VALUE_REQUIRED=false values; only 5 true exceptions remain visible
- retained DESCRIPTION_REQUIRED because it changes lookup/hydration behavior
- retained all transform-, role-, reference-, lookup- and crosswalk-specific columns
- retained all 155 rows, execution statuses, paths, transforms and mapping semantics
- archived the exact v8 committed/read-back-verified CSV before replacement
- bumped mapper compatibility release to lean-csv-registry-v9-clean-mapping

No Snowflake DML was performed by this repository update.

Evidence boundary:
v8 is committed/read-back verified. V9 is a new mapping artifact and must pass a
fresh SSP PREVIEW before any additional COMMIT. If V9 produces only unchanged
rows, that will prove this cleanup is behavior-preserving against the committed
v8 target.
