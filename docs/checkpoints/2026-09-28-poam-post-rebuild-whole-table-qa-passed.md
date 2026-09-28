# POAM post-rebuild whole-table QA passed

Evidence date: September 28, 2026.
Owner result timestamp: 2026-09-28 15:58:08.824 -0400.
Repository: theenduser009/Oscal-mapping-strategy.
Branch: simplify-metadata-boundary.
Head inspected before this documentation update: 8f5061142894ed7fffec45ee4930c85643dc1ce3.

## Evidence reviewed
The owner reported "Pass" and supplied the complete check-order 0-16 result grid for sql/qa/POAM_POST_REBUILD_QA_2026-09-28.sql. The screenshot shows the check names and observed counts below. The rightmost STATUS column is outside the screenshot; PASS is owner-reported and independently consistent with the visible counts and the retrieved SQL's result logic. No additional screenshot or repeat run is needed for this acceptance.

The exact QA SQL was retrieved at the inspected head; blob cbc5976391adb791420908dde6e6f657e222ddde. It reads the complete POAM DIM/FACT pair with no source-record or namespace filter. The overall observed count counts non-PASS checks, not bad rows. The private screenshot is not published here.

| CHECK_ORDER | QA_CHECK | OBSERVED_COUNT |
| --- | --- | ---: |
| 0 | OVERALL_POAM_REBUILD_QA | 0 |
| 1 | DIM_ROWS | 2821 |
| 2 | FACT_ROWS | 8 |
| 3 | ROOT_ROWS | 2813 |
| 4 | POAM_ITEM_ROWS | 8 |
| 5 | NULL_OR_DUPLICATE_KEY_GROUPS | 0 |
| 6 | INVALID_SOURCE_OWNERSHIP_ROWS | 0 |
| 7 | UNEXPECTED_ELEMENT_TYPES | 0 |
| 8 | RECORDS_WITHOUT_EXACTLY_ONE_ROOT | 0 |
| 9 | NULL_OR_BLANK_FACT_REFERENCES | 0 |
| 10 | ORPHAN_SOURCE_FK | 0 |
| 11 | ORPHAN_TARGET_FK | 0 |
| 12 | UUID_MISMATCH | 0 |
| 13 | CROSS_RECORD_OR_NAMESPACE_EDGES | 0 |
| 14 | INVALID_CONTAINS_OR_ROOT_ITEM_EDGES | 0 |
| 15 | WRONG_PARENT_COUNT | 0 |
| 16 | EDGE_MINUS_NONROOT_COUNT | 0 |

Four release-baseline counts match and all twelve structural defect checks are zero. All sixteen checks therefore satisfy the retrieved SQL's PASS rule; the overall non-PASS check count is zero.

## Accepted status and supersession
The current POAM orphan-data defect is closed for this inspected September 28 snapshot. The earlier 2,575 fully disconnected FACT rows are no longer present as orphan facts in the current table-wide result; the table now contains eight FACT rows with valid checked relationships. This does not establish the historical cause of the discrepancy.

This supersedes the whole-table-QA-pending status in docs/checkpoints/2026-09-28-poam-rebuild-commit-readback-verified.md and the project-only rebuild/endpoint-summary checkpoints. It does not replace or invalidate earlier dated observations.

The rebuild's separate COMMITTED_AND_VERIFIED/readback evidence remains accepted: 2,813 source records, 2,821 DIM rows, eight FACT rows, and zero remaining staged inserts/updates. Together, the rebuild report and this new whole-table check establish committed batch readback plus post-rebuild structural QA. No additional truncation, repeat COMMIT or unchanged QA rerun is requested.

## Remaining boundaries
The existing approved POAMS reference mapping and its identity policy are unchanged. This is not full POAM item-detail hydration, raw-to-target field-semantic parity, a fresh source identity comparison, full OSCAL document conformance or sign-off of every Source One model. Other model mappings and tables were outside this recovery action.

The Cell 6 validation-coverage limitation remains separate and open. Actual _load_scope/_load_preflight code was retrieved at the inspected head (notebooks/cells/06_validation_and_guarded_loader.py, lines 225-265; blob a206e316427b3aac7d20f4bb25c9af73c3a54c0b). A fully disconnected noncandidate FACT can remain outside its scoped orphan check. The standalone passing QA query and the data rebuild did not modify that code. Closing this data defect does not prove future recurrence is prevented.

## Validation and changes performed in this update
Reviewed the owner-provided result, current branch, actual QA SQL, prior committed/readback checkpoint, AGENTS.md and relevant loader source. The September 14 handoff and coverage supplement remain historical context, not current run evidence. No source values or private screenshots were added to GitHub.

Only this dated status document is added. No runtime, SQL, CSV, registry or loader changes; no new tests or CI run. No Snowflake operations were executed by this chat. The live QA evidence is the owner's result, not a claimed remote database session.

## Next action
No further POAM repair SQL or reload is needed. Recommended next engineering item: close the daily loader's whole-table orphan-detection gap with a scoped, reviewed change and regression tests before operational sign-off. That change is proposed, not implemented by this checkpoint. It must not alter approved mappings, identity rules, or other model data, and it must not be described as establishing the cause of the historical orphan records.
