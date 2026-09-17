# Source 2 native workbook checkpoint — 2026-09-17

Branch before this checkpoint: `simplify-metadata-boundary` at `ec4d71e661c910d07f84c4b2be2429c3d4f16edb`.

## Material update

Created and published the consolidated Source 2 review workbook:

`Mapping/Archer_Authoritative_Sources_OSCAL_Mappings.xlsx`

The workbook is assembled from the four existing GitHub review CSVs and preserves their text exactly, including `[CLIPPED]`, unresolved questions, and review/transcription status. It is a consolidated review artifact, not a new source of semantic approval and not the original owner-provided native workbook.

Sheets and source-row counts:

- `sources_source` — 56 review rows from `SOURCE2_SOURCE_MAPPING.csv`
- `sources_topic` — 52 review rows from `SOURCE2_TOPIC_MAPPING.csv`
- `sources_section` — 62 review rows from `SOURCE2_SECTION_MAPPING.csv`
- `sources_sub_section` — 73 review rows from `SOURCE2_SUB_SECTION_MAPPING.csv`
- Total — 243 review rows

## Validation actually performed

- Local workbook export completed successfully.
- XLSX ZIP/package validation passed locally.
- Four expected sheet names were verified.
- GitHub read-back at commit `ec4d71e661c910d07f84c4b2be2429c3d4f16edb` reports:
  - path: `Mapping/Archer_Authoritative_Sources_OSCAL_Mappings.xlsx`
  - blob SHA: `fd0d41c7764923e5cc23710adae05d901cec1ea7`
  - size: `29026` bytes
- The earlier partial/corrupt binary published at commit `4a428116d0479b5636fe5cd6aec314394d52f3b3` is superseded by the fixed workbook commit above.

## What did not change

- No Source 2 review row was promoted to runtime approval by this workbook creation.
- No existing `ARCHER_OSCAL_MAPPINGS.csv` runtime status was changed.
- No seven-cell mapper source was changed by this workbook creation.
- No registry, DDL, or Snowflake data change was performed by this workbook creation.

## Next action

Use `sources_source` as the consolidated review sheet and map the Source level end-to-end now: resolve every row supported by current workbook/source evidence, keep only genuinely unresolved rows deferred, and then build the corresponding runtime metadata/registry/configuration as one coherent Source-level change before PREVIEW.
