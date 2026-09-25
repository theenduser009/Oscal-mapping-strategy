# Source One Assessment Results final-field PREVIEW passed — 2026-09-25

## Repository basis
- Branch: simplify-metadata-boundary
- Head inspected before checkpoint: cdc3f3b70cff2122de6b9f2e7b52568c4022794c

## Owner-provided Snowflake PREVIEW evidence

### Source One / Assessment Results
- mode = PREVIEW
- status = PREVIEW_COMPLETE
- source = source-one
- model = ASSESSMENT_RESULTS
- release = oscal-lean-daily-v3.1
- source_records = 2,813
- nodes = 109,630
- edges = 106,817
- pre_write_validation_passed = true
- validation_passed = true
- storage_verified = true
- writes_executed = false
- persisted = false
- committed = false
- target_dml_attempted = false
- route status = PREVIEW_PASSED_NO_TARGET_DML

Expected changes:
- DIM: INSERTS 3,129 / UPDATES 0 / UNCHANGED 106,501
- FACT: INSERTS 3,129 / UPDATES 0 / UNCHANGED 103,688

Exact reconciliation:
- FINDINGS null-preserved result property: 2,813 new property nodes
- RISK_ASSESSMENT_REPORT populated source arrays: 316 new property nodes
- 2,813 + 316 = 3,129

The PREVIEW proposes exactly 3,129 new DIM rows and 3,129 new FACT edges, with no updates. This exactly matches the two final AR source-preservation mappings.

### Source Two / Assessment Results
The same selected model also executed source-two-source / ASSESSMENT_RESULTS:
- source_records = 148
- nodes = 1,460
- edges = 1,312
- expected changes: zero inserts/updates; all unchanged
- route status = PREVIEW_PASSED_NO_TARGET_DML

This Source Two route is not part of the Source One closeout claim.

## Interpretation
The Source One AR final mappings are PREVIEW-validated and fully reconciled:
- RISK_ASSESSMENT_REPORT -> results[].props[] via stable json-text
- FINDINGS -> results[].props[] with explicit JSON-null preservation

No native findings[] nodes are emitted because current source contains no finding identity/content.

## Next action
In the same notebook session, change only Cell 7 to OSCAL_LOAD_MODE="COMMIT" and run Cell 7 once.

Expected post-commit readback for Source One AR if successful:
- DIM: INSERTS 0 / UPDATES 0 / UNCHANGED 109,630
- FACT: INSERTS 0 / UPDATES 0 / UNCHANGED 106,817
- status = COMMITTED_AND_VERIFIED

Do not rerun Cells 1-6, refresh source/mapping snapshots, or run cleanup before this commit.
