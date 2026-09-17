# Source 2 Catalog registry live pass — 2026-09-17

Branch before pilot runtime publication: `simplify-metadata-boundary` at `6e38fd0c4dea52fea04226b6bd41b809bdd5f490`.

## Owner-reported Snowflake result

The owner ran `sql/registry/ENABLE_CATALOG_METADATA_PILOT.sql` in Snowflake and reported the expected result:

- `STATUS = CATALOG_METADATA_PILOT_REGISTRY_VERIFIED`
- `ACTIVE_ROWS = 2`
- `COMMITTED = TRUE`

This is the current live checkpoint for the Catalog Metadata pilot registry. It supersedes the earlier read-only state where Catalog returned zero registry rows.

The two intended active paths are:

1. `catalog`
2. `catalog.metadata`

No Catalog property, Back Matter, Topic, Section, Sub-Section, control or other-model registry rows are claimed by this checkpoint.

## Current implementation status

- Source-level RAW contract: read-back verified.
- Source-level `CONTENT_ID`: 148 rows / 148 distinct / zero missing, owner-provided read-back.
- `CURATED_JSON`: zero null rows in the same read-back.
- Catalog DIM/FACT physical tables: read-back verified present.
- Catalog pilot registry: **committed and owner-reported verified** for two rows.
- Pilot runtime mapping CSV: committed after this live checkpoint as `Mapping/SOURCE2_CATALOG_PILOT_RUNTIME.csv`.
- Pilot Cell 1 configuration: committed after this live checkpoint as `notebooks/pilots/SOURCE2_CATALOG_PILOT_CELL1.py`.
- Cells 2-7: unchanged.
- Main `Mapping/ARCHER_OSCAL_MAPPINGS.csv`: unchanged.
- Maintained generic `notebooks/cells/01_initialization_and_configuration.py`: unchanged.
- Catalog PREVIEW: not yet run.
- Catalog target DML: not yet performed by the seven-cell mapper.

## Next action

Use the pilot runtime CSV and pilot Cell 1 with the existing shared Cells 2-7. Keep `EXECUTE_WRITES = False` and Cell 7 `OSCAL_LOAD_MODE = "PREVIEW"`. Run Cells 1 through 7 in one Snowflake notebook session and return the aggregate pipeline report.

The pilot intentionally enables only:

- `SOURCE_NAME -> catalog.metadata.title`
- `SOURCE_VERSION -> catalog.metadata.version`

All doubtful Source 2 mappings remain outside executable scope.
