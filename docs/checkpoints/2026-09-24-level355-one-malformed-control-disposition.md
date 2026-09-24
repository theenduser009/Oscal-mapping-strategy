# Level-355 one malformed control row disposition — 2026-09-24

## Evidence
The one-row fallback checks established:
- 127,496 matched Level-355 rows total
- 127,495 have CONTROL_NUMBER
- 1 row has no CONTROL_NUMBER
- FEED_CONTROL_NUMBER does not cover it
- CONTROL_NUMBER_ONLY does not cover it
- CONTROL_NAME prefix fallback is not proven:
  - 3 prefix mismatches among rows with CONTROL_NUMBER
  - the one missing CONTROL_NUMBER row also lacks a usable CONTROL_NAME prefix

Therefore no defensible control-id can be derived for that row.

## Decision
Do not invent a control-id.

The generic joined-record builder now skips a child record when a registry-required
payload member is absent. The graph report records SKIPPED_JOINED_RECORDS.

Because the first Level-355 batch had already persisted one invalid child before
projected VARIANT decoding was corrected, a one-time guarded cleanup SQL was added:

`sql/validation/2026-09-24_cleanup_one_invalid_level355_implemented_requirement.sql`

The cleanup aborts unless it finds exactly:
- 1 invalid implemented-requirement DIM row;
- 1 incoming FACT edge;
- 0 outgoing FACT edges.

It deletes only that bad node/edge and verifies zero remain.

## Next action
1. Run the guarded one-time cleanup SQL.
2. Refresh current Cell 4.
3. Run Cell 4, then Cell 7 in PREVIEW mode.
4. Expect 127,495 implemented-requirement children plus the normal SSP structure.
5. Reconcile the update count for decoded control-id values + real implementation
   descriptions before any COMMIT.
