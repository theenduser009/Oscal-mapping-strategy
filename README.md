# OSCAL Mapping Strategy

This repository is the durable checkpoint for the metadata-driven Archer-to-OSCAL mapper.

## Authoritative files

- [`notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`](notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py) — the complete seven-cell Snowflake/Snowpark notebook source.
- [`notebooks/setup/SETUP_SSP_METADATA_ROLE_PARTY_REGISTRY.py`](notebooks/setup/SETUP_SSP_METADATA_ROLE_PARTY_REGISTRY.py) — the guarded, insert-only setup cell for the governed metadata role and party registry paths.
- [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md) — verified state, safety gate, and the single next action.
- [`docs/ARCHITECTURE_CONTEXT.md`](docs/ARCHITECTURE_CONTEXT.md) — design guardrails that must survive future edits.
- [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md) — dated project decisions and GitHub checkpoints.
- [`docs/OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md`](docs/OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md) — pinned version sources and the first-tier required SSP contract.
- [`docs/SSP_MAPPER_BUSINESS_LOGIC_AND_TEST_GUIDE.md`](docs/SSP_MAPPER_BUSINESS_LOGIC_AND_TEST_GUIDE.md) — tester-facing business rules, field-to-node expectations, PK/FK checks, known gaps, and complete acceptance procedure.
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
and no writes. It also confirmed 1,435 approved component hydration rows: 7
software and 1,428 interconnections, with 7 software descriptions and 968
interconnection descriptions. The exact graph stability proves hydration
changed payload content without changing node or edge identity.

The earlier 67,683-node / 64,870-edge graph was confirmed after the
system-characteristics collection-contract release. That release remains
accepted; no further metadata or system-characteristics rerun is pending.
Work now moves to the next evidence-backed downstream SSP branch, with writes
still disabled.

The component source contract is now captured: all 4,804 populated references
use either `ContentId,LevelId` objects or scalar content IDs. The mapper now
uses the registry-governed content ID as component identity, emits the declared
component type and deterministic UUID, and rejects cross-type identity
conflicts. The owner-approved partial hydration release now adds software title
and description plus interconnection title and populated description from the
two proved RAW lookup sources. Status, missing interconnection descriptions,
and hardware hydration remain explicit gaps and are not defaulted.

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

The partial component hydration release is implemented in the authoritative
notebook and synchronized split Cells 2, 4, and 5. It performs bounded,
server-side joins from only the three approved Excel routes, rejects duplicate
or missing lookup rows before graph construction, and collects only the 1,435
currently routed title/description records. It neither prints component values
nor adds a write path. All 156 repository tests pass.

The component hydration run is accepted; do not rerun Cells 1 through 7 or the
component discovery, source-contract extraction, or source-routing audit for
this release. Keep `EXECUTE_WRITES = False` and use the
[tester guide](docs/SSP_MAPPER_BUSINESS_LOGIC_AND_TEST_GUIDE.md) for the formal
mapped-scope acceptance cycle.

## Read-only inspection SQL

- [Show full OSCAL paths, DIM payloads, and FACT relationships for one SSP](sql/show_oscal_path_and_payload.sql)
- [Drill into `system-characteristics` and all descendant payloads](sql/drill_down_system_characteristics.sql)

- [Inspect security-impact-level and extract confidentiality, integrity, and availability](sql/drill_down_security_impact_level.sql)

