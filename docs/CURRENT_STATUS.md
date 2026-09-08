# Current Status

Last reconciled: 2026-09-08

## Verified notebook

- Current live Snowflake notebook: `NB_ARCHER_OSCAL_MAPPER_V2`.
- Generic architecture remains: configuration, inputs, canonical mapping, helpers/transforms, graph builder, guarded loader, orchestrator.
- Keep `EXECUTE_WRITES = False` while validating.
- Repository conformance target: NIST OSCAL SSP `1.2.3`, pinned in authoritative Cell 1.

## Latest verified mapper rerun

Latest screenshot-confirmed read-only mapper run after the 1.2.3 pin:

```text
OSCAL MAPPING RUN
Model: SSP
Run ID: 20260908T220830Z

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

The graph remains structurally clean and unchanged from the prior post-normalization checkpoint.

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

## Payload semantics validation

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

## Latest pinned OSCAL SSP 1.2.3 security/status cardinality review

Screenshot-confirmed header:

```text
READ-ONLY OSCAL SSP SECURITY/STATUS CARDINALITY REVIEW
Provisional evaluation target: OSCAL SSP 1.2.3
CONFIG-pinned OSCAL version: 1.2.3
```

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
Confidentiality with no populated source candidate: 1
Confidentiality with source candidate but no generated value: 0

Integrity missing child occurrences in partial assemblies: 89
Integrity with no populated source candidate: 89
Integrity with source candidate but no generated value: 0

Availability missing child occurrences in partial assemblies: 89
Availability with no populated source candidate: 89
Availability with source candidate but no generated value: 0

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
Records with a security source/output discrepancy: 0
Records with a status source/output discrepancy: 0
Unique records requiring review in this narrow check: 131
Records ready within only this narrow check: 2682
Records with source parse/resolution errors: 0
```

The source/output reconciliation is especially important: every missing C/I/A child in the partial assemblies corresponds to no populated source candidate; there are zero cases where a populated source candidate disappeared during generation. The current blocker population is therefore source completeness/cardinality, not an observed mapper-loss defect in this narrow check.

### Optional-omission projection only

```text
Current graph nodes: 51500
Current graph edges: 48687
No-objective security nodes eligible for final-output omission: 2453
Actual incoming edges to those nodes: 2453
Projected nodes if graph policy also omits them: 49047
Projected edges if graph policy also omits them: 46234
```

The mapper still materializes structural `{}` nodes. This is only a projection and is not a requested graph change.

### Safety result

```text
EXECUTE_WRITES = False
No DIM/FACT writes or permanent objects were created.
RESULT: REVIEW REQUIRED; WRITES REMAIN BLOCKED
```

## Current interpretation

- OSCAL SSP 1.2.3 is now explicitly pinned in `CONFIG` and confirmed by the live diagnostic.
- Graph integrity remains clean: zero duplicate keys and zero dangling edges.
- Source-to-graph record coverage is exact for all 2,813 records.
- Security/status source values reconcile exactly with generated payload presence.
- 2,453 empty security-impact assemblies are optional under OSCAL SSP 1.2.3 and are not required-field gaps.
- 90 partial security-impact assemblies remain blockers if emitted; they are missing 179 required C/I/A child occurrences.
- The diagnostic shows those 179 missing child occurrences have no populated source candidates; zero populated source candidates were lost by generation.
- 42 records are missing required `status.state`.
- One record belongs to both blocker groups, yielding 131 unique records requiring review.
- 2,682 records pass this narrow security/status check.
- Component hydration remains incomplete: 4,452 raw Archer component-reference payloads remain.
- The current 17-path registry/mapping subset is not yet a complete OSCAL SSP.
- This narrow check does not prove whole-document SSP conformance or write readiness.
- Writes remain blocked.

## Immediate next action

The next Snowflake cell already visible in the notebook is the read-only OSCAL SSP 1.2.3 minimum-required-scope audit. Run that audit next and capture its complete aggregate output. It will establish the version-specific backlog for missing required SSP branches/fields beyond this narrow security/status review.

Do not enable writes and do not change graph policy yet.
