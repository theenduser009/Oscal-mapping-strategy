# SSP Mapping Progress Checkpoint

## SSP notebook checkpoint — 2026-09-10

Source: screenshots from `NB_ARCHER_OSCAL_MAPPER_V2` shared in ChatGPT for Codex context.

### SSP mapped-scope assembly

```text
=== SSP MAPPED-SCOPE ASSEMBLY ===
Safety: aggregate-only; no identifiers or payloads printed
Documents assembled: 2813
Graph nodes consumed: 70102
Graph edges consumed: 67289
Root nodes consumed: 2813
Writes executed: False
Result: MAPPED-SCOPE ASSEMBLY PASSED
Complete SSP claim: False
OSCAL schema-valid claim: False
```

### Interpretation

- The current mapped SSP scope assembles successfully for all 2,813 source/root records.
- The in-memory graph consumed 70,102 nodes and 67,289 edges.
- No DIM/FACT write should be inferred from this checkpoint; writes were disabled.
- This is **not** yet evidence that the full SSP is complete.
- This is **not** yet evidence that the assembled documents are OSCAL schema-valid.

## Assessment Results mapped-scope checkpoint — 2026-09-11

Source: notebook screenshots from `NB_ARCHER_OSCAL_MAPPER_V2`; this evidence set was re-confirmed from the later screenshot sequence on 2026-09-11.

Mapping release:

```text
ar-observation-scores-v2-17-fields
```

Target OSCAL path:

```text
assessment-results.results[].observations[]
```

Status:

```text
MAPPED_SCOPE_BUILT
```

Selected fields (17):

```text
VULNERABILITY_SCORE
ANTIVIRUS_SCORE
PATCH_SCORE
SECURITY_COMPLIANCE_SCORE
STANDARD_OPERATING_ENVIRONMENT_SCORE
COMPUTER_PASSWORD_AGE_SCORE
VULNERABILITY_REPORTING_SCORE
SECURITY_COMPLIANCE_REPORTING_SCORE
TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE
AVG_AUTHORIZATION_PACKAGE_RISK_SCORE
RISK_SCORE_GRADE
AVG_VULNERABILITY_SCORE
AVG_PATCH_SCORE
AVG_ANTIVIRUS_SCORE
AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE
AVG_COMPUTER_PASSWORD_AGE_SCORE
AVG_VULNERABILITY_REPORTING_SCORE
```

Run evidence:

```text
OTHER_AR_MAPPING_ROWS_NOT_PROCESSED: 28
MAPPING_CONTRACT_ERRORS: []
REGISTRY_CONTRACT_ERRORS: []
SOURCE_RECORDS: 2813
INVALID_SOURCE_RECORDS: 0
DUPLICATE_SOURCE_RECORDS: 0
```

Per-field evidence visible in the screenshots:

```text
VULNERABILITY_SCORE                         emitted=2813 missing=0   invalid=0
ANTIVIRUS_SCORE                             emitted=2813 missing=0   invalid=0
PATCH_SCORE                                 emitted=2813 missing=0   invalid=0
SECURITY_COMPLIANCE_SCORE                   emitted=2813 missing=0   invalid=0
STANDARD_OPERATING_ENVIRONMENT_SCORE        emitted=2813 missing=0   invalid=0
COMPUTER_PASSWORD_AGE_SCORE                 emitted=2813 missing=0   invalid=0
VULNERABILITY_REPORTING_SCORE               emitted=2813 missing=0   invalid=0
SECURITY_COMPLIANCE_REPORTING_SCORE         emitted=2813 missing=0   invalid=0
TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE      emitted=2813 missing=0   invalid=0
AVG_AUTHORIZATION_PACKAGE_RISK_SCORE        emitted=2813 missing=0   invalid=0
RISK_SCORE_GRADE                            emitted=2546 missing=267 invalid=0
AVG_VULNERABILITY_SCORE                     emitted=2800 missing=13  invalid=0
AVG_PATCH_SCORE                             emitted=2812 missing=1   invalid=0
AVG_ANTIVIRUS_SCORE                         emitted=2800 missing=13  invalid=0
AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE    emitted=2272 missing=541 invalid=0
AVG_COMPUTER_PASSWORD_AGE_SCORE             emitted=2800 missing=13  invalid=0
AVG_VULNERABILITY_REPORTING_SCORE           emitted=2800 missing=13  invalid=0
```

Graph/output evidence:

```text
WRITES_EXECUTED: false
FULL_MODEL_COMPLETE: false
SCHEMA_VALIDATED: false
CANDIDATE_NODES: 52586
CANDIDATE_EDGES: 49773
COUNTS_ARE_CANDIDATES: false
DUPLICATE_NODE_KEYS: 0
DUPLICATE_EDGE_KEYS: 0
DANGLING_EDGES: 0
OUTPUTS_PUBLISHED: true
NODES: 52586
EDGES: 49773
DOCUMENTS: 2813
FIELDS_WITH_POPULATED_EVIDENCE: 17
```

### Assessment Results interpretation

- The Assessment Results observation-score slice has expanded from 4 to 17 selected fields.
- All 2,813 source records were accepted; no invalid or duplicate source records were reported.
- No mapping-contract or registry-contract errors were reported for this slice.
- The current generated slice contains 52,586 nodes and 49,773 edges with zero duplicate node keys, zero duplicate edge keys, and zero dangling edges.
- Missing values are source-data evidence, not invalid values: all 17 visible fields report `invalid=0`.
- `OUTPUTS_PUBLISHED=true` refers to notebook result publication; `WRITES_EXECUTED=false` means no DIM/FACT database writes were performed.
- `FULL_MODEL_COMPLETE=false` and `SCHEMA_VALIDATED=false`: do not claim full Assessment Results completion or OSCAL conformance yet.
- 28 other Assessment Results mapping rows remain outside this run.

### Immediate next objective

Keep writes disabled. Continue processing the remaining 28 Assessment Results mapping rows, preserving the same mapping/registry/graph integrity gates, then run full-model OSCAL schema and constraint validation before claiming completion or enabling DIM/FACT writes.
