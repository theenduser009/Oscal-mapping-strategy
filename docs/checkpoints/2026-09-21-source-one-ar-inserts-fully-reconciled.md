# Source One Assessment Results PREVIEW insert reconciliation — 2026-09-21

## Owner-provided live Snowflake evidence
The owner ran the read-only `RUN_NOW.py` reconciliation after the final Source One
Assessment Results PREVIEW.

Observed generated node counts by newly executable mapping:
- avg-security-compliance-reporting-score = 2,813
- avg-security-compliance-score = 2,813
- total-package-inherent-risk = 2,813
- risk-acceptance-rbds = 1
- workflow-current-node = 602
- workflow-process-version = 615
- workflow-job-status = 615
- workflow-status = 2,813
- due-date = 0
- workflow-current-node-hrtn = 587
- workflow-status-changed = 2,813

Reconciliation totals:
- NEW_MAPPING_NODE_TOTAL = 16,485
- EXPECTED_DIM_INSERTS = 16,485
- EXPECTED_FACT_INSERTS = 16,485
- DIM_DELTA_NOT_ATTRIBUTED = 0
- FACT_DELTA_NOT_ATTRIBUTED = 0
- RESULT = SOURCE_ONE_AR_INSERTS_FULLY_RECONCILED

## Status distinction
- GitHub mapping metadata: committed.
- Cell 3 compilation: verified live.
- Final Source One AR PREVIEW: passed.
- Proposed insert delta: fully reconciled to the 11 newly executable mappings.
- Existing target rows: preview predicted 0 updates to the prior Source One AR baseline.
- Target DML: not attempted in the PREVIEW.
- COMMIT/read-back: not yet established.
- RISK_ASSESSMENT_REPORT remains the documented attachment exception and is not compiled.

## Conclusion
The final Source One Assessment Results mapping batch is ready for a COMMIT decision.
This checkpoint does not authorize or claim a COMMIT.

## Next action
If the owner authorizes COMMIT, rerun the guarded pipeline in COMMIT mode using the
same current mapping CSV and notebook cells, then capture the post-commit read-back
report before calling Source One Assessment Results persisted/verified.
