# OSCAL Mapping Strategy

This repository is the durable checkpoint for the metadata-driven Archer-to-OSCAL mapper.

## Authoritative files

- [`notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`](notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py) — the complete seven-cell Snowflake/Snowpark notebook source.
- [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md) — verified state, safety gate, and the single next action.
- [`docs/ARCHITECTURE_CONTEXT.md`](docs/ARCHITECTURE_CONTEXT.md) — design guardrails that must survive future edits.
- [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md) — dated project decisions and GitHub checkpoints.

The earlier three-cell `ssp_props_read_only_cells.py` and its copy pages were temporary diagnostics. They have been removed to prevent them from being mistaken for the production mapper.

## Safety

The committed notebook always starts with:

```python
"EXECUTE_WRITES": False
```

Cell 6 validates the graph and target load frames before any merge. Cell 7 is the only execution cell. Do not enable writes until the read-only run has zero duplicate keys, zero null primary keys, and zero dangling edges.

## Immediate next action

Determine whether the confirmed two-times duplication originates in the physical Archer table:

```sql
SELECT
    COUNT(*) AS RAW_ROWS,
    COUNT(DISTINCT CONTENT_ID) AS DISTINCT_CONTENT_IDS
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW;
```

Return only the two counts. The notebook's Cell 2 now fails closed when duplicates exist without an approved technical recency column; it never applies blind `DISTINCT` or arbitrary `drop_duplicates` logic.



## Read-only inspection SQL

- [Show full OSCAL paths, DIM payloads, and FACT relationships for one SSP](sql/show_oscal_path_and_payload.sql)
- [Drill into `system-characteristics` and all descendant payloads](sql/drill_down_system_characteristics.sql)

- [Inspect security-impact-level and extract confidentiality, integrity, and availability](sql/drill_down_security_impact_level.sql)
