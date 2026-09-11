# SSP ten-record development batch checkpoint — 2026-09-11

Status: **committed and verified in live Snowflake**.

This checkpoint records the visible notebook result for the first bounded
ten-record SSP batch after the previously reconciled first record.

## Execution summary

```text
RELEASE: ssp-ten-record-dev-batch-v1
MODE: COMMIT
MODEL: SSP
MAX_SOURCE_RECORDS: 10
SOURCE_RECORDS: 10
SELECTION: NEXT_TEN_ROOT_IDS_AFTER_PROTECTED_FIRST
STATUS: TEN_RECORD_BATCH_COMMITTED_AND_VERIFIED
PERSISTED: true
TARGET_DML_ATTEMPTED: true
BACKUP_POLICY: TRANSACTION_ONLY_DEV
RECOVERY_LIMITATION: NO_DURABLE_COPY_AFTER_COMMIT
PROTECTED_FIRST_RECORDS: 1
PROTECTED_FIRST_RECORD_UNCHANGED: true
ROLLBACK_RESTORED_BASELINE: true
```

## Reconciled scope

| Metric | Count |
|---|---:|
| Old DIM rows | 420 |
| Old FACT rows | 410 |
| New DIM rows | 289 |
| New FACT rows | 279 |
| Selected source records | 10 |

The rehearsal and commit each deleted the exact scoped 420 DIM / 410 FACT rows
and inserted 289 DIM / 279 FACT rows on pass 1. The insert-only idempotency
second pass inserted 0 DIM and 0 FACT rows. Both phases reported
`VERIFIED_PASSES: 2`; the rehearsal reported `STATUS: ROLLED_BACK`, and the
commit reported `STATUS: COMMITTED`.

## Validation evidence

Candidate, rehearsal, commit, and final readback reported the expected 289 nodes
and 279 edges for 10 records. All displayed validation counters were zero:

- cross-record edges
- dangling source and target keys
- DIM and FACT duplicate or null keys
- disconnected records
- invalid node ownership or UUID
- invalid record shapes
- null foreign keys
- UUID link mismatches
- wrong parent counts
- wrong relationship type
- missing or mismatched saved DIM/FACT keys

Saved-value checks reported 289 DIM and 279 FACT target rows in key scope, matching
the staged rows. The previously reconciled first record remained unchanged.

## Recovery limitation

This batch used `TRANSACTION_ONLY_DEV`. It did not create or verify a durable
backup table, and the report explicitly states
`RECOVERY_LIMITATION: NO_DURABLE_COPY_AFTER_COMMIT`. This evidence establishes
successful scoped persistence and validation; it does not establish durable
post-commit recovery protection or authorize an unbounded/full-table run.
