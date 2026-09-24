# Engineering correction: joined-record required field + pipeline observability — 2026-09-24

## Problem
The Level-355 graph still failed after the joined-record operator was changed to skip
children missing registry-required members.

The actual cause is now confirmed from code:
- CONTROL_NUMBER mapping had VALUE_REQUIRED=true.
- `_metadata_mapped_value()` raises immediately when a required mapped value is absent.
- therefore the joined-record operator never reached its later
  `REQUIRED_MEMBERS` skip logic for the one malformed child.

This was a duplicated requirement policy at two layers.

## Correction
- CONTROL_NUMBER mapping VALUE_REQUIRED changed to false.
- Registry `REQUIRED_MEMBERS=control-id` remains authoritative for child validity.
- joined-record operator skips only the malformed child and records
  SKIPPED_JOINED_RECORDS.
- no control-id is invented.

## Observability improvement
Cell 7 now includes `error_message=str(error)` in OSCAL_PIPELINE_REPORT.
Future route failures expose the underlying exception directly instead of requiring
a separate RUN_NOW diagnostic just to reveal the error message.

Updated:
- Mapping/ARCHER_OSCAL_MAPPINGS.csv
- notebooks/cells/07_mapper_orchestrator.py
- notebooks/cells_v2/07_mapper_orchestrator.py

## Next action
If the one-time cleanup SQL has not yet been run, run it once. Do not rerun it if
it already returned LEVEL355_SINGLE_BAD_IMPLEMENTED_REQUIREMENT_REMOVED.

Then refresh the current mapping CSV and Cell 7, run Cell 2 -> Cell 3 -> Cell 7 in
PREVIEW mode. Cell 4 does not need to be rerun if the current session already has
the latest projected-VARIANT decode + malformed-child skip code loaded.
