# Assessment Results - accepted load and future runs

Updated September 13, 2026. Use the existing seven-cell mapper and the updated
[maintained CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv).

## Current acceptance

The [posted AR COMMIT](checkpoints/2026-09-13-assessment-results-commit-completed-and-verified.md)
inserted 73,189 DIM elements and 70,376 FACT relationships for 2,813 source
records, then verified committed readback. Status is COMMITTED_AND_VERIFIED.
AR storage is accepted for this mapped graph. Do not repeat this unchanged run
or the empty-table DDL; the tables are now populated. The next selected model
work is POA&M. Instructions below apply only to future intended data loads.

## Scope now

| Scope | Status |
| --- | --- |
| SSP agreed mapping subset | Committed and read-back verified in DEV; the latest batch changed no rows. |
| SSP system implementation | Six component-reference mappings implemented; software/interconnection hydration is partial. This is part of SSP, not another model. |
| AR original 17 fields | Original in-memory baseline retained; current shared AR graph is now persisted/read-back verified. |
| AR next 13 fields | Enabled in the CSV through the existing scalar-score transform; current shared AR graph persisted/read-back verified; individual populated-field coverage remains separate. |
| Remaining 15 AR rows | Deferred for the specific decisions below; not counted as completed mappings. |
| POA&M | Reference mapping recorded; item source/identity, hierarchy and destination still need confirmation. |

SSP is not fully complete: the parked PTA/property-name corrections and Control
Implementation remain separate. See [SSP scope](SSP_DONE_AND_NEXT.md).
The owner's target is to progress AR, POA&M and remaining models by Monday;
that is a delivery target, not evidence of completed mapping or storage.

## Future intended AR loads

1. Keep the already updated AR30 mapping CSV in notebook Files. Replace
   [Cell One](../notebooks/cells/01_initialization_and_configuration.py) with the
   version containing the AR storage contract; Cells Two through Seven are unchanged.
2. In existing Cell One, set `SELECTED_MODELS = ("ASSESSMENT_RESULTS",)`.
   Preserve deployment settings and `CONFIG["EXECUTE_WRITES"] = False`.
3. Confirm AR's tables match the [shared definition](../sql/CREATE_ASSESSMENT_RESULTS_TABLES.sql).
   Both DIM timestamps are TIMESTAMP_TZ(9), as in SSP. The SQL creates missing
   tables only; it does not replace existing rows or repair an existing schema.
   Set Cell Seven's `OSCAL_LOAD_MODE = "COMMIT"` for the owner-authorized load.
   Use `PREVIEW` instead if a separate no-write comparison is desired.
4. Run matching Cells One through Seven in order in one session. No replacement
   runtime, separate AR mapper or registry reset is required.
5. Post Cell Three's AR routing summary and the complete `OSCAL_PIPELINE_REPORT`.

Expected signals: Cell Three is `READY` with `SELECTED_ROWS = 30`; Cell Seven
first previews the route and validates the live schema before DML. COMMIT
success is `COMMITTED_AND_VERIFIED`, one AR group, writes/persisted/committed
true and successful DIM/FACT verification. In PREVIEW, require
`PREVIEW_PASSED_NO_TARGET_DML` with storage/pre-write validation true and writes
false. Report actual source/node/edge and insert/update/unchanged counts;
the old 17-field counts are not AR30 expected counts.
Do not run the old standalone 34-field candidate.

## Shared storage rules

The [owner decision](checkpoints/2026-09-13-ar-shared-ssp-storage-contract.md)
confirms identical SSP physical rules for AR and future models, with different
table/key names. Use the full-name AR pair in Cell One; the abbreviated AR DIM
is not selected. Exact source/model/root identity checks remain enforced.
The live schema has not been read from this workstation. A reported
TARGET_SCHEMA_MISMATCH means actual AR columns still differ; reconcile them
with the standard before rerunning. Do not bypass the checks or drop rows.
An unknown commit outcome or failed committed readback requires inspection,
not an automatic retry.

## Thirteen additions and their existing approval

All use one observation per populated source field, with one named inline
scalar property. Original alternative target paths and Notes remain intact;
the explicit runtime target is `assessment-results.results[].observations[]`.
The [September 11 owner approval](ASSESSMENT_RESULTS_START_HERE.md#approved-alternative-path-batch---seventeen-more-fields-pending-live)
already defines this representation. No score or threshold is calculated.

- `TOTAL_PACKAGE_RESIDUAL_RISK`
- `ADJUSTED_TOTAL_RISK_SCORE`
- `ADJUSTED_AVERAGE_RISK_SCORE`
- `CURRENT_HIGHEST_DEVICE_RISK_SCORE`
- `CURRENT_AVERAGE_DEVICE_RISK_SCORE`
- `CURRENT_CONTROL_RISK_SCORE`
- `PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD`
- `PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD`
- `BASELINE_HIGHEST_DEVICE_RISK_SCORE`
- `BASELINE_AVERAGE_DEVICE_RISK_SCORE`
- `BASELINE_CONTROL_RISK_SCORE`
- `RISK_ASSESSMENT`
- `INITIAL_RISK_ASSESSMENT`

Both PCT threshold fields and INITIAL_RISK_ASSESSMENT had no populated evidence
in the historical candidate. Synthetic tests cover them; populated live
acceptance is still needed.

## Remaining decisions

- Two current-risk threshold names: historical approval retains leading
  underscores; the maintained CSV does not. Resolve source-name provenance
  before enabling either row; no alias fallback is introduced.
- Two average-compliance rows: the historical transcription duplicated a name;
  the maintained CSV contains distinct score/reporting names. Prior deferral
  remains until the exact mapping rows are reconciled.
- `RISK_ACCEPTANCE_RBDS`: define the intended reference representation.
- `RISK_ASSESSMENT_REPORT`: define the meaning of its multiple numeric values.
- `TOTAL_PACKAGE_INHERENT_RISK`: reconcile the original target/Notes.
- `FINDINGS`: establish finding source, UUID identity and result association.
- Seven workflow audit rows remain owner-deferred.

Current inventory is 45 AR-target row occurrences: 17 live accepted + 13
enabled/pending live + 15 deferred. Full AR/OSCAL conformance and AR persistence
are separate from this field-mapping increment.

SQL creation behavior follows [Snowflake CREATE TABLE](https://docs.snowflake.com/en/sql-reference/sql/create-table).
IF NOT EXISTS leaves an existing table unchanged; OR REPLACE is not used.
