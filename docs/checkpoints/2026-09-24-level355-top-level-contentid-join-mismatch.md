# Level-355 top-level ContentId join mismatch — targeted join-key check — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `24ceb81b478629d2ca4e4c39135dd89e885a04bd`

## Owner-provided live Snowflake evidence
The expected Level-355 table now exists:
`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`

Observed:
- table has 7 physical columns including RAW_DATA, CURATED_JSON and CONTENT_ID
- raw rows = 160,000
- distinct top-level CONTENT_ID values = 34,071
- null/blank top-level IDs = 0
- distinct Authorization Package Level-355 references reported by the prior query = 252,165
- exact top-level CONTENT_ID matches = 0
- missing references = 252,165
- the field profile from the prior helper was empty because it profiled only the zero-row matched set
- current registry does not yet expose an active implemented-requirements[] path

## Interpretation
Do not conclude that the Level-355 table is wrong yet. Zero exact matches across all
references strongly suggests either:
- the Authorization Package reference identity is stored in another field/path
  inside the Level-355 payload, or
- the current Level-355 dataset is not the same identity population referenced by
  the Authorization Packages.

## Next action
Root `RUN_NOW.py` now performs one narrow read-only join-key diagnostic:
- compares reference/top-level-ID shapes
- checks numeric-normalized top-level matches
- profiles key Level-355 fields on the current control records independently
- searches a deterministic 100-reference sample recursively in CURATED_JSON and
  RAW_DATA and prints only matching JSON paths

This is the fastest way to identify the actual join key without another broad
table search.
