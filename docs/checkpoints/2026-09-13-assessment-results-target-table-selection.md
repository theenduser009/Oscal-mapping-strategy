# Assessment Results target table selection

Date posted: **2026-09-13**

Transcribed from the supplied Snowflake Information Schema screenshot.

## Required choice

Use the full Assessment Results table name:

```text
ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT
```

Do **not** choose the abbreviated alternative until its purpose is separately confirmed:

```text
ES_ESC_GRC_CURATED.DIM_OSCAL_AR_ELEMENT
```

Both names appear in the same schema with a similar DIM element column structure, so they appear duplicate or overlapping. The explicit target-table choice is therefore required before the Assessment Results target contract is configured.

## Columns visible for the selected table

| Column | Data type |
| --- | --- |
| `PK_DIM_OSCAL_ASSESSMENT_RESULTS_ELE…` | `BINARY` |
| `ELEMENT_TYPE` | `TEXT` |
| `OSCAL_UUID` | `TEXT` |
| `METADATA_JSON` | `VARIANT` |
| `SOURCE_SYSTEM_NAME` | `TEXT` |
| `SOURCE_TABLE_NAME` | `TEXT` |
| `SOURCE_RECORD_ID` | `TEXT` |
| `DW_LOAD_TIMESTAMP` | `TIMESTAMP_NTZ` |
| `DW_PIPELINE_RUN_ID` | `TEXT` |

> The primary-key column is recorded with an ellipsis because its full text is truncated in the supplied screenshot.
