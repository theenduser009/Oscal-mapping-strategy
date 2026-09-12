# Mapper V2 - seven copy-ready cells

**Compact lean release:** all 691 local tests pass. Exact accepted SSP, CIA11
and AR17 outputs remain unchanged. The compactness audit is closed: duplicate
registry parsing and SSP-only loader compatibility were removed without changing
the seven-cell interface. Live registry setup and notebook preview are still
pending. No new execution cells were added.

Field mappings come from the [CSV](../../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
Structure and identity come from the original nine registry columns. Only
`OPERATOR`, `UUID_POLICY` and `REQUIRED_MEMBERS` are added as sparse execution
rules. **No JSON catalog is required.** These pages are generated from one
maintained implementation.

## First: one-time registry setup

Run the [lean registry metadata SQL](../../sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql)
in a fresh Snowflake SQL worksheet and share its aggregate result. It adds or
verifies only three DEV registry columns, leaves any earlier experimental
columns untouched, and does not access DIM/FACT. Follow the
[exact setup and preview steps](../../docs/REGISTRY_METADATA_SETUP.md).

## Then: the same seven Python cells

After registry setup is verified, upload the updated mapping CSV to notebook
Files and replace all seven matching cells. Run in order in one session with
writes disabled and Cell Seven in PREVIEW.

1. [Cell 1 - Configuration](01_initialization_and_configuration.py)
2. [Cell 2 - Source, mapping and registry inputs](02_source_mapping_registry_inputs.py)
3. [Cell 3 - Mapping contracts and routing](03_canonical_mapping_contract.py)
4. [Cell 4 - Parsing and transformations](04_parsing_transform_payload_helpers.py)
5. [Cell 5 - Shared graph construction](05_registry_graph_builder.py)
6. [Cell 6 - Validation and guarded persistence](06_validation_and_guarded_loader.py)
7. [Cell 7 - Orchestration](07_mapper_orchestrator.py)

Cell One's `SELECTED_MODELS` is the only model selector: `"SSP"`,
`"ASSESSMENT_RESULTS"`, or `("SSP", "ASSESSMENT_RESULTS")` (default).
Unknown models are not enabled automatically. AR has no verified destination
and remains graph-preview-only.

Accepted SSP/CIA and AR17 outputs pass local regression checks; this does not
prove a new Snowflake run or authorize COMMIT. Do not rerun old pilots, standalone
AR candidates or the accepted full DEV reload.

Developers edit [notebooks/cells](../cells/README.md) once; run
`python tools/sync_notebook_cells.py` to regenerate these pages and the
[combined notebook](../NB_ARCHER_OSCAL_MAPPER_V1.py).

