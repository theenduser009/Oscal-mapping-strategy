# Decision Log

## 2026-09-08 — Repository reconciliation

- `NB_ARCHER_OSCAL_MAPPER_V1` is the only current mapper notebook.
- The older SSP-specific notebook remains a conceptual reference only and is not copied into this repository.
- Temporary three-cell props diagnostics are retired to avoid conflicting sources.
- GitHub becomes the durable checkpoint for code, current status, architectural context, and future substantive project responses.
- Writes remain disabled until a read-only Snowflake run passes every validation gate.

## Current technical decision

The observed 5,626 rows versus 2,813 distinct source IDs is treated as an upstream source-selection problem until the physical RAW-table count proves otherwise. Cell 2 now permits deterministic deduplication only when an approved technical recency column is present; otherwise it raises an error.

## Next decision required

Review the RAW row count and distinct `CONTENT_ID` count. Then confirm which available technical timestamp or version column is the authoritative tie-breaker for duplicate Archer records.



## 2026-09-08 — Cleanup completed

The main branch now contains one 1,083-line, seven-cell Mapper V1 source plus the authoritative current-status and architecture documents. The notebook passes Python syntax compilation. Snowflake runtime validation remains pending, and `EXECUTE_WRITES` remains `False`.

Removed from the current branch as superseded:

- the three-cell props inspection script;
- the four copy-page files generated from that partial script;
- the older SSP progress file;
- the older response log.

All removed material remains recoverable through Git history. Future substantive project checkpoints are recorded in this decision log.


## 2026-09-08 — Path and payload demonstration query

Added a read-only SQL query that starts from the SSP DIM root, follows parent-child links in the FACT table, reconstructs each structural path, resolves registered array paths, and displays the payload written to each DIM element. It defaults to test content ID `565189` and performs no writes.

Query: [`sql/show_oscal_path_and_payload.sql`](../sql/show_oscal_path_and_payload.sql)
