# Source 2 Source RAW read-back checkpoint — 2026-09-17

Branch before this checkpoint: `simplify-metadata-boundary` at `f42262406a8e5e38ec3a4a7852382055d1132b43`.

## Owner-provided Snowflake evidence

The owner supplied Snowflake screenshots from the read-only discovery SQL.

### Physical Source-level RAW object confirmed

`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW`

The Information Schema result shows seven columns on the RAW table:

- `RAW_DATA` — VARIANT
- `LOAD_TIMESTAMP` — TIMESTAMP_NTZ
- `SOURCE_FILE_NAME` — TEXT
- `FILE_DATE` — DATE
- `ETL_LOAD_TS` — TIMESTAMP_LTZ
- `CURATED_JSON` — VARIANT
- `CONTENT_ID` — TEXT

This is read-back evidence of the physical RAW contract. It supersedes earlier uncertainty about the Source-level physical object name and confirms the seven-cell loader's required `CONTENT_ID` + `CURATED_JSON` columns are present.

### Sample CURATED_JSON read-back confirmed

The second result set selected `CONTENT_ID`, `TYPEOF(CURATED_JSON)`, `SOURCE_NAME`, and `SOURCE_VERSION` from the RAW table. Five returned rows showed:

- `CURATED_JSON_TYPE = OBJECT`
- populated `SOURCE_NAME`
- populated `SOURCE_VERSION`
- distinct-looking `CONTENT_ID` values in the five-row sample

Business values are intentionally not reproduced in this public checkpoint.

This establishes sample-level source presence and shape for the first two clean Catalog Metadata candidates:

- `SOURCE_NAME -> catalog.metadata.title`
- `SOURCE_VERSION -> catalog.metadata.version`

It does not yet prove whole-table uniqueness, target-table existence, Catalog registry readiness, or full-field completeness.

## Implementation status

- Source 2 RAW binding: **read-back confirmed for Source level**.
- `CONTENT_ID` and `CURATED_JSON` columns: **read-back confirmed**.
- `SOURCE_NAME` / `SOURCE_VERSION` sample presence: **read-back confirmed**.
- Runtime mapping rows: not yet added.
- Catalog Cell 1 source/model binding: not yet added.
- Catalog registry rows: not yet verified live.
- Catalog DIM/FACT live DDL: not yet read-back verified.
- Seven-cell code: unchanged.
- Source 1: unchanged.
- Snowflake writes: none performed by this checkpoint.

## Next action

Run the GitHub-published read-only readiness SQL:

`sql/SOURCE2_CATALOG_PILOT_READINESS.sql`

That script checks only the remaining implementation gates needed before promoting the first clean Source -> Catalog Metadata pilot rows:

1. whole-table `CONTENT_ID` identity quality and null coverage,
2. live Catalog DIM/FACT target columns,
3. live Catalog registry rows.

Do not run the seven-cell mapper yet. No runtime or registry changes should be made until those three read-only result sets are reviewed.
