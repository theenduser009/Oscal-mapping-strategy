# SSP — replace one reviewed development record

Status: **v2 implemented; live replacement remains pending**.

## Current owner-approved policy — no permanent backup

On September 11, the owner approved skipping permanent backup creation for
**only the previously reviewed SSP development record**. The earlier v1 attempt
passed old-key checks and stopped before target DML because its execution role
could not create a permanent backup in the curated schema. This change removes
that backup-creation operation; it does not grant privileges or establish that
target INSERT/DELETE permissions are available.

The cell's `SSP_RECONCILE_BACKUP_POLICY = "TRANSACTION_ONLY_DEV"` is already set.
Temporary old/new snapshots, transaction rollback, rollback rehearsal, exact
record scope and primary/foreign-key/readback checks remain required.
**After COMMIT, there is no separate durable copy of the old graph.**
Temporary snapshots must not be treated as permanent recovery protection.
This is not authorization to skip backups for another record, bulk load or production.

## Run once

Open [RECONCILE_SSP_ONE_RECORD_WRITE.py](../notebooks/persistence/RECONCILE_SSP_ONE_RECORD_WRITE.py).

1. Replace only your separate reconciliation Python cell with the complete file.
2. At line 10 set `SSP_RECONCILE_MODE = "COMMIT"`. Leave the preset backup policy unchanged.
3. Keep `CONFIG["EXECUTE_WRITES"] = False` and pause other writers to the SSP DEV targets.
4. In the same accepted notebook session, run only that replacement cell once
   and post its complete printed report. No old pilot, registry or error-history rerun is needed.

If the session closed, first rebuild unchanged Cells 1–7 with writes disabled.
The accepted overall graph remains 70,102 nodes / 67,289 edges.
PREVIEW is optional and makes no target DML; COMMIT includes the same preflight.

## Scope and checks retained

- Targets remain the two configured SSP **development** DIM/FACT tables.
  AR, registry, Matillion and other records are outside this operation.
- Select the same lowest-root SSP record used in the reviewed comparison:
  old **21 DIM / 20 FACT**, new **19 DIM / 18 FACT**, zero old/new key overlap.
  Changed counts, ownership or scope stop the cell; no fallback record is selected.
- Freeze the complete old/new data. Every edge touching the old record must
  have both endpoints inside it. Check PK uniqueness/nulls, both FK endpoints,
  UUID links, relationship type, root, parent counts and connected hierarchy.
- At the start of each transaction, compare live scoped targets against the old
  snapshot. Delete only the frozen **20 old FACT keys**, then **21 old DIM keys**,
  with exact deleted-row counts required.
- Insert **19 new DIM / 18 new FACT**, verify every projected saved value and key,
  then repeat the insert-only merges: require zero extra inserts and verify again.
- Roll back the first transaction and prove the old baseline is restored.
  Only then repeat replacement in a second transaction and COMMIT.
- Verify saved data and PK/FK integrity again after commit. Keep old physical keys
  in the comparison scope so leftover old nodes/edges cannot escape checks.

