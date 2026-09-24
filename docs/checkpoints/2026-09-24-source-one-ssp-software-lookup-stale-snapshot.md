# Source One SSP software lookup snapshot stale — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before this checkpoint: `c02da5b30a9fc364c01bb57012e3d58a1a89933d`

## Owner-provided live Snowflake evidence
The corrected component hydration diagnostic completed.

Source One:
- SOURCE_SELECTED_ROWS = 2,813

Software references:
- SOFTWARE distinct references = 7
- REQUIRED_DISTINCT_REFERENCES = 7
- frozen software lookup rows = 0
- frozen software distinct IDs = 0
- frozen matched references = 0
- frozen missing references = 7
- live software RAW rows = 15,619
- live software distinct IDs = 15,619
- live matched references = 7
- live missing references = 0

Interconnection references:
- INTERCONNECTIONS distinct references = 1,405
- INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM distinct references = 82
- combined required distinct interconnection references = 1,428
- frozen interconnection lookup rows = 2,140
- frozen matched references = 1,428
- frozen missing references = 0
- live interconnection RAW rows = 2,140
- live matched references = 1,428
- live missing references = 0

Result:
`LIVE_LOOKUPS_COMPLETE_RERUN_CELL_2_THEN_3_AND_7`

## Interpretation
The SSP graph failure is explained by a stale Cell-2 software lookup snapshot.
Cell 2 froze `ARCHER_CONTENT_SOFTWARE_RAW` while it contained zero rows, but the
live table has since repopulated and contains all 7 software ContentIds required by
the current Source One snapshot.

The interconnection lookup is already complete in both frozen and live state.

No mapper logic or mapping contract change is required.

## Next action
In the same notebook session:
1. rerun Cell 2 to refresh Source One and component lookup snapshots;
2. rerun Cell 3 to compile against the refreshed inputs;
3. rerun Cell 7 with `OSCAL_LOAD_MODE = "PREVIEW"`.

Cells 4-6 do not need to be rerun if their function definitions remain loaded in
the same session.

Do not run COMMIT until the refreshed SSP PREVIEW succeeds and the expected
authorization-decision delta is reconfirmed.
