# Source 2 full Source-tab mapping workbook refresh — 2026-09-17

## Repository checkpoint

Branch reviewed immediately before this checkpoint: `simplify-metadata-boundary` at `3dbde10f6c66eff776fcb3903af83a3bdee3f132` (`Refresh Source 2 mapping workbook`).

## What changed

The lowercase Source 2 master workbook was refreshed in GitHub at:

`Mapping/archer_authoritative_sources_oscal_mappings.xlsx`

The workbook retains the four lowercase tabs:

- `sources_source`
- `sources_topic`
- `sources_section`
- `sources_sub_section`

The `sources_source` tab now carries the 2026-09-17 full Source-level review across all 56 photographed worksheet entries. The original evidence columns remain present and the review adds explicit status, runtime-transform/target candidates, decision/next-action text, source-shape evidence, and review references. Uncertain rows remain marked deferred/remap-required rather than being silently approved.

The other three tabs continue to be rebuilt from the existing row-by-row GitHub review CSVs. Their `[CLIPPED]`/missing-text evidence remains unresolved; the builder does not invent replacement text.

## Reproducible packaging

Two repository artifacts now make the binary workbook reproducible from GitHub text sources:

- `tools/build_source2_workbook.py`
- `.github/workflows/build-source2-workbook.yml`

The workflow run `35240641425` completed successfully on 2026-09-17. It rebuilt and committed the workbook as `3dbde10f6c66eff776fcb3903af83a3bdee3f132`.

Read-back of that commit's tree shows the refreshed workbook blob:

- blob SHA: `ff514a0908ee5473c012d01ac78821e1fa312330`
- size: `38082` bytes

This supersedes the earlier lowercase workbook blob `fd0d41c7764923e5cc23710adae05d901cec1ea7` (29026 bytes) for the Source-tab review state.

## Validation actually performed

- Workbook generation workflow: **completed / success**.
- Branch head after generated workbook commit: **read-back verified** at `3dbde10f...`.
- Refreshed workbook path/blob/size: **read-back verified** from the commit tree.
- Local workbook generation before publication was checked for four lowercase tab names and formula error strings.
- This checkpoint does **not** claim that GitHub can semantically inspect the binary XLSX after publication; the text generator/review source plus binary tree read-back are the publication evidence.

## What did not change

- `Mapping/ARCHER_OSCAL_MAPPINGS.csv`: unchanged by this workbook refresh.
- Maintained seven-cell mapper in `notebooks/cells/`: unchanged.
- Catalog DIM/FACT: no DML performed by this work.
- Catalog registry: no additional rows were written by this work; the previously owner-reported two-row `catalog` / `catalog.metadata` pilot registry setup is separate.
- Source 1 mappings: unchanged.

## Status distinction

- Full Source-tab review: **implemented in the master workbook and published to GitHub**.
- Workbook publication: **committed and repository-tree read-back verified**.
- READY review rows: **not yet promoted into the production runtime CSV** unless already present in the earlier two-row pilot artifact.
- Seven-cell Source 2 execution: **not performed as part of this workbook refresh**.

## Next action

Use the reviewed `sources_source` tab to prepare one coherent Source-level runtime batch for all rows whose review status is READY/READY-with-condition, leaving SME/model-design/source-shape rows deferred. Before PREVIEW, add only the registry paths and reusable mapper capability required by that approved batch, then run the existing seven-cell framework in PREVIEW with no target writes.