Snowflake uses [READ COMMITTED isolation](https://docs.snowflake.com/en/sql-reference/transactions#read-committed-isolation-level);
these checks are not a serializable reservation. Other writers must stay paused.

## Read the report correctly

Success requires `ONE_RECORD_RECONCILED_AND_VERIFIED`, `PERSISTED: true`,
`ROLLBACK_RESTORED_BASELINE: true`, and clean final saved-value/key checks.

For the approved no-permanent-backup policy, these report fields are expected:

```text
BACKUP_POLICY: TRANSACTION_ONLY_DEV
BACKUP_TABLES: {}
BACKUPS_VERIFIED: false
RECOVERY_LIMITATION: NO_DURABLE_COPY_AFTER_COMMIT
```

A replacement error must roll back its transaction; an uncertain BEGIN, COMMIT
or ROLLBACK reports `UNKNOWN_DO_NOT_RETRY`. A post-commit verification failure can
report `PERSISTED: true`; that is not a successful rollback. Do not retry, perform
DDL, or automatically restore after an uncertain result. No automatic restoration
is provided, and this policy creates no durable backup for later restoration.

Do not rerun after success: the old-shape guard is expected to stop another
replacement. This does not advance to another record or authorize bulk loading.

The callable helper retains `backup_policy="DURABLE"` for callers that explicitly
need the original behavior; the notebook entry point passes the owner-approved
development-only policy above. No permanent backup table is created on that path.
All 339 local tests pass, including seven focused no-backup policy regressions.
These are not proof of Snowflake write acceptance or complete OSCAL conformance.

## Historical evidence — previous permanent-backup policy

The v1 report and permission finding below are retained verbatim. Their instruction
to obtain backup-creation permission applied to v1; the owner-approved v2 policy
above supersedes that requirement only for this reviewed development record.

## Live Snowflake evidence — 2026-09-11

Latest COMMIT attempt **did not persist the replacement**.

Observed report:

```text
MODE: COMMIT
MODEL: SSP
NODES: 19
EDGES: 18
PERSISTED: false
PHASE: DURABLE_BACKUP
RELEASE: ssp-one-record-reconcile-v1
SELECTION: PREVIOUSLY_REVIEWED_LOWEST_ROOT
SOURCE_RECORDS: 1
STATUS: RECONCILIATION_OPERATION_FAILED
TARGET_DML_ATTEMPTED: false
WRITE_POLICY: BACKUP_AND_REPLACE_ONE_REVIEWED_RECORD
```

The operation proposed/created uniquely named DIM and FACT backup tables under
`RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED` and then stopped in the durable
backup phase with `ERROR_DETAILS.CAUSE = SQL_OR_CLIENT_ERROR`,
`SQL_ERROR_CODE = 3001` (query ID was also reported by Snowflake).

The reviewed scope was still exactly the expected old/new shape:

```text
NEW_DIM_ROWS: 19
NEW_FACT_ROWS: 18
OLD_DIM_ROWS: 21
OLD_FACT_ROWS: 20
```

The old-key integrity checks shown in the report were clean: dangling source/target
keys 0, DIM duplicate/null key groups 0, FACT duplicate/null key groups 0, null
foreign keys 0, roots 1, UUID link mismatches 0, wrong parent counts 0, and wrong
relationship type 0.

**Important:** `PERSISTED=false` and `TARGET_DML_ATTEMPTED=false`. Therefore this
failure is currently evidence of a backup/SQL-client operation problem, not a
failed DIM/FACT replacement. Do not rerun COMMIT blindly. First inspect the exact
Snowflake query/error associated with the reported query ID and determine which
backup statement failed and whether either listed backup table actually exists.


### Exact backup failure retrieved from query history

The read-only query-history lookup returned the failing statement:

```text
QUERY_ID: 01c70132-0000-f4df-0002-490cc3694983
START_TIME: 2026-09-11 14:26:01 -0400
QUERY_TYPE: CREATE_TABLE_AS_SELECT
ROLE_NAME: PUBLIC
DATABASE_NAME: USERSC95077009
SCHEMA_NAME: PUBLIC
ERROR_CODE: 3001
ERROR_MESSAGE: SQL access control error: Insufficient privileges to operate on schema 'ES_ESC_GRC_CURATED'. Your primary role PUBLIC must have CREATE TABLE granted on schema RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.
```

This confirms that the reconciliation stopped because its permanent backup CTAS
ran with primary role `PUBLIC`, which lacks `CREATE TABLE` on the curated DEV
schema. The failure occurred before target DIM/FACT DML; it is not evidence of a
failed replacement. Do not retry COMMIT under `PUBLIC`, do not bypass the durable
backup, and do not enable the general notebook write flag. The next execution
requires an approved role that can create and verify the two scoped permanent
backup tables in `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED`.
