# Level-355 current RAW binding diagnostic correction — 2026-09-21

## Owner-provided live evidence before failure
The read-only Level-355 binding check successfully resolved:
- LEVEL_ID = 355
- LEVEL_NAME = CONTROL
- MODULE_ID = 549
- MODULE_NAME = ALLOCATED CONTROLS
- private Level-355 ContentId sample size = 100

The run then failed before candidate-table matching with a Snowflake SQL parse
error caused by the diagnostic query's LIKE/ESCAPE syntax. This was a helper-code
error, not a source-data or mapping failure.

## Correction
Root `RUN_NOW.py` now identifies candidate current Archer RAW tables using:
- `STARTSWITH(UPPER(TABLE_NAME), 'ARCHER_CONTENT')`
- `ENDSWITH(UPPER(TABLE_NAME), '_RAW')`

This removes the fragile LIKE/ESCAPE expression entirely.

## Status
- No mapper cells changed.
- No mapping CSV rows changed.
- No registry rows changed.
- No DIM/FACT DML occurred.
- Level-355 current RAW binding remains unresolved until the corrected helper runs.

## Next action
Run only the corrected root `RUN_NOW.py` in the current notebook session.
Do not rerun Cells 1-7 for this correction.
