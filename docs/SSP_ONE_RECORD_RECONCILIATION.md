# SSP — replace one reviewed development record

Status: **implemented and locally tested; live replacement is not yet accepted**.

The owner approved replacing only the SSP record selected by the same lowest-root
rule used in the posted comparison. That evidence showed 21 old DIM rows and
20 old FACT rows, versus 19 new nodes and 18 new edges, with zero key overlap.
The subsequent new-record-only pilot found no eligible record, including after
the owner rebuilt Cells 1–7. Those attempts reported no target DML and no
persistence. This replacement is separately authorized; it is not a guard bypass.

## Run once

Open [RECONCILE_SSP_ONE_RECORD_WRITE.py](../notebooks/persistence/RECONCILE_SSP_ONE_RECORD_WRITE.py).

1. In the current accepted SSP notebook session, paste the complete file into
   **one new Python cell**. It is standalone: no old pilot or diagnostic is needed.
2. At line 10 set **SSP_RECONCILE_MODE = "COMMIT"**.
3. Keep **CONFIG["EXECUTE_WRITES"] = False**. Pause all other writers to the SSP
   development DIM/FACT tables and do not run other cells concurrently.
4. Run only the new reconciliation cell once. Post the complete printed report,
   including the backup-table names. Do not start a bulk load afterward.

If the session has closed, first rebuild the unchanged SSP Cells 1–7 with writes
disabled. The required accepted graph is still 70,102 nodes / 67,289 edges.
A separate PREVIEW run is optional, not required: COMMIT performs every preflight
check before replacing anything. PREVIEW creates only temporary snapshots.

## Scope and recovery protection

- Only the configured SSP development DIM and FACT tables are replacement targets.
  AR, registry, Matillion and other source records are outside this replacement.
- Choose the deterministic lowest SSP root, freeze it, and require the reviewed
  candidate shape: 19 nodes / 18 containment edges. Never fall back to another
  source record if a check fails.
- Snapshot its existing target scope and require exactly 21 DIM / 20 FACT rows,
  no duplicate or null keys, zero old/new key overlap, the same source ownership,
  and one connected legacy tree using parent_of relationships.
- Every existing relationship touching the selected graph must stay within that
  record. Cross-record/external endpoints stop replacement; they are not removed.
- Before target DML, create and verify two uniquely named **permanent backup
  tables**, containing every column of the old 21/20 rows. No OR REPLACE, DROP or
  TRUNCATE is used. Backups survive notebook closure and are intentionally retained.
  Creating these backups requires CREATE TABLE permission in the curated DEV
  schema; lack of permission stops before any target row is changed.
- Backup names appear in BACKUP_TABLES. If backup creation partly fails, a listed
  name is only a proposed name until BACKUPS_VERIFIED is true. Keep any successfully
  created backup; there is no automatic cleanup.

## What gets verified while writing

Both rehearsal and commit use the same frozen old/new data:

1. BEGIN and compare the current target scope and durable backups against the
   complete old snapshot. Any drift stops before deletion.
2. Delete only the frozen **20 old FACT keys**, then **21 old DIM keys**.
   Both exact deleted-row counts are required.
3. Insert **19 new DIM rows / 18 new FACT rows** and compare every projected saved
   value, physical key, UUID and parsed JSON payload with the frozen candidate.
4. Check null/duplicate primary keys, null foreign keys, missing source/target
   endpoints, UUID link mismatches, relationship type, parent cardinality and
   the single SSP root. All error counts must be zero.
5. Repeat the insert-only merges: require **zero new inserts** and verify again.

The first transaction is rolled back and the complete old baseline must be
restored. Only then does the second transaction repeat replacement and COMMIT.
The code performs one more saved-value and integrity readback after commit.

The comparison retains the old physical keys in scope after deletion, so orphaned
legacy edges or leftover old nodes cannot disappear from verification. These are
checks for the selected record and all relationships touching it, not a claim
that every unrelated record in the database has been validated.

Snowflake uses [READ COMMITTED isolation](https://docs.snowflake.com/en/sql-reference/transactions#read-committed-isolation-level),
so the checks are not a serializable reservation: keep other writers paused.
DELETE statements are bounded by [frozen-key filters](https://docs.snowflake.com/en/sql-reference/sql/delete);
backups use [CREATE TABLE AS SELECT](https://docs.snowflake.com/en/sql-reference/sql/create-table).

## Success, failure and recovery

Success requires **ONE_RECORD_RECONCILED_AND_VERIFIED**, **PERSISTED: true**,
verified backups, a restored rehearsal baseline, and clean final READBACK.
Do not rerun after success: the old 21/20 guard should now stop this one-record
replacement. It does not advance to another record.

A failure during replacement rolls back that transaction. A failed backup or
preflight makes no target row changes. Permanent backups are still retained.
A failed post-commit check can report PERSISTED true: it must not be described
as a successful rollback. Any outcome marked UNKNOWN_DO_NOT_RETRY requires
transaction-state/readback recovery before any retry or restore. Do not run
DDL, auto-restore, delete backups, or repeatedly execute the cell in that state.

The durable backup tables are the recovery source if a later approved restoration
is required. Restore is intentionally not automatic: first establish transaction
state and compare the current record against the saved backup/new snapshot, then
perform a separately reviewed, scoped transaction. This avoids overwriting later
changes or running a second replacement after an uncertain commit.

All 332 local repository tests pass, including 16 new reconciliation tests for
frozen-key deletion, rollback faults, preserved unrelated rows, counts, legacy
ownership, retained old-edge scope, durable-backup ordering and PK/FK corruption.
Static code review found no blocking defect. These checks do not establish live
Snowflake execution, all-record migration, or full OSCAL schema conformance.

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
