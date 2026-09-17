# Source 2 Catalog registry empty + pilot setup checkpoint — 2026-09-17

## Repository version

Branch: `simplify-metadata-boundary`
Reviewed before this update at: `c9334079257735df048187e69f59aef7e868f840`.

## New owner evidence

The owner confirmed the Catalog registry query returned **zero rows** for this Source 2 / Catalog scope.

This means there is no existing Catalog hierarchy in `RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY` to reuse or extend for the first pilot.

Earlier live read-back already established:

- Source RAW table exists: `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW`.
- 148 RAW rows.
- 0 missing `CONTENT_ID` rows.
- 148 distinct `CONTENT_ID` values.
- 0 NULL `CURATED_JSON` rows.
- Catalog DIM and FACT tables exist with the expected shared physical layout.

## What was added

A guarded setup script was added:

`sql/registry/ENABLE_CATALOG_METADATA_PILOT.sql`

The script creates/enables only these two active registry paths:

1. `catalog`
2. `catalog.metadata`

It is intentionally limited to the first clean Source -> Catalog Metadata pilot for:

- `SOURCE_NAME -> catalog.metadata.title`
- `SOURCE_VERSION -> catalog.metadata.version`

It does **not** add `catalog.metadata.props[]`, Back Matter, controls, Topic, Section, Sub-Section, dates, permissions, or any mapping that is still awaiting an SME/source-owner decision.

## Guardrails in the script

- Refuses to run inside an active transaction.
- Rechecks for conflicting or unexpected Catalog registry rows before changing anything.
- Rejects duplicate `catalog` / `catalog.metadata` paths.
- Uses one transaction for the two-row registry change.
- Read-back verifies the two expected active rows before commit.
- Rejects unexpected additional active Catalog rows during this pilot setup.
- Does not perform DIM/FACT DML.
- Does not run the seven-cell mapper.
- Does not modify Source 1.

## Validation actually performed

Repository/code review confirmed the current Cell 3 compiler requires one root, valid ancestry, explicit operator-compatible UUID policy, and uses the registry as the structural contract. The existing Assessment Plan registry setup was used only as an implementation-pattern reference; this checkpoint does not claim that historical setup proves Catalog runtime behavior.

The new Catalog setup SQL was committed to GitHub. Snowflake execution has **not** yet been performed.

## Remaining gaps

After the registry setup is executed and read back successfully, the remaining first-pilot work is:

1. add the Catalog Source 2 source/model binding in Cell 1,
2. add only the approved `SOURCE_NAME` and `SOURCE_VERSION` runtime mapping rows,
3. run Cells 1–7 in PREVIEW with writes disabled,
4. review the actual PREVIEW report before any COMMIT.

Property-name overrides, description/information handling, publication/update dates, select-list properties, Back Matter, and four-table hierarchy remain separate unresolved or later-scope items.

## Next action

Run the whole GitHub-published `sql/registry/ENABLE_CATALOG_METADATA_PILOT.sql` in Snowflake and return the single result object. Expected success status:

`CATALOG_METADATA_PILOT_REGISTRY_VERIFIED`

with `ACTIVE_ROWS = 2` and `COMMITTED = TRUE`.
