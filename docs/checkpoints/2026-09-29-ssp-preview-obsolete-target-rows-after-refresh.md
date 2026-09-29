# SSP PREVIEW blocked by obsolete target rows after refreshed Source One load

Date: September 29, 2026
Status: Owner-posted Snowflake notebook screenshot reviewed. No writes were executed.

## Owner-posted pipeline evidence

The Source One / SSP run returned:
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

This is a loader safety stop. It means at least one row currently stored in the loader's scoped SSP DIM/FACT target is absent from the newly generated candidate graph.

The screenshot does not establish which rows are obsolete or why. Do not assume the cause is Meta User enrichment, RequestedObject.Id, Level-355 cleanup, or ordinary source drift until the exact rows are classified.

## Important runtime detail

Current Cell 6 creates temporary N/E/D/F/BD/BF stage tables before running the obsolete-row preflight. If _load_preflight raises during _load_prepare, the context is never returned and the normal cleanup path does not remove that failed run's temporary tables.

Therefore the failed PREVIEW's exact candidate tables should still be inspectable in the same Snowflake notebook session. Do not rerun Cell 7 yet, because a rerun would create a new candidate stage and make diagnosis less direct.

## Diagnostic published

Path:
- notebooks/validation/12_ssp_obsolete_target_rows_diagnostic.py

Publication commit:
- 75bf7ce6451ed2b49de9febfbedff37f634ee843

Read-back blob:
- db36149cb0af0cfbbdb8422624f0fbf6ecf096ca

The diagnostic is read-only. It:
- discovers the newest complete TMP_OSCAL_* stage set in the current session;
- reproduces Cell 6 DIM/FACT scope logic;
- counts obsolete DIM and FACT rows;
- groups obsolete DIM rows by ELEMENT_TYPE;
- classifies whether the new graph has the same SOURCE_RECORD_ID + ELEMENT_TYPE under a different key;
- lists up to 25 affected source-record IDs and element types;
- summarizes obsolete FACT rows by DEPENDENCY_TYPE.

No payload values are printed and no temp tables are dropped.

## Next action

In the same notebook session, run only notebooks/validation/12_ssp_obsolete_target_rows_diagnostic.py and return its printed output. Do not rerun Cell 7 and do not delete/merge target rows before the obsolete rows are identified.
