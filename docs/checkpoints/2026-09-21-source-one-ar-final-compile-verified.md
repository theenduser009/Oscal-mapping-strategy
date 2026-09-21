# Source One Assessment Results final mapping compile verification — 2026-09-21

## Repository basis
- Branch before this checkpoint: `332da8da2b39a3b02d02efcb3b0c65e362acff85`

## Owner-provided live Snowflake notebook evidence
After replacing the notebook-visible `ARCHER_OSCAL_MAPPINGS.csv` with the current
GitHub version and rerunning Cells 1-3, the owner ran `RUN_NOW.py`.

Observed output:
- `ROUTE_STATUS: READY`
- `SELECTED_ROWS_TOTAL: 43`
- `RISK_ACCEPTANCE_RBDS | reference-ids | assessment-results.results[].props[]`
- `WORKFLOW_JOB_STATUS | archer-select | assessment-results.results[].props[]`
- `RISK_ASSESSMENT_REPORT | DEFERRED | NOT_COMPILED`
- `RESULT: SOURCE_ONE_AR_FINAL_MAPPING_READY_FOR_PREVIEW`

## Status distinction
- Mapping metadata: committed in GitHub.
- Cell 3 compilation: owner-reported live verification passed.
- Cells 4-7 PREVIEW: not yet rerun after the final correction.
- DIM/FACT DML: not authorized and not performed by this checkpoint.
- RISK_ASSESSMENT_REPORT remains a documented attachment exception, not a hidden failure.

## Next action
In the same Snowflake notebook session:
1. Keep `EXECUTE_WRITES = False`.
2. Keep Cell 7 `OSCAL_LOAD_MODE = "PREVIEW"`.
3. Run Cells 4, 5, 6, and 7 in order.
4. Capture the resulting `OSCAL_PIPELINE_REPORT`.

Review Source One and Source Two Assessment Results separately if both routes are selected.
Do not switch to COMMIT until the new PREVIEW is reconciled.
