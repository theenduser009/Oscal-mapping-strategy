# Review the accepted SSP preview's proposed updates

Use [READ_ONLY_SSP_PREVIEW_UPDATE_REVIEW.py](READ_ONLY_SSP_PREVIEW_UPDATE_REVIEW.py)
in **one new Python cell in the same Snowflake notebook session** as the
[accepted preview](../../docs/checkpoints/2026-09-13-oscal-lean-daily-v3.1-preview-accepted.md).
Replace the earlier review cell with this extended version and run only that
cell. Keep `EXECUTE_WRITES = False` and the existing `MODEL_GRAPHS`,
`PIPELINE_REPORT` and `SOURCE_INPUTS`. No registry work or seven-cell rerun is
needed. This is a one-time diagnostic, not an eighth daily pipeline cell.

The helper reads transaction state, then compares the retained candidate with
the current configured DIM target in one joined query. It does not call the
loader or explicitly create tables or views. Snowpark can internally
materialize its existing list-backed candidate; an active transaction blocks
the comparison before that can happen. No target DML is issued.

The JSON report groups changed nodes and distinct affected records by OSCAL
element path and JSON member. Its additional `VALUE_RECONCILIATION` section
groups controlled old/new impact labels and reads the retained source snapshot
to check the mapping and sensitivity source values. Other values are redacted;
record IDs and full payloads are never printed.
JSON pointers identify literal field names and array positions; an array
reordering appears as changes at those positions.

- `READ_ONLY_REVIEW_COMPLETE`: current classification matches the accepted
  0 inserts, 1,994 updates and 68,108 unchanged nodes, with no reported anomaly.
- `READ_ONLY_REVIEW_DRIFT_DETECTED`: inspect counts and anomalies before relying
  on the field summary. Do not rerun the pipeline or enable writes to resolve it.
- `READ_ONLY_REVIEW_STOPPED`: retain the session and share the short error code.

Share the aggregate JSON report including `VALUE_RECONCILIATION`. The original
preview snapshots were removed, so this compares the accepted candidate to
the **current target**. Matching counts cannot establish that the historical
target baseline is unchanged. It is not COMMIT approval.

The one-line FIPS casing correction is documented in the
[reconciliation checkpoint](../../docs/checkpoints/2026-09-13-fips-value-reconciliation.md).
Do not rerun Cell Two before this comparison: the retained graph and lookups
belong to the accepted run. The report separately evaluates canonical lowercase
lookup behavior without changing them. A future corrected preview is still needed
before writing corrected payloads.

Tests cover JSON differences, aggregation, privacy, drift, source reconciliation
and execution guards. The installed Snowpark test covers binary-key joins and
duplicate/missing matches with explicit SQL projection adapters. The first
structural comparison has live execution evidence; the extended value report
still needs its live run.
Run the current release suite with `python -m unittest discover -s tests/lean -v`.
