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
- The visible error message shows a missing/not-authorized transient Snowpark object in curated schema, approximately `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.SNOWPARK_TEMP_TABLE_DFATXMI5EU`.
- Additional recent `SELECT` failures under role `RTX_ES_ESC_GRC_RAW_DEV_FULL`, database `RTX_RAW_DEV`, schema `ES_ESC_GRC` also show error code `2003` for Archer source objects that were not found or not authorized.
- One visible source-object error references `ARCHER_AUTHORIZATION_PACKAGE_DATA_RAW` as not existing or not authorized.

## SSP one-record write-pilot markdown result checkpoint

Visible Python exception:

```text
PilotError: EXTRA_TARGET_ROWS_REQUIRE_REVIEW
```

Pilot result:

```json
{
  "EDGES": 18,
  "ERROR_DETAILS": {"CAUSE": "EXTRA_TARGET_ROWS_REQUIRE_REVIEW"},
  "MODE": "PREVIEW",
  "MODEL": "SSP",
  "NODES": 19,
  "PERSISTED": false,
  "PHASE": "SCHEMA_AND_STAGING",
  "RELEASE": "one-record-write-v3-temp-materialization",
  "SOURCE_RECORDS": 1,
  "STATUS": "EXTRA_TARGET_ROWS_REQUIRE_REVIEW",
  "TARGET_DML_ATTEMPTED": false
}
```

## Read-only candidate-vs-target comparison checkpoint

A subsequent read-only comparison completed successfully. The notebook explicitly reports:

- `BASELINE = CURRENT_ACCEPTED_GRAPH_NOT_ORIGINAL_FROZEN_SNAPSHOT`
- `CANDIDATE_NODES = 19`
- `CANDIDATE_EDGES = 18`
- `SOURCE_RECORDS = 1`
- `STATUS = READ_ONLY_COMPARISON_COMPLETE`
- `TARGET_DML_ATTEMPTED = false`

Visible extra DIM rows by element type:

| Element type | Rows |
|---|---:|
| authorization-boundary | 1 |
| components | 3 |
| document-ids | 1 |
| metadata | 1 |
| props | 3 |
| responsible-parties | 6 |
| security-impact-level | 1 |
| status | 1 |
| system-characteristics | 1 |
| system-ids | 1 |
| system-implementation | 1 |
| system-security-plan | 1 |

Visible FACT comparison:

- `parent_of`: 20 extra FACT rows; `SOURCE_IN_BATCH=false`, `TARGET_IN_BATCH=false`.

Summary counts reported by the notebook:

| Metric | Count |
|---|---:|
| CANDIDATE_EDGES | 18 |
| CANDIDATE_NODES | 19 |
| DIM_DUPLICATE_KEY_GROUPS | 0 |
| EXTRA_DIM_DISTINCT_KEYS | 21 |
| EXTRA_DIM_ROWS | 21 |
| EXTRA_FACT_DISTINCT_KEYS | 20 |
| EXTRA_FACT_ROWS | 20 |
| FACT_DUPLICATE_KEY_GROUPS | 0 |
| TARGET_DIM_ROWS | 21 |
| TARGET_FACT_ROWS | 20 |

Interpretation for Codex: the comparison is now complete and confirms that the currently accepted target graph contains 21 DIM rows and 20 FACT rows relevant to this comparison, while the one-record candidate contains 19 nodes and 18 edges. There are no duplicate DIM or FACT key groups. This is read-only evidence only; no target DML was attempted. The baseline is explicitly the current accepted graph, not an original frozen snapshot, so do not treat this comparison as proof of equivalence to the original pre-existing target state.

This checkpoint records the actual physical Snowflake table contract and visible notebook evidence. No database changes were made by this documentation update.

## SSP one-record reconciliation — durable-backup failure — 2026-09-11

Source: the subsequently supplied screenshot from `NB_ARCHER_OSCAL_MAPPER_V2`. The following is a transcription of the displayed report, not a Snowflake execution performed by this documentation update. Earlier checkpoints above are retained as historical evidence.

### Displayed report

