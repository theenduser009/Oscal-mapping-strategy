# Source 2 Catalog pilot readiness read-back — 2026-09-17

Branch reviewed before this checkpoint: `simplify-metadata-boundary` at `a50f952645f48253e4f742ff71e5c97fe34988f5`.

## Owner-provided Snowflake evidence

The owner ran `sql/SOURCE2_CATALOG_PILOT_READINESS.sql` and supplied screenshots of all three result sets.

### 1. Source-level RAW identity quality — PASS

For `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW`:

- `RAW_ROWS = 148`
- `MISSING_CONTENT_ID_ROWS = 0`
- `DISTINCT_CONTENT_IDS = 148`
- `NULL_CURATED_JSON_ROWS = 0`
- therefore `DUPLICATE_CONTENT_ID_EXCESS_ROWS = 0`

This is read-back verification that the current Source-level RAW snapshot has one nonblank `CONTENT_ID` per row and a non-null `CURATED_JSON` payload for all 148 rows. It satisfies the seven-cell input identity requirement for this snapshot; it does not by itself approve any OSCAL mapping.

### 2. Catalog physical targets — read-back verified

The Catalog target query returned 16 column rows across the two committed physical tables in `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED`:

- `DIM_OSCAL_CATALOG_ELEMENT`
- `FACT_OSCAL_CATALOG_DEPENDENCY`

The visible DIM columns include the expected Catalog PK, element type, OSCAL UUID, metadata JSON, source-system/table/record provenance, pipeline run ID and load timestamps. The visible FACT columns include the expected dependency PK, source/target element hashes, dependency type and source/target OSCAL UUIDs.

This is live existence/schema read-back evidence for the Catalog destination. The DDL file alone is no longer the only evidence.

### 3. Catalog registry — confirmed absent

The Catalog registry query returned **0 rows** from `RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY`.

This means Catalog cannot yet compile in the current seven-cell runtime because Cell 3 requires an active model hierarchy. The absence is a setup gap, not a mapper failure.

## Current implementation state

- Source 2 Source RAW binding: read-back verified.
- Source 2 Source `CONTENT_ID` quality: read-back verified for all 148 current rows.
- Source 2 Source `CURATED_JSON` non-null coverage: read-back verified for all 148 current rows.
- Catalog DIM/FACT target presence: read-back verified.
- Catalog registry rows: absent; setup required before PREVIEW.
- Runtime Source 2 mapping rows: not yet added.
- Catalog Cell 1 source/model binding: not yet added.
- Seven-cell code: unchanged.
- Source 1 behavior: unchanged by this checkpoint.
- Snowflake writes: none performed by this checkpoint.

## Next action

Run the GitHub-published read-only inspection:

`sql/SOURCE2_CATALOG_REGISTRY_READ_ONLY.sql`

It reads the live registry schema and representative active root/metadata/property rows from already-working models, and confirms again that no Catalog rows exist. The purpose is to derive the exact guarded Catalog registry insert from the **live current registry contract**, not from an old setup script.

Do not manually insert Catalog rows and do not run the seven-cell mapper until that read-back is reviewed.
