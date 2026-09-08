# Current Status

Last reconciled: 2026-09-08

## Verified notebook

- Current notebook: `NB_ARCHER_OSCAL_MAPPER_V1` / live Snowflake copy shown as `NB_ARCHER_OSCAL_MAPPER_V2` during the latest validation run.
- Generic architecture remains: configuration, inputs, canonical mapping, helpers/transforms, graph builder, guarded loader, orchestrator.
- Keep `EXECUTE_WRITES = False` while validating.

## Restored generic capabilities

The consolidated mapper includes:

- Registry-first hierarchy construction.
- Deterministic node, UUID, and edge identity.
- One canonical mapping contract.
- Archer select-value lookup.
- FIPS 199 Low/Moderate/High normalization.
- Approved responsible-party role transformations.
- Generic Direct/Transform/Extension dispatch.
- Fail-closed source-record selection for duplicate source IDs.
- Mapping coverage output for sprint reporting.
- Graph validation, pre-write validation, idempotent DIM/FACT merge, and post-load verification.

## Duplicate-source investigation

A prior run had:

- Source rows: 5,626
- Distinct `SOURCE_RECORD_ID`: 2,813
- Duplicate graph keys were produced and Cell 6 correctly blocked writes.

Do not blindly add `.distinct()` or `drop_duplicates()` to hide this. If duplicate source rows reappear, resolve them using a deterministic technical version/load ordering rule.

## Resolved parent-cardinality issue

A prior run failed with:

```text
ValueError: Ambiguous collection parent for
system-security-plan.system-characteristics.authorization-boundary
instance singleton
```

Cause identified: cardinality leaked from mapping type into graph structure. Extension mappings must not create collection cardinality unless the owning registry path is actually a collection such as `props[]`. Registry remains authoritative.

## Latest successful read-only graph checkpoint

```text
OSCAL MAPPING RUN
Model: SSP
Run ID: 20260908T185543Z

Graph nodes: 51772
Graph edges: 48959
Duplicate node keys: 0
Duplicate edge keys: 0
Dangling source edges: 0
Dangling target edges: 0
PRE-WRITE VALIDATION PASSED
EXECUTE_WRITES = False; no DIM/FACT changes were made

OSCAL MAPPING RUN COMPLETE
Nodes: 51772
Edges: 48959
Writes: False
```

## Latest SSP read-only scope validation

```text
Nodes: 51772
Edges: 48959
Source records: 2813
SSP roots: 2813
Expected tree edges: 48959
PASS - Cell 7 graph validation passed
PASS - Cell 7 pre-write validation passed
PASS - Writes were not executed
PASS - Graph contains nodes
PASS - Graph contains source records
PASS - Exactly one SSP root per source record
PASS - Tree edge count reconciles
```

The reconciliation is exact:

```text
51,772 nodes - 2,813 SSP roots = 48,959 expected tree edges
Observed edges = 48,959
```

Registry/mapping scope from that run:

```text
Active registry paths: 17
Mapped registry owner paths: 10
Structural paths without owned field mappings: 7
```

Generated node counts by element type:

```text
authorization-boundary  2813
components              4804
document-ids            2813
metadata                2813
props                   12307
responsible-parties     9344
security-impact-level   2813
status                  2813
system-characteristics  2813
system-ids              2813
system-implementation   2813
system-security-plan    2813
```

Payload presence:

```text
Non-empty payload nodes: 43399
Structural/empty payload nodes: 8373
```

Field-level mapping coverage:

```text
Canonical mapping rows: 54
Mappings with source data: 38
Mappings without source data: 16
Mappings with source data percent: 70.37
```

## LATEST SSP READ-ONLY PAYLOAD SEMANTICS VALIDATION

Latest screenshot shows the semantic validator completed and produced the following aggregate results.

