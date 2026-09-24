# Level-355 PREVIEW blocked by one obsolete target row — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before this checkpoint: `82d2d39a3e9d8d629e6f9570635b2ceb7030708e`

## Owner-provided live Snowflake evidence
Fresh Source One / SSP PREVIEW returned:
- mode = PREVIEW
- status = FAILED_BEFORE_COMMIT
- writes_executed = false
- commit_attempted = false
- failed route = source-one / SSP
- error type = LoadError
- load status = OBSOLETE_TARGET_ROWS_BLOCKED
- phase = PREPARATION
- pre_write_validation_passed = false
- target_dml_attempted = false

## Interpretation
This is the loader's intended safety behavior.

The current graph now skips the single malformed Level-355 child that has no
defensible control-id. The previously committed invalid child node/edge still
exists in the target, so the loader correctly blocks because target scope contains
an obsolete row that is absent from the new graph.

This is not a new graph/mapping failure.

## Existing cleanup
The one-time guarded cleanup script already exists:
`sql/validation/2026-09-24_cleanup_one_invalid_level355_implemented_requirement.sql`

It aborts unless it finds exactly:
- one invalid implemented-requirement DIM row;
- one incoming FACT edge;
- zero outgoing FACT edges.

## Next action
Run the one-time guarded cleanup SQL once. If it returns
`LEVEL355_SINGLE_BAD_IMPLEMENTED_REQUIREMENT_REMOVED`, rerun Cell 7 in PREVIEW
mode in the same notebook session. Do not rerun the cleanup after a successful run.
