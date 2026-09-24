# Level-355 recovery: current SSP payload-update PREVIEW passed

Evidence date: 2026-09-24

## Repository basis
- Repository: theenduser009/Oscal-mapping-strategy.
- Branch: simplify-metadata-boundary.
- Head freshly read before this documentation update: 78c2060389a815e724dc0b05d5f94f973995ff69.
- Reads pinned to that commit: maintained Cell 4 parsing/transforms and joined-record handling; current CONTROL_NUMBER and IMPLEMENTATION_DETAILS mapping rows; maintained Cell 6 preflight, comparison, guarded MERGE and readback; maintained Cell 7 orchestrator.
- Read blobs: Cell 4 a724b4328faa361827c04142fea993c27cd3ff25; mapping CSV 7790f23e52767a7d4f5bc31226c1e26198e60557; Cell 6 a206e316427b3aac7d20f4bb25c9af73c3a54c0b; Cell 7 78166e558cf99600d75e2995a7bae4144dad9534.
- The screenshot identifies loader release oscal-lean-daily-v3.1, not a Git commit. The notebook's exact loaded Git revision is not independently attested by the screenshot.

## Latest owner-provided Snowflake evidence
The latest screenshot shows one source-one / SSP route:
- pipeline mode = PREVIEW
- pipeline status = PREVIEW_COMPLETE
- release = oscal-lean-daily-v3.1
- source_records = 2,813
- nodes = 250,844
- edges = 248,031
- pre_write_validation_passed = true
- validation_passed = true
- storage_verified = true
- writes_executed = false
- persisted = false
- committed = false
- target_dml_attempted = false
- aggregate commit_attempted = false
- route status = PREVIEW_PASSED_NO_TARGET_DML
- temporary_cleanup = REMOVED

Expected target changes:
| Kind | INSERTS | UPDATES | UNCHANGED |
| --- | ---: | ---: | ---: |
| DIM | 0 | 127495 | 123349 |
| FACT | 0 | 0 | 248031 |

Arithmetic: 127,495 + 123,349 = 250,844 DIM rows. All 248,031 FACT rows are unchanged.

## Interpretation and supersession
This successful current PREVIEW supersedes the preceding failed PREVIEW/OBSOLETE_TARGET_ROWS_BLOCKED status for the scope and snapshot shown. The loader reached and passed its current graph, stored-key/provenance, obsolete-row, parent and edge checks. No additional target cleanup is indicated by this PREVIEW.

The graph totals are one node and one edge below the earlier first-batch COMMIT/readback totals (250,845 / 248,032). Together with the prior one-row source exception and zero-stale-row evidence, this is consistent with the malformed child being omitted and the current target matching the corrected graph keys. This does not establish which earlier operation removed the node/edge.

The current 127,495 DIM updates equal the number of usable Level-355 controls established by earlier owner checks. They must NOT be described as 127,495 populated implementation descriptions. Current Cell 4 retains the accepted child identity representation while JSON-decoding mapped payload values. The two active joined mappings are CONTROL_NUMBER -> control-id and IMPLEMENTATION_DETAILS -> description. The all-child update count is consistent with control-id serialization normalization plus descriptions on populated rows; the aggregate report does not independently separate those causes or certify every description value.

No claim of full OSCAL document/schema validation or catalog/profile control-id compatibility is made. Existing mapping scope and unresolved decisions are retained.

## Accepted decisions retained
- Package lineage: Level-355 CONTENT_ID joins Authorization Package CONTENT_ID.
- Child instance identity: ALLOCATED_CONTROL_ID, with current historical representation retained to avoid rekeying persisted children.
- CONTROL_NUMBER VALUE_REQUIRED=false at mapping level; registry REQUIRED_MEMBERS=control-id controls child validity.
- The one source child lacking a defensible control-id remains an explicit skipped source-data exception, not an invented control reference.
- IMPLEMENTATION_DETAILS is mapped to the requirement description; OVERALL_IMPLEMENTATION_DETAILS is not silently substituted.
- Do not run any earlier cleanup, identity-guessing, fallback profiler, or obsolete exact-count COMMIT_NOW helper.

## Changes and validation actually performed
This turn changes only this documentation checkpoint. No runtime code, mapping, registry, source or target data was changed. Validation performed: visual reading of the owner report, arithmetic reconciliation, and pinned code/mapping review. No new synthetic tests or live Snowflake query were run by the assistant. The PREVIEW evidence is owner-supplied, not a direct assistant database read.

## Next single action
In the same notebook session, keeping the same frozen source inputs, lookup snapshots, compiled mappings and source-one/SSP selection, change only Cell 7's OSCAL_LOAD_MODE from PREVIEW to COMMIT and run Cell 7 once. Keep shared EXECUTE_WRITES=False. Avoid concurrent changes to OSCAL targets during this run.

Use the existing guarded pipeline, which performs a preliminary PREVIEW and then its per-route transactional MERGE/readback. Do not rerun Cells 1-6 or refresh source/mapping inputs before this commit step. Do not use old COMMIT_NOW.py, whose expected counts describe a previous batch.

Expected completion, not yet observed:
- status = COMMITTED_AND_VERIFIED
- writes_executed, persisted, committed = true
- DIM verification: INSERTS=0, UPDATES=0, UNCHANGED=250844
- FACT verification: INSERTS=0, UPDATES=0, UNCHANGED=248031

Return the complete commit and verification report. Until that evidence arrives, the description/normalization change is PREVIEW-PASSED only, not committed/read-back verified. If an error or unknown outcome occurs, stop and preserve the report rather than rerunning cleanup or COMMIT blindly.
