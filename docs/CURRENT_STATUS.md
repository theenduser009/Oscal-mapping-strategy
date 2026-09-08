# Current Status

Last reconciled: 2026-09-08

## Verified notebook

- Current notebook: `NB_ARCHER_OSCAL_MAPPER_V1`.
- The generic seven-cell architecture is preserved: configuration, inputs, canonical mapping, helpers/transforms, graph builder, guarded loader, and orchestrator.
- Keep `EXECUTE_WRITES = False` while debugging.

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

## Prior successful read-only graph run

A later read-only SSP run reached graph validation successfully:

- Graph nodes: **19,691**
- Graph edges: **16,878**
- Duplicate node keys: **0**
- Duplicate edge keys: **0**
- Dangling source edges: **0**
- Dangling target edges: **0**
- Pre-write validation: **PASSED**
- `EXECUTE_WRITES = False`, therefore no DIM/FACT changes were made.

That run then failed only in the mapping-coverage helper with:

```text
ValueError: Cannot infer schema from empty data
```

Trace location:

```text
Cell 7 -> run_oscal_mapping -> build_mapping_coverage
Cell 4 -> build_mapping_coverage -> session.create_dataframe(output)
```

This means the coverage helper produced an empty Python `output` list. Do not mask this with an empty-schema workaround until the filtering/ownership reason for zero coverage rows is understood.

## Latest Snowflake runtime error

The newest screenshot shows the mapper now failing earlier during graph construction:

```text
OSCAL MAPPING RUN
Model: SSP
Run ID: 20260908T162917Z

ValueError: Ambiguous collection parent for
system-security-plan.system-characteristics.authorization-boundary
instance singleton
```

Traceback:

```text
Cell 7, line 45, in <module>
  run_oscal_mapping(...)

Cell 7, line 15, in run_oscal_mapping
  nodes_df, edges_df = build_oscal_graph(...)

Cell 5, line 200, in build_oscal_graph
  raise ValueError(...)
```

### What Codex should inspect next

Do **not** redesign the notebook and do **not** change the identity contract.

Inspect only the parent-resolution logic around Cell 5 line ~200 and the active registry rows for:

```text
system-security-plan.system-characteristics
system-security-plan.system-characteristics.authorization-boundary
```

`authorization-boundary` is expected to behave as a singleton child under the singleton `system-characteristics` branch. The error text says the builder is treating its parent relationship as ambiguous/collection-like. Determine whether this is caused by:

1. an incorrect `IS_COLLECTION` / `INSTANCE_KEY_RULE` registry value,
2. multiple parent instances being created for the same source record,
3. collection-parent detection using path syntax incorrectly, or
4. source duplication reappearing upstream.

Do not patch around the exception until the exact cause is identified.

## Immediate next action

From Codex/Desktop, pull this file and the current `notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`, then inspect the active registry values and Cell 5 parent-resolution branch that raises the `Ambiguous collection parent` exception.

## Latest correction prepared

The ambiguous parent error is caused by cardinality leaking from mapping type into graph structure. In Cell 4, the prior condition treated every Extension mapping as a request to create a separate collection instance. If such a row was owned by the singleton `system-characteristics` node, it produced multiple parents, so the singleton `authorization-boundary` child could not choose one.

The correction now creates property collection instances only when the owning registry path is actually `props[]`. Extension mappings can still resolve Archer lookup values, but mapping type no longer changes node cardinality. The registry remains authoritative. The complete notebook and copy-ready Cell 4 contain the correction, and both Python syntax validation and a focused singleton/props regression test pass.

### Snowflake next step

In the existing live session, replace and run only copy-ready Cell 4, then rerun Cell 7. Keep `EXECUTE_WRITES = False`. If the session has restarted, run Cells 1 through 7 in order.

## Error handoff convention

When a new Snowflake error is reported, the newest error and screenshot-derived traceback will be recorded in this `docs/CURRENT_STATUS.md` file. Codex should read this file first, reconcile it with the authoritative notebook, fix the owning cell, validate it, and keep the corresponding copy-ready cell synchronized.

