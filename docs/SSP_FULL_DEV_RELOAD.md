# Full SSP development truncate-and-reload

Status: **prepared; full-table Snowflake execution is not yet accepted**.
The one-record and [ten-record batch](SSP_TEN_RECORD_DEV_BATCH_2026-09-11.md)
already passed live persistence checks: eleven source records in total.

The owner explicitly requested a full reload instead of incremental batches,
including those eleven records, and waived permanent backups for these DEV tables.

## Run this cell

[Open the complete full-reload Python cell](../notebooks/persistence/RELOAD_ALL_SSP_DEV.py).

1. Keep the accepted Cells 1–7 outputs in the same active notebook session.
   If that session is still active, do **not** rerun those cells or the old pilots.
2. Pause any other jobs or sessions writing these two SSP targets.
3. Paste the entire file into **one new Snowflake Python cell**.
4. At line 10, set `SSP_RELOAD_MODE = "COMMIT"`.
   Keep the ordinary mapper's `CONFIG["EXECUTE_WRITES"] = False`.
5. Run only that new cell once and post its complete printed summary.

No record-ID inputs, registry setup, separate rehearsal, manual truncate query,
or permanent backup table is required. The default `PREVIEW` mode stages and
checks data but performs no target DML; it is not a committed reload.
If the notebook session restarted, rebuild unchanged Cells 1–7 with normal
writes disabled before running the reload.

## Exact replacement scope

The cell replaces **all rows** in these two fixed development tables:

- `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT`
- `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY`

Replacement is the entire accepted in-memory SSP graph:
**2,813 source records, 70,102 DIM nodes and 67,289 FACT relationships**.
Previously stored rows absent from that graph are removed. The eleven verified
records are included in this reload, not skipped or protected separately.
Other databases, tables, OSCAL models, registry rows and Matillion jobs are outside scope.

This persists the approved mapped scope; it does not complete missing Excel rules
or establish full OSCAL schema conformance.

## What happens in the one run

Before target writes, the cell freezes the full graph, checks source/root totals,
live physical datatypes and widths, SSP paths and JSON objects, and validates
every record's node keys, foreign keys, UUID links and parent-child hierarchy.
It creates **session-only temporary snapshots** to compare old rows if rollback
is needed. No permanent backup is created.

One explicit transaction then:

1. Truncates FACT, then DIM, and confirms both are empty.
2. Loads DIM before FACT using the already-tested physical conversion and merge logic.
3. Compares all saved values and keys against the staged graph and validates the full hierarchy.
4. Repeats the insert-only merges; both must insert zero rows.
5. Commits only after these checks pass, then performs a final saved-data readback.

There is no incremental cursor, hundred-record loop, or separate rollback rehearsal.
All temporary-table creation happens before the transaction because Snowflake
DDL can implicitly commit; Snowflake classifies TRUNCATE itself as transactional DML.
[Snowflake transactions](https://docs.snowflake.com/en/sql-reference/transactions)

## Permissions and recovery limits

The current role needs `TRUNCATE` on **both** targets, in addition to the read,
temporary-table and insert permissions used by the successful pilots. Earlier
DELETE/INSERT success does not establish TRUNCATE permission. This cell never
changes roles or grants. A truncate/load/validation failure triggers rollback;
it checks the restored table rows against the temporary snapshots.
[Snowflake privileges](https://docs.snowflake.com/en/user-guide/security-access-control-privileges)

TRUNCATE also clears file-load metadata. Row snapshots do not preserve that
metadata, which Snowflake documents as not recoverable. These are graph target
tables, but any external COPY-based dependency must be considered before running.
[Snowflake TRUNCATE TABLE](https://docs.snowflake.com/en/sql-reference/sql/truncate-table)

There is **no durable copy of the previous graph after commit**. Transaction
rollback does not undo a completed commit. Do not assume Time Travel retention.
An uncertain BEGIN/COMMIT/ROLLBACK or a failed post-commit readback stops with an
explicit report; the cell never retries or restores old data automatically.

## Acceptance

Only the complete final report establishes live success:

`STATUS: FULL_SSP_RELOAD_COMMITTED_AND_VERIFIED`
and `PERSISTED: true`.

Expected source records: **2,813**; saved DIM: **70,102**; saved FACT: **67,289**.
Both second-pass insert counts must be zero. All saved-value, duplicate/null key,
dangling/cross-record edge, UUID, parent-count and reachability checks must be clean.

If it fails, post the full printed report, including its phase and error details.
Do not rerun automatically, especially if persistence is unknown or already true.
Local tests and the prior eleven accepted records are not proof that this full
reload has executed successfully.
