# Source 2 CONTROL_PROCEDURES owner mapping evidence — 2026-09-18

Repository branch: `simplify-metadata-boundary`
Repository head inspected before this checkpoint: `3ec9bee424857e07fce34871a2ff8de03bf7abfa`

## Owner-provided mapping evidence

The owner supplied a screenshot of the original Source worksheet on 2026-09-18. The `CONTROL_PROCEDURES` row is visible as:

- Archer data type: `VARCHAR`
- Cardinality: `Single`
- OSCAL model: `Catalog or Component Definition`
- Catalog target: `catalog.control[@id].part[@name='statement']`
- Component Definition target: `component-definition.component.control-implementation.implemented-requirement.statement`

This confirms the dual-target wording is in the mapping document; it is not an artifact of the earlier transcription.

## NIST v1.2.3 technical reconciliation

Current NIST Component Definition JSON structure uses:
- `component-definition.components[]`
- `components[].control-implementations[]`
- `control-implementations[].implemented-requirements[]`

A control-implementation set requires a source reference to the Catalog/Profile supplying the control definition. An implemented requirement requires a `control-id` and `description`. Statement-level implementation is represented by structured `statements[]` objects with `statement-id` and `description`.

Therefore the photographed Component Definition path is not directly executable as a scalar JSON path in OSCAL v1.2.3. The developer must not silently convert the single `CONTROL_PROCEDURES` string into a complete control-implementation hierarchy without the missing source/control identity mappings.

## Status

- Original mapping row: owner-provided/read-back visible.
- Component Definition registry: previously read-back verified.
- Runtime mapping for `CONTROL_PROCEDURES`: not approved/executable yet.
- No notebook/runtime/target DML change made by this checkpoint.

## Next requirement

Obtain an exact executable target decision for `CONTROL_PROCEDURES`. If Component Definition is selected, identify the parent control-implementation source and implemented-requirement control-id and whether the text is control-level `description` or statement-level `statements[].description`.
