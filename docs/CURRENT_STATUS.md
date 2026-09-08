# Current Status

Last reconciled: 2026-09-08

## Verified notebook

- Current notebook: `NB_ARCHER_OSCAL_MAPPER_V1` / live Snowflake copy shown as `NB_ARCHER_OSCAL_MAPPER_V2` during the latest validation run.
- Generic architecture remains: configuration, inputs, canonical mapping, helpers/transforms, graph builder, guarded loader, orchestrator.
- Keep `EXECUTE_WRITES = False` while validating.

## Latest successful read-only graph checkpoint

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

Source records / SSP roots: 2813 / 2813. Tree reconciliation is exact: 51,772 - 2,813 = 48,959 edges.

## Latest scope validation

- Active registry paths: 17
- Mapped registry owner paths: 10
- Structural paths without owned mappings: 7
- Canonical mapping rows: 54
- Mappings with source data: 38
- Mappings without source data: 16
- Mapping-row source-data coverage: 70.37%

Generated nodes include: authorization-boundary 2813, components 4804, document-ids 2813, metadata 2813, props 12307, responsible-parties 9344, security-impact-level 2813, status 2813, system-characteristics 2813, system-ids 2813, system-implementation 2813, system-security-plan 2813.

## Payload semantics checkpoint

- Security-impact: 2813 nodes; 2453 empty; 360 populated invalid; 0 populated valid; 90 incomplete objective nodes; 901 unrecognized value occurrences.
- Status: 2813 invalid / 0 valid.
- Properties: 12035 valid / 272 invalid.
- Responsible parties: 9344 valid / 0 invalid.
- Document IDs: 2813 invalid / 0 valid.
- Components: 4452 raw Archer reference payloads; 352 non-raw.

## LATEST SSP READ-ONLY SEMANTIC FAILURE DIAGNOSTIC

The follow-up diagnostic completed safely. It displayed no source record IDs or payload values and performed no writes.

### Relevant mapping dispatch

Important dispatch observations from the runtime output:

```text
metadata.document-ids[] | source=TRACKING_ID | target=identifier | dispatch=direct-pass-through

system-characteristics.props[] | source=CRITICAL_INFRASTRUCTURE | dispatch=archer-select-lookup
system-characteristics.props[] | source=DAILY_LOSS_AMOUNT_FROM_OUTAGE | dispatch=skip-unapproved
system-characteristics.props[] | source=FINANCIAL_SYSTEM | dispatch=archer-select-lookup
system-characteristics.props[] | source=FISMA_REPORTABLE | dispatch=archer-select-lookup
system-characteristics.props[] | source=HELPER_PTA_CALC | dispatch=direct-pass-through
system-characteristics.props[] | source=INFORMATION_CLASSIFICATION | dispatch=archer-select-lookup
system-characteristics.props[] | source=MISSION_CRITICAL | dispatch=archer-select-lookup
system-characteristics.props[] | source=PACKAGE_TYPE | dispatch=archer-select-lookup
system-characteristics.props[] | source=PACKAGE_TYPE_HELPER_CALC | dispatch=skip-transient
system-characteristics.props[] | source=PIA_REQUIRED | dispatch=archer-select-lookup

security-impact-level | source=RECOMMENDED_SECURITY_CATEGORY | dispatch=archer-select-lookup
status | source=AUTHORIZATION_COMMENTS | target=remarks | dispatch=archer-select-lookup
status | source=AUTHORIZATION_DECISION | target=state | dispatch=skip-unapproved
status | source=OPERATIONAL_STATUS | target=state | dispatch=direct-pass-through

components[] | sources include HARDWARE, INTERCONNECTIONS,
INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM,
SAP_INTAKE_FORM_INTERCONNECTIONS, SOFTWARE, SUBSYSTEMS
```

### Security impact diagnostic

```text
classification:lookup-resolves-to-standard = 110
classification:recognized-archer-nonstandard-label = 791
missing-objective-fields = 7538
nodes = 2813
not-resolvable-by-current-fips-helper = 791
objective-value-type:object = 901
resolvable-by-current-fips-helper = 110
resolved-standard-value:low = 110
```

Security-objective candidate collision profile:

```text
security-objective-availability:one-populated-candidate = 271
security-objective-availability:zero-populated-candidates = 2542
security-objective-confidentiality:one-populated-candidate = 359
security-objective-confidentiality:zero-populated-candidates = 2454
security-objective-integrity:one-populated-candidate = 271
security-objective-integrity:zero-populated-candidates = 2542
```

Key conclusion: there were no displayed multi-populated-candidate collision buckets. The 901 objective occurrences split into 110 values resolvable to standard `low` by the current FIPS helper and 791 recognized Archer non-standard labels that are not currently resolvable by that helper. Security-impact normalization should therefore classify/approve those Archer labels rather than alter graph identity or hierarchy.

