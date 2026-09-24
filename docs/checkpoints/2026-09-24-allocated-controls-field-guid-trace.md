# ALLOCATED_CONTROLS field-ID search found only base metadata rows — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `a0a183d143e7b0311c0e90342376309a715c1db9`

## Owner-provided live Snowflake evidence
The exact FIELD_ID search for Source One ALLOCATED_CONTROLS returned:

- SOURCE_FIELD_ID = 23429
- candidate tables inspected = 12
- field-id-like columns = 2
- matches:
  - ARCHER_META_FIELD.FIELD_ID = 23429
  - ARCHER_META_FIELD_STG.FIELD_ID = 23429

Both rows describe the same source field:
- FIELD_TYPE_ID = 9
- FIELD_GUID = E84D64F5-668F-47B5-AC50-89B6F6E67692
- LEVEL_ID = 353
- MODULE_ID = 547
- SQL field = ALLOCATED_CONTROLS

No separate relationship row was found by FIELD_ID.

## Interpretation
The current Snowflake metadata layer may store relationship/config references by
FIELD_GUID rather than by numeric FIELD_ID, or may not expose the Archer
relationship table at all.

## Next action
Root `RUN_NOW.py` now searches GUID-like columns for the exact ALLOCATED_CONTROLS
FIELD_GUID and, separately, lists only metadata/relationship schemas that expose
source/target/reference-like field columns.

This remains read-only and avoids another broad business-table search.
