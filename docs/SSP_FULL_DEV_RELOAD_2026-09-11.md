# SSP full development truncate-and-reload checkpoint — 2026-09-11

Status: **committed and verified in live Snowflake**.

This checkpoint records the visible notebook result for the full SSP development
table truncate-and-reload.

## Execution summary

```text
RELEASE: ssp-full-dev-truncate-reload-v1
MODE: COMMIT
MODEL: SSP
STATUS: FULL_SSP_RELOAD_COMMITTED_AND_VERIFIED
PERSISTED: true
TARGET_DML_ATTEMPTED: true
WRITE_POLICY: FULL_TABLE_TRUNCATE_AND_RELOAD
BACKUP_POLICY: TRANSACTION_ONLY_DEV
RECOVERY_LIMITATION: NO_DURABLE_COPY_AFTER_COMMIT
LOAD_METADATA_POLICY: TRUNCATE_CLEARS_LOAD_METADATA
SOURCE_RECORDS: 2813
OLD_DIM_ROWS: 126453
OLD_FACT_ROWS: 122939
NEW_DIM_ROWS: 70102
NEW_FACT_ROWS: 67289
TRUNCATED_TARGETS: FACT, DIM
VERIFIED_PASSES: 2
```

## Candidate and final integrity

The candidate, commit checks, and final readback reported the same scope:

- 2,813 selected SSP records
- 70,102 DIM nodes
- 67,289 FACT edges
- zero cross-record edges
- zero dangling source or target keys
- zero null or duplicate DIM/FACT keys
- zero null foreign keys
- zero disconnected records
- zero invalid node ownership/UUID rows
- zero invalid record shapes
- zero UUID-link mismatches
- zero wrong parent counts
- zero wrong relationship types

Saved-value verification reported 70,102 DIM and 67,289 FACT rows in target key
scope, with zero missing keys, mismatched keys, staged duplicate/null keys, or
target duplicate keys.

The first insert pass wrote 70,102 DIM rows and 67,289 FACT rows. The second
idempotency pass inserted zero DIM and zero FACT rows. The commit status was
`COMMITTED`.

## Important recovery limitation

This run used `TRANSACTION_ONLY_DEV` and explicitly reported
`NO_DURABLE_COPY_AFTER_COMMIT`. The previous 126,453 DIM and 122,939 FACT rows
were not retained in durable backup tables by this run. The successful validation
does not remove that recovery limitation.
