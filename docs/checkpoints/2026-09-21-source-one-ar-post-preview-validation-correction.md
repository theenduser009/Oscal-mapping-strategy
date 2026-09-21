# Source One AR post-preview validation correction — 2026-09-21

## Why this checkpoint exists
The first post-preview validation SQL incorrectly assumed that
`ARCHER_OSCAL_MAPPINGS.csv` was materialized as the Snowflake table
`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_OSCAL_MAPPINGS`. That assumption was wrong for
this mapper architecture.

The mapper's actual contract remains:
- Cell 2 loads `Mapping/ARCHER_OSCAL_MAPPINGS.csv` from the notebook/runtime filesystem.
- Cell 3 compiles that CSV with the OSCAL element registry into `MAPPING_CONTEXTS`.
- Cell 7 runs PREVIEW/COMMIT from those compiled contexts.
No Snowflake mapping table is required or implied.

## Corrective repository changes
- Removed:
  `sql/validation/2026-09-21_source_one_ar_post_preview_mapping_check.sql`
- Added:
  `notebooks/validation/2026-09-21_source_one_ar_post_preview_compiled_check.py`

The replacement is read-only and runs in the same Snowflake notebook session
after Cells 1-7. It verifies the 12 newly approved Source One Assessment Results
fields directly from `MAPPING_CONTEXTS`, counts present/null/populated source
values without printing private values, and echoes the Source One AR preview
group from `PIPELINE_REPORT`.

## Evidence preserved
Owner-supplied PREVIEW screenshots on 2026-09-21 showed:
- Source One / ASSESSMENT_RESULTS: 2,813 source records, 90,016 nodes,
  87,203 edges, validation passed, storage verified, no target DML.
- Source Two / ASSESSMENT_RESULTS: 148 source records, 1,460 nodes,
  1,312 edges, with 296 proposed DIM updates, no target DML.

These screenshots establish PREVIEW evidence only. They do not establish a
Snowflake COMMIT for the newly approved Source One mappings.

## Next action
Run the new notebook validation file after Cells 1-7 and capture:
- ROUTE_STATUS
- SELECTED_ROWS_TOTAL
- NEW_FIELDS_COMPILED
- per-field PRESENT / NULL / POPULATED counts
- Source One AR PREVIEW status and expected changes

Do not create a Snowflake ARCHER_OSCAL_MAPPINGS table to satisfy the removed SQL.
