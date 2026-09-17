# Source 2 sources_source Assessment Results route ready — 2026-09-17

## Repository checkpoint

Runtime change commit: `9a259f26074ec7062bca95753d48c806ae039574` (`Add Source 2 Assessment Results runtime route`) on branch `simplify-metadata-boundary`.

## Owner-reported Component target setup

The owner reported that `sql/REBUILD_COMPONENT_DEFINITION_TABLES.sql` was run after the Component DIM was observed empty. This is execution evidence supplied by the owner, but this checkpoint does not claim independent read-back verification of the rebuilt Component DIM/FACT definitions because a post-rebuild DESC/result screenshot has not yet been supplied.

## Implemented Source 2 Assessment Results route

The universal Source 2 Source profile now binds both:

- `CATALOG`
- `ASSESSMENT_RESULTS`

A source-specific `MODEL_STORAGE_CONTRACTS["ASSESSMENT_RESULTS"]` override routes `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW` to the existing shared Assessment Results targets:

- `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT`
- `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY`

This uses the existing generic Cell 3 per-source/per-model storage override capability; Cell 6 was not changed.

## Runtime mapping promoted

`Mapping/sources_source_runtime.csv` now contains one Source 2 Assessment Results row:

- source field: `COUNT_OF_NONCOMPLIANT_CONTROLS`
- model: `Assessment Results`
- runtime path: `assessment-results.results[].props[]`
- transform: `direct`
- property name: `noncompliant-count`
- source key: `source-two-source`

Basis: owner-provided live evidence showed `148/148` populated INTEGER values, and the live Assessment Results registry showed `assessment-results.results[]` as a record collection keyed by `SOURCE_RECORD_ID` with `assessment-results.results[].props[]` available beneath it.

No attempt is made here to force `COMPLIANCE_RATING` into a reviewed-control instance because the Source record does not identify a specific reviewed-control grain. The populated deviation/control relationship also remains deferred until its finding/deviation parent semantics are established.

## Validation actually performed

GitHub Actions run `35252281631` completed successfully.

- Source 2 AR binding/runtime-row application: passed.
- Static source-specific storage contract check: passed.
- Generated notebook synchronization: passed.
- Generated notebook sync verification: passed.
- `git diff --check`: passed.
- Commit/push step: passed.

The workflow intentionally did not use the repository-wide historical `mapper-checks` workflow as its acceptance gate because that workflow has unrelated historical helper-file failures already documented elsewhere.

## Read-back verification

GitHub read-back at commit `9a259f26074ec7062bca95753d48c806ae039574` confirms:

- Source 2 `MODEL_BINDINGS = ("CATALOG", "ASSESSMENT_RESULTS")`.
- Source 2 Assessment Results storage override points to the Source 2 RAW table and existing AR DIM/FACT targets.
- `COUNT_OF_NONCOMPLIANT_CONTROLS` is present exactly once as an approved Source 2 Assessment Results runtime row with property name `noncompliant-count`.

## Status distinction

- Source 2 AR route code/metadata: **implemented, tested, committed, and GitHub read-back verified**.
- Source 2 AR Snowflake PREVIEW: **not yet run**.
- Source 2 AR target DML: **not authorized / not attempted**.
- Component target rebuild: **owner-reported executed; post-rebuild read-back evidence still pending**.

## Next action

Use the current universal Cell 1 from GitHub. Set `SELECTED_MODELS = ("ASSESSMENT_RESULTS",)` and keep Cell 7 in `PREVIEW`. Run Cells 1-7 and review both route groups. Because Source One also binds Assessment Results, the preview can include both `source-one` and `source-two-source`; no target DML should occur in PREVIEW. The Source 2 group is the new evidence needed here.
