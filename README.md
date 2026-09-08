# OSCAL Mapping Strategy

This repository is the durable checkpoint for the metadata-driven Archer-to-OSCAL mapper.

## Authoritative files

- [`notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`](notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py) — the complete seven-cell Snowflake/Snowpark notebook source.
- [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md) — verified state, safety gate, and the single next action.
- [`docs/ARCHITECTURE_CONTEXT.md`](docs/ARCHITECTURE_CONTEXT.md) — design guardrails that must survive future edits.
- [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md) — dated project decisions and GitHub checkpoints.
- [`docs/OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md`](docs/OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md) — pinned version sources and the first-tier required SSP contract.

The earlier three-cell `ssp_props_read_only_cells.py` and its copy pages were temporary diagnostics. They have been removed to prevent them from being mistaken for the production mapper.

## Safety

The committed notebook always starts with:

```python
"EXECUTE_WRITES": False
```

Cell 6 validates the graph and target load frames before any merge. Cell 7 is the only execution cell. Do not enable writes until the read-only run has zero duplicate keys, zero null primary keys, and zero dangling edges.

## Latest verified checkpoint

Snowflake run `20260908T201705Z` passed graph and pre-write validation with
51,500 nodes, 48,687 edges, zero duplicate or dangling keys, and no writes.
The populated mapped values passed their reviewed normalization rules.

The earlier 2,585 aggregate was corrected: under pinned OSCAL SSP 1.2.3,
2,453 no-objective security-impact assemblies are optional absences. The
narrow emitted/required security/status gap is 221 field occurrences: 179
missing objectives inside 90 partial security-impact assemblies plus 42
missing `status.state` values.

## Immediate next action

The minimum-required-scope audit now proves that all 2,813 current records are
blocked by SSP completeness gaps. In the same live Snowflake session, run the
aggregate-only
[required-source readiness audit](notebooks/validation/RUN_AFTER_07_ssp_v123_required_source_readiness_audit.py).
It determines whether each missing path and field already has executable
mapping/source evidence, needs registry activation, needs nested-payload
shaping, or requires an approved controlled configuration value.

No rerun of Mapper Cells 1-7 is needed in the active session. This diagnostic
does not expose source identifiers or values, change the graph, assemble final
OSCAL JSON, replace official validation, or authorize writes. Keep
`EXECUTE_WRITES = False`.

## Read-only inspection SQL

- [Show full OSCAL paths, DIM payloads, and FACT relationships for one SSP](sql/show_oscal_path_and_payload.sql)
- [Drill into `system-characteristics` and all descendant payloads](sql/drill_down_system_characteristics.sql)

- [Inspect security-impact-level and extract confidentiality, integrity, and availability](sql/drill_down_security_impact_level.sql)
