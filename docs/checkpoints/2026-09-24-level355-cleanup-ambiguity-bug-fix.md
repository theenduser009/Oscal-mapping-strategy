# Level-355 cleanup ambiguity bug fixed — 2026-09-24

## Owner-reported failure
The source-derived cleanup reached the target-identity guard but raised:
`LEVEL355_BAD_TARGET_IDENTITY_AMBIGUOUS`.

## Root cause in cleanup logic
The cleanup computed two historical deterministic key candidates:
- one from decoded ALLOCATED_CONTROL_ID;
- one from JSON-serialized ALLOCATED_CONTROL_ID.

It counted matches for those two encodings separately and required the **sum** of
the two counts to equal one.

That is incorrect when both encodings produce the same candidate hash / same
target row. In that case one physical target row can be counted twice and the
script falsely reports ambiguity.

## Correction
The cleanup now:
1. creates both possible historical key candidates;
2. deduplicates them with `UNION`;
3. joins those distinct candidates to the target;
4. requires exactly one **distinct persisted DIM row**;
5. then applies the existing 1-incoming / 0-outgoing edge guard;
6. deletes and read-back verifies only that one node/edge.

No mapper or target data was changed by this correction itself.

## Next action
Run the updated cleanup SQL once. If it returns
`LEVEL355_SINGLE_BAD_IMPLEMENTED_REQUIREMENT_REMOVED`, run Cell 7 PREVIEW in the
current notebook session. Do not run any further diagnostic helper first.
