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

This checkpoint records the actual physical Snowflake table contract shown in the notebook screenshots. No database changes were made by creating this documentation.