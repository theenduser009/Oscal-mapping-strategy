# Current Status

Last reconciled: 2026-09-08

## Verified notebook

- Current notebook: `NB_ARCHER_OSCAL_MAPPER_V1` / live Snowflake copy shown as `NB_ARCHER_OSCAL_MAPPER_V2` during the latest validation run.
- Generic architecture remains: configuration, inputs, canonical mapping, helpers/transforms, graph builder, guarded loader, orchestrator.
- Keep `EXECUTE_WRITES = False` while validating.
- Repository conformance target: NIST OSCAL SSP `1.2.3`, pinned in authoritative Cell 1.

## Latest verified mapper run

```text
OSCAL MAPPING RUN
Model: SSP
Run ID: 20260908T201705Z

Graph nodes: 51500
Graph edges: 48687
Duplicate node keys: 0
Duplicate edge keys: 0
Dangling source edges: 0
Dangling target edges: 0
PRE-WRITE VALIDATION PASSED
EXECUTE_WRITES = False; no DIM/FACT changes were made

OSCAL MAPPING RUN COMPLETE
Nodes: 51500
Edges: 48687
Writes: False
```

The current graph is structurally clean and remains read-only.

## Latest SSP scope validation

```text
Nodes: 51500
Edges: 48687
Source records: 2813
SSP roots: 2813
Expected tree edges: 48687
PASS - Cell 7 graph validation passed
PASS - Cell 7 pre-write validation passed
PASS - Writes were not executed
PASS - Exactly one SSP root per source record
PASS - Tree edge count reconciles
```

Registry/mapping scope:

```text
Active registry paths: 17
Mapped registry owner paths: 10
Structural paths without owned field mappings: 7
Canonical mapping rows: 54
Mappings with source data: 38
Mappings without source data: 16
Mappings with source data percent: 70.37
```

Generated node counts include:

```text
authorization-boundary  2813
components              4804
document-ids            2813
metadata                2813
props                   12035
responsible-parties     9344
security-impact-level   2813
status                  2813
system-characteristics  2813
system-ids              2813
system-implementation   2813
system-security-plan    2813
```

## Payload semantics validation

After the reviewed semantic normalization:

```text
Security-impact nodes: 2813
  Empty/no source values: 2453
  Semantically valid populated nodes: 360
  Semantically invalid populated nodes: 0
  Incomplete objective nodes: 90
  Standard value occurrences: 110
  Reviewed legacy LOE occurrences: 791
  Invalid type/empty occurrences: 0
  Unreviewed label occurrences: 0

Status nodes: 2813
  Semantically valid: 2771
  Semantically invalid: 0
  Empty/no source state: 42

Property nodes: 12035
  Valid OSCAL name/value shape: 12035
  Invalid OSCAL name/value shape: 0

Responsible-party nodes: 9344
  Valid role/UUID shape: 9344
  Invalid role/UUID shape: 0

Document-ID nodes: 2813
  Valid identifier shape: 2813
  Invalid identifier shape: 0

Component-reference nodes: 4804
  Raw Archer reference payloads: 4452
  Non-raw payloads: 352
```

Phase 1 payload shapes pass for populated mapped values. Component hydration remains Phase 2.

## Latest read-only OSCAL SSP security/status cardinality review

Repository contract: OSCAL SSP 1.2.3 is now pinned in Cell 1. The latest verified Snowflake session predates that repository change, so its live `CONFIG` may not display the version; its existing aggregate read-only results remain valid.

### Record and graph reconciliation

```text
Source rows: 2813
Unique source records: 2813
Unique graph records: 2813
Source/graph intersection: 2813
Source-only records: 0
Graph-only records: 0
Blank graph record IDs: 0
Unique security-node records: 2813
Source records without a security node: 0
Orphan security-node records: 0
Duplicate security nodes: 0
Duplicate status nodes: 0
Source JSON parse errors: 0
Source path resolution errors: 0
Security payload parse errors: 0
Status payload parse errors: 0
```

### Security-impact source/output overlap

Configured candidate population reconciles to generated output with no source/output discrepancy:

```text
Confidentiality: source_present=359, generated_present=359, both=359, source_only=0, output_only=0
Integrity:       source_present=271, generated_present=271, both=271, source_only=0, output_only=0
Availability:    source_present=271, generated_present=271, both=271, source_only=0, output_only=0
```

