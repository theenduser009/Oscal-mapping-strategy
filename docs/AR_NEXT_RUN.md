# Assessment Results - next run

Updated September 13, 2026. Use the existing seven-cell mapper and the updated
[maintained CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv).

## Scope now

| Scope | Status |
| --- | --- |
| SSP agreed mapping subset | Committed and read-back verified in DEV; the latest batch changed no rows. |
| SSP system implementation | Six component-reference mappings implemented; software/interconnection hydration is partial. This is part of SSP, not another model. |
| AR original 17 fields | Previously live accepted in memory; no AR database load is accepted. |
| AR next 13 fields | Enabled in the CSV through the existing scalar-score transform; local regression coverage, live preview pending. |
| Remaining 15 AR rows | Deferred for the specific decisions below; not counted as completed mappings. |
| POA&M | Reference mapping recorded; item source/identity, hierarchy and destination still need confirmation. |

SSP is not fully complete: the parked PTA/property-name corrections and Control
Implementation remain separate. See [SSP scope](SSP_DONE_AND_NEXT.md).
The owner's target is to progress AR, POA&M and remaining models by Monday;
that is a delivery target, not evidence of completed mapping or storage.

## Run AR30 in preview

1. Upload the revised `ARCHER_OSCAL_MAPPINGS.csv` to notebook Files.
2. In existing Cell One, set `SELECTED_MODELS = ("ASSESSMENT_RESULTS",)`.
   Preserve deployment settings and `CONFIG["EXECUTE_WRITES"] = False`.
3. In Cell Seven, set `OSCAL_LOAD_MODE = "PREVIEW"`.
4. Run matching Cells One through Seven in order in one session. No replacement
   runtime, separate AR mapper or registry reset is required.
5. Post Cell Three's AR routing summary and the complete `OSCAL_PIPELINE_REPORT`.

Expected signals: Cell Three is `READY` with `SELECTED_ROWS = 30`; Cell Seven
reports `PREVIEW_COMPLETE`, one AR group and
`MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING`, with writes false.
The missing destination contract is expected at this stage. Report actual
source/node/edge counts; the old 17-field counts are not AR30 expected counts.
Do not run the old standalone 34-field candidate.

## Destination evidence for AR and subsequent models

Run [READ_ONLY_OSCAL_DESTINATION_COLUMNS.sql](../notebooks/validation/READ_ONLY_OSCAL_DESTINATION_COLUMNS.sql)
in a Snowflake SQL worksheet and post its result. It requires no notebook
variables and reads only column metadata in the currently used DEV schema.
Completion is the result grid, including an empty result if no matching columns
are visible. Empty output does not prove absence from other schemas or roles.

Use the returned table names, key/UUID types and column definitions to bind AR
to its actual destination in Cell One. Reuse the existing Cell Six loader.
AR COMMIT remains unavailable until that destination is verified and the
expanded preview is accepted.

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
