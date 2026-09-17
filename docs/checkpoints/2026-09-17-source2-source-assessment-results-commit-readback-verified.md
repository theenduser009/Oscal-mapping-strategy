# Source 2 sources_source Assessment Results COMMIT read-back verified — 2026-09-17

## Repository version

Branch: `simplify-metadata-boundary`
Repository head immediately before this checkpoint: `9af2819aad837858cc67d49af0e18ab6a699f123`.

## Evidence basis

Owner-provided Snowflake notebook screenshots from the universal seven-cell mapper run on 2026-09-17 with Cell 7 set to `COMMIT` after a successful PREVIEW.

## Source One Assessment Results route

The existing Source One route was revalidated in COMMIT mode and remained unchanged:

- source: `source-one`
- model: `ASSESSMENT_RESULTS`
- mode: `COMMIT`
- source records: 2,813
- nodes: 90,016
- edges: 87,203
- expected DIM changes: 0 inserts / 0 updates / 90,016 unchanged
- expected FACT changes: 0 inserts / 0 updates / 87,203 unchanged
- verification DIM: 0 inserts / 0 updates / 90,016 unchanged
- verification FACT: 0 inserts / 0 updates / 87,203 unchanged
- pre-write validation passed: true
- validation passed: true
- storage verified: true
- status: `COMMITTED_AND_VERIFIED`

`writes_executed=true` and `target_dml_attempted=true` reflect that the guarded COMMIT path executed for the selected route even though the target comparison was unchanged.

## Source Two sources_source Assessment Results route

The new Source Two route committed successfully:

- source: `source-two-source`
- model: `ASSESSMENT_RESULTS`
- mode: `COMMIT`
- source records: 148
- nodes: 444
- edges: 296
- pre-write validation passed: true
- validation passed: true
- storage verified: true
- expected DIM changes before write: 444 inserts / 0 updates / 0 unchanged
- expected FACT changes before write: 296 inserts / 0 updates / 0 unchanged
- verification DIM after write: 0 inserts / 0 updates / 444 unchanged
- verification FACT after write: 0 inserts / 0 updates / 296 unchanged
- persisted: true
- committed: true
- target DML attempted: true
- writes executed: true
- status: `COMMITTED_AND_VERIFIED`

The post-write verification counts prove that the committed Source Two graph was read back unchanged from the target after the insert.

## Runtime mapping represented

The committed Source Two Assessment Results batch currently covers the promoted mapping:

- source field: `COUNT_OF_NONCOMPLIANT_CONTROLS`
- target: `assessment-results.results[].props[]`
- property name: `noncompliant-count`

The executable mapping artifact is `Mapping/sources_source_runtime.csv`.

## Status distinction

- Runtime route: implemented, tested, committed to GitHub, and read-back verified.
- Snowflake PREVIEW: owner-run and screenshot read-back verified PASS.
- Snowflake COMMIT: owner-run and screenshot read-back verified PASS.
- Target DML: executed.
- Post-write read-back: verified.

## Remaining sources_source Assessment Results scope

This checkpoint does not claim all Source-tab Assessment Results fields are complete. `COMPLIANCE_RATING` and `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS` remain unresolved for exact model grain / relationship semantics and must not be silently treated as complete.

The Excel audit workbook still needs synchronization with the latest executable decisions; the runtime CSV drove this commit.