### OSCAL 1.2.3 cardinality classification

```text
Optional absent security-impact assemblies: 2453
Complete security-impact assemblies: 270
Partial security-impact assemblies: 90
Missing security structural nodes: 0
Malformed/invalid security assemblies: 0

Confidentiality missing child occurrences in partial assemblies: 1
Integrity missing child occurrences in partial assemblies: 89
Availability missing child occurrences in partial assemblies: 89
Missing required security-objective occurrences: 179
Invalid security value occurrences: 0

Missing required status.state occurrences: 42
Invalid populated status assemblies: 0
Missing required field occurrences in emitted/required assemblies: 221
```

### Unique-record impact

```text
Records with partial security-impact assembly: 90
Records with missing required status.state: 42
Records in both groups: 1
Records requiring review in this narrow check: 131
Records ready within only this narrow check: 2682
Records with source parse/resolution errors: 0
Records with a security source/output discrepancy: 0
Records with a status source/output discrepancy: 0
```

This is the key correction to the earlier aggregate `2585` source-gap interpretation: the 2,453 completely empty security-impact assemblies are optional absence under the pinned OSCAL 1.2.3 contract, not required-field failures. The actual narrow security/status review population is 131 unique records.

### Optional-omission projection only

The mapper currently materializes structural `{}` security-impact nodes. No graph-policy change has been requested or applied.

If the 2,453 no-objective optional security-impact nodes were also omitted from the graph, the projection would be:

```text
Current graph nodes: 51500
Current graph edges: 48687
No-objective security nodes eligible for final-output omission: 2453
Actual incoming edges to those nodes: 2453
Projected nodes: 49047
Projected edges: 46234
```

This is a projection only, not a production change.

## OSCAL 1.2.3 version pin and next gate

- The user confirmed OSCAL SSP 1.2.3 as the repository target.
- Authoritative Mapper V1 Cell 1 and its split copy now set `OSCAL_VERSION = "1.2.3"`.
- The existing cardinality and payload validators now label 1.2.3 as the pinned contract. They accept an absent version only in an already-running pre-pin session and fail closed on a conflicting version.
- The new [minimum-required-scope audit](../notebooks/validation/RUN_AFTER_07_ssp_v123_minimum_required_scope_audit.py) checks required SSP branches, cardinality, and minimum payload fields using aggregate-only output.
- The exact audit contract and NIST source links are documented in [OSCAL SSP 1.2.3 Minimum Contract](OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md).
- The new audit has passed local syntax and representative in-memory tests but has not yet been run against Snowflake. No new runtime counts are claimed here.

## Current interpretation

- Graph integrity is clean: zero duplicate keys and zero dangling edges.
- Source-to-graph record coverage is exact for all 2,813 records.
- Security/status source values reconcile exactly with generated payload presence; no transformation-loss discrepancy was detected in this check.
- 2,453 empty security-impact assemblies are optional under the pinned OSCAL SSP 1.2.3 contract.
- 90 partial security-impact assemblies remain blockers if emitted because they are missing 179 required C/I/A child occurrences.
- 42 records are missing required `status.state`.
- One record belongs to both blocker groups, producing 131 unique records requiring review.
- 2,682 records pass this narrow security/status cardinality check.
- Component hydration remains incomplete: 4,452 raw Archer component-reference payloads remain.
- The current 17-path registry/mapping subset is not a complete OSCAL SSP.
- This narrow cardinality check does not prove whole-document SSP conformance or write readiness.
- `EXECUTE_WRITES = False`; no DIM/FACT writes or permanent objects were created by these diagnostics.

## Immediate next action

If the Snowflake session that produced run `20260908T201705Z` is still active, run only the read-only [OSCAL 1.2.3 minimum-required-scope audit](../notebooks/validation/RUN_AFTER_07_ssp_v123_minimum_required_scope_audit.py) in a new Python cell. You do not need to rerun Mapper Cells 1-7 solely for this audit; it recognizes a pre-pin live session. If the session was restarted, replace Cell 1 with the pinned copy and run Cells 1-7 first.

Paste the complete aggregate output into this file and report `check status`. The result will become the version-specific mapping backlog for missing required paths and fields. Do not enable writes.
