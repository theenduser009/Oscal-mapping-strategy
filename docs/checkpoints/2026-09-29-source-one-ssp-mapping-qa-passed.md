# Source One SSP mapping QA passed with no populated-source target gaps

Date: September 29, 2026
Status: Owner-posted output from notebooks/validation/14_source_one_mapping_qa.py reviewed for the currently selected SSP route. Read-only QA only; no target DML occurred.

## Repository basis

- Branch: simplify-metadata-boundary
- QA script: notebooks/validation/14_source_one_mapping_qa.py
- QA script blob: 5b14c6d9b9ab46c3f41a40fc9e569a1a797e41d5
- Prior SSP party-name enrichment is already COMMITTED_AND_VERIFIED.

## Owner-posted SSP QA summary

- MODELS_VALIDATED = SSP
- ACTIVE_MAPPING_ROWS = 89
- TARGET_EVIDENCE_PRESENT = 48
- RELATIONSHIP_EXCEPTION_EVIDENCE_PRESENT = 9
- SUPPORT_CONFIG_NOT_ARCHER_FIELD = 2
- NO_POPULATED_SOURCE_DATA = 24
- NO_POPULATED_SOURCE_DATA_META_FIELD_NOT_FOUND = 6
- ATTENTION_ROWS = 15
- DISPOSITION_ROWS = 16

Sample value verification:
- 15 deterministic Content IDs
- 427 source-to-target value checks
- MATCH = 427
- no MISMATCH was reported

## Interpretation

No active SSP mapping row with populated source data was reported as POPULATED_SOURCE_TARGET_EMPTY.

The 15 attention rows are not target-mapping failures:
- 9 are Archer relationship/reference exceptions with target evidence present;
- 6 are current-source-empty fields whose Archer Meta Field lookup was not found.

The six no-data / Meta Field not-found rows visible in the owner output are:
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED
- CURRENT_CONTROL_RISK_THRESHOLD
- EXPORT_CONTROLLED_DATA_ITARAR_IF_APPLICABLE
- OF_SATISFIED_CONTROLS

Because SOURCE_POPULATED = 0 for these rows, this is not evidence of a broken mapping and does not count as a tested populated mapping. They remain traceability/data-availability items for mapping-owner review.

The 9 relationship exceptions include populated field types 9/23 and were intentionally validated as relationship/reference evidence rather than forced through scalar equality.

The 16 disposition rows remain outside approved executable mappings and include:
- RECOMMENDED_SECURITY_CATEGORY = BLOCKED_IF_POPULATED
- ADD_OVERLAY = DEFERRED
- BASELINE_RECOMMENDATION = DEFERRED
- the remaining explicit EXCLUDED helper/control fields.

## Current SSP QA conclusion

For the currently populated SSP scalar/non-reference scope:
- target evidence exists;
- 427 sampled source-to-target values matched;
- no sampled mismatch was reported;
- no populated-source target-empty condition was reported.

This closes the SSP read-only mapping QA gate for the current Source One snapshot, while preserving the six no-source/meta-field gaps as unresolved traceability items rather than false failures.

## Next action

Run the same read-only QA gate for Source One Assessment Results next. Do not rerun Matillion. Change the notebook selector to ASSESSMENT_RESULTS, run the normal PREVIEW route, then run notebooks/validation/14_source_one_mapping_qa.py and review its exceptions before moving to POAM and Security Assessment Plan.
