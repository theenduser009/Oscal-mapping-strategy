# Source One Control Implementation final populated-arrays PREVIEW passed — 2026-09-25

## Repository basis
- Branch: simplify-metadata-boundary
- Head inspected before checkpoint: d47e80942d4b49c3d513a0ead7000fefde53fb29
- Latest mapping change for the two remaining populated Control Implementation arrays was already committed before this PREVIEW.

## Owner-provided Snowflake PREVIEW evidence
Screenshot shows:
- mode = PREVIEW
- status = PREVIEW_COMPLETE
- source = source-one
- model = SSP
- release = oscal-lean-daily-v3.1
- source_records = 2,813
- nodes = 521,482
- edges = 518,669
- pre_write_validation_passed = true
- validation_passed = true
- storage_verified = true
- writes_executed = false
- persisted = false
- committed = false
- target_dml_attempted = false
- route status = PREVIEW_PASSED_NO_TARGET_DML
- temporary_cleanup = REMOVED

Expected changes:
- DIM: INSERTS 903; UPDATES 0; UNCHANGED 520,579
- FACT: INSERTS 903; UPDATES 0; UNCHANGED 517,766

## Exact reconciliation
The immediately prior owner-provided source-shape query established:
- INHERITABLE_CONTROLS: 877 INTEGER array items
- ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS: 26 INTEGER array items

877 + 26 = 903.

The PREVIEW proposes exactly 903 new DIM rows and 903 new FACT edges, with zero updates. This exactly reconciles the two new property mappings to the profiled current-source item population.

No target DML occurred in this PREVIEW.

## Current Control Implementation status
- APPROVED: 22
- EXCLUDED: 10
- DEFERRED: 12
- Total runtime rows: 44

The 12 deferred rows had no populated values in the most recent all-remaining-field Source One profile. No values are fabricated for them.

## Next action
In the SAME notebook session and without rerunning Cells 1-6 or refreshing source/mapping snapshots, change only Cell 7 to OSCAL_LOAD_MODE="COMMIT" and run Cell 7 once.

Expected post-commit readback if successful:
- DIM: INSERTS 0; UPDATES 0; UNCHANGED 521,482
- FACT: INSERTS 0; UPDATES 0; UNCHANGED 518,669
- status = COMMITTED_AND_VERIFIED

After that, proceed to the final all-Source-One PREVIEW/COMMIT across SSP, ASSESSMENT_RESULTS, POAM, and SECURITY_ASSESSMENT_PLAN.
