# Control Implementation fast-batch PREVIEW passed — 2026-09-24

## Repository basis
- Branch: simplify-metadata-boundary
- Head inspected before this checkpoint: 364393b33d625199d6b7de2ca36e8583e25e6e1d
- Mapping CSV blob: 766f56d90b1f21c1f59e532fa3dc6225f3e91079
- Current approved Control Implementation property mappings: 16 rows to system-security-plan.system-characteristics.props[].

## Owner-provided Snowflake PREVIEW evidence
Screenshot shows:
- mode = PREVIEW
- status = PREVIEW_COMPLETE
- source = source-one
- model = SSP
- release = oscal-lean-daily-v3.1
- source_records = 2,813
- nodes = 520,579
- edges = 517,766
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
- DIM: INSERTS 269,735; UPDATES 0; UNCHANGED 250,844
- FACT: INSERTS 269,735; UPDATES 0; UNCHANGED 248,031

Arithmetic:
- 269,735 + 250,844 = 520,579 DIM rows
- 269,735 + 248,031 = 517,766 FACT rows

## Interpretation
The current seven-cell graph validates cleanly with the seven-field fast batch. The 16 Control Implementation rows targeting system-characteristics.props[] are already present in the maintained CSV; they are not 16 additional rows still waiting to be mapped.

This PREVIEW includes the latest five newly approved package-property mappings plus the two newly approved responsible-party mappings from the fast batch, along with all previously accepted SSP mappings.

No target DML occurred in this PREVIEW.

## Next action
In the SAME notebook session and without rerunning Cells 1-6 or refreshing source/mapping snapshots, change only Cell 7 to OSCAL_LOAD_MODE="COMMIT" and run Cell 7 once.

Do not run cleanup, RUN_NOW.py, COMMIT_NOW.py, or another profiler. Return the COMMIT/read-back report.

If COMMIT succeeds with COMMITTED_AND_VERIFIED and zero post-commit changes, this 16-prop current mapping state is finished for today.
