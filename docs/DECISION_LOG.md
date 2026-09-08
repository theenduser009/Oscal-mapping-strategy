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

