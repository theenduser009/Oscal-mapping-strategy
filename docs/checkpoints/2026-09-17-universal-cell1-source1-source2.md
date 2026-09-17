# Universal Cell 1 for Source 1 and Source 2 — 2026-09-17

## Repository checkpoint

Branch: `simplify-metadata-boundary`

Implemented commit: `5bddf459fc51e26c3217cb4fd529e60dd704d4dd` (`Make Cell 1 universal for Source 1 and Source 2`).

This checkpoint supersedes the need to swap between the maintained Source 1 Cell 1 and the temporary Source 2 pilot Cell 1 for normal notebook operation.

## Decision

Cell 1 is now the single universal configuration entrypoint.

Both source families are configured at the same time:

- `source-one` -> `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`
  - SSP
  - Assessment Results
  - POAM
  - Security Assessment Plan
  - mapping file: `ARCHER_OSCAL_MAPPINGS.csv`
- `source-two-source` -> `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW`
  - Catalog
  - mapping file: `sources_source_runtime.csv`

The Catalog storage contract is now part of the maintained Cell 1 alongside the existing Source 1 model contracts.

## User control

Only one selector is intended to change between runs:

`SELECTED_MODELS`

Examples:

- Source 1 SSP only: `("SSP",)`
- Source 2 Catalog only: `("CATALOG",)`
- both routes in one PREVIEW: `("SSP", "CATALOG")`

No source table names, mapping files, target tables, or alternate Cell 1 files should need to be swapped manually.

## Preservation of Source 1

The existing Source 1 physical table, mapping file, model bindings, source-order candidates, software lookup contract, interconnection lookup contract, and SSP/AR/POAM/SAP storage contracts were preserved in the universal Cell 1.

The default selector remains `("SSP",)` so replacing the old maintained Cell 1 with this universal version does not silently start Source 2.

## Source 2 Catalog binding

The maintained Cell 1 now includes:

- source key: `source-two-source`
- RAW table: `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW`
- identity: `CONTENT_ID`
- business payload: `CURATED_JSON`
- mapping file: `sources_source_runtime.csv`
- model binding: `CATALOG`
- Catalog DIM: `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_CATALOG_ELEMENT`
- Catalog FACT: `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_CATALOG_DEPENDENCY`

## Validation actually performed

GitHub Actions run `35245840388` completed successfully before the tested universal Cell 1 was committed.

- static universal Cell 1 contract check: passed
- generated notebook synchronization: passed
- Source-profile boundary regression module `tests/lean/test_metadata_gaps.py`: passed
- `tools/sync_notebook_cells.py --check`: passed
- `git diff --check`: passed
- tested code committed by the workflow as `5bddf459fc51e26c3217cb4fd529e60dd704d4dd`
- maintained Cell 1 was read back at that commit and confirms both source profiles and all five model contracts are present

## Status distinction

Implemented/tested/committed/read-back verified:

- universal maintained Cell 1
- synchronized generated Cell 1 copies
- Source 1 + Source 2 Source configuration coexistence

Previously owner-verified but superseded for current execution proof:

- the Source 2 Catalog PREVIEW at 1,549 nodes / 1,401 edges was produced with the temporary Source 2 pilot Cell 1

Because Cell 1 is now materially different, that earlier PREVIEW remains historical evidence but is not fresh execution proof for the universal Cell 1.

## Next action

Before the first Catalog COMMIT under the universal configuration:

1. replace notebook Cell 1 with `notebooks/cells/01_initialization_and_configuration.py`
2. set only `SELECTED_MODELS = ("CATALOG",)` for the current Source 2 Catalog run
3. keep `EXECUTE_WRITES = False` and Cell 7 in PREVIEW
4. rerun Cells 1–7 and the existing read-only Catalog inspection
5. confirm the universal run still returns the accepted 148-source-record / 1,549-node / 1,401-edge checkpoint before COMMIT

Do not use the temporary `notebooks/pilots/source2_catalog_source_cell1.py` for new runs once the universal Cell 1 is installed.