```json
{
  "BACKUP_TABLES": {
    "DIM": "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.BACKUP_SSP_RECONCILE_F53AB9083B324F0C950E13B0D0248CF4_DIM",
    "FACT": "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.BACKUP_SSP_RECONCILE_F53AB9083B324F0C950E13B0D0248CF4_FACT"
  },
  "EDGES": 18,
  "ERROR_DETAILS": {
    "CAUSE": "SQL_OR_CLIENT_ERROR",
    "QUERY_ID": "01c70132-0000-f4df-0002-490cc3694983",
    "SQL_ERROR_CODE": "3001"
  },
  "MODE": "COMMIT",
  "MODEL": "SSP",
  "NODES": 19,
  "PERSISTED": false,
  "PHASE": "DURABLE_BACKUP",
  "RELEASE": "ssp-one-record-reconcile-v1",
  "REVIEWED_SCOPE": {
    "NEW_DIM_ROWS": 19,
    "NEW_FACT_ROWS": 18,
    "OLD_DIM_ROWS": 21,
    "OLD_FACT_ROWS": 20,
    "OLD_KEY_INTEGRITY": {
      "DANGLING_SOURCE_KEYS": 0,
      "DANGLING_TARGET_KEYS": 0,
      "DIM_DUPLICATE_KEY_GROUPS": 0,
      "DIM_NULL_KEYS": 0,
      "FACT_DUPLICATE_KEY_GROUPS": 0,
      "FACT_NULL_KEYS": 0,
      "NULL_FOREIGN_KEYS": 0,
      "ROOTS": 1,
      "UUID_LINK_MISMATCHES": 0,
      "WRONG_PARENT_COUNTS": 0,
      "WRONG_RELATIONSHIP_TYPE": 0
    }
  },
  "SELECTION": "PREVIOUSLY_REVIEWED_LOWEST_ROOT",
  "SOURCE_RECORDS": 1,
  "STATUS": "RECONCILIATION_OPERATION_FAILED",
  "TARGET_DML_ATTEMPTED": false,
  "WRITE_POLICY": "BACKUP_AND_REPLACE_ONE_REVIEWED_RECORD"
}
```

### Visible exception and traceback

```text
PilotError: RECONCILIATION_OPERATION_FAILED

File "Cell [cell8]", line 643, in <module>
    ssp_reconciliation_report = run_ssp_one_record_reconciliation(
File "Cell [cell8]", line 635, in run_ssp_one_record_reconciliation
```

The screenshot ends before the remainder of the traceback. No hidden traceback text or full SQL error message has been reconstructed.

### Scope and safety interpretation for Codex

- This report is from `MODE=COMMIT`, unlike the earlier preview. It nevertheless reports failure at `PHASE=DURABLE_BACKUP`, `PERSISTED=false`, and `TARGET_DML_ATTEMPTED=false`. Do not describe the target replacement as completed.
- The reviewed old scope contains 21 DIM rows and 20 FACT rows; the proposed new scope contains 19 DIM rows and 18 FACT rows. The old graph reports one root and zero for every listed key/relationship-integrity error counter. These checks do not establish semantic equivalence between old and new graphs.
- `BACKUP_TABLES` lists the names reported by the operation. This alone does not prove that both backup tables were created, populated, or verified. `TARGET_DML_ATTEMPTED=false` is not evidence that no backup DDL or other preparatory operation occurred.
- The latest reported SQL error code is `3001`. It is distinct from the earlier `2003` query-history checkpoint. The screenshot provides no full SQL error message; do not infer its precise cause from the code alone or carry forward the earlier missing-object diagnosis as a confirmed cause.
- The next diagnostic should be read-only: inspect the query-history entry for `01c70132-0000-f4df-0002-490cc3694983` to obtain the failed statement and full error, and verify the reported backup state before considering a retry. This documentation does not authorize rerunning COMMIT mode, changing permissions, or deleting/replacing any target or backup data.

Only this Markdown documentation was updated in GitHub. No notebook code, registry configuration, or Snowflake data was changed by this posting.
