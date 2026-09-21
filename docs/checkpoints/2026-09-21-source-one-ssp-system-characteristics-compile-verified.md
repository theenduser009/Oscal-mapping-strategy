# Source One SSP System Characteristics final compile verified — 2026-09-21

## Owner-provided live Snowflake evidence
After replacing the notebook-visible mapping CSV and rerunning Cells 1-3 with SSP
selected, the owner ran the final System Characteristics compile check.

Observed:
- ROUTE_STATUS: READY
- SELECTED_ROWS_TOTAL: 54
- AUTHORIZATION_DECISION -> archer-select ->
  system-security-plan.system-characteristics.props[]
- FULL_CONTROL_ASSESSMENT_HELPER -> EXCLUDED / NOT_COMPILED
- RESULT: SSP_SYSTEM_CHARACTERISTICS_READY_FOR_PREVIEW

## Status distinction
- GitHub mapping metadata: committed.
- Cell 3 compilation: live verification passed.
- SSP PREVIEW for the authorization-decision addition: not yet rerun.
- No DIM/FACT DML is established by this checkpoint.

## Next action
Run Cells 4-7 with SSP selected, EXECUTE_WRITES=False, and Cell 7 in PREVIEW.
Then run the root RUN_NOW.py to reconcile the authorization-decision property
population (expected 2,308) against the new graph and loader delta before any COMMIT.
