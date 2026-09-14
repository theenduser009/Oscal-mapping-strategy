# OSCAL Mapping Strategy

Archer-to-OSCAL mapping through one metadata-driven, seven-cell Snowflake notebook.

**Start with [the project walkthrough](docs/PROJECT_WALKTHROUGH.md).** It explains
the full journey from SSP to Assessment Plan, each cell/function, field mappings,
keys and relationships, testing, accepted loads and remaining work.

## Current package

The seven maintained cells total **1,903 lines**. The mapping CSV contains 153
rows; selected execution rows are SSP 49, Assessment Results 32, POAM one and
Assessment Plan five. These are mapping-row counts, not distinct source fields
or complete OSCAL models. See the [field index](docs/MAPPING_FIELD_INDEX.md).

SSP and AR have accepted historical COMMIT/readback reports. The new SSP
daily-loss field still needs live acceptance. POAM's accepted report is a preview,
not a committed load. Assessment Plan's registry setup root-identity defect is
fixed; a successful live setup/preview/load report remains unverified.

The owner acknowledged the Assessment Plan DDL step. That acknowledgement is
recorded separately from a full run report. Use [current status](docs/CURRENT_STATUS.md)
and the [SAP run guide](docs/SAP_NEXT_RUN.md) for the active setup/preview step.
No SSP/AR/POAM reload or registry reset is implied.

## Code, metadata and explanation

- [Seven maintained source cells](notebooks/cells/README.md) and [generated copy pages](notebooks/cells_v2/README.md).
- [Cells One through Four explained](docs/CELLS_1_TO_4_EXPLAINED.md): configuration, reads, compilation, transformations.
- [Cells Five through Seven explained](docs/CELLS_5_TO_7_EXPLAINED.md): graph, storage, validation and execution.
- [Mapping CSV](Mapping/ARCHER_OSCAL_MAPPINGS.csv): exact field names, one chosen execution path and approved behavior.
- [Architecture](docs/ARCHITECTURE_CONTEXT.md): registry ownership, configuration and common runtime boundaries.
- [Handoff](docs/PROJECT_HANDOFF.md), [mapping progress](docs/MAPPING_PROGRESS.md), [decision log](docs/DECISION_LOG.md).
- [Assessment Plan table DDL](sql/CREATE_ASSESSMENT_PLAN_TABLES.sql) and [corrected registry SQL](sql/registry/ENABLE_ASSESSMENT_PLAN_METADATA.sql).

## Testing and operation

[All 237 implementation CI tests passed with zero skips](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/34855613652).
These include installed Snowpark APIs and local SQL-adapter tests; they do not
replace live Snowflake acceptance. Relevant private screenshot excerpts are
checked separately without publishing private source data.

```shell
python tools/sync_notebook_cells.py --check
python -m unittest discover -s tests/lean -v
```

Keep shared EXECUTE_WRITES false and select PREVIEW or COMMIT in Cell Seven.
PREVIEW does not write the target DIM/FACT tables; temporary staging is used.
COMMIT previews all routes first, then uses a separate transaction per route.
Recorded readback establishes a batch result, not full OSCAL conformance.
SSP Control Implementation's 42 rows remain deferred.

## Historical evidence

The [walkthrough timeline](docs/PROJECT_WALKTHROUGH.md#how-we-got-here) links the
SSP milestones, simplification, FIPS reconciliation, AR, POAM and SAP changes.
Older dated checkpoints retain their original evidence; their old next-step
instructions do not override current status. The [previous README](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/README.md)
is retained in Git history. No source data or screenshot transcript is published.
