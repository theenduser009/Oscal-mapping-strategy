# Component Definition target rebuild prepared — 2026-09-17

## Repository checkpoint

Branch inspected before this material update: `simplify-metadata-boundary` at `bfdaf6432a1fcca292ccc1626215bb39e71ca781` (`Checkpoint Source 2 Source final disposition`).

The Component Definition DDL was then committed as `2b862968e3b686c0d42e42f6d2529a2326c7e878`.

## Owner-provided live Snowflake evidence

The owner-provided read-only target inventory shows:

- `DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT`: existing/populated.
- `FACT_OSCAL_ASSESSMENT_PLAN_DEPENDENCY`: existing/populated.
- `DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT`: existing/populated.
- `FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY`: existing/populated.
- `DIM_OSCAL_COMPONENT_ELEMENT`: exists with `ROW_COUNT = 0`.
- no `FACT_OSCAL_COMPONENT_DEPENDENCY` was returned by the `%OSCAL%COMPONENT%` target discovery.
- Catalog targets were separately created and Source-level Catalog data was already committed/read-back verified.

The owner screenshot of `DIM_OSCAL_COMPONENT_ELEMENT` shows an older nine-column shape, including `PK_OSCAL_COMPONENT_ELEMENT_HASH` and `DW_LOAD_TIMESTAMP TIMESTAMP_NTZ`, and no `DW_LOAD_TIMESTAMP_TZ` column. This does not match the current Cell 6 `BINARY16_UUID32` contract.

## Shared physical contract used

The prepared Component targets mirror the current maintained loader contract and the Assessment Plan / Assessment Results / Catalog target definitions:

DIM:

- `PK_DIM_OSCAL_COMPONENT_ELEMENT_HASH BINARY(16) NOT NULL`
- `ELEMENT_TYPE VARCHAR(64)`
- `OSCAL_UUID VARCHAR(32)`
- `METADATA_JSON VARIANT`
- `SOURCE_SYSTEM_NAME VARCHAR(100)`
- `SOURCE_TABLE_NAME VARCHAR(128)`
- `SOURCE_RECORD_ID VARCHAR(128)`
- `DW_PIPELINE_RUN_ID VARCHAR(64)`
- `DW_LOAD_TIMESTAMP TIMESTAMP_TZ(9)`
- `DW_LOAD_TIMESTAMP_TZ TIMESTAMP_TZ(9)`

FACT:

- `PK_FACT_OSCAL_COMPONENT_DEPENDENCY_HASH BINARY(16) NOT NULL`
- `FK_SOURCE_ELEMENT_HASH BINARY(16) NOT NULL`
- `FK_TARGET_ELEMENT_HASH BINARY(16) NOT NULL`
- `DEPENDENCY_TYPE VARCHAR(32) NOT NULL`
- `SOURCE_OSCAL_UUID VARCHAR(32) NOT NULL`
- `TARGET_OSCAL_UUID VARCHAR(32) NOT NULL`

## Implemented repository artifact

`sql/REBUILD_COMPONENT_DEFINITION_TABLES.sql`

The SQL intentionally touches only the Component Definition DIM/FACT targets. It does not recreate or modify Assessment Plan, Assessment Results, Catalog, POA&M, or SSP targets.

Because the current Component DIM is owner-confirmed empty, the script uses `CREATE OR REPLACE` for that DIM and creates/replaces the matching Component FACT. The file must not be rerun after Component data is loaded without re-proving both Component targets are empty.

## Current status distinction

- Component target DDL: **implemented / committed / GitHub read-back verified**.
- Component DIM rebuild in Snowflake: **not yet owner-run/read-back verified**.
- Component FACT creation in Snowflake: **not yet owner-run/read-back verified**.
- Component Definition registry paths: **not present in the owner-provided registry result shown in this checkpoint**.
- Component Definition universal Cell 1 storage/model contract: **not yet implemented**.
- Component Definition mapping PREVIEW/COMMIT: **not run**.

## Next action

Run `sql/REBUILD_COMPONENT_DEFINITION_TABLES.sql` once in Snowflake, confirm the pre-write Component DIM count is still `0`, and return the two `DESC TABLE` outputs plus the final two-row count result. After live target read-back passes, add the generic Component Definition model/storage contract and the required registry paths before any PREVIEW.
