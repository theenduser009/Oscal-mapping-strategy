# OSCAL Mapping Strategy

This repository is the durable checkpoint for the metadata-driven Archer-to-OSCAL mapper.

## Authoritative files

- [`notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`](notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py) — the complete seven-cell Snowflake/Snowpark notebook source.
- [`notebooks/setup/SETUP_SSP_METADATA_ROLE_PARTY_REGISTRY.py`](notebooks/setup/SETUP_SSP_METADATA_ROLE_PARTY_REGISTRY.py) — the guarded, insert-only setup cell for the governed metadata role and party registry paths.
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

The latest accepted read-only Snowflake run passed graph and pre-write
validation with 67,671 nodes, 64,858 edges, zero duplicate or dangling keys,
and no writes. This is the component identity/type release; its exact
12-node/12-edge reduction matches the proved cross-field deduplication.

The earlier 67,683-node / 64,870-edge graph was confirmed after the
system-characteristics collection-contract release. That release remains
accepted; no further metadata or system-characteristics rerun is pending.
Work now moves to the next evidence-backed downstream SSP branch, with writes
still disabled.

The component source contract is now captured: all 4,804 populated references
use either `ContentId,LevelId` objects or scalar content IDs. The mapper now
uses the registry-governed content ID as component identity, emits the declared
component type and deterministic UUID, and rejects cross-type identity
conflicts. Title, description, and status remain blocked on a referenced-record
lookup source and are not defaulted.

The earlier 2,585 aggregate was corrected: under pinned OSCAL SSP 1.2.3,
2,453 no-objective security-impact assemblies are optional absences. Cell 4
now also omits the 90 partial assemblies, while retaining complete C-I-A
assemblies; Cell 5 no longer recreates omitted security-impact data as empty
structural nodes. The live read-only rerun passed and the graph decreased by
exactly those 2,543 nodes and edges. The 42 missing required `status.state`
values remain a source-data gap.

The complete Excel-first
[mapping-artifact progress audit](docs/checkpoints/2026-09-09_SSP_MAPPING_ARTIFACT_PROGRESS_AUDIT.md)
was executed next. It retained 104 SSP rows: 17 are presence-reconciled, 80
need more information, 5 have no source data, and 2 are not applicable. No row
is explicitly marked complete, the loaded 608 rows still differ from the
spreadsheet screenshot's 609, and no global completion claim is allowed. It
selected `system-security-plan.metadata.last-modified` as the next
implementation-ready path because its Transform handler is missing.

The subsequent metadata audit found that the package-prefixed candidate is
empty and `LAST_UPDATED` supplies all 2,813 current values. Those timestamps
are parseable but timezone-naive. The user chose to preserve them unchanged
for now, so timestamp normalization remains a final conformance gap. Cell 5
now safely injects the already-pinned OSCAL version into every singleton
metadata payload; a live Snowflake rerun is now complete. The rerun retained
the healthy 51,500-node / 48,687-edge graph,
passed all structural and pre-write gates, and made no writes. A direct
aggregate payload check was then run and recorded `PASSED` for all 2,813
metadata nodes, with every failure count at zero and no writes.
The direct `TRACKING_ID` document-ID mapping is also now closed: all 2,813
generated identifiers exactly match their transformed source values with zero
failures and no writes.

Cell 4 now contains production timestamp resolution for the Excel-defined
`metadata.published` and `metadata.last-modified` source clusters. It preserves
the selected source string exactly, accepts a single populated value or
identical populated values, and fails closed when populated sources disagree.
It does not infer or attach a timezone.

The same release makes the optional `security-impact-level` branch atomic:
only payloads containing all three confidentiality, integrity, and
availability objectives are emitted. Missing values are never invented.

## Immediate next action

The component identity/type release and broad lookup discovery are accepted.
The discovery found all 1,436 governed IDs with zero profiling failures and no
writes. The three generic metadata layers contain identity only; two RAW
objects contain hydration evidence, while hardware source,
interconnection completeness/status, and software field choices remain open.

Run only the new read-only
[Excel-driven component source-routing audit](notebooks/validation/RUN_AFTER_07_ssp_component_source_routing_audit.py)
in the same still-open notebook session; do not rerun Cells 1 through 7 or the
broad discovery. It reconciles the exact six approved Excel component mappings
to the two evidence-backed RAW objects, reports only aggregate coverage, and
cannot approve or configure a lookup source or transformation. Post its full
output for the hydration contract. All 133 repository tests pass.

## Read-only inspection SQL

- [Show full OSCAL paths, DIM payloads, and FACT relationships for one SSP](sql/show_oscal_path_and_payload.sql)
- [Drill into `system-characteristics` and all descendant payloads](sql/drill_down_system_characteristics.sql)

- [Inspect security-impact-level and extract confidentiality, integrity, and availability](sql/drill_down_security_impact_level.sql)

