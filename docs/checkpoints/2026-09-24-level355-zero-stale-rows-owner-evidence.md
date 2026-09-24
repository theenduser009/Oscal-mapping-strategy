# Level-355 recovery: zero stale rows observed; stop cleanup

Evidence date: 2026-09-24

## Repository basis and actual reads
- Repository: theenduser009/Oscal-mapping-strategy.
- Branch: simplify-metadata-boundary.
- Branch head read before this documentation update: 14ef0b5f22fb2fe23f587c506fbcf745589a5253.
- All file reads below were pinned to that commit.
- Read sql/validation/READ_LEVEL355_FAILED_CLEANUP_STATE.sql; blob cc7524191cba1f5a386be034fe43db3c726d20d7.
- Read the joined-record projection/identity and required-member handling in maintained Cell 4; blob a724b4328faa361827c04142fea993c27cd3ff25.
- Read maintained Cell 7; blob 78166e558cf99600d75e2995a7bae4144dad9534.
- Read the current CONTROL_NUMBER and IMPLEMENTATION_DETAILS mapping rows; CSV blob 7790f23e52767a7d4f5bc31226c1e26198e60557.

## Latest owner-provided Snowflake result
The owner returned a screenshot of READ_LEVEL355_FAILED_CLEANUP_STATE.sql output. Readable counts are:

| CHECK_NAME | OBSERVED_VALUE |
| --- | ---: |
| BAD_SOURCE_ROWS | 1 |
| PACKAGE_SOURCE_ROWS | 111 |
| GENERATED_VALID_KEY_ROWS | 220 |
| DISTINCT_NONNULL_VALID_KEYS | 220 |
| TARGET_ROWS_FOR_PACKAGE_BEFORE_METADATA_FILTERS | 149 |
| TARGET_IR_ROWS_AFTER_EXACT_METADATA_FILTERS | 110 |
| TARGET_IR_ROWS_MATCHING_VALID_KEYS | 110 |
| STALE_ROWS_CAPTURED_BY_FAILED_CLEANUP | 0 |
| DISTINCT_STALE_KEYS | 0 |
| PACKAGE_KEY_MATCHES_WITHOUT_METADATA_FILTERS | 110 |
| ALL_TARGET_ROWS_IN_CONFIGURED_TABLE | 250844 |

Stored source namespace/type labels for the affected package match ARCHER / ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW. Its implemented-requirements count is 110. Other visible element-type counts reconcile to 149 total package DIM rows.

The BAD_SOURCE, PACKAGE_SOURCE, VALID_KEYS and STALE_IR measurements read temporary artifacts retained from the failed cleanup. The package target counts and total configured DIM count read the target at inspection time. This is owner-supplied query evidence, not a direct assistant database read.

## Interpretation and supersession
1. The failed cleanup captured ZERO stale target rows, not multiple rows. That explains its exact-one STALE_SHAPE failure.
2. For the affected package, all 110 scoped target implemented-requirement rows match the generated valid-key candidate set. There is no row identified for deletion by this check.
3. The 111 source rows include one source row without a defensible CONTROL_NUMBER, leaving 110 usable source controls. Do not invent a number for the malformed source row.
4. The observed configured DIM total is 250,844, one less than the earlier first-batch committed report of 250,845. This is consistent with the malformed child no longer being present in the affected target package. It does not establish which earlier operation changed the target, when, or whether a corresponding FACT edge was removed.
5. The 220 distinct non-null key candidates show that the two generated representations do not collapse to a single key per valid sibling in this observed package. Earlier assertions that duplicate candidate counting was the proven cause are not supported by this result.
6. This checkpoint supersedes prior instructions to rerun the one-row cleanup and prior claims that exactly one stale target row was still present. STOP all cleanup retries. Do not loosen or bypass the loader's obsolete-row guard.

## Current code decisions retained
- Parent join: Level-355 CONTENT_ID to Authorization Package CONTENT_ID.
- Child instance identity: ALLOCATED_CONTROL_ID, retaining the first-batch projected representation in current Cell 4; mapped payload values are decoded separately.
- CONTROL_NUMBER -> implemented-requirements[].control-id, VALUE_REQUIRED=false at mapping level; the registry-required member determines child validity.
- A joined child missing the registry-required member is skipped and counted in SKIPPED_JOINED_RECORDS.
- IMPLEMENTATION_DETAILS -> implemented-requirements[].description remains mapped. Its later payload updates are NOT committed/read-back verified by this count inspection.
- OVERALL_IMPLEMENTATION_DETAILS is not silently substituted for IMPLEMENTATION_DETAILS.

## Validation and limits
Performed: screenshot interpretation, arithmetic reconciliation, pinned repository reads of the relevant diagnostic/runtime/mapping code.
Changed: this evidence checkpoint only. No mapper, CSV, registry, cleanup SQL, source, DIM, or FACT changes were performed.
No new synthetic tests were run because no executable code was changed. No live Snowflake execution was performed by the assistant.
The result does not establish global key parity against the current notebook graph, current FACT integrity, full OSCAL conformance, or a successful new PREVIEW/COMMIT.

## One next action
In the existing notebook session with current successful Cells 1-3 and Cell 6 still loaded, replace Cell 4 with the current maintained notebooks/cells/04_parsing_transform_payload_helpers.py from simplify-metadata-boundary, run Cell 4, then run the current Cell 7 with OSCAL_LOAD_MODE="PREVIEW". Keep shared EXECUTE_WRITES=False.

Do not rerun cleanup, COMMIT_NOW.py, the fallback profiler, or another deletion script. Do not refresh the frozen source inputs merely for this retry. Return the PREVIEW pipeline report so the current complete DIM/FACT comparison, including any remaining identity mismatch, can be evaluated before any further write.
