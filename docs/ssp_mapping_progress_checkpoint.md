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

## Assessment Results mapped-scope checkpoint — 2026-09-10

Target OSCAL path:

```text
assessment-results.results[].observations[]
```

Status:

```text
MAPPED_SCOPE_BUILT
```

Selected source fields:

```text
VULNERABILITY_SCORE
ANTIVIRUS_SCORE
PATCH_SCORE
SECURITY_COMPLIANCE_SCORE
```

Run evidence captured from the notebook:

```text
OTHER_AR_MAPPING_ROWS_NOT_PROCESSED: 41
MAPPING_CONTRACT_ERRORS: []
REGISTRY_CONTRACT_ERRORS: []
SOURCE_RECORDS: 2813
INVALID_SOURCE_RECORDS: 0
DUPLICATE_SOURCE_RECORDS: 0
```

Per-field output evidence:

```text
VULNERABILITY_SCORE
  emitted: 2813
  missing: 0
  invalid: 0

ANTIVIRUS_SCORE
  emitted: 2813
  missing: 0
  invalid: 0

PATCH_SCORE
  emitted: 2813
  missing: 0
  invalid: 0

SECURITY_COMPLIANCE_SCORE
  emitted: 2813
  missing: 0
  invalid: 0
```

Graph/output evidence:

```text
WRITES_EXECUTED: false
FULL_MODEL_COMPLETE: false
SCHEMA_VALIDATED: false
CANDIDATE_NODES: 16878
CANDIDATE_EDGES: 14065
COUNTS_ARE_CANDIDATES: false
DUPLICATE_NODE_KEYS: 0
DUPLICATE_EDGE_KEYS: 0
DANGLING_EDGES: 0
OUTPUTS_PUBLISHED: true
NODES: 16878
EDGES: 14065
DOCUMENTS: 2813
FIELDS_WITH_POPULATED_EVIDENCE: 4
```

### Assessment Results interpretation

- All 2,813 source records produced mapped evidence for the four selected Assessment Results scoring fields.
- No invalid or duplicate source records were reported.
- No mapping-contract or registry-contract errors were reported for this slice.
- The generated slice contains 16,878 nodes and 14,065 edges with zero duplicate node keys, zero duplicate edge keys, and zero dangling edges.
- `OUTPUTS_PUBLISHED=true` refers to the notebook's in-memory/published result state; `WRITES_EXECUTED=false` means no database writes were performed by this run.
- This checkpoint covers only the selected mapped Assessment Results slice. It does **not** establish full Assessment Results completion or OSCAL schema validity.
- 41 other Assessment Results mapping rows were not processed in this specific run.

### Immediate next objective

Keep writes disabled. Continue processing the remaining Assessment Results mapping rows, then perform full-model OSCAL schema and constraint validation before claiming Assessment Results completion or enabling DIM/FACT writes.
