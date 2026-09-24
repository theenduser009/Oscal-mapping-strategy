# Level-355 implemented-requirement first batch prepared — 2026-09-24

## Live evidence
Owner-provided Snowflake results establish the Level-355 working grain:

- matched Level-355 control rows = 127,496
- matched Authorization Packages = 1,895
- null ALLOCATED_CONTROL_ID rows = 0
- distinct ALLOCATED_CONTROL_ID values = 127,496
- distinct package + ALLOCATED_CONTROL_ID pairs = 127,496
- distinct package + CONTROL_NUMBER pairs = 127,473
- duplicate ALLOCATED_CONTROL_ID identity query = 0 rows
- Level-355 AUTHORIZATION_PACKAGE reverse-reference pairs = 1,895
- same-ID pairs = 1,895
- different-ID pairs = 0

Therefore:
- top-level Level-355 CONTENT_ID is package lineage;
- ALLOCATED_CONTROL_ID is the stable per-control instance identity;
- CONTROL_NUMBER must not be used as graph identity because package/control-number
  pairs are not unique for all rows;
- CONTROL_NUMBER is the first approved OSCAL payload field and maps to
  `implemented-requirements[].control-id`.

The displayed sample also shows some rows with populated implementation text, but
the earlier population query used VARIANT `IS NOT NULL` and can count JSON nulls
as present. Description/status fields are intentionally deferred to the next batch.

## Implementation changes
- Cell 1: added current Level-355 RAW as joined lookup source.
- Cell 2: loads joined lookup snapshots.
- Cell 3: added generic `joined-records` registry operator and LOOKUP_KEY handling.
- Cell 4: builds child collections by package CONTENT_ID and uses registry-defined
  child identity.
- cells_v2 01-04 synchronized with maintained cells.
- mapping CSV: added approved CONTROL_NUMBER -> implemented-requirement.control-id.
- registry SQL added:
  `sql/registry/ENABLE_SSP_CONTROL_IMPLEMENTATION_LEVEL355.sql`

No DIM/FACT DML has been performed by this change.

## Next action
1. Run `sql/registry/ENABLE_SSP_CONTROL_IMPLEMENTATION_LEVEL355.sql`.
2. Refresh notebook files from `simplify-metadata-boundary`.
3. Run Cells 1-7 with `SELECTED_MODELS=("SSP",)` and Cell 7 in PREVIEW.
4. Reconcile the new implemented-requirements[] node/edge delta before any commit.
