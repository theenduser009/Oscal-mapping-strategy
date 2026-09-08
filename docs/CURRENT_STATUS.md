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

## LATEST SSP READ-ONLY SCOPE VALIDATION

Latest screenshots show the separate read-only scope validation cell completed successfully.

### Forest / graph reconciliation

```text
SSP READ-ONLY SCOPE VALIDATION
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

### Registry and mapping scope

```text
Active registry paths: 17
Mapped registry owner paths: 10
Structural paths without owned field mappings: 7
```

Structural/unmapped registry paths shown for review:

```text
system-security-plan
system-security-plan.system-implementation
system-security-plan.system-implementation.components[].component
system-security-plan.system-implementation.components[].component.links[]
system-security-plan.system-implementation.components[].component.props[]
system-security-plan.system-implementation.components[].component.protocols[]
system-security-plan.system-implementation.components[].component.responsible-roles[]
```

These are structural paths and are not automatically treated as validation failures.

### Generated node counts by element type

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

### Generated node counts by registry path

```text
system-security-plan                                                        2813
system-security-plan.metadata                                               2813
system-security-plan.metadata.document-ids[]                                2813
system-security-plan.metadata.responsible-parties[]                         9344
system-security-plan.system-characteristics                                 2813
system-security-plan.system-characteristics.authorization-boundary          2813
system-security-plan.system-characteristics.props[]                         12307
system-security-plan.system-characteristics.security-impact-level           2813
system-security-plan.system-characteristics.status                          2813
system-security-plan.system-characteristics.system-ids[]                    2813
system-security-plan.system-implementation                                  2813
system-security-plan.system-implementation.components[]                     4804
```

### Payload presence

```text
Non-empty payload nodes: 43399
Structural/empty payload nodes: 8373
```

Breakdown visible in validation output:

```text
authorization-boundary  populated 2519 / empty 294
components              populated 4804
metadata                populated 2813
props                   populated 12307
responsible-parties     populated 9344
security-impact-level   populated 360 / empty 2453
status                  populated 2813
system-characteristics  populated 2813
system-ids              populated 2813
system-implementation   empty 2813
system-security-plan    empty 2813
```

### Field-level mapping coverage

```text
Canonical mapping rows: 54
Mappings with source data: 38
Mappings without source data: 16
Mappings with source data percent: 70.37
```

Coverage summary shown in the screenshot includes mapping types/statuses such as:

```text
Calculated          In Progress  HAS_SOURCE_DATA=True   2
Direct              In Progress  HAS_SOURCE_DATA=True   7
Direct/Transform    In Progress  HAS_SOURCE_DATA=False  6
Direct/Transform    In Progress  HAS_SOURCE_DATA=True   5
Extension Property  In Progress  HAS_SOURCE_DATA=False  4
Extension Property  In Progress  HAS_SOURCE_DATA=True   6
Reference           In Progress  HAS_SOURCE_DATA=False  2
Reference           In Progress  HAS_SOURCE_DATA=True   4
TBD                 In Progress  HAS_SOURCE_DATA=False  2
TBD                 In Progress  HAS_SOURCE_DATA=True   5
Transform           In Progress  HAS_SOURCE_DATA=False  2
Transform           In Progress  HAS_SOURCE_DATA=True   9
```

### Mappings without source data

The validation output explicitly listed the following no-source-data mappings for review:

```text
ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED
  -> system-security-plan.metadata.last-modified

ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER
  -> system-security-plan.metadata.props[]

ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED
  -> system-security-plan.metadata.published

DAILY_LOSS_AMOUNT_FROM_OUTAGE
  -> system-security-plan.system-characteristics.props[]

FINANCIAL_SYSTEM
  -> system-security-plan.system-characteristics.props[]

FISMA_REPORTABLE
  -> system-security-plan.system-characteristics.props[]

PIA_REQUIRED
  -> system-security-plan.system-characteristics.props[]

RECOMMENDED_SECURITY_CATEGORY
  -> system-security-plan.system-characteristics.security-impact-level

CNSS_AVAILABILITY_RATING
  -> system-security-plan.system-characteristics.security-impact-level.security-objective-availability

RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY
  -> system-security-plan.system-characteristics.security-impact-level.security-objective-availability

CNSS_CONFIDENTIALITY_RATING
  -> system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality

RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY
  -> system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality

CNSS_INTEGRITY_RATING
  -> system-security-plan.system-characteristics.security-impact-level.security-objective-integrity

RECOMMENDED_INTEGRITY_CONTROL_CATEGORY
  -> system-security-plan.system-characteristics.security-impact-level.security-objective-integrity

SAP_INTAKE_FORM_INTERCONNECTIONS
  -> system-security-plan.system-implementation.components[]

SUBSYSTEMS
  -> system-security-plan.system-implementation.components[]
```

### Validation conclusion

```text
SSP READ-ONLY SCOPE VALIDATION PASSED
Review the displayed element/path and coverage tables before writes.
```

## Interpretation / next engineering focus

This is now the authoritative current checkpoint.

- Graph integrity is clean.
- Duplicate and dangling-edge problems are not present in this validated run.
- Forest edge reconciliation is exact.
- Exactly one SSP root exists per source record.
- The current generated SSP scope is 51,772 nodes / 48,959 edges from 2,813 source records.
- 54 canonical mappings are in scope; 38 currently have source data and 16 do not (70.37% populated at mapping-row level).
- Structural registry paths without direct owned field mappings are expected and should not be confused with unmapped Archer fields.
- Several security-impact-level mappings are sparse/no-data, which explains the large empty count for that node type.
- Component-related deeper registry paths remain structural/unmapped and need review before declaring full SSP implementation coverage.

## Safety / next-step rule

Do **not** enable `EXECUTE_WRITES` yet solely because this validation passed.

Next: review the 16 no-source-data mappings and the 7 structural registry paths, distinguish true missing implementation from legitimate no-data/structural nodes, and then decide whether the current SSP scope is complete enough for write-enabled validation. Preserve the seven-cell mapper architecture and frozen deterministic identity contract.

## Handoff to Codex

Codex/Desktop should pull this file first and treat this scope-validation output as the latest verified runtime evidence. Continue from these exact counts and mappings; do not reproduce the earlier duplicate-source or ambiguous-parent debugging unless a regression appears.

## Error/checkpoint handoff convention

When a new Snowflake result or error is reported from the phone, update this `docs/CURRENT_STATUS.md` file with the exact observed counts/error and enough context for Codex to continue from desktop without requiring screenshots to be re-sent.
