# Mapper V2 — individual cells

Seven separate, copy-ready Python files for the published shared mapper. Each cell is generated from `notebooks/cells/`. The current revision executes reviewed mapping metadata through the shared engine; publication does not establish live acceptance. Cell Four no longer includes the historical SSP/AR engines; their frozen copy is test-only, not a notebook dependency.

## Open each cell

1. [Cell 1 — Configuration](01_initialization_and_configuration.py)
2. [Cell 2 — Source, mapping and registry inputs](02_source_mapping_registry_inputs.py)
3. [Cell 3 — Mapping contracts and routing](03_canonical_mapping_contract.py)
4. [Cell 4 — Parsing and transformations](04_parsing_transform_payload_helpers.py)
5. [Cell 5 — Shared graph construction](05_registry_graph_builder.py)
6. [Cell 6 — Validation and guarded persistence](06_validation_and_guarded_loader.py)
7. [Cell 7 — Orchestration](07_mapper_orchestrator.py)

## One model selector

### Current routing correction

Replace the notebook Files copy of [mapper_contract.v1.json](../metadata/mapper_contract.v1.json) and replace only [Cell Three](03_canonical_mapping_contract.py). In the existing active session, run Cell One to reload that catalog, then Cell Three, then Cell Seven in PREVIEW. Keep the existing model selection and writes disabled. Cells Two/Four/Five/Six and their session inputs can stay as they are. If the session has ended, run the matching seven cells in order instead. No extra runtime cell or registry change.

The registry now establishes model ownership before mapping; placeholder policy is metadata-driven. This correction does not approve deferred rows or enable other models. Local tests pass; post the new complete pipeline report for live acceptance.

In Cell One, edit only `SELECTED_MODELS`. Use `"SSP"` for SSP only,
`"ASSESSMENT_RESULTS"` for AR graph preview, or `("SSP", "ASSESSMENT_RESULTS")`
for both. Internal model keys and legacy configuration are derived automatically.
Unknown models are rejected; AR does not borrow SSP destination tables.

Upload [mapper_contract.v1.json](../metadata/mapper_contract.v1.json) to notebook Files alongside the approved mapping CSV. Cell One loads model/source contracts and executable field rules from that reviewed artifact. See the [metadata contract](../metadata/README.md). Accepted scope, deferred rows and write safeguards are unchanged.

## Usage and current scope

Keep the seven-cell order in the same Snowflake notebook session; these are not seven standalone scripts. Keep normal `EXECUTE_WRITES` disabled and `OSCAL_LOAD_MODE` set to `PREVIEW`. Reorganizing the files does not itself require a new notebook run.

The published shared implementation covers Source One SSP and the 17 accepted Assessment Results mappings. AR database persistence remains unverified and requires an explicit verified target contract. Do not treat this folder as approval to write or reload data.

See [shared workflow, scope and preview instructions](../../docs/SHARED_SEVEN_CELL_MAPPER.md) and [current project status](../../docs/CURRENT_STATUS.md). Developers edit the original [split cells](../cells/README.md) once and generate these pages and the [combined notebook](../NB_ARCHER_OSCAL_MAPPER_V1.py) using `tools/sync_notebook_cells.py`. Do not maintain a separate V2 implementation.
