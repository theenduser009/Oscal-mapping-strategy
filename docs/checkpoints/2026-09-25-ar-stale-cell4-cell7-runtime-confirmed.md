# AR PREVIEW still using stale notebook runtime — 2026-09-25

## Owner evidence
Latest screenshot still shows:
- status = FAILED_BEFORE_COMMIT
- failed_route = source-one / ASSESSMENT_RESULTS
- error_type = ValueError
- no error_message field
- writes_executed = false
- commit_attempted = false

## Repository evidence
At current branch head 765a4f9e9cdf98fe09526c96a2853e59051a8106:
- maintained Cell 7 includes error_message=str(error) in the pipeline report.
- maintained Cell 4 includes the json-text transform required by the newly approved RISK_ASSESSMENT_REPORT mapping.
- current CSV has RISK_ASSESSMENT_REPORT APPROVED using json-text and FINDINGS APPROVED with NULL_POLICY=preserve.

Therefore the screenshot proves the executed notebook Cell 7 is not the current maintained Cell 7. The AR-only ValueError is also consistent with a stale Cell 4 that does not know json-text while the latest Cell 3 mapping plan does.

## Next action
Do not change mappings and do not rerun cleanup.

Refresh from Git and execute only:
1. notebooks/cells/04_parsing_transform_payload_helpers.py
2. notebooks/cells/07_mapper_orchestrator.py

Run Cell 4, then Cell 7 in PREVIEW with the already-compiled source-one / ASSESSMENT_RESULTS context.

If failure remains, the current Cell 7 will expose error_message and that exact text becomes the next debugging evidence.
