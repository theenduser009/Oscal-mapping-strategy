# SSP PREVIEW still blocked after allocated-controls source loaded

Date: September 29, 2026
Status: Owner-posted Snowflake screenshot reviewed. No target write or commit occurred.

## Owner-posted evidence

After ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW finished loading, the Source One / SSP PREVIEW still returned:
- mode = PREVIEW
- status = FAILED_BEFORE_COMMIT
- writes_executed = false
- commit_attempted = false
- target_dml_attempted = false
- failed_route = source-one / SSP
- error_type = LoadError
- load status = OBSOLETE_TARGET_ROWS_BLOCKED
- phase = PREPARATION
- pre_write_validation_passed = false

This proves that merely repopulating the allocated-controls source did not clear the failure.

## Remaining cache caveat

Current Cell 2 freezes joined lookup inputs with cache_result(). If Cell 2 was not rerun after the allocated-controls table completed loading, the notebook can still be using the earlier empty cached snapshot.

Therefore:
- if Cell 2 was not rerun after source completion, refresh Cell 2 first and rerun dependent graph cells;
- if Cell 2 was rerun after source completion and the same failure remains, the empty-table explanation is ruled out as the sole cause.

## Next diagnostic

Use the existing read-only diagnostic:
notebooks/validation/12_ssp_obsolete_target_rows_diagnostic.py

Current read-back blob:
db36149cb0af0cfbbdb8422624f0fbf6ecf096ca

Run it in the same notebook session immediately after the failed PREVIEW. It inspects the failed run's TMP_OSCAL_* candidate tables and identifies:
- obsolete DIM / FACT counts;
- affected element types;
- affected source records;
- whether same source-record + element-type exists under a different key;
- obsolete dependency types.

Do not delete target rows, rerun cleanup scripts, or commit until the exact obsolete rows are classified.
