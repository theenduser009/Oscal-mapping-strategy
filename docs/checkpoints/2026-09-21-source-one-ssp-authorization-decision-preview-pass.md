# Source One SSP authorization-decision PREVIEW pass — 2026-09-21

## Owner-provided live Snowflake evidence
After the final System Characteristics metadata correction compiled successfully,
the owner ran Cells 4-7 with SSP selected in PREVIEW mode.

Observed:
- mode: PREVIEW
- status: PREVIEW_COMPLETE
- source: source-one
- model: SSP
- source records: 2,813
- nodes: 89,629
- edges: 86,816
- pre-write validation passed: true
- validation passed: true
- storage verified: true
- writes executed: false
- persisted: false
- committed: false
- target DML attempted: false
- route status: PREVIEW_PASSED_NO_TARGET_DML
- temporary cleanup: REMOVED

Expected target changes:
- DIM inserts: 2,308
- DIM updates: 0
- DIM unchanged: 87,321
- FACT inserts: 2,308
- FACT updates: 0
- FACT unchanged: 84,508

## Interpretation
The prior accepted SSP graph baseline was 87,321 DIM nodes / 84,508 FACT edges.
This PREVIEW adds exactly 2,308 nodes and 2,308 parent-child edges, which matches
the live populated AUTHORIZATION_DECISION count observed before mapping.

The generic property reconciliation must still confirm that all 2,308 new nodes
are actually named `authorization-decision` and that the excluded
FULL_CONTROL_ASSESSMENT_HELPER emits zero nodes before any COMMIT.

## Status distinction
- Mapping metadata: committed in GitHub.
- Cell 3 compile verification: passed.
- SSP PREVIEW: passed.
- Target DML: not attempted.
- COMMIT/read-back: not yet established.

## Next action
Run the current root `RUN_NOW.py` in the same notebook session. It is read-only
and verifies:
- authorization-decision property count = 2,308
- full-control-assessment-helper property count = 0
- PREVIEW/no-write state remains intact

Do not COMMIT until that reconciliation passes.
