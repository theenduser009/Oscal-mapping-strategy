# Source 2 Source runtime mapping batch — 2026-09-17

## Repository checkpoint

Branch reviewed immediately before the runtime batch work: `simplify-metadata-boundary` at `d62ca9f528b4402305f15cd5f984e3606ece78f8`.

## Source evidence used

- Lowercase master workbook: `Mapping/archer_authoritative_sources_oscal_mappings.xlsx`.
- Source tab: `sources_source`.
- Physical Source table read-back: `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW`.
- Whole-table identity read-back: 148 RAW rows, 0 missing `CONTENT_ID`, 148 distinct `CONTENT_ID`, 0 NULL `CURATED_JSON`.
- Owner-provided `CURATED_JSON` sample established scalar, Archer value-list, cross-reference and permission-object shapes.
- Existing Catalog target DIM/FACT were owner read-back verified.
- Owner reported the guarded Catalog pilot registry setup completed with the expected two active paths: `catalog` and `catalog.metadata`.

## Mapping work completed

The full 56-row Source tab remains the review scope. This checkpoint promotes only the rows whose destination and source shape are sufficiently supported into one coherent runtime-ready batch. Doubtful rows remain deferred/remap-required rather than being silently approved.

New executable batch artifact:

`Mapping/sources_source_runtime.csv`

It contains 14 approved Source -> Catalog Metadata rows:

1. `SOURCE_NAME -> catalog.metadata.title`
2. `SOURCE_VERSION -> catalog.metadata.version`
3. `DISCLAIMER -> catalog.metadata.props[]` (`disclaimer`)
4. `NUMBER_OF_CONTROL_STANDARDS_SOURCE_LEVEL -> catalog.metadata.props[]` (`control-count`)
5. `COUNT_OF_CONTROLS -> catalog.metadata.props[]` (`total-controls`)
6. `SOURCE_TYPE -> catalog.metadata.props[]` (`source-type`)
7. `CRITICALITY -> catalog.metadata.props[]` (`criticality`)
8. `SOURCE_CRITICALITY_VALUE -> catalog.metadata.props[]` (`criticality-value`)
9. `AUTH_SOURCES_FILTER -> catalog.metadata.props[]` (`filter-category`)
10. `EFFECTIVE_DATE -> catalog.metadata.props[]` (`effective-date`)
11. `OFFICIAL_RETIREMENT_DATE -> catalog.metadata.props[]` (`retirement-date`)
12. `RTX_RETIREMENT_DATE -> catalog.metadata.props[]` (`rtx-retirement-date`)
13. `RECORD_STATUS -> catalog.metadata.props[]` (`record-status`)
14. `CONTENT_SOURCE -> catalog.metadata.props[]` (`content-source`)

Archer value-list-backed rows use the existing `archer-select` transform. Date-property rows use the existing calendar-date transform. The exact property name is carried in a new optional runtime metadata column `PROPERTY_NAME`; rows that do not need a property name leave it blank.

## Registry preparation published

New guarded registry script:

`sql/registry/enable_catalog_source_metadata.sql`

It preserves the owner-reported existing two-row Catalog branch and adds only:

`catalog.metadata.props[]`

with reviewed execution metadata:

- parent: `catalog.metadata`
- `IS_COLLECTION = TRUE`
- `INSTANCE_KEY_RULE = SOURCE_FIELD_NAME+VALUE`
- `ITEM_PATH = '$'`
- `OPERATOR = properties`
- `UUID_POLICY = omit`

The script is transactional, conflict-checked and read-back verified inside the statement. It has not been reported as executed in Snowflake at this checkpoint.

## Source 2 Cell 1 configuration published

New PREVIEW-only configuration:

`notebooks/pilots/source2_catalog_source_cell1.py`

It binds the verified Source RAW table, `source-two-source`, the Catalog DIM/FACT targets, and `Mapping/sources_source_runtime.csv`. `EXECUTE_WRITES` remains `False`.

## Important remaining implementation gate

The maintained Cell 4 currently derives property names from `SOURCE_FIELD_NAME`. Five of the approved rows require a different explicit property name (`control-count`, `total-controls`, `criticality-value`, `filter-category`, `retirement-date`). Therefore **do not run the seven-cell Source batch yet**. A small generic, backward-compatible `PROPERTY_NAME` override must be implemented and validated first; Source 1 behavior must remain unchanged when the column is absent.

This is one reusable mapper capability, not a Source-2-specific rewrite and not seven new cells.

## Status distinction

- Full Source-tab review in master workbook: **implemented and GitHub-published**.
- 14-row Source runtime batch: **committed and text read-back verified**.
- Catalog property registry extension SQL: **committed; not yet Snowflake-executed/read-back verified**.
- Source 2 full Cell 1 PREVIEW configuration: **committed; not executed**.
- `PROPERTY_NAME` mapper support: **required next; not yet implemented**.
- Seven-cell Source 2 PREVIEW: **not run**.
- Target DIM/FACT writes: **none**.

## Next action

Implement and test the single optional `PROPERTY_NAME` override in the shared mapper while preserving current Source 1 behavior. Only after that change is read-back verified should the owner run `sql/registry/enable_catalog_source_metadata.sql`, upload `sources_source_runtime.csv`, and run the seven cells in PREVIEW.
