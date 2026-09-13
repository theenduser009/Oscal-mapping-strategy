# Review the accepted SSP preview's proposed updates

Use [READ_ONLY_SSP_PREVIEW_UPDATE_REVIEW.py](READ_ONLY_SSP_PREVIEW_UPDATE_REVIEW.py)
in **one new Python cell in the same Snowflake notebook session** as the
[accepted preview](../../docs/checkpoints/2026-09-13-oscal-lean-daily-v3.1-preview-accepted.md).
Run only that new cell. Keep `EXECUTE_WRITES = False` and the existing
`MODEL_GRAPHS` and `PIPELINE_REPORT`. No registry work or seven-cell rerun is
needed. This is a one-time diagnostic, not an eighth daily pipeline cell.

The helper reads transaction state, then compares the retained candidate with
the current configured DIM target in one joined query. It does not call the
loader or explicitly create tables or views. Snowpark can internally
materialize its existing list-backed candidate; an active transaction blocks
the comparison before that can happen. No target DML is issued.

The JSON report groups changed nodes and distinct affected records by OSCAL
element path and JSON member. It includes no payload values or record IDs.
JSON pointers identify literal field names and array positions; an array
reordering appears as changes at those positions.

- `READ_ONLY_REVIEW_COMPLETE`: current classification matches the accepted
  0 inserts, 1,994 updates and 68,108 unchanged nodes, with no reported anomaly.
- `READ_ONLY_REVIEW_DRIFT_DETECTED`: inspect counts and anomalies before relying
  on the field summary. Do not rerun the pipeline or enable writes to resolve it.
- `READ_ONLY_REVIEW_STOPPED`: retain the session and share the short error code.

Share the aggregate JSON report to review which fields changed. The original
preview snapshots were removed, so this compares the accepted candidate to
the **current target**. Matching counts cannot establish that the historical
target baseline is unchanged. It is not COMMIT approval.

Twelve unit tests cover JSON differences, aggregation, privacy, drift and
execution guards. One installed Snowpark test covers binary-key joins and
duplicate/missing matches; the local emulator requires explicit projection
adapters, so native SQL and live warehouse execution remain live checks.
Run the current release suite with `python -m unittest discover -s tests/lean -v`.
