# Mapper V2 — individual cells

Seven separate, copy-ready Python files for the published shared mapper. This V2 folder is a packaging change: each cell is byte-for-byte identical to the corresponding published file in `notebooks/cells/` at creation. It does not add new mapping behavior or establish live acceptance.

## Open each cell

1. [Cell 1 — Configuration](01_initialization_and_configuration.py)
2. [Cell 2 — Source, mapping and registry inputs](02_source_mapping_registry_inputs.py)
3. [Cell 3 — Mapping contracts and routing](03_canonical_mapping_contract.py)
4. [Cell 4 — Parsing and transformations](04_parsing_transform_payload_helpers.py)
5. [Cell 5 — Shared graph construction](05_registry_graph_builder.py)
6. [Cell 6 — Validation and guarded persistence](06_validation_and_guarded_loader.py)
7. [Cell 7 — Orchestration](07_mapper_orchestrator.py)

## Usage and current scope

Keep the seven-cell order in the same Snowflake notebook session; these are not seven standalone scripts. Keep normal `EXECUTE_WRITES` disabled and `OSCAL_LOAD_MODE` set to `PREVIEW`. Reorganizing the files does not itself require a new notebook run.

The published shared implementation covers Source One SSP and the 17 accepted Assessment Results mappings. AR database persistence remains unverified and requires an explicit verified target contract. Do not treat this folder as approval to write or reload data.

See [shared workflow, scope and preview instructions](../../docs/SHARED_SEVEN_CELL_MAPPER.md) and [current project status](../../docs/CURRENT_STATUS.md). The original [split cells](../cells/README.md) and [combined notebook](../NB_ARCHER_OSCAL_MAPPER_V1.py) remain unchanged. Future code updates must keep these copies synchronized.
