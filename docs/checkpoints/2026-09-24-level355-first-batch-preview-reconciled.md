# Source One SSP Level-355 first batch PREVIEW reconciled — 2026-09-24

## Owner-provided live Snowflake evidence
Fresh PREVIEW after the joined-record memory fix:

- source = source-one
- model = SSP
- mode = PREVIEW
- status = PREVIEW_COMPLETE
- source_records = 2,813
- nodes = 250,845
- edges = 248,032
- validation_passed = true
- storage_verified = true
- writes_executed = false
- commit_attempted = false

Expected target changes:
- DIM inserts = 130,309
- DIM updates = 0
- DIM unchanged = 120,536
- FACT inserts = 130,309
- FACT updates = 0
- FACT unchanged = 117,723
- route status = PREVIEW_PASSED_NO_TARGET_DML

## Exact delta reconciliation
Previous persisted SSP graph baseline:
- 120,536 nodes
- 117,723 edges

New Level-355 structure:
- 2,813 `control-implementation` parent nodes (one per Source One SSP)
- 127,496 `implemented-requirements[]` child nodes, keyed by ALLOCATED_CONTROL_ID

Total new nodes = 2,813 + 127,496 = 130,309.

Each new node contributes one CONTAINS edge:
- SSP -> control-implementation = 2,813
- control-implementation -> implemented-requirement = 127,496

Total new edges = 130,309.

Therefore the entire target delta is explained with no unattributed rows.

## First-batch mapping contract
- parent/package join: Level-355 CONTENT_ID = Authorization Package CONTENT_ID
- child instance identity: ALLOCATED_CONTROL_ID
- OSCAL control reference: CONTROL_NUMBER -> implemented-requirement.control-id

CONTROL_NUMBER is not used as graph identity because package/control-number pairs
were not unique for every matched row.

## Next action
A guarded `COMMIT_NOW.py` is prepared for this exact PREVIEW. Run it in the same
notebook session. Success must return:
`RESULT: SOURCE_ONE_SSP_LEVEL355_FIRST_BATCH_COMMIT_AND_READBACK_VERIFIED`

After read-back verification, proceed to the second Level-355 field batch
(implementation description/status/roles/parameters) using corrected JSON-null-aware
population evidence.
