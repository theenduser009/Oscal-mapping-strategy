# Current Status

Last reconciled: 2026-09-08

## Verified notebook

- Current notebook: `NB_ARCHER_OSCAL_MAPPER_V1` / live Snowflake copy shown as `NB_ARCHER_OSCAL_MAPPER_V2` during the latest validation run.
- Generic architecture remains: configuration, inputs, canonical mapping, helpers/transforms, graph builder, guarded loader, orchestrator.
- Keep `EXECUTE_WRITES = False` while validating.

## Previously validated baseline

Prior clean read-only checkpoint before the semantic revision:

```text
Graph nodes: 51772
Graph edges: 48959
Duplicate node keys: 0
Duplicate edge keys: 0
Dangling source edges: 0
Dangling target edges: 0
PRE-WRITE VALIDATION PASSED
EXECUTE_WRITES = False
```

The semantic review identified four Phase 1 fixes: security-impact normalization, status normalization, document-ID string shaping, and exclusion of transient `HELPER_PTA_CALC`. Component hydration remains Phase 2.

## Controlled-vocabulary review used for the revision

Security-impact labels observed:

- Confidentiality: `<missing>` 2454, Legacy LOE C 148, Legacy LOE C + DFARS 115, Low 36, Legacy LOE D + DFARS 30, Legacy LOE A 13, Legacy LOE D 12, Legacy LOE B 5.
- Integrity: `<missing>` 2542, Legacy LOE C + DFARS 98, Legacy LOE C 80, Low 37, Legacy LOE D + DFARS 30, Legacy LOE D 12, Legacy LOE A 9, Legacy LOE B 5.
- Availability: `<missing>` 2542, Legacy LOE C + DFARS 98, Legacy LOE C 80, Low 37, Legacy LOE D + DFARS 30, Legacy LOE D 12, Legacy LOE A 9, Legacy LOE B 5.

Status labels observed:

```text
Decommissioned = 1104
Operational = 1060
Under Development = 550
Reauthorize = 57
<missing> = 42
```

Reviewed semantic code revision:

- Security objectives route by stable owner path and target field.
- `Low` normalizes to `low`.
- Reviewed legacy LOE labels remain explicit reviewed legacy values and are not falsely classified as Low/Moderate/High.
- Status crosswalk: `Operational -> operational`, `Under Development -> under-development`, `Decommissioned -> disposition`, `Reauthorize -> other` with explanatory remark.
- Scalar document identifiers convert to strings.
- `HELPER_PTA_CALC` is excluded as a transient helper.
- Unknown/multi-valued security/status labels fail closed.
- Component hydration remains Phase 2.

## LATEST VERIFIED POST-REVISION SNOWFLAKE RUN

Run shown in Snowflake after replacing/rerunning the semantic helper cell and rerunning the mapper:

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

This exactly matches the expected structural delta from excluding 272 transient `HELPER_PTA_CALC` property nodes:

```text
51772 - 272 = 51500 nodes
48959 - 272 = 48687 edges
```

## LATEST SSP READ-ONLY SCOPE VALIDATION

```text
Nodes: 51500
Edges: 48687
Source records: 2813
SSP roots: 2813
Expected tree edges: 48687
PASS - Cell 7 graph validation passed
PASS - Cell 7 pre-write validation passed
PASS - Writes were not executed
PASS - Graph contains nodes
PASS - Graph contains source records
PASS - Exactly one SSP root per source record
PASS - Tree edge count reconciles
```

Registry/mapping scope remains:

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
props                   12035
responsible-parties     9344
security-impact-level   2813
status                  2813
system-characteristics  2813
system-ids              2813
system-implementation   2813
system-security-plan    2813
```

Generated node counts by registry path reconcile with those counts, including `system-characteristics.props[] = 12035` and `system-implementation.components[] = 4804`.

Payload presence:

```text
Non-empty payload nodes: 43127
Structural/empty payload nodes: 8373
```

Notable payload-presence breakdown:

```text
authorization-boundary false=2519 true=294
components false=4804
document-ids false=2813
metadata false=2813
props false=12035
responsible-parties false=9344
security-impact-level false=360 true=2453
status false=2813
system-characteristics false=2813
system-ids false=2813
system-implementation true=2813
system-security-plan true=2813
```

Field-level mapping coverage remains:

```text
Canonical mapping rows: 54
Mappings with source data: 38
Mappings without source data: 16
Mappings with source data percent: 70.37
```

The current no-source-data list still includes the visible rows from the previous scope review, including metadata publication timestamps, some props, several security-impact candidates, and component references such as `SAP_INTAKE_FORM_INTERCONNECTIONS` and `SUBSYSTEMS`. This is a source-availability/reporting issue, not a graph-integrity failure.

Scope validation result:

```text
SSP READ-ONLY SCOPE VALIDATION PASSED
Review the displayed element/path and coverage tables before writes.
```

## LATEST SSP READ-ONLY PAYLOAD SEMANTICS VALIDATION

The semantic revision now passes Phase 1 payload shape validation:

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

Readiness result:

```text
PHASE 1 PAYLOAD SHAPES PASSED
REQUIRED-FIELD SOURCE GAPS REMAIN: 2585 aggregate empty/incomplete node observations
PHASE 2 COMPONENT HYDRATION REMAINS: 4452 raw reference payloads
NEXT ENGINEERING FOCUS: required-field source-gap review
```

## Interpretation

This is the authoritative latest checkpoint.

- The controlled semantic revision worked as intended.
- Graph integrity remains clean: zero duplicate node/edge keys and zero dangling edges.
- The 272-node/edge reduction is fully explained by the deliberate exclusion of transient `HELPER_PTA_CALC` props.
- Security-impact populated nodes are now all semantically accepted under the reviewed policy: 110 standard occurrences and 791 reviewed legacy LOE occurrences, with zero unreviewed/invalid occurrences.
- Status is now valid for all 2771 populated states; 42 records are empty/no-source rather than semantically invalid.
- All 12,035 emitted properties now have valid OSCAL name/value shape.
- All 2,813 document IDs now have valid identifier shape.
- All 9,344 responsible-party nodes remain valid.
- Phase 1 payload shape work is therefore complete for the currently populated mapped scope.
- Remaining Phase 1 concern is source completeness: 2,585 aggregate empty/incomplete observations.
- Phase 2 still requires hydration/resolution of 4,452 raw Archer component references.

## Immediate engineering focus

Keep `EXECUTE_WRITES = False`.

The next action is a **read-only required-field source-gap review**. Determine which of the 2,585 empty/incomplete observations are:

1. legitimate optional/missing source values,
2. source fields that are expected but currently unpopulated,
3. mapping candidates with no source data in this dataset,
4. true required-field gaps that should block write readiness.

Do not reopen graph structure, deterministic identity, security/status crosswalk, document-ID shaping, or helper-property handling unless a regression appears. Do not begin component hydration until this Phase 1 source-gap review is complete.

## Handoff to Codex

Codex/Desktop should pull this file first and treat the `20260908T201705Z` run plus the post-revision scope/semantic validators as the latest verified Snowflake evidence.

Continue with a read-only required-field source-gap diagnostic while keeping `EXECUTE_WRITES = False`. The mapper should not be redesigned; the semantic revision is now validated.
