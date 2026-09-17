# Source 2 Assessment Results full preview reconciled — 2026-09-17

Repository branch: `simplify-metadata-boundary`
Repository checkpoint before this note: `5d12d2632e85e2b257ffc3c572e73f00d7b6d221`
Runtime implementation commit in ancestry: `6563d1f9f121d0c9e781f7b8419cc6621d47e0e9`

## Evidence status
Owner-provided Snowflake notebook screenshots on 2026-09-17 were reviewed. This project has no direct Snowflake connection, so the live figures below are screenshot/read-back evidence rather than independently queried database results.

## Source 1 Assessment Results
Preview remained unchanged:
- source records: 2,813
- DIM nodes: 90,016
- FACT edges: 87,203
- expected DIM changes: 0 inserts / 0 updates / 90,016 unchanged
- expected FACT changes: 0 inserts / 0 updates / 87,203 unchanged
- status: `PREVIEW_PASSED_NO_TARGET_DML`

## Source 2 Source Assessment Results
Full no-defer preview passed:
- source records: 148
- DIM nodes: 1,460
- FACT edges: 1,312
- expected DIM changes: 1,016 inserts / 0 updates / 444 unchanged
- expected FACT changes: 1,016 inserts / 0 updates / 296 unchanged
- validation passed: true
- storage verified: true
- writes executed: false
- target DML attempted: false
- status: `PREVIEW_PASSED_NO_TARGET_DML`

## Reconciliation of the 1,016 new nodes and edges
The increase reconciles exactly to the verified live Source2 shapes already captured on 2026-09-17:
- `COMPLIANCE_RATING`: 148 populated source records -> 148 result-level `compliance-rating` properties
- `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS`: 847 referenced control-standard identifiers across 21 populated source records -> 847 `linked-control-standard` finding properties
- optional finding parent: 21 source records have finding-branch descendant data -> 21 finding nodes

Arithmetic: `148 + 847 + 21 = 1,016` new nodes. Each new node adds one parent dependency edge, so the FACT increase is also `1,016`.

The previously committed Source2 graph remains unchanged at 444 DIM / 296 FACT; therefore the new full preview does not rewrite or duplicate those rows.

## Duplicate control
`_OF_NONCOMPLIANT_CONTROLS` remains explicitly excluded. `COUNT_OF_NONCOMPLIANT_CONTROLS` is the sole executable owner of the `noncompliant-count` property.

## Current checkpoint
Implemented in repository: yes.
Registry read-back verified: yes (owner-provided 2026-09-17 read-back showed six active Assessment Results registry rows including `results[].findings[]` and `results[].findings[].props[]`).
Full Source2 preview: passed and reconciled.
Committed to Snowflake targets for this 1,016-row extension: no — not yet authorized/run.

## Next action
Switch Cell 7 only to `OSCAL_LOAD_MODE = "COMMIT"` in the same notebook session and run Cell 7. Verify Source 1 remains unchanged and Source 2 returns `COMMITTED_AND_VERIFIED` with the 1,460 DIM / 1,312 FACT graph read back unchanged after merge. Stop if the commit report differs from the preview reconciliation.
