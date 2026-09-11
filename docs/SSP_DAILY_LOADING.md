# SSP daily loading through Cells 6 and 7

Status: **implemented and locally verified; live Snowflake acceptance pending**.
Local repository suite: 407 tests passed, including 28 focused daily-loader/orchestrator checks.
This is a preview-ready release, not a production or live-write acceptance claim.
The earlier [full DEV reload](SSP_FULL_DEV_RELOAD_2026-09-11.md) remains accepted and must not be rerun for this change.

## What changes

There is no additional SSP execution cell. Cell 6 remains the loader; Cell 7 remains the runner. Cells 1-5 and the accepted mapping rules are unchanged. Matillion still owns raw field-ID-to-CURATED_JSON conversion upstream.

Cell 7 has an explicit `SSP_LOAD_MODE` setting. Its default is `PREVIEW`.
The shared Cell 1 `CONFIG["EXECUTE_WRITES"]` stays `False`. Cell 7 makes a
per-run configuration copy and enables that copy only for an explicit
`COMMIT`; it does not turn on writes for other cells, AR or a later diagnostic.

## Daily write policy

- Insert new keys.
- Update existing keys only when mapped business values differ.
- Do not update unchanged rows just because the new run has fresh audit values.
- Preserve rows belonging to source records outside the current input.
- Do not truncate or delete. If a currently selected record has stored nodes or edges absent from its newly generated graph, block the write and report the difference. A changed collection key or newly empty field can require this review.
- Keep accepted mappings, deterministic identity, registry and SSP targets unchanged.

This release's conservative obsolete-row policy is **block, not delete**. It
supports new rows and same-key updates; it is not automatic deletion synchronization.
A future deletion/reconciliation rule needs explicit approval and separate tests.
Preserving a source record absent from the current input does not prove it was
deleted upstream or that input was complete.

## Integrated safeguards

Cell 6 reuses the physical-storage contract proven in the separate persistence
work: binary hashes are decoded from their existing hexadecimal identity, physical
UUIDs use the required compact representation, and payloads are parsed into VARIANT.
It inspects the live schema, freezes staging in uniquely named temporary tables,
then checks keys, ownership and hierarchy before target mutations.

Business comparison excludes the three technical audit columns. Exact mapped
business values and graph links are verified after upserts; unchanged rows retain
their stored audit values. A repeat MERGE must insert and update zero rows.

DIM and FACT writes share one explicit transaction. Staging DDL happens before
that transaction. A pre-commit failure attempts rollback; an unknown commit outcome
or a failed post-commit readback is not a successful run and must not be blindly
retried. No permanent backup tables or privilege changes are introduced.

Coverage computation occurs before the loader. Cell 7 clears prior outputs at
the beginning, so a failed new run cannot look successful merely because an old
`run_result` remains in the notebook.

## First updated run — do not use a pilot or reload cell

1. Replace only [Cell 6](../notebooks/cells/06_validation_and_guarded_loader.py) and
   [Cell 7](../notebooks/cells/07_mapper_orchestrator.py) with their complete updated
   files.
2. Keep Cell 7 `SSP_LOAD_MODE = "PREVIEW"` and shared
   `CONFIG["EXECUTE_WRITES"] = False`.
3. If Cells 1-5 inputs/helpers are still available in the active session, run
   Cell 6 then Cell 7. If the session restarted, run the unchanged Cells 1-5
   first, then the updated Cells 6 and 7.
4. Post the complete aggregate load report. PREVIEW can create temporary staging
   but performs no target DML. Do not run Cell 8, an old write pilot, registry setup,
   assembly or discovery cells for this check.

Before a later approved COMMIT, confirm preview has no schema, identity, obsolete-row
or integrity blockers, confirm the reported scope, and pause other writers to the
same targets. Change only Cell 7's mode to `COMMIT` and run Cell 7 in the active
session. It rebuilds the graph from the current in-memory inputs; it is not bound
to an old preview result. For a new daily source snapshot, refresh input Cells 1-5
as part of the seven-cell workflow.

The printed `OSCAL_LOAD_REPORT` is the report to share. PREVIEW success is
`DAILY_SSP_PREVIEW_PASSED_NO_TARGET_DML` with no target DML. COMMIT success is
`DAILY_SSP_COMMITTED_AND_VERIFIED` with `persisted: true`. Reported expected
changes separate inserts, updates and unchanged rows for DIM and FACT.

A successful COMMIT must be followed by verified persisted data. An all-unchanged
run should report no inserts or updates. Do not claim changed-row or new-row live
behavior was exercised if that run changed nothing.

## Still not claimed

- Full SSP document/schema completeness.
- Reconciliation of the 56,351 old DIM / 55,650 old FACT row reduction from the earlier full reload.
- A completed AR loader or acceptance of the blocked 34-field AR candidate.
- A scheduled daily job, incremental extraction/watermark, or production readiness.
- Recovery of the old graph after the accepted transaction-only full reload.

Local tests and code review are not live Snowflake acceptance. Keep that distinction
in [current status](CURRENT_STATUS.md) and the [project handoff](PROJECT_HANDOFF.md).
