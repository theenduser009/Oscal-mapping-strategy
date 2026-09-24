# Level-355 joined-record out-of-memory correction — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head after Cell 4 optimization: `90bf3a6a78ab443bbd8fbb1ca88958e6233e73dc`

## Owner-provided live evidence
The Snowflake notebook session ended with an out-of-memory message while running
the Level-355 SSP joined-record diagnostic/build.

The first Level-355 batch can involve approximately 127,496 matched child control
rows across 1,895 Authorization Packages.

## Root cause in mapper code
The initial generic joined-record implementation streamed every matched Level-355
row into Python with the **entire CURATED_JSON object** and retained those objects
in a parent-keyed dictionary before graph construction.

Each Level-355 CURATED_JSON contains a large control record with many fields.
Retaining roughly 127k complete records in Python is unnecessarily memory-heavy.

This is an implementation-memory issue, not evidence of bad source data or an
invalid Level-355 mapping.

## Correction
Cell 4 now pushes projection into Snowflake before rows are streamed to Python.

For each joined-record binding, it keeps only:
- the package join key;
- the registry identity field (currently ALLOCATED_CONTROL_ID);
- source fields actually used by approved mappings (currently CONTROL_NUMBER).

The full Level-355 CURATED_JSON is no longer retained in Python for this batch.

Updated maintained/generated files:
- notebooks/cells/04_parsing_transform_payload_helpers.py
- notebooks/cells_v2/04_parsing_transform_payload_helpers.py

No mapping decision, registry row, source data, DIM or FACT target was changed.

## Next action
The prior notebook session ended, so start a fresh session and run the current
Cells 1-7 from `simplify-metadata-boundary`.

Keep:
- SELECTED_MODELS = ("SSP",)
- OSCAL_LOAD_MODE = "PREVIEW"

Do not run COMMIT.

If PREVIEW still encounters memory pressure, the next optimization target is the
Python node/edge accumulation in Cell 5; do not increase warehouse size first as a
substitute for fixing avoidable client-side retention.
