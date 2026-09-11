# SSP DIM / FACT Physical Schema Checkpoint

Captured from Snowflake notebook output on 2026-09-11 for Codex context.

## DIM_OSCAL_SSP_ELEMENT

Fully qualified table:
`RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT`

Observed columns:

| Column | Type | Nullable | Default |
|---|---|---:|---:|
| PK_OSCAL_SSP_ELEMENT_HASH | BINARY(16) | N | false |
| ELEMENT_TYPE | VARCHAR(64) | Y | false |
| OSCAL_UUID | VARCHAR(32) | Y | false |
| METADATA_JSON | VARIANT | Y | false |
| SOURCE_SYSTEM_NAME | VARCHAR(100) | Y | false |
| SOURCE_TABLE_NAME | VARCHAR(128) | Y | false |
| SOURCE_RECORD_ID | VARCHAR(128) | Y | false |
| DW_PIPELINE_RUN_ID | VARCHAR(64) | Y | false |
| DW_LOAD_TIMESTAMP | TIMESTAMP_TZ(9) | Y | false |
| DW_LOAD_TIMESTAMP_TZ | TIMESTAMP_TZ(9) | Y | false |

## FACT_OSCAL_SSP_DEPENDENCY

Fully qualified table:
`RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY`

Observed columns:

| Column | Type | Nullable | Default |
|---|---|---:|---:|
| PK_FACT_OSCAL_DEPENDENCY_HASH | BINARY(16) | N | false |
| FK_SOURCE_ELEMENT_HASH | BINARY(16) | N | false |
| FK_TARGET_ELEMENT_HASH | BINARY(16) | N | false |
| DEPENDENCY_TYPE | VARCHAR(32) | N | false |
| SOURCE_OSCAL_UUID | VARCHAR(32) | N | false |
| TARGET_OSCAL_UUID | VARCHAR(32) | N | false |

## Architectural meaning

The DIM is the SSP graph-node table. The FACT is the factless graph-edge/dependency table. Source and target hashes in FACT reference SSP element hashes in DIM; source/target OSCAL UUIDs are also persisted on the dependency rows.

## Snowflake query-history error checkpoint — 2026-09-11

A read-only query-history check was run with `INFORMATION_SCHEMA.QUERY_HISTORY_BY_USER` for approximately the previous two hours and filtered to `ERROR_CODE = 2003`.

Observed recent failures included:

- `CREATE_VIEW` attempts under role `PUBLIC`, database `USERSC95077009`, schema `PUBLIC`.
- Error code `2003` (`SQL compilation error`).
- The visible error message shows a missing/not-authorized transient Snowpark object in curated schema, approximately:
  `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.SNOWPARK_TEMP_TABLE_DFATXMI5EU`
  with message: `does not exist or not authorized`.
- Additional recent `SELECT` failures under role `RTX_ES_ESC_GRC_RAW_DEV_FULL`, database `RTX_RAW_DEV`, schema `ES_ESC_GRC` also show error code `2003` for Archer source objects that were not found or not authorized.
- One visible source-object error references `ARCHER_AUTHORIZATION_PACKAGE_DATA_RAW` as not existing or not authorized.

Interpretation for Codex: the notebook is encountering object-resolution / authorization failures rather than a DIM/FACT schema-definition problem. Snowpark temporary-object lifetime or session scope is a likely contributor for the `SNOWPARK_TEMP_TABLE_*` failures; source-table naming/authorization should be checked separately for the Archer raw-object failures.

This checkpoint records the actual physical Snowflake table contract and the visible query-history evidence from the notebook screenshots. No database changes were made by creating this documentation.