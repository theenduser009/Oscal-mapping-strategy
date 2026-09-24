# Level-355 PREVIEW failed after projected VARIANT decode — targeted control-id check — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `d605c504f80b00f5dd77bff3b77dace6e5f2800c`

## Owner-provided live evidence
After the projected VARIANT decode correction, the SSP PREVIEW stopped with:
- mode = PREVIEW
- status = FAILED_BEFORE_COMMIT
- groups = []
- writes_executed = false
- commit_attempted = false
- failed route = source-one / SSP
- error type = ValueError

No target DML was attempted.

## Leading hypothesis
The first Level-355 batch originally treated projected VARIANT scalar strings as
already-decoded Python values. After the correction, true JSON nulls now become
Python None.

Because `CONTROL_NUMBER` is a required member for every
`implemented-requirements[]` child, any real null/blank CONTROL_NUMBER row now
correctly blocks graph construction. The earlier 127,496 populated count used
VARIANT `IS NOT NULL` semantics and could have counted JSON nulls.

## Next action
Root `RUN_NOW.py` now checks only:
- effective CONTROL_NUMBER coverage;
- FEED_CONTROL_NUMBER fallback coverage for any missing CONTROL_NUMBER rows;
- ALLOCATED_CONTROL_ID coverage;
- the exact underlying graph ValueError.

No broad profiling and no writes.
