# Current Status

Last reconciled: 2026-09-08

## Verified state

- Current notebook: `NB_ARCHER_OSCAL_MAPPER_V1`.
- The generic seven-cell architecture is preserved: configuration, inputs, canonical mapping, helpers/transforms, graph builder, guarded loader, and orchestrator.
- A prior run read 5,626 source rows but only 2,813 distinct source record IDs.
- Cell 5 consequently produced duplicate node and edge keys.
- Cell 6 correctly blocked all writes.
- The physical RAW-table count has not yet been supplied, so the duplication's physical origin is still unconfirmed.
- Repository source passes Python syntax compilation. Snowflake runtime validation remains pending because this environment is not connected to the user's Snowflake session or mapping CSV.

## What the consolidated notebook restores

- Registry-first hierarchy construction.
- Deterministic node, UUID, and edge identity.
- One canonical mapping contract.
- Archer select-value lookup.
- FIPS 199 Low/Moderate/High normalization.
- Approved responsible-party role transformations.
- A generic Direct/Transform/Extension dispatcher.
- A fail-closed source-record selector using available technical recency columns.
- Mapping coverage output for sprint reporting.
- Graph validation, pre-write validation, idempotent DIM/FACT merge, and post-load verification.

## Safety gate

Keep `EXECUTE_WRITES = False`.

The source selector behaves as follows:

1. If RAW has one row per `CONTENT_ID`, it passes rows through.
2. If RAW contains duplicates and an approved technical load/version column exists, it selects the newest row deterministically.
3. If RAW contains duplicates but no approved ordering column exists, it stops with an error instead of silently discarding data.

## Immediate next action

Run this read-only SQL in Snowflake:

```sql
SELECT
    COUNT(*) AS RAW_ROWS,
    COUNT(DISTINCT CONTENT_ID) AS DISTINCT_CONTENT_IDS
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW;
```

Send back:

```text
RAW_ROWS = ...
DISTINCT_CONTENT_IDS = ...
```

After those counts are reviewed, run Cells 1 through 7 with writes still disabled. Runtime results will determine whether the technical source-order candidates need adjustment before SSP mapping resumes at `system-characteristics.props[]`.

