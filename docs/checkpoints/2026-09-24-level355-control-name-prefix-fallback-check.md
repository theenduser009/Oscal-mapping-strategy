# Level-355 control-id has one row with no direct number candidate — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before fallback-validation helper: `f25b6bcb22e60b8cd544ab5aa675067a946db9d8`

## Owner-provided live Snowflake evidence
The one-row fallback check returned:
- MATCHED_ROWS = 127,496
- CONTROL_NUMBER_MISSING = 1
- FEED_FALLBACK_COVERS = 0
- CONTROL_NUMBER_ONLY_COVERS = 0
- ANY_FALLBACK_COVERS = 0
- MISSING_ALL_CONTROL_NUMBER_CANDIDATES = 1

Therefore the one row cannot be resolved from the three explicit control-number
fields. Do not invent a control-id from ALLOCATED_CONTROL_ID.

## Next action
Validate one deterministic fallback already suggested by the source shape:
CONTROL_NAME visibly begins with the control number in ordinary rows.

Root `RUN_NOW.py` now verifies across the full 127,496-row matched set that:
- CONTROL_NAME's first token equals CONTROL_NUMBER everywhere CONTROL_NUMBER exists;
- the one missing CONTROL_NUMBER row still has a nonblank CONTROL_NAME prefix.

Only if both conditions hold will CONTROL_NAME prefix be accepted as the one-row
fallback. No values or IDs are printed.
