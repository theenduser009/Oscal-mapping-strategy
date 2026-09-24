# SSP component diagnostic helper import fix — 2026-09-24

## Owner-provided live evidence before helper failure
The corrected component diagnostic successfully parsed current Source One component references before stopping:

- SOURCE_SELECTED_ROWS = 2,813
- SOFTWARE distinct references = 7
- INTERCONNECTIONS distinct references = 1,405
- INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM distinct references = 82

For SOFTWARE, before the helper stopped:
- REQUIRED_DISTINCT_REFERENCES = 7
- frozen software lookup present = true
- frozen software lookup rows = 0
- frozen software distinct IDs = 0
- live software RAW rows = 15,619
- live software distinct IDs = 15,619

The helper then failed with:
`NameError: name 'F' is not defined`

## Interpretation
This is a diagnostic-helper bug, not a mapper or source-data conclusion. The
corrected reference counts supersede the earlier false zero-reference result.

The graph-builder failure remains:
`Component hydration lookup record is missing`

The current leading hypothesis is that Cell 2 froze the software lookup during an
empty software RAW window, while the live software table later repopulated.
That hypothesis is not yet proven because the helper failed before calculating
live/frozen reference matches.

## Correction
Root `RUN_NOW.py` now imports Snowpark functions as `F` and otherwise preserves
the same read-only aggregate coverage check.

## Next action
Run only the current root `RUN_NOW.py` again. Do not rerun mapper cells and do
not commit until the frozen/live match counts are returned.
