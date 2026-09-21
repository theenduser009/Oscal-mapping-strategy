# Source One SSP Control Implementation bulk review start — 2026-09-21

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head after publishing the bulk read-only profiler: `92c37948313a19e57f108958ee8a2e0c50e81c7c`

## Current status before Control Implementation review
- Source One Assessment Results September 21 batch: COMMIT/read-back verified.
- SSP responsible-party metadata correction: PREVIEW reconciled with zero target delta.
- SSP System Characteristics AUTHORIZATION_DECISION addition: PREVIEW fully reconciled
  at 2,308 new DIM nodes / 2,308 new FACT edges.
- The owner has not yet supplied the result of the guarded SSP COMMIT helper for
  that 2,308-row addition in this chat. Do not infer a successful COMMIT from the
  PREVIEW checkpoint.

## Next Source One mapping area
Current runtime CSV still has 42 DEFERRED SSP Control Implementation
rows representing 41 unique source field names.
Duplicate deferred field names detected: HELPER_ALLOCATED_CONTROLS.

Historical evidence already established that ALLOCATED_CONTROLS can contain
`{ContentId, LevelId: 355}` references and that Archer Level 355 is strongly
control-oriented. That September 14 evidence remains discovery support only; it
does not by itself approve the remaining field mappings.

## Action prepared
Root `RUN_NOW.py` now performs one bulk, read-only inventory across every unique
currently deferred Control Implementation field:
- present/populated counts
- top-level shapes
- compact array/object signatures
- referenced LevelId counts without printing ContentIds
- select cardinality/labels without printing select IDs
- exact ARCHER_META_FIELD type/level/module/select metadata

No mapping status, registry row, notebook mapper cell, or DIM/FACT target is
changed by this profiling step.

## Next action
Run the current root `RUN_NOW.py` in the existing Source One notebook session
with the current Source One input loaded. Return the output. Use the resulting
shape/type groups to resolve the 42-row backlog in reusable batches rather than
one field at a time.
