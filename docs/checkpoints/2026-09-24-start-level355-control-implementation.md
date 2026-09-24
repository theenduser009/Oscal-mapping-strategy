# Start Level-355 Control Implementation mapping — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before this helper: `c99c47e3935dbcc4ba5b2fa6199afa170b021d6b`

## Current state
The first Control Implementation package-summary batch has been mapped and the
owner reports that the load completed as expected. The exact COMMIT report is not
captured in this checkpoint, so this note does not independently elevate that run
to read-back-verified status.

The remaining Control Implementation work is the actual per-control branch.

Expected current source:
`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`

Historical and current evidence already establish:
- Authorization Package ALLOCATED_CONTROLS contains ContentId / LevelId refs
- LevelId 355 = CONTROL
- Module 549 = ALLOCATED CONTROLS
- Level 355 metadata contains control number/name, implementation details/status,
  parameters, responsible role, inheritance, control entity/set and related fields

## Immediate next action
Root `RUN_NOW.py` now performs one focused read-only readiness pass:
- confirms the physical Level-355 table schema
- checks ContentId uniqueness
- reconciles all current Authorization Package Level-355 references to the table
- profiles only the key fields needed for the first implemented-requirements[]
  design
- reads the current SSP control-implementation registry branch

No mapping/code/registry/target DML is performed.

Use this result to decide the first actual implemented-requirements[] mapping
batch without additional broad discovery.
