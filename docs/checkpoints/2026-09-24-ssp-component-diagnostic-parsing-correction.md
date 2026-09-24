# Correction: SSP component hydration diagnostic source parsing — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before correction: `70e4040b02e61ecfd5a08a73b012baaa03f6328c`

## Why this supersedes the prior coverage interpretation
The previous component-hydration aggregate helper reported zero SOFTWARE and
interconnection references, while a subsequent graph build still raised:
`Component hydration lookup record is missing`.

Review of the actual mapper code identified a diagnostic mismatch:
- the graph builder parses CURATED_JSON with `_metadata_parse()`;
- `_metadata_parse()` JSON-decodes the value when Snowpark returns VARIANT as
  a Python string;
- the prior aggregate helper only accepted already-materialized Python dicts and
  skipped string-form CURATED_JSON records.

Therefore the prior conclusion that all component-reference counts were zero is
not reliable and is superseded by this checkpoint.

## Important live clue retained
The prior helper did reliably read lookup-table counts:
- frozen software lookup rows = 0
- live software RAW rows = 15,619
- frozen interconnection lookup rows = 2,140
- live interconnection RAW rows = 2,140

Given the graph-builder error, stale/empty frozen software lookup coverage is now
a leading hypothesis, but it must be verified against correctly parsed source
references before refreshing Cell 2.

## Corrected diagnostic
Root `RUN_NOW.py` now:
- reuses the mapper's own `_metadata_parse()`
- reuses `resolve_json_path()` and `_component_reference_content_ids()`
- compares correctly parsed source references against frozen and live lookup data
- prints aggregate match/missing counts only

## Next action
Run only the corrected root `RUN_NOW.py`.

If it returns `LIVE_LOOKUPS_COMPLETE_RERUN_CELL_2_THEN_3_AND_7`, refresh Cell 2
so its component lookup snapshots match the live source and then rerun Cell 3 and
Cell 7 PREVIEW.

Do not weaken the component hydration contract or attempt COMMIT until verified.