### Status diagnostic

```text
crosswalk-bucket:already-allowed = 1610
crosswalk-bucket:candidate-disposition = 1104
crosswalk-bucket:needs-approved-crosswalk = 57
empty-after-select-lookup = 42
lookup-result-type:string = 2771
nodes = 2813
state-type:null = 42
state-type:object = 2771
```

Key conclusion: the source lookup produces strings, but current generated `state` is an object for 2771 nodes and null for 42. The 2771 populated values are classified into 1610 already-allowed, 1104 candidate-disposition, and 57 requiring an approved crosswalk. Do not invent a crosswalk for the 57.

### Document-ID diagnostic

```text
extracted-type:number = 2813
identifier-type:number = 2813
nodes = 2813
payload-keys:identifier = 2813
single-scalar-identifier-candidate = 2813
```

Key conclusion: the correct `identifier` key is present on all 2813 document-ID nodes. The semantic failure is type shaping: the identifier is numeric and must be shaped to the OSCAL-required representation rather than changing collection ownership.

### Property diagnostic

```text
invalid = 272
nodes = 12307
valid = 12035
```

The invalid profile is completely concentrated in one source:

```text
source=HELPER_PTA_CALC | reason=non-string-value | type=number | object_keys=<not-object> | count=272
```

Key conclusion: the property problem is narrow and deterministic. Do not broadly stringify all property objects/arrays; review the approved handling for `HELPER_PTA_CALC` specifically.

### Component-reference diagnostic

```text
no-known-raw-reference-key = 352
nodes = 4804
raw-reference-at-any-depth = 4452
```

Component key profiles:

```text
keys=ContentId,LevelId | count=4452
keys=interconnections-connecting-information-system | count=352
```

Key conclusion: 4452 component nodes remain raw Archer references and belong to Phase 2 hydration. The remaining 352 have a distinct non-raw key profile. Do not mix component hydration into the Phase 1 semantic correction.

### Safety result

```text
READ-ONLY DIAGNOSTIC COMPLETE
EXECUTE_WRITES = False
No DIM/FACT writes or permanent objects were created.
```

## Current interpretation / controlled next step

Graph structure and deterministic identity remain validated. The diagnostic has now isolated the Phase 1 semantic failures enough to prepare a controlled mapper revision:

1. Security impact: add only approved normalization for the recognized Archer non-standard labels; current helper already resolves 110 occurrences to `low`. No candidate collisions were shown.
2. Status: preserve the measured buckets; normalize only values with an approved mapping and leave the 57 unapproved cases fail-closed.
3. Document IDs: shape the existing numeric `identifier` to the required OSCAL identifier representation.
4. Properties: handle the 272 `HELPER_PTA_CALC` numeric values explicitly according to approved property semantics; do not blanket-stringify arbitrary payloads.
5. Components: leave the 4452 raw references for Phase 2 hydration.

Do **not** enable `EXECUTE_WRITES` yet. Production mapper changes should be reviewed as one controlled Cell 3/Cell 4 semantic revision, followed by the same read-only graph, scope, and semantic validators before any write-enabled run.

## Handoff to Codex

Codex/Desktop should pull this file first. Treat the semantic failure diagnostic above as the latest verified Snowflake runtime evidence. Continue from the Phase 1 semantic correction plan; do not reopen duplicate-source, graph-cardinality, or edge-linkage investigations unless a regression appears. Keep `EXECUTE_WRITES = False`.

## Next checkpoint: controlled-vocabulary labels

The semantic failure diagnostic has been reviewed. It is sufficient to define
the deterministic document-ID and helper-property corrections, but it
deliberately did not display the controlled-vocabulary labels needed to approve
security-impact and status mappings.

Run
`notebooks/validation/RUN_AFTER_07_ssp_crosswalk_review.py`
in the existing successful Cell 7 session. This read-only cell displays only
Archer lookup metadata labels and aggregate occurrence counts for the three
security objectives and `status.state`. It does not display Archer IDs, source
record IDs, or complete payloads and performs no writes.

After that output is reviewed, make one synchronized production revision to
the authoritative notebook and affected split cells:

- convert the document `identifier` to its OSCAL string representation;
- exclude `HELPER_PTA_CALC` as a transient helper rather than emitting it as
  an OSCAL property;
- route security objectives through a stable target-path transform and apply
  only an approved label crosswalk;
- resolve and normalize `status.state` using an approved explicit crosswalk,
  leaving unknown values fail-closed;
- keep component hydration in Phase 2.

Keep `EXECUTE_WRITES = False`.
