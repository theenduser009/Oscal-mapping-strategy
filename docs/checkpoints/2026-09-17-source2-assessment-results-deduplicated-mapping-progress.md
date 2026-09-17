# Source 2 sources_source Assessment Results deduplicated mapping progress — 2026-09-17

## Repository version

Branch: `simplify-metadata-boundary`
Repository head immediately before this checkpoint: `cc6e8d71add55fd26a23425ec6846ac48705d8b1`.

## Owner direction

Assessment Results is being completed as one model before moving to Component Definition or Topic. Mapping rows are not deferred merely because the current source value is null. Current nulls mean a valid mapping emits no runtime node until data is populated.

Duplicate protection is mandatory: one business mapping has one canonical executable owner. Duplicate/truncated source aliases must not create a second node/property for the same target.

## Ten Source-tab Assessment Results fields

The model-specific mapping contract is:

`Mapping/sources_source_assessment_results_mapping.csv`

It contains all ten Source-tab Assessment Results fields and distinguishes workbook intent, canonical runtime target, current source shape, runtime readiness, identity gates, and duplicate ownership.

## Executable mappings now present

`Mapping/sources_source_runtime.csv` currently contains these Source 2 Assessment Results rows:

1. `COUNT_OF_NONCOMPLIANT_CONTROLS`
   - target: `assessment-results.results[].props[]`
   - property: `noncompliant-count`
   - implemented, committed, and Snowflake read-back verified.

2. `PCT_OF_NONCOMPLIANT_CONTROLS`
   - target: `assessment-results.results[].props[]`
   - property: `noncompliant-percentage`
   - approved/runtime-ready.
   - current source snapshot: 0 populated rows; therefore it should emit no node in the current preview.

3. `_OF_NONCOMPLIANT_CONTROLS`
   - explicitly `EXCLUDED` as the duplicate/truncated alias for the canonical noncompliant-count mapping.
   - it has no transform, no runtime target, and cannot create a duplicate property.

4. `FINDINGS`
   - target: `assessment-results.results[].findings[]`
   - approved as a reference collection keyed by referenced `ContentId`.
   - current source snapshot: 0 populated rows; therefore it should emit no finding node now.
   - registry extension prepared in `sql/registry/ENABLE_ASSESSMENT_RESULTS_FINDINGS_REFERENCE.sql`.

## Registry change prepared

`sql/registry/ENABLE_ASSESSMENT_RESULTS_FINDINGS_REFERENCE.sql` adds only:

`assessment-results.results[].findings[]`

with:

- parent: `assessment-results.results[]`
- collection: true
- identity: `CONTENT_ID`
- item path: `$`
- operator: `references`
- UUID policy: `node`

The script verifies the existing accepted `results[]` parent first, rejects duplicate/conflicting finding rows, performs an idempotent MERGE, and reads the row back before COMMIT. It changes registry metadata only; it performs no target DIM/FACT DML.

## Remaining mapped fields with runtime identity gates

The following are mapped in the model contract but are not executable until their required parent/reference identity exists. They are not classified as unmapped simply because current data is null:

- `COMPLIANCE_RATING` — reviewed-control/control-id identity gate; do not fabricate control IDs.
- `FINDINGS_AUTHORITATIVE_SOURCES` — related observation identity gate.
- `CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT` — finding parent identity gate.
- `DEVIATIONS_AUTHORITATIVE_SOURCES` — finding parent identity gate.
- `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS` — finding/observation/control relationship identity gate; 21 current rows are populated.
- `EVIDENCE_REPOSITORY` — observation parent + URI-reference identity gate.

## Mapping workbook

A refreshed project copy of `archer_authoritative_sources_oscal_mappings.xlsx` has been generated with the Source-tab Assessment Results review rows updated to the above statuses. The binary GitHub workbook has not been claimed updated by this checkpoint unless a later binary commit/read-back explicitly proves it.

## Next action

1. Run `sql/registry/ENABLE_ASSESSMENT_RESULTS_FINDINGS_REFERENCE.sql`.
2. Confirm status `AR_FINDINGS_REFERENCE_REGISTRY_VERIFIED`, `ACTIVE_ROWS=1`, `COMMITTED=true`.
3. Replace the Snowflake notebook copy of `sources_source_runtime.csv` with the latest GitHub version.
4. Keep `SELECTED_MODELS=("ASSESSMENT_RESULTS",)`.
5. Change Cell 7 back to `PREVIEW`.
6. Run Cells 1–7 in order.
7. The Source 2 graph is expected to remain 444 DIM / 296 FACT for the current snapshot because the two newly executable fields are currently unpopulated and the duplicate alias is excluded.
8. Stop before COMMIT and review the preview output.
