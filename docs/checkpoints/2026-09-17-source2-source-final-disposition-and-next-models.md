# Source 2 sources_source final disposition and next-model readiness — 2026-09-17

## Repository checkpoint

Branch immediately before this checkpoint: `simplify-metadata-boundary` at `cdcfa99d6b922f0a2755743150fd074d2922ffbe` (`Mark Source tracking ID runtime promoted`).

## Owner direction preserved

Finish the entire `sources_source` worksheet before moving to Topic, while leaving the known shared-target pair unresolved rather than forcing an overwrite.

The unresolved pair is:

- `SOURCE_DESCRIPTION`
- `INFORMATION`

The workbook maps both to the singleton `catalog.metadata.remarks` destination. No concatenation, precedence, or overwrite rule has been invented. `SOURCE_DESCRIPTION` is populated for all 148 current records; `INFORMATION` is currently unpopulated.

## 56-row disposition completed

Every worksheet row 2-57 now has an explicit disposition in:

`Mapping/sources_source_final_disposition.csv`

The file records the workbook model, live population/type evidence, final status, target/review destination, and decision rationale.

The dispositions distinguish:

- already committed/read-back-verified Catalog mappings,
- a newly runtime-promoted Catalog mapping awaiting preview,
- currently unpopulated mappings retained for future data,
- relationship/hierarchy inputs that require identity-aware graph support,
- populated other-model rows that require their model grain,
- remaps where the live source shape does not support the photographed target semantics,
- excluded Archer/system security or ETL metadata,
- the one preserved shared-target decision pair above.

## Catalog runtime change

`Mapping/sources_source_runtime.csv` now contains 15 approved rows instead of 14.

New row:

- `SOURCE_TRACKING_ID` -> `catalog.metadata.props[]`
- `PROPERTY_NAME = tracking-id`
- `TRANSFORM_ID = direct`
- live evidence: 148/148 populated, INTEGER
- design decision: preserve the Archer scalar tracking identifier as an OSCAL property; do not coerce it into OSCAL UUID identity.

This change is committed/read-back verified in GitHub only. It has **not** yet been live-previewed or committed to Snowflake. The existing Catalog target remains proven only for the prior 14-row batch until a new PREVIEW is run.

## Remaining populated other-model rows

Live evidence shows populated Source-tab rows still assigned by the workbook to other models, including:

- Assessment Results: `COMPLIANCE_RATING`, `COUNT_OF_NONCOMPLIANT_CONTROLS`, and the deviation/control relationship field.
- Component Definition: policy references, descendant policy relationships, source-policy selection, and policy count.
- Assessment Plan: `ENGAGEMENT_SCOPE_IN_CONTROL_SOURCE`.

These are not being misrouted into Catalog.

`sql/SOURCE2_SOURCE_OTHER_MODELS_READINESS.sql` was added as a read-only evidence gate. It checks live registry paths and physical curated targets for Assessment Results, Security Assessment Plan, and Component Definition, plus the source population shapes already identified. It performs no writes.

## Current status distinction

- Original Source Catalog 14-row batch: **committed + read-back verified**.
- `SOURCE_TRACKING_ID` additional Catalog runtime row: **implemented in GitHub; PREVIEW pending; no Snowflake DML yet**.
- Full 56-row Source worksheet disposition: **completed and committed in GitHub**.
- `SOURCE_DESCRIPTION` / `INFORMATION` shared target: **intentionally unresolved by owner direction**.
- Remaining populated Assessment Results / Component Definition / Assessment Plan rows: **classified; runtime implementation depends on live registry/target/grain evidence**.
- Topic work: **paused until Source completion work is resolved**.

## Next action

Run `sql/SOURCE2_SOURCE_OTHER_MODELS_READINESS.sql` read-only and return its aggregate results. That will determine which remaining populated Source-tab fields can be promoted immediately into the existing generic framework and which require a new model contract/registry branch. Separately, the 15-row Catalog runtime should be PREVIEWed before any additional Catalog COMMIT so the new `tracking-id` property is validated against the already-populated Catalog target.
