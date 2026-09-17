# Source 2 sources_source Assessment Results PREVIEW pass — 2026-09-17

## Repository version

Branch: `simplify-metadata-boundary`
Repository head immediately before this checkpoint: `321533b9a30fa6cb1bcc2bb4dd300e2ecdfcdfd3`.

## Evidence basis

Owner-provided Snowflake notebook screenshots from the universal seven-cell mapper run on 2026-09-17 with `SELECTED_MODELS = ("ASSESSMENT_RESULTS",)` and Cell 7 in PREVIEW.

## Source One Assessment Results route

The existing Source One route remained stable:

- source: `source-one`
- model: `ASSESSMENT_RESULTS`
- mode: `PREVIEW`
- source records: 2,813
- nodes: 90,016
- edges: 87,203
- expected DIM changes: 0 inserts / 0 updates / 90,016 unchanged
- expected FACT changes: 0 inserts / 0 updates / 87,203 unchanged
- status: `PREVIEW_PASSED_NO_TARGET_DML`
- writes executed: false
- target DML attempted: false

This is fresh evidence that the new Source Two route did not disturb the established Source One Assessment Results target comparison in this preview.

## Source Two sources_source Assessment Results route

The new Source Two route passed validation:

- source: `source-two-source`
- model: `ASSESSMENT_RESULTS`
- mode: `PREVIEW`
- source records: 148
- nodes: 444
- edges: 296
- pre-write validation passed: true
- validation passed: true
- storage verified: true
- expected DIM changes: 444 inserts / 0 updates / 0 unchanged
- expected FACT changes: 296 inserts / 0 updates / 0 unchanged
- status: `PREVIEW_PASSED_NO_TARGET_DML`
- writes executed: false
- target DML attempted: false

Structural reconciliation:

- 148 Assessment Results root nodes
- 148 `assessment-results.results[]` nodes
- 148 `assessment-results.results[].props[]` nodes for `COUNT_OF_NONCOMPLIANT_CONTROLS`
- total nodes = 148 + 148 + 148 = 444
- edges = 148 root-to-result + 148 result-to-property = 296

The promoted Source Two mapping is:

- `COUNT_OF_NONCOMPLIANT_CONTROLS`
- target: `assessment-results.results[].props[]`
- property name: `noncompliant-count`

## Status distinction

- Source Two Assessment Results runtime route: implemented in GitHub and read-back verified.
- Source Two Assessment Results PREVIEW: owner-run and screenshot read-back verified PASS.
- Source Two Assessment Results COMMIT: not yet attempted / not yet authorized in this checkpoint.

## Important remaining scope

This preview covers only the newly promoted safe Source Two Assessment Results mapping for `COUNT_OF_NONCOMPLIANT_CONTROLS`. Other populated Source-tab Assessment Results fields, including `COMPLIANCE_RATING` and `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS`, remain unresolved for model-grain / relationship semantics and are not claimed complete here.

The Excel audit workbook also still needs to be brought into sync with the latest executable runtime decisions; the runtime CSV, not the XLSX, drove this preview.
