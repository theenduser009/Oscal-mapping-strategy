# Level-355 current RAW binding not found in first pass — 2026-09-21

## Owner-provided live evidence
The corrected Level-355 binding diagnostic completed against the current Source One
environment.

Confirmed:
- LEVEL_ID = 355
- LEVEL_NAME = CONTROL
- MODULE_ID = 549
- MODULE_NAME = ALLOCATED CONTROLS
- private reference sample size = 100
- current *_RAW candidate tables with both CONTENT_ID and CURATED_JSON = 45
- matching current RAW tables = none
- full-sample match tables = none
- result = LEVEL_355_CURRENT_RAW_BINDING_NOT_FOUND

## Interpretation
This does not yet prove that the current Level-355 source is absent. The first
binding search considered only current RAW tables that expose both CONTENT_ID and
CURATED_JSON. Some newer RAW ingestion tables may instead expose RAW_DATA or a
different VARIANT payload contract.

Historical structured/STG tables remain excluded from the future OSCAL runtime
source contract per owner direction.

## Status
- Level-355 business metadata: confirmed.
- First current RAW binding attempt: no match.
- Control Implementation mapping remains unresolved.
- No mapping CSV, registry, notebook mapper cell, or DIM/FACT target was changed.
- No DML occurred.

## Next action
Run the current root RUN_NOW.py. It performs a narrow schema-only inventory of
current ARCHER_CONTENT*_RAW tables whose names contain CONTROL or ALLOCAT and
prints only table/column metadata. Use that result to determine whether the
Level-355 source exists under a RAW_DATA-style contract before declaring a source
coverage gap.
