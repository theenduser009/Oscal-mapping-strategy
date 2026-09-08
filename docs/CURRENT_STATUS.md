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

## Semantic failure diagnostic summary

### Security impact

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

Candidate profile showed only zero- or one-populated-candidate buckets for each objective; no multi-populated candidate collisions were displayed.

### Status

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

### Document IDs

```text
identifier-type:number = 2813
payload-keys:identifier = 2813
single-scalar-identifier-candidate = 2813
```

### Properties

```text
invalid = 272
nodes = 12307
valid = 12035
source=HELPER_PTA_CALC | reason=non-string-value | type=number | count=272
```

### Components

```text
no-known-raw-reference-key = 352
nodes = 4804
raw-reference-at-any-depth = 4452
keys=ContentId,LevelId | count=4452
keys=interconnections-connecting-information-system | count=352
```

## LATEST SSP READ-ONLY CONTROLLED-VOCABULARY CROSSWALK REVIEW

The controlled-vocabulary review completed safely. It displayed only lookup metadata labels and aggregate counts, with no source/Archer IDs or complete payloads.

```text
SSP READ-ONLY CONTROLLED-VOCABULARY CROSSWALK REVIEW
security-impact nodes = 2813
status nodes = 2813
```

### security-objective-confidentiality

```text
<missing> = 2454
Legacy LOE C = 148
Legacy LOE C + DFARS = 115
Low = 36
Legacy LOE D + DFARS = 30
Legacy LOE A = 13
Legacy LOE D = 12
Legacy LOE B = 5
```

### security-objective-integrity

```text
<missing> = 2542
Legacy LOE C + DFARS = 98
Legacy LOE C = 80
Low = 37
Legacy LOE D + DFARS = 30
Legacy LOE D = 12
Legacy LOE A = 9
Legacy LOE B = 5
```

### security-objective-availability

```text
<missing> = 2542
Legacy LOE C + DFARS = 98
Legacy LOE C = 80
Low = 37
Legacy LOE D + DFARS = 30
Legacy LOE D = 12
Legacy LOE A = 9
Legacy LOE B = 5
```

### status.state

```text
Decommissioned = 1104
Operational = 1060
Under Development = 550
Reauthorize = 57
<missing> = 42
```

### Safety result

```text
READ-ONLY CROSSWALK REVIEW COMPLETE
EXECUTE_WRITES = False
No source/Archer IDs or complete payloads were displayed.
No DIM/FACT writes or permanent objects were created.
```

## Interpretation / controlled next step

This latest review provides the exact label populations needed for an approved crosswalk decision.

- Security impact: `Low` is already OSCAL-compatible and occurs 36/37/37 times across confidentiality/integrity/availability. The remaining populated labels are legacy Archer LOE labels (`Legacy LOE A/B/C/D`, with some `+ DFARS`) and require an architect/business-approved mapping to OSCAL `low|moderate|high`. Do not infer those mappings automatically.
- Status: `Operational`, `Under Development`, `Decommissioned`, and `Reauthorize` are the only populated labels observed, plus 42 missing. Before changing production logic, approve an explicit OSCAL status crosswalk. The previous diagnostic bucketed 1,610 values as already allowed, 1,104 as candidate disposition, and 57 as needing approved crosswalk; the explicit labels now show exactly which populations those buckets represent.
- Document ID shaping remains deterministic: convert the existing numeric `identifier` to the required OSCAL string representation.
- `HELPER_PTA_CALC` remains the only invalid property profile and should be treated as a transient/helper field rather than broadly stringifying values.
- Component hydration remains Phase 2 and should stay out of the Phase 1 semantic revision.

Do **not** enable `EXECUTE_WRITES` yet.

The next production change should be one controlled Cell 3/Cell 4 semantic revision only after the security-impact and status crosswalks are approved. Then rerun the existing read-only graph, scope, payload-semantics, semantic-failure, and crosswalk validators before considering writes.

## Handoff to Codex

Codex/Desktop should pull this file first and treat this controlled-vocabulary review as the latest verified Snowflake evidence. Continue from crosswalk approval and controlled semantic correction; do not reopen graph, duplicate-source, or edge-linkage investigations unless a regression appears. Keep `EXECUTE_WRITES = False`.

## Reviewed semantic code revision committed

The authoritative notebook, split Cell 4, payload-semantics validator, and
crosswalk review are now synchronized with the reviewed runtime labels.

Implemented:

- Security objectives are routed by stable owner path and target field.
  `Low` normalizes to `low`; reviewed legacy LOE labels remain strings and
  are not falsely reclassified as Low/Moderate/High.
- Status uses the explicit crosswalk:
  `Operational -> operational`,
  `Under Development -> under-development`,
  `Decommissioned -> disposition`, and
  `Reauthorize -> other` with an explanatory remark.
- Scalar document identifiers are converted to strings.
- `HELPER_PTA_CALC` is excluded as a transient helper.
- Unknown or multi-valued security/status labels fail closed.
- Component hydration remains unchanged in Phase 2.
- `EXECUTE_WRITES = False` remains unchanged.

Local verification passed Python compilation, focused transformation tests for
all observed labels, document conversion, helper exclusion, and a mock
payload-validator test.

### Exact next Snowflake action

In the current notebook session:

1. Replace Cell 4 with
   `notebooks/cells/04_parsing_transform_payload_helpers.py`.
2. Rerun Cells 4, 5, 6, and 7 in order. Cell 3 does not need replacement or
   rerunning because the diagnostic proved its `identifier` target is already
   correct.
3. Rerun `RUN_AFTER_07_ssp_scope_validation.py`.
4. Rerun the updated
   `RUN_AFTER_07_ssp_payload_semantics_validation.py`.
5. Post both complete outputs here.

Expected structural delta: excluding the 272 helper props should reduce nodes
from 51,772 to approximately 51,500 and edges from 48,959 to approximately
48,687 while preserving the forest invariant. Treat these as expectations, not
hard-coded pass criteria.

Do not enable writes.
