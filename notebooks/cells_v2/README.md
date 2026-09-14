# Seven copy-ready mapper cells

Current package: [Security Assessment Plan](../../docs/SAP_NEXT_RUN.md).
Replace Cells One, Three and Four; upload the CSV and apply the scoped SAP
registry/table setup before its first preview. The seven cells total 1,903
lines and use matching lean-csv-registry-v4 compiler/helpers. Existing SSP/AR
acceptance and owner-resolved AR source keys remain intact. Earlier run
instructions below are historical where they differ from SAP_NEXT_RUN.md.

These pages contain the lean seven-cell implementation and are generated from
[notebooks/cells](../cells/README.md). Keep a matching release; older compiled
contexts and field-report APIs are not supported.

Field mappings come from [ARCHER_OSCAL_MAPPINGS.csv](../../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
The original nine registry columns own structure and identity, with three sparse
execution columns: `OPERATOR`, `UUID_POLICY` and `REQUIRED_MEMBERS`. No JSON
catalog or test fixtures are uploaded to the notebook.

## Setup and run

Current work preserves explicit AR source nulls in warehouse observation
properties. Follow [AR next run](../../docs/AR_NEXT_RUN.md): replace Cells One,
Three and Four together, then preview all seven cells. CSV, registry and table
definitions are unchanged. Existing SSP/AR committed checkpoints and POAM's
accepted preview remain recorded separately.

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
`PREVIEW_COMPLETE`; the configured SSP/AR/POAM destinations expect
`PREVIEW_PASSED_NO_TARGET_DML`. A deliberately unbound model instead reports
`MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING` and cannot commit.

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

The [release tests](../../tests/lean/README.md) preserve accepted SSP/CIA and
AR17 output and compare the 13 AR additions with the earlier mapper.
AR30 live preview and AR storage verification are pending; the successful
SSP no-change commit does not establish AR persistence or full conformance.

Developers edit [notebooks/cells](../cells/README.md), then run
`python tools/sync_notebook_cells.py` to regenerate these pages and the
[combined notebook](../NB_ARCHER_OSCAL_MAPPER_V1.py). The `--check` option detects
generated-file drift; this tool is not a Snowflake execution cell.
