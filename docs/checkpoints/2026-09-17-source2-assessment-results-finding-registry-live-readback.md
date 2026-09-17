# Source 2 Assessment Results finding registry live read-back — 2026-09-17

Branch inspected before checkpoint: `simplify-metadata-boundary` at `c893e4691003ee1fe1c603b822ff927c48ac9a69`.

Owner-provided Snowflake screenshot shows six active `ASSESSMENT_RESULTS` registry rows after the full finding-branch registry update.

Visible live read-back confirms these two newly added paths:

- `assessment-results.results[].findings[]`
  - element type: `findings`
  - parent: `assessment-results.results[]`
  - collection: `TRUE`
  - instance key rule: `SOURCE_RECORD_ID`
  - process order: `5`
  - active: `TRUE`

- `assessment-results.results[].findings[].props[]`
  - element type: `props`
  - parent: `assessment-results.results[].findings[]`
  - collection: `TRUE`
  - instance key rule: `SOURCE_FIELD_NAME+VALUE`
  - process order: `6`
  - active: `TRUE`
  - item path visible as `$`

The screenshot also shows the pre-existing four active Assessment Results rows remain present: root, `results[]`, `results[].props[]`, and `results[].observations[]`.

Evidence limitation: the screenshot viewport does not show the `OPERATOR`, `UUID_POLICY`, or any columns to the right of `ITEM_PATH`, so this checkpoint does not independently re-verify those hidden columns from Snowflake. The repository SQL/code defines the intended contracts; live screenshot verifies the visible path/parent/collection/identity/order/active columns.

Status distinction:
- Registry change: owner-run and live read-back verified for the visible columns above.
- Runtime mapper code: GitHub committed and tested at implementation commit `6563d1f9f121d0c9e781f7b8419cc6621d47e0e9`.
- Full 10-field Source 2 Assessment Results Snowflake PREVIEW with the latest Cell 3 / Cell 4 / runtime CSV: still pending.
- No new DIM/FACT COMMIT is authorized by this checkpoint.

Next action: replace the Snowflake notebook copies of Cell 3, Cell 4, and `sources_source_runtime.csv` with the latest GitHub versions, keep `SELECTED_MODELS=("ASSESSMENT_RESULTS",)` and Cell 7 in `PREVIEW`, then run Cells 1–7 and return the pipeline report before any COMMIT.
