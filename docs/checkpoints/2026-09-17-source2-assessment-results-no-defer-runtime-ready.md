# Source 2 sources_source Assessment Results no-defer runtime ready — 2026-09-17

## Repository version

Branch: `simplify-metadata-boundary`
Implemented/read-back code head before this checkpoint: `6563d1f9f121d0c9e781f7b8419cc6621d47e0e9`.
Bot commit message: `Make all nonduplicate Source 2 Assessment Results mappings executable`.

## Owner decision superseding earlier status

For the `sources_source` Assessment Results model, a known mapping is not left `DEFERRED` merely because the current source value is empty. Empty approved fields remain executable and emit nothing. The confirmed duplicate/truncated `_OF_NONCOMPLIANT_CONTROLS` is the one intentional non-executable row and remains `EXCLUDED` so it cannot create a second `noncompliant-count` property.

This checkpoint supersedes the earlier 2026-09-17 runtime state in which six legitimate Assessment Results rows were present in `sources_source_runtime.csv` but marked `DEFERRED`.

## Ten-field runtime state

There are exactly 10 Source-tab Assessment Results mapping rows:

- 9 `APPROVED`
- 1 `EXCLUDED` duplicate alias
- 0 `DEFERRED`

Executable representation:

1. `COMPLIANCE_RATING` -> `assessment-results.results[].props[]`, property `compliance-rating`, `archer-select`.
2. `COUNT_OF_NONCOMPLIANT_CONTROLS` -> `assessment-results.results[].props[]`, property `noncompliant-count`, already committed/read-back verified.
3. `PCT_OF_NONCOMPLIANT_CONTROLS` -> `assessment-results.results[].props[]`, property `noncompliant-percentage`; current snapshot empty.
4. `_OF_NONCOMPLIANT_CONTROLS` -> `EXCLUDED` duplicate of the canonical count field.
5. `FINDINGS` -> `assessment-results.results[].findings[].props[]`, property `source-finding-reference`, `reference-ids`.
6. `FINDINGS_AUTHORITATIVE_SOURCES` -> finding property `authoritative-source-finding-reference`, `reference-ids`.
7. `CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT` -> finding property `test-result`.
8. `DEVIATIONS_AUTHORITATIVE_SOURCES` -> finding property `deviation`.
9. `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS` -> one finding property `linked-control-standard` per referenced control identifier, `reference-ids`.
10. `EVIDENCE_REPOSITORY` -> finding property `evidence-repository`.

The source mapping document's detailed workbook target remains preserved in `OSCAL_ELEMENT_PATH`. Where source data does not contain the child identity required to instantiate the workbook's deeper reviewed-control/observation structure safely, `RUNTIME_TARGET_PATH` uses a named OSCAL extension property at the available result/finding grain instead of fabricating IDs or creating duplicate model elements.

## Duplicate safeguards

- `_OF_NONCOMPLIANT_CONTROLS` is `EXCLUDED`.
- `COUNT_OF_NONCOMPLIANT_CONTROLS` is the only approved owner of property name `noncompliant-count`.
- Finding records are optional per source record: the new `optional-record` operator materializes a finding parent only when at least one mapped finding-descendant source field is populated.
- `properties` retains `SOURCE_FIELD_NAME+VALUE` identity, so repeated referenced control identifiers are de-duplicated deterministically rather than creating duplicate properties/nodes.

## Code changes

`notebooks/cells/03_canonical_mapping_contract.py`:
- supports reusable transform `reference-ids`;
- supports reusable registry operator `optional-record` with `SOURCE_RECORD_ID` identity;
- permits nested property collections below an optional record parent.

`notebooks/cells/04_parsing_transform_payload_helpers.py`:
- reference extraction recognizes singular `ContentId` as well as existing containers;
- `reference-ids` extracts source reference identifiers without interpreting them as hrefs;
- `_metadata_descendant_has_value` detects whether an optional parent is needed;
- `optional-record` emits no empty finding parent when every descendant source field is absent/empty.

`Mapping/sources_source_runtime.csv`:
- all nine nonduplicate Assessment Results rows are `APPROVED`;
- the duplicate alias remains `EXCLUDED`;
- no Assessment Results row remains `DEFERRED`.

`Mapping/sources_source_assessment_results_mapping.csv`:
- repaired as a well-formed 10-row audit contract;
- records the executable runtime representation while retaining the workbook target separately.

## Registry change prepared, not yet owner-run

`sql/registry/ENABLE_ASSESSMENT_RESULTS_FINDING_BRANCH_FULL.sql` is prepared and committed. It is registry-only DML and does not write Assessment Results DIM/FACT targets. It idempotently establishes:

- `assessment-results.results[].findings[]` as an `optional-record` collection keyed by `SOURCE_RECORD_ID`;
- `assessment-results.results[].findings[].props[]` as a `properties` collection keyed by `SOURCE_FIELD_NAME+VALUE`.

A successful owner run must return `AR_FULL_FINDING_BRANCH_REGISTRY_VERIFIED`, `ACTIVE_ROWS=2`, `COMMITTED=true` before the full runtime PREVIEW.

## Validation actually performed

Corrected guarded GitHub Actions run `35263331339` completed all workflow steps successfully before the bot commit:

- reusable patch tool applied successfully;
- Cell 3 and Cell 4 Python syntax compiled;
- reference extraction smoke checks passed;
- optional finding-parent descendant detection smoke checks passed;
- ten-field contract check passed: 10 AR rows, 9 approved, 1 excluded, zero deferred;
- duplicate noncompliant-count ownership check passed;
- generated notebook synchronization passed;
- generated notebook synchronization read-back check passed;
- `git diff --check` passed;
- bot commit/push succeeded.

A prior broader pytest attempt in an earlier workflow did not run because its runner lacked `pandas` and the repository test import path; that failed setup is not counted as a mapper test pass. No Snowflake execution is implied by the GitHub Actions validation above.

## Live Snowflake status and next checkpoint

Already live/verified: the earlier one-field Source 2 Assessment Results batch remains committed/read-back verified at 444 DIM nodes and 296 FACT edges for 148 source records.

Not yet live-tested: the full nine-approved-row no-defer runtime described here.

Next action:
1. Owner runs `sql/registry/ENABLE_ASSESSMENT_RESULTS_FINDING_BRANCH_FULL.sql` and returns the verification object.
2. Owner updates Snowflake notebook Cells 3 and 4 plus `sources_source_runtime.csv` from this branch.
3. Keep Cell 1 `SELECTED_MODELS=("ASSESSMENT_RESULTS",)` and `EXECUTE_WRITES=False`; Cell 7 remains `PREVIEW`.
4. Run Cells 1 through 7 and return the Source 2 group report.
5. Do not COMMIT until that full-model PREVIEW is reviewed.