```text
SSP READ-ONLY PAYLOAD SEMANTICS VALIDATION

Security-impact nodes: 2813
  Empty/no source values: 2453
  Semantically valid populated nodes: 0
  Semantically invalid populated nodes: 360
  Incomplete objective nodes: 90
  Unrecognized value occurrences: 901

Status nodes: 2813
  Semantically valid: 0
  Semantically invalid: 2813

Property nodes: 12307
  Valid OSCAL name/value shape: 12035
  Invalid OSCAL name/value shape: 272

Responsible-party nodes: 9344
  Valid role/UUID shape: 9344
  Invalid role/UUID shape: 0

Document-ID nodes: 2813
  Valid identifier shape: 0
  Invalid identifier shape: 2813

Component-reference nodes: 4804
  Raw Archer reference payloads: 4452
  Non-raw payloads: 352
```

Readiness result from the validator:

```text
PHASE 1 REVIEW REQUIRED
- security-impact normalization: 360 invalid populated nodes
- status normalization: 2813 invalid populated nodes
- property shaping: 272 invalid populated nodes
- document-ID shaping: 2813 invalid populated nodes

PHASE 2 COMPONENT HYDRATION REMAINS: 4452 raw reference payloads
NEXT ENGINEERING FOCUS: security-impact normalization
```

## Interpretation

This is the authoritative latest checkpoint.

- Graph integrity remains clean and writes remain disabled.
- Structural graph correctness is no longer the blocker.
- The remaining work is semantic payload shaping/normalization.
- Responsible-party shaping is currently clean: 9,344 / 9,344 valid.
- Property shaping is mostly correct but has 272 invalid nodes that need inspection.
- Security-impact is the first priority because all 360 populated nodes fail semantic validation, with 90 incomplete-objective nodes and 901 unrecognized value occurrences.
- Status shaping is also fully invalid in current output and needs normalization review.
- Document IDs are present structurally but all 2,813 fail the expected identifier shape.
- Component references are still largely raw Archer references: 4,452 of 4,804 require later hydration/resolution.

## Immediate engineering focus

Do not enable `EXECUTE_WRITES` yet.

Next read-only work should focus on **security-impact normalization** first, using the existing Archer value lookup/FIPS-199 logic rather than changing graph structure or identity. After that, address status normalization, the 272 malformed property payloads, and document-ID shaping. Component hydration remains Phase 2.

## Handoff to Codex

Codex/Desktop should pull this file first and treat the payload-semantics output above as the latest verified Snowflake runtime evidence. Continue from semantic normalization; do not reopen duplicate-source, graph-cardinality, or edge-linkage investigations unless a regression appears.

## Error/checkpoint handoff convention

When a new Snowflake result or error is reported from the phone, update this `docs/CURRENT_STATUS.md` file with the exact observed counts/error and enough context for Codex to continue from desktop without requiring screenshots to be re-sent.

## Codex analysis of payload-semantics results

The semantic-validator parser is working correctly. The successful 12,035
property rows and all 9,344 responsible-party rows rule out a general
`METADATA_JSON` parsing or Snowpark Row-access problem.

Current evidence indicates:

- Security-impact object keys are correct, but the payload contains
  non-standard/legacy Archer labels. Those labels must be classified separately
  from truly unresolved IDs. More than one source mapping can also converge on
  the same security objective, so candidate collisions must be measured before
  choosing a precedence rule.
- Status currently reaches `state` without a dedicated approved OSCAL
  normalization. The next diagnostic will classify the resolved status into
  safe crosswalk buckets without printing the value.
- The document-ID owner collection can fall back to a source-derived
  `tracking-id` key when the canonical target field is blank; the required
  `identifier` target must be confirmed and then made explicit in the
  canonical mapping contract.
- The 272 invalid properties are a narrow value-type/shape gap. Raw objects or
  arrays must not be blindly JSON-stringified to make validation pass.
- Responsible-party shape is currently clean.
- Component-reference hydration remains Phase 2 and must not be mixed into the
  Phase 1 semantic corrections.

The exact next step is the read-only
`notebooks/validation/RUN_AFTER_07_ssp_semantic_failure_diagnostic.py`
cell. It prints mapping dispatch, aggregate type/key profiles, security
candidate-collision counts, and safe classification buckets. It prints no
source record IDs or payload values and performs no writes.

Run it in the existing successful Cell 7 session with
`EXECUTE_WRITES = False`, then add its complete output below this checkpoint.
Do not modify the production mapper until this diagnostic is reviewed, so the
status, document-ID, property, and security changes can be made together in one
controlled Cell 3/Cell 4 revision.
