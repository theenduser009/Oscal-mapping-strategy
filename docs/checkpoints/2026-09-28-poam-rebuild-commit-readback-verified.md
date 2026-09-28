# POAM rebuild committed and read-back verified; whole-table QA pending

Evidence date: September 28, 2026.
Repository: theenduser009/Oscal-mapping-strategy.
Branch: simplify-metadata-boundary.
Head inspected before this update: 2b9ec6d652d78c9341d30fa94a766600b570c3a1.
New QA SQL commit: 7c0e3391fc9c6c9c1a90933486335ba8ef1d5dc7.
SQL path: sql/qa/POAM_POST_REBUILD_QA_2026-09-28.sql.
SQL blob read back: cbc5976391adb791420908dde6e6f657e222ddde, matching the locally tested file.

## New owner-provided COMMIT evidence
The September 28 screenshot shows OSCAL_PIPELINE_REPORT with overall mode COMMIT and status COMMITTED_AND_VERIFIED. The displayed route is source-one / POAM; release is oscal-lean-daily-v3.1.

Route flags: writes_executed, persisted, committed, target_dml_attempted, pre_write_validation_passed, validation_passed and storage_verified are all true.

Source records: 2,813. Nodes: 2,821. Edges: 8.

| Phase | DIM inserts | DIM updates | DIM unchanged | FACT inserts | FACT updates | FACT unchanged |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Expected changes in successful committed run | 2821 | 0 | 0 | 8 | 0 | 0 |
| Post-commit verification | 0 | 0 | 2821 | 0 | 0 | 8 |

Route status is COMMITTED_AND_VERIFIED; temporary_cleanup is REMOVED. This is a new committed/readback result, not a reuse of September 25 acceptance or the earlier PREVIEW.

The image is owner-provided evidence, not a live query executed by this chat. It identifies the loader release but does not embed an exact notebook Git SHA or independently establish the full table contents. No private screenshot or source record value is published in this checkpoint.

## Supersession and limits
This supersedes the rebuild-PREVIEW/COMMIT-pending status in docs/checkpoints/2026-09-28-poam-only-rebuild-approved.md and the later project-only truncation/preview checkpoints. Do not request another truncation or repeat COMMIT for this accepted batch.

The earlier table-wide finding of 2,575 fully disconnected POAM FACT rows remains historical evidence. The current repair's batch is verified, but removal of every old orphan from the full table is not yet established by this batch-scoped report. The already-identified Cell 6 whole-table orphan-validation gap is not fixed by reloading data or by adding a standalone SQL file.

Current states:
- Approved POAM mapping reused; no new mapping or item-detail hydration.
- Rebuild batch committed and read-back verified.
- Post-rebuild whole-table graph checks pending.
- Historical orphan root cause unestablished; owner chose replacement rather than recovery.
- Loader prevention fix and full OSCAL document conformance remain separate work.
- SSP, Assessment Results, Assessment Plan and Catalog are outside this recovery action; no reload is requested.

## Next action prepared
Run the entire sql/qa/POAM_POST_REBUILD_QA_2026-09-28.sql as-is. It is one SELECT reading only the complete POAM DIM and FACT tables, without a source-record or namespace filter. No substitutions, notebook execution, source read or database mutation.

It returns 17 rows: an overall status, four count comparisons with this new rebuild's baseline (2,821 DIM, eight FACT, 2,813 roots and eight item nodes), and twelve structural checks. Checks include null/duplicate DIM/FACT primary keys and DIM UUIDs, ownership, element types, one root per represented record, missing FACT references, both orphan directions, null-safe UUID equality, same-record/namespace edges, root-to-item CONTAINS structure, parent counts and graph cardinality.

PASS means these counts and structural checks agree with the committed rebuild. DRIFT means counts differ; FAIL means a structural check fails. Counts are not permanent business constants. The overall observed count counts non-PASS checks, not distinct bad rows. Individual defect counts can overlap; duplicate DIM keys can multiply joined defect counts and are separately flagged.

This gate does not compare source field values, prove root identity equality against a fresh RAW snapshot, validate JSON payload contents or UUID syntax, certify full-document OSCAL conformance, or become part of the daily loader automatically.

## Validation actually performed
- Read 00_START_HERE.txt and coverage supplement from the supplied context; their September 14 counts do not override September 28 owner evidence.
- Read current branch and current AGENTS.md; inspected current production QA count/cardinality and relationship-check SQL at the pinned head.
- Read the new COMMIT screenshot directly, with no inferred source values.
- Built a focused SQL file from the reviewed POAM bindings and graph checks; no runtime, CSV or registry edits.
- Executed the new SELECT through SQLite 3.46.1, adapting only qualified table names and CURRENT_TIMESTAMP() syntax. BINARY keys used synthetic bytes; a read-only authorizer denied writes during each query execution.
- Nine synthetic cases passed: clean full-size baseline; 2,575 disconnected FACT rows; duplicate DIM key/UUID; null FACT UUID; cross-record ownership; self/item-parent edges; missing incoming edge; empty tables; and valid baseline drift. Each result had 17 rows.
- No Snowflake compilation/execution or CI run of the new SQL is claimed. The actual Snowflake result remains pending.
- SQL committed and its full content/blob read back, matching the locally tested file.

Immediate request: return the 17-row post-rebuild QA result. No further writes before its review.
