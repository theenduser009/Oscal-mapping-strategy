# Source 2 Assessment Results full commit read-back verified — 2026-09-18

Repository branch: `simplify-metadata-boundary`
Repository head inspected before this checkpoint: `3f8c1e3c11f44e202382f06f789b77e22ae34611`

## Evidence boundary

This checkpoint is based on owner-provided Snowflake notebook screenshots from 2026-09-18. This project does not have a direct Snowflake connection, so the database facts below are screenshot/read-back verified rather than independently queried here.

## Top-level pipeline result

- mode: `COMMIT`
- status: `COMMITTED_AND_VERIFIED`
- writes_executed: `true`
- commit_attempted: `true`

## Source 1 Assessment Results

The Source 1 route remained stable:

- source: `source-one`
- model: `ASSESSMENT_RESULTS`
- source_records: 2,813
- nodes: 90,016
- edges: 87,203
- writes_executed: true
- persisted: true
- committed: true
- target_dml_attempted: true
- pre_write_validation_passed: true
- validation_passed: true
- storage_verified: true
- expected DIM changes on this run: 0 inserts / 0 updates / 90,016 unchanged
- expected FACT changes on this run: 0 inserts / 0 updates / 87,203 unchanged
- verification DIM: 0 inserts / 0 updates / 90,016 unchanged
- verification FACT: 0 inserts / 0 updates / 87,203 unchanged
- status: `COMMITTED_AND_VERIFIED`
- temporary_cleanup: `REMOVED`

## Source 2 Source Assessment Results

The full Source 2 Assessment Results graph is now present and read-back verified:

- source: `source-two-source`
- model: `ASSESSMENT_RESULTS`
- source_records: 148
- nodes: 1,460
- edges: 1,312
- writes_executed: true
- persisted: true
- committed: true
- target_dml_attempted: true
- pre_write_validation_passed: true
- validation_passed: true
- storage_verified: true
- expected DIM changes on this run: 0 inserts / 0 updates / 1,460 unchanged
- expected FACT changes on this run: 0 inserts / 0 updates / 1,312 unchanged
- verification DIM: 0 inserts / 0 updates / 1,460 unchanged
- verification FACT: 0 inserts / 0 updates / 1,312 unchanged
- status: `COMMITTED_AND_VERIFIED`
- temporary_cleanup: `REMOVED`

## Interpretation

The prior 2026-09-17 preview predicted the full Source 2 graph at 1,460 DIM / 1,312 FACT, with a 1,016-node and 1,016-edge increase over the earlier 444 / 296 checkpoint.

The 2026-09-18 COMMIT read-back confirms the final full graph size of 1,460 / 1,312 and reports all rows unchanged on this particular COMMIT run. Therefore this screenshot proves the full graph is already persisted and matches the candidate graph; it does **not** by itself prove that this specific run inserted the prior 1,016-row delta. Do not claim insertion provenance beyond the read-back evidence.

The earlier checkpoint statement that the full 1,016-row extension was not yet committed is superseded by this checkpoint.

## Mapping scope status

For Source 2 `sources_source` Assessment Results:
- 9 mappings are executable/approved
- 1 duplicate alias (`_OF_NONCOMPLIANT_CONTROLS`) remains excluded
- 0 rows remain deferred in this Source 2 Assessment Results runtime scope
- registry finding branch was previously read-back verified
- full preview passed
- full target graph is now COMMIT/read-back verified

## Current completion status

**Source 2 `sources_source` Assessment Results is complete for the currently approved mapping scope.**

This does not close unrelated SME-blocked mappings in other models or Source 1 deferred rows.

## Next action

Choose the next OSCAL model to finish. Before any new substantive mapping work, inspect the current repository head and the relevant mapping/source evidence for that model. Do not use this Assessment Results checkpoint as proof of another model's completion.
