# Assessment Results DIM and FACT target-table evidence

Date posted: **2026-09-13**

Transcribed from the two supplied Snowflake Information Schema screenshots.

## Fully qualified Assessment Results targets

```text
RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY
```

These are the full Assessment Results table names visible in the screenshots.

## DIM columns

Table: `DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT`

| Column | Data type |
| --- | --- |
| `PK_DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT_HASH` | `BINARY` |
| `ELEMENT_TYPE` | `TEXT` |
| `OSCAL_UUID` | `TEXT` |
| `METADATA_JSON` | `VARIANT` |
| `SOURCE_SYSTEM_NAME` | `TEXT` |
| `SOURCE_TABLE_NAME` | `TEXT` |
| `SOURCE_RECORD_ID` | `TEXT` |
| `DW_LOAD_TIMESTAMP` | `TIMESTAMP_NTZ` |
| `DW_PIPELINE_RUN_ID` | `TEXT` |

## FACT columns

Table: `FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY`

| Column | Data type |
| --- | --- |
| `PK_FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY_HASH` | `BINARY` |
| `FK_SOURCE_ELEMENT_HASH` | `BINARY` |
| `FK_TARGET_ELEMENT_HASH` | `BINARY` |
| `DEPENDENCY_TYPE` | `TEXT` |
| `SOURCE_OSCAL_UUID` | `TEXT` |
| `TARGET_OSCAL_UUID` | `TEXT` |

## Duplicate-name caution visible in the schema

The schema also contains the abbreviated table `DIM_OSCAL_AR_ELEMENT`. For the Assessment Results contract, choose the explicit full-name pair documented above.
