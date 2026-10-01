# SSP selective lineage preview checkpoint — 2026-10-01

Previous repository checkpoint: `d9f07dcc7fe682c5650f3c65ca0ffac15a42ec88`.

Owner-provided Snowflake PREVIEW evidence after loading the updated mapping sheet:
- pipeline `PREVIEW_COMPLETE`
- source/model `source-one / SSP`
- `writes_executed=false`
- `target_dml_attempted=false`
- validation and storage checks passed
- 2,813 source records
- 550,380 candidate nodes / 547,567 candidate edges
- DIM expected changes: 3,581 inserts / 0 updates / 546,799 unchanged
- FACT expected changes: 3,581 inserts / 0 updates / 543,986 unchanged
- `LINEAGE_PROPS=3581`
- `LINEAGE_GAPS=0`
- `LINEAGE_COMPLETE=true`

Interpretation: this supersedes the immediately prior preview where `LINEAGE_PROPS=0`. It is PREVIEW evidence only, not COMMIT/read-back evidence.

This update adds the read-only notebook helper:
`notebooks/validation/16_ssp_selective_lineage_sample.py`
at commit `46340d7be6b91b968a85fd1c4121cbe226ec6339`.

Evidence boundary: the user loaded an updated mapping sheet directly into the notebook. This checkpoint does not establish that that notebook-loaded mapping sheet is already committed to GitHub or packaged for the eventual remote deployment.

Next action: use the helper to inspect a small sample of candidate lineage props and confirm the minimal `source-field` structure before any COMMIT.
