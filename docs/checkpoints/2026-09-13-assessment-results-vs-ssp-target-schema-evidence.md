# Assessment Results and SSP target-schema evidence

Date posted: **2026-09-13**

Transcribed from the three supplied Snowflake `DESC TABLE` screenshots. The SSP DIM schema was also supplied for comparison.

## Assessment Results DIM

```text
RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
```

| Column | Type | Nullable | Primary key |
| --- | --- | --- | --- |
| `PK_DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT_HASH` | `BINARY(16)` | N | Y |
| `ELEMENT_TYPE` | `VARCHAR(32)` | Y | N |
| `OSCAL_UUID` | `VARCHAR(32)` | Y | N |
| `METADATA_JSON` | `VARIANT` | Y | N |
| `SOURCE_SYSTEM_NAME` | `VARCHAR(100)` | Y | N |
| `SOURCE_TABLE_NAME` | `VARCHAR(50)` | Y | N |
| `SOURCE_RECORD_ID` | `VARCHAR(32)` | Y | N |
| `DW_LOAD_TIMESTAMP` | `TIMESTAMP_NTZ` | Y | N |
| `DW_PIPELINE_RUN_ID` | `VARCHAR(50)` | Y | N |

## Assessment Results FACT

```text
RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY
```

| Column | Type | Nullable | Primary key |
| --- | --- | --- | --- |
| `PK_FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY_HASH` | `BINARY(16)` | N | Y |
| `FK_SOURCE_ELEMENT_HASH` | `BINARY(16)` | N | N |
| `FK_TARGET_ELEMENT_HASH` | `BINARY(16)` | N | N |
| `DEPENDENCY_TYPE` | `VARCHAR(32)` | N | N |
| `SOURCE_OSCAL_UUID` | `VARCHAR(32)` | N | N |
| `TARGET_OSCAL_UUID` | `VARCHAR(32)` | N | N |

## SSP DIM supplied for comparison

```text
RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
```

| Column | Type | Nullable | Primary key |
| --- | --- | --- | --- |
| `PK_OSCAL_SSP_ELEMENT_HASH` | `BINARY(16)` | N | Y |
| `ELEMENT_TYPE` | `VARCHAR(64)` | Y | N |
| `OSCAL_UUID` | `VARCHAR(32)` | Y | N |
| `METADATA_JSON` | `VARIANT` | Y | N |
| `SOURCE_SYSTEM_NAME` | `VARCHAR(100)` | Y | N |
| `SOURCE_TABLE_NAME` | `VARCHAR(128)` | Y | N |
| `SOURCE_RECORD_ID` | `VARCHAR(128)` | Y | N |
| `DW_PIPELINE_RUN_ID` | `VARCHAR(64)` | Y | N |
| `DW_LOAD_TIMESTAMP` | `TIMESTAMP_TZ(9)` | Y | N |
| `DW_LOAD_TIMESTAMP_TZ` | `TIMESTAMP_TZ(9)` | Y | N |

## Visible schema differences

The Assessment Results DIM and SSP DIM are not column-identical. Visible differences include the primary-key column name, several VARCHAR lengths, timestamp type, and the SSP-only `DW_LOAD_TIMESTAMP_TZ` column.
