# Source One AR PREVIEW failed before commit after final AR mappings — 2026-09-25

## Owner-provided evidence
The owner supplied a Cell 7 screenshot showing:
- mode = PREVIEW
- status = FAILED_BEFORE_COMMIT
- failed_route = source-one / ASSESSMENT_RESULTS
- error_type = ValueError
- groups = []
- writes_executed = false
- commit_attempted = false
- load_error = {}

No target DML occurred.

## Repository verification
At branch head f780f179ff18f5cf486659ee532a9bb83a351a70:
- maintained Cell 4 contains the new json-text transform required by RISK_ASSESSMENT_REPORT;
- maintained Cell 7 includes error_message=str(error) in failed pipeline reports;
- current mapping CSV has RISK_ASSESSMENT_REPORT APPROVED with json-text and FINDINGS APPROVED with NULL_POLICY=preserve.

The screenshot does not show error_message, so the notebook's executed Cell 7 is older than the maintained repository Cell 7. Because the new AR mapping also depends on the latest Cell 4 transform while SSP does not, stale Cell 4 is a likely cause of an AR-only ValueError. This remains a diagnosis to verify, not a claim of the exact hidden exception.

## Next action
Refresh and run the latest maintained Cell 4 and Cell 7 from simplify-metadata-boundary. Keep the already-compiled Source One ASSESSMENT_RESULTS route and run Cell 7 in PREVIEW.

If it still fails, the current Cell 7 will expose error_message, which becomes the exact next debugging evidence. Do not COMMIT and do not run cleanup.
