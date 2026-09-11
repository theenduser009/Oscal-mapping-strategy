# One-record SSP development write pilot

Status: **temporary-view staging correction locally verified; live write/readback pending**.
The owner approved one SSP record in the configured development DIM/FACT tables.
This is not approval for a bulk load, AR writes, registry changes, or deletes.

## Latest correction: temporary graph snapshots

The posted [error-history checkpoint](ssp_dim_fact_physical_schema_checkpoint_2026-09-11.md)
shows CREATE_VIEW failures for a Snowpark temporary backing object. Release
`ssp-one-record-write-v3-temp-materialization` replaces those two views with
session-temporary table snapshots of the existing accepted DataFrames. It does
not alter mappings, privileges, database/schema context, or persistent targets.

This removes view-schema dependency resolution from graph staging; it cannot
restore an expired source object or grant missing access. Keep the accepted
DataFrames and pilot in the same active session. The code materializes both
frames before any transaction, uses unique temporary names, and refuses to
replace existing objects. If source materialization fails, the report identifies
the node/edge step and available failed-query ID without emitting source SQL.

The existing approved COMMIT instruction below still includes all preflight
checks and rollback rehearsal. No separate schema/history rerun is needed.
See the [bounded correction and test evidence](checkpoints/2026-09-11_ssp_pilot_temp_materialization_fix.md).

## Earlier correction after the first live schema stop

The owner-uploaded [physical schema](ssp_dim_fact_physical_schema_checkpoint_2026-09-11.md)
is now covered by release `ssp-one-record-write-v2-binary16`. The failed earlier
attempt stopped before target DML; **schema capture is complete, not another run
step**. Replace the old pilot cell before the next attempt.

- The four hash columns use `BINARY(16)`: validate the graph's 32 hexadecimal
  characters, then decode with explicit `TO_BINARY(value, 'HEX')`. No rehashing.
- The three UUID columns use `VARCHAR(32)`: validate the canonical dashed UUID,
  then remove hyphens for physical storage only. UUIDs inside JSON stay canonical.
- Invalid identity syntax, incorrect byte width, duplicate projected keys and
  oversized other strings stop before any target MERGE. No silent truncation.
- Scope, ownership, MERGE and readback compare the same projected physical
  representations. Existing conflicting target keys still require review.

These are lossless representation conversions, not new mappings or schema DDL.
Snowflake documents explicit hexadecimal decoding in
[TO_BINARY](https://docs.snowflake.com/en/sql-reference/functions/to_binary) and
byte-size checking in [OCTET_LENGTH](https://docs.snowflake.com/en/sql-reference/functions/octet_length).

## Run this separate cell

Open [PILOT_SSP_ONE_RECORD_WRITE.py](../notebooks/persistence/PILOT_SSP_ONE_RECORD_WRITE.py).

1. Use the notebook session containing the accepted SSP Cell 7 outputs:
   `final_nodes_df`, `final_edges_df`, and `run_result` (70,102 nodes / 67,289 edges).
   If that session has closed, rebuild those outputs with the unchanged SSP Cells
   1–7, keeping `CONFIG["EXECUTE_WRITES"] = False`. Do not run AR for this pilot.
2. Pause other loaders/writers to these two DEV tables during the pilot. Do not
   run other SQL or notebook cells concurrently in this Snowflake session.
3. Copy the **entire pilot file into one new Python cell**. Do not replace any of
   the seven SSP cells or the separate AR cell. Do not rerun registry setup.
4. For the approved persistence pilot, change only the new cell's
   `SSP_PILOT_MODE = "PREVIEW"` to `SSP_PILOT_MODE = "COMMIT"` and run that cell.
   The normal mapper's `CONFIG["EXECUTE_WRITES"]` must remain **False**.
5. Post the printed aggregate report to the usual GitHub status checkpoint.
   Successful persistence ends with `ONE_RECORD_COMMITTED_AND_VERIFIED` and
   `PERSISTED: true`. Do not start a bulk load afterward.

`PREVIEW` is available if you want only preflight: it reads the live schemas,
creates session-temporary stages/snapshots, and checks the SQL/readback plans.
It does **not** modify DIM/FACT rows, but it is not a SELECT-only cell because it
creates temporary objects. A separate preview run is not mandatory before COMMIT;
COMMIT includes the same preflight checks.

## Exactly what COMMIT does

The cell chooses the lowest source-record ID among SSP root nodes in the accepted
graph, freezes that record's complete tree and both-ended containment edges, and
rejects cross-record links or conflicting target keys. It does not choose a
different record merely because the target already contains the first one.

The only allowed persistent targets are:

- `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT`
- `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY`

Live `DESC TABLE` is checked before target DML. Unsupported types, missing required
key/payload/UUID/provenance columns, or unknown required columns without defaults
stop the pilot; their values are never invented. The three known load-audit
columns are projected when present, matching the existing loader. Existing extra rows for this record also stop the
pilot for review instead of being silently deleted.

All temporary stages and baseline snapshots are created before transactions.
Then the cell performs:

1. **Rollback rehearsal:** BEGIN → DIM MERGE → FACT MERGE → compare saved values,
   keys, UUIDs and parsed JSON → repeat both MERGEs and compare → ROLLBACK.
2. **Restore proof:** compare the record's target rows to the complete pre-pilot
   snapshots. No retained target changes are allowed from the rehearsal.
3. **Persistence:** repeat the verified transaction against the same frozen
   batch, COMMIT, and read back again after commit.

The repeat check proves idempotence for the same frozen batch. It is not proof
of a new full mapper run, concurrent-writer safety, all-record loading, or full
OSCAL schema conformance. Accepted SSP mappings and AR status are unchanged.

## If it stops

- A preflight stop means no target DML was attempted.
- `TRANSACTION_ROLLED_BACK` means the active pilot transaction was rolled back;
  the report retains the safe check/phase cause. Do not repeatedly run unchanged
  code—post the report first.
- Any `*_OUTCOME_UNKNOWN` requires transaction-state/readback recovery before
  retrying. Do not run DDL, other notebook cells, or blindly retry the pilot.
- A failed **post-commit** readback can have `PERSISTED: true`: the commit already
  succeeded, so it must not be reported as a clean rollback.
- Catchable cancellation triggers rollback. A hard session/network failure may
  still require recovery. Session-temporary objects are intentionally not
  automatically dropped after uncertain outcomes.

Local tests cover transaction faults, cancellation, schema rejection, structural
JSON comparisons, key discrepancies, preview/commit ordering and stale-report
prevention. No live Snowflake execution is claimed by those tests.

Implementation references: Snowflake [transactions](https://docs.snowflake.com/en/sql-reference/transactions),
[DESC TABLE](https://docs.snowflake.com/en/sql-reference/sql/desc-table), and
[PARSE_JSON](https://docs.snowflake.com/en/sql-reference/functions/parse_json).
