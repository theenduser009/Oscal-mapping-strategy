# SSP — capped ten-record development write

Status: **implemented; live batch write acceptance pending**.

The first SSP development record was committed and verified in the
[posted one-record report](SSP_ONE_RECORD_RECONCILIATION.md#live-transaction-only-reconciliation-result--2026-09-11).
Do not rerun that cell. This next increment caps the write at **ten additional
source records**, not all remaining records. It retains the approved no-permanent-
backup development approach and uses rollback rehearsal followed by commit in
one cell; no separate test-cell run is requested.

## Run this cell once

Open [PILOT_SSP_TEN_RECORD_BATCH_WRITE.py](../notebooks/persistence/PILOT_SSP_TEN_RECORD_BATCH_WRITE.py).

1. In the same accepted SSP notebook session, add **one new Python cell** and
   paste the entire file. Leave the successful one-record cell unchanged.
2. At **line 10**, set **SSP_BATCH_MODE = "COMMIT"**.
3. Keep **CONFIG["EXECUTE_WRITES"] = False**. Leave the fixed batch cap unchanged.
   Pause all other writers to the SSP DEV DIM/FACT tables.
4. Run only this new cell once, then post the full printed report.

If the accepted session closed, rebuild unchanged Cells 1–7 with writes disabled
first. Accepted input totals remain 70,102 graph nodes / 67,289 edges.
A separate PREVIEW run is not required; COMMIT includes all preflight checks.

## Exact scope and behavior

- The two configured SSP DEV DIM/FACT tables remain the only targets.
  No AR, registry, Matillion or mapper changes are made.
- Exclude the deterministic lowest SSP root: the already verified first record.
  Freeze its complete stored graph separately and require its known 19/18 shape.
- Select at most ten next source IDs in sorted order. This is a fixed batch,
  **not a moving cursor**. Rerunning selects the same records, not another ten.
- Materialize accepted graph data and physical stages inside Snowflake.
  Reuse the verified BINARY(16) key and compact UUID storage conversions.
  Source values and IDs are not printed in the aggregate report.
- Check each old/new record separately: one root, correct parent counts,
  edges = nodes minus one, full reachability, matching UUIDs and no cross-record
  edges—even between two selected records.
- A wholly absent old record is allowed; a partly missing or invalid old tree is
  rejected. Actual old/new row counts are frozen and used for DML verification,
  rather than assuming every SSP has 19/18 nodes/edges.
- Shared old/new primary keys must retain ownership. Same-owner overlap and
  legacy parent_of to CONTAINS normalization are allowed; changed ownership or
  FACT endpoints stop before deletion.
- Freeze exact old keys. Delete only selected FACT keys, then DIM keys, requiring
  exact row counts. Insert complete staged DIM/FACT rows and verify all projected
  saved values, keys and payloads. Repeat merges must insert zero additional rows.
- Roll back the first transaction and prove the full original baseline is restored.
  Only then repeat the operation and COMMIT. Perform one final readback.
- The first accepted record is compared against its complete snapshot during
  verification and after rollback. Its rows are not replacement targets.
  Retain old incident-edge scope to detect leftover legacy rows.

This creates temporary snapshots, **not permanent backups**. There is no separate
durable recovery copy after commit. Transaction rollback does not undo a commit.
Other writers must stay paused: baseline checks are not a concurrency lock.

## Accept the result

Require all of:

- STATUS: **TEN_RECORD_BATCH_COMMITTED_AND_VERIFIED**
- PERSISTED: **true**
- SOURCE_RECORDS: between 1 and 10
- ROLLBACK_RESTORED_BASELINE: **true**
- Second-pass inserts: **0 DIM / 0 FACT**
- Final saved-value/key checks clean, and PROTECTED_FIRST_RECORD_UNCHANGED: **true**

A pre-commit failure rolls back its transaction; the runner also checks the
restored selected/protected baselines. A failed rollback verification or uncertain
BEGIN/COMMIT/ROLLBACK is not accepted and must not be retried automatically.
A post-commit readback failure can report PERSISTED true: inspect it rather than
claiming rollback or running the batch again.

**Do not rerun after success or start an all-record load.** Post the report first.
Local validation: 358 repository tests pass, including 19 batch transaction,
relational integrity, selection and runner checks. Local tests and static review
do not establish live Snowflake persistence for this batch or full OSCAL validity.
