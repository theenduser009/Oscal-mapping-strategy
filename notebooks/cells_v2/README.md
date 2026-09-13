# Seven copy-ready mapper cells

These pages contain the lean seven-cell implementation and are generated from
[notebooks/cells](../cells/README.md). Replace all seven cells together; older
compiled contexts and field-report APIs are not supported.

Field mappings come from [ARCHER_OSCAL_MAPPINGS.csv](../../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
The original nine registry columns own structure and identity, with three sparse
execution columns: `OPERATOR`, `UUID_POLICY` and `REQUIRED_MEMBERS`. No JSON
catalog or test fixtures are uploaded to the notebook.

## Setup and run

Complete the recorded DEV cleanup and verify the registry migration using the
[registry deployment guide](../../docs/REGISTRY_METADATA_SETUP.md). Their live
completion remains unverified here. Then upload the exact mapping CSV to notebook
Files and run these matching Python cells in order in one session:

1. [Configuration](01_initialization_and_configuration.py)
2. [Source, mapping and registry inputs](02_source_mapping_registry_inputs.py)
3. [CSV and registry compilation](03_canonical_mapping_contract.py)
4. [Reusable transforms and registry operators](04_parsing_transform_payload_helpers.py)
5. [Nodes and parent-child edges](05_registry_graph_builder.py)
6. [Validation, preview and persistence](06_validation_and_guarded_loader.py)
7. [Pipeline runner](07_mapper_orchestrator.py)

Cell One defaults to `SELECTED_MODELS = ("SSP",)`. Use
`("ASSESSMENT_RESULTS",)` for AR alone or `("SSP", "ASSESSMENT_RESULTS")` for
both. Keep `CONFIG["EXECUTE_WRITES"] = False` and Cell Seven's
`OSCAL_LOAD_MODE = "PREVIEW"` for deployment verification.

Cell Seven calls `run_oscal_pipeline(SOURCE_INPUTS, MAPPING_CONTEXTS,
OSCAL_LOAD_MODE)`. It publishes `MODEL_GRAPHS` and `PIPELINE_REPORT`, printing the
aggregate report after `OSCAL_PIPELINE_REPORT`. A successful preview reports
`PREVIEW_COMPLETE`; SSP's load status is `PREVIEW_PASSED_NO_TARGET_DML`.
AR's expected status is `MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING` because
it has no verified destination.

The lower-level `run_oscal_mapping(source_df, canonical_mapping_df,
element_registry_df, config, context)` returns nodes, edges and the load result.
The compiled context from Cell Three supplies mapping and registry execution;
the runner passes `None` for the two retained DataFrame arguments.

## Persistence and verification

Cell Seven's COMMIT mode previews every selected route before its first commit.
Each route has its own DIM/FACT transaction; a later route's failure cannot undo
an earlier committed route. Every selected route needs a verified destination,
and other target writers must be paused. Keep the shared write flag false;
the runner enables writes only on its per-run configuration.

Unknown transaction outcomes or failed post-commit readback require inspection
before retrying. The writer preserves unchanged rows and records absent from the
input; obsolete keys within selected records block the load.

Accepted SSP/CIA and AR17 behavior is covered by the
[release tests](../../tests/lean/README.md). Local tests and Snowpark emulator
checks do not establish live registry or daily-loader acceptance, which remain
pending. Historical pilots and the accepted full DEV reload are separate from
this deployment.

Developers edit [notebooks/cells](../cells/README.md), then run
`python tools/sync_notebook_cells.py` to regenerate these pages and the
[combined notebook](../NB_ARCHER_OSCAL_MAPPER_V1.py). The `--check` option detects
generated-file drift; this tool is not a Snowflake execution cell.
