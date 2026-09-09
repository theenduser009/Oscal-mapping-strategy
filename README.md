# OSCAL Mapping Strategy

This repository is the durable checkpoint for the metadata-driven Archer-to-OSCAL mapper.

## Authoritative files

- [`notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`](notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py) — the complete seven-cell Snowflake/Snowpark notebook source.
- [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md) — verified state, safety gate, and the single next action.
- [`docs/ARCHITECTURE_CONTEXT.md`](docs/ARCHITECTURE_CONTEXT.md) — design guardrails that must survive future edits.
- [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md) — dated project decisions and GitHub checkpoints.
- [`docs/OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md`](docs/OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md) — pinned version sources and the first-tier required SSP contract.
- [`docs/MAPPING_ARTIFACT_SCREENSHOT_EVIDENCE_2026-09-09.md`](docs/MAPPING_ARTIFACT_SCREENSHOT_EVIDENCE_2026-09-09.md) — filtered visual evidence from the SSP mapping workbook; it is not a replacement for the complete workbook.

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
The reviewed security-impact and status transformations passed their scoped
normalization checks; that statement does not cover every Transform row.

The earlier 2,585 aggregate was corrected: under pinned OSCAL SSP 1.2.3,
2,453 no-objective security-impact assemblies are optional absences. The
narrow emitted/required security/status gap is 221 field occurrences: 179
missing objectives inside 90 partial security-impact assemblies plus 42
missing `status.state` values.

The complete Excel-first
[mapping-artifact progress audit](docs/checkpoints/2026-09-09_SSP_MAPPING_ARTIFACT_PROGRESS_AUDIT.md)
was executed next. It retained 104 SSP rows: 17 are presence-reconciled, 80
need more information, 5 have no source data, and 2 are not applicable. No row
is explicitly marked complete, the loaded 608 rows still differ from the
spreadsheet screenshot's 609, and no global completion claim is allowed. It
selected `system-security-plan.metadata.last-modified` as the next
implementation-ready path because its Transform handler is missing.

## Immediate next action

In the same live Snowflake session, run the aggregate-only
[metadata last-modified readiness audit](notebooks/validation/RUN_AFTER_07_ssp_metadata_last_modified_audit.py)
in one new Python cell. The two spreadsheet rows for this singleton target
currently pass raw values through Cell 4, and mapping order can silently decide
which value remains. The diagnostic reports candidate population, overlap,
timestamp/timezone quality, normalized equality/conflicts, and the current
generated winner without printing timestamps, payloads, or record IDs.

Do not rerun Mapper Cells 1-7 solely for this diagnostic. Do not infer source
precedence, select the latest timestamp, or assign a timezone before its
aggregate evidence is reviewed. It performs no writes and does not establish
whole-SSP conformance. Keep `EXECUTE_WRITES = False`.

## Read-only inspection SQL

- [Show full OSCAL paths, DIM payloads, and FACT relationships for one SSP](sql/show_oscal_path_and_payload.sql)
- [Drill into `system-characteristics` and all descendant payloads](sql/drill_down_system_characteristics.sql)

- [Inspect security-impact-level and extract confidentiality, integrity, and availability](sql/drill_down_security_impact_level.sql)
