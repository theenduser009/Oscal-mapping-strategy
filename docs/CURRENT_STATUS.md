# Current Status

Last reconciled: 2026-09-08

## Verified notebook

- Current notebook: `NB_ARCHER_OSCAL_MAPPER_V1`.
- The generic seven-cell architecture is preserved: configuration, inputs, canonical mapping, helpers/transforms, graph builder, guarded loader, and orchestrator.
- Keep `EXECUTE_WRITES = False` while debugging/validating.

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

## Earlier read-only graph checkpoint

An earlier SSP run reached:

- Graph nodes: **19,691**
- Graph edges: **16,878**
- Duplicate node keys: **0**
- Duplicate edge keys: **0**
- Dangling source edges: **0**
- Dangling target edges: **0**
- Pre-write validation: **PASSED**
- `EXECUTE_WRITES = False`

That run then exposed an empty mapping-coverage helper condition (`Cannot infer schema from empty data`).

## Resolved parent-cardinality issue

A subsequent run failed with:

```text
ValueError: Ambiguous collection parent for
system-security-plan.system-characteristics.authorization-boundary
instance singleton
```

The identified cause was cardinality leaking from mapping type into graph structure. Extension mappings must not create collection cardinality unless the owning registry path is actually a collection such as `props[]`. The registry remains authoritative for hierarchy/cardinality.

## LATEST VERIFIED SNOWFLAKE RUNTIME CHECKPOINT

Screenshot received 2026-09-08 shows a successful full read-only SSP mapper run after the correction.

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

### Interpretation

This is now the authoritative latest runtime checkpoint:

- Graph construction completed.
- The earlier ambiguous collection-parent failure is no longer present in this run.
- Duplicate-node and duplicate-edge validation both pass at zero.
- Both referential/dangling-edge checks pass at zero.
- Pre-write validation passes.
- Safety gate remained OFF, so no DIM or FACT changes were made.
- Node/edge counts are **51,772 / 48,959** for this run.

Do not replace these counts with the older 19,691 / 16,878 checkpoint when discussing current state.

## Safety / next-step rule

Do **not** enable `EXECUTE_WRITES` merely because this read-only run passed. Before any write-enabled run, reconcile the 51,772 nodes / 48,959 edges with expected registry/mapping scope and confirm mapping coverage/element-type counts. Keep the duplicate-source guard and graph validation intact.

## Handoff to Codex

Codex/Desktop should pull this file first. Treat the 20260908T185543Z run above as the latest verified Snowflake runtime evidence. Continue from this checkpoint rather than reproducing the earlier duplicate-source or ambiguous-parent investigations unless a regression appears.

The immediate engineering focus is validation of the resulting SSP scope/content (including mapping coverage and expected element-type populations) while `EXECUTE_WRITES=False`; do not redesign the seven-cell mapper or change the frozen deterministic identity contract.

## Error/checkpoint handoff convention

When a new Snowflake result or error is reported from the phone, update this `docs/CURRENT_STATUS.md` file with the exact observed counts/error and enough context for Codex to continue from desktop without requiring screenshots to be re-sent.

## Read-only scope validation prepared

A separate copy-ready validation cell is now available at
`notebooks/validation/RUN_AFTER_07_ssp_scope_validation.py`. It is not an
eighth production cell and makes no permanent changes.

The latest counts already satisfy the primary forest reconciliation:

```text
51,772 nodes - 2,813 source records = 48,959 expected edges
Observed edges = 48,959
```

The validation cell additionally checks one SSP root per source record, Cell 7
validation flags, the write gate, active registry versus mapped owner paths,
node counts by element type and full registry path, empty versus populated
payloads, field-level source-data coverage, and mappings with no source data.

Run it after Cell 7 in the same live Snowflake session with
`EXECUTE_WRITES=False`. Record its complete summary and tables in this file
as the next runtime checkpoint. Do not enable writes based only on the current
graph counts.

