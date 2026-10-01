# Maintained seven-cell mapper — October 1, 2026

This is the single maintained implementation. All seven files below now contain the delivered contribution-aware candidate: `lean-csv-registry-v5-lineage` / `oscal-lean-daily-v3.2-lineage`.

| Cell | Copy the full file | Responsibility |
|---|---|---|
| 1 | [Initialization and configuration](01_initialization_and_configuration.py) | Sources, selected models, safe options |
| 2 | [Source, mapping, and registry inputs](02_source_mapping_registry_inputs.py) | Frozen inputs; actual joined-child source identity |
| 3 | [Canonical mapping contract](03_canonical_mapping_contract.py) | Approved plan, ambiguity detection, mapping fingerprint |
| 4 | [Parsing, transform, and payload helpers](04_parsing_transform_payload_helpers.py) | Actual surviving contributions; shared property construction |
| 5 | [Registry graph builder](05_registry_graph_builder.py) | Exact owner/instance attribution; explicit placement gaps |
| 6 | [Validation and guarded loader](06_validation_and_guarded_loader.py) | Existing safeguards; COMMIT block for lineage gaps |
| 7 | [Mapper orchestrator](07_mapper_orchestrator.py) | PREVIEW default, matching versions, route reports |

Use all seven as a matching set. Keep `CONFIG["EXECUTE_WRITES"] = False` and Cell 7 `OSCAL_LOAD_MODE = "PREVIEW"`. Do not interpret code publication as a request to run a new Snowflake write.

The [combined notebook](../NB_ARCHER_OSCAL_MAPPER_V1.py) and [copy-ready mirrors](../cells_v2/README.md) are generated from these files. Do not edit the three representations separately. From the repository root run `python tools/sync_notebook_cells.py`, then `python tools/sync_notebook_cells.py --check`.

The [property reader](../validation/15_ssp_universal_lineage_prop_preview.py) is read-only and separate from the seven production cells; it consumes existing MODEL_GRAPHS, not a guessed physical DIM schema. MODEL_GRAPHS and PIPELINE_REPORT are the current runtime outputs.

The local candidate checks passed (73 scenarios + 53 focused tests). Full repository/native compatibility and production release gates remain pending. See [current status](../../docs/CURRENT_STATUS.md), [publication checkpoint](../../docs/checkpoints/2026-10-01-seven-cells-published-to-github.md), and [file hashes](../../docs/checkpoints/2026-10-01-seven-cell-publication-manifest.json).

The earlier README and all detailed historical diagnostic instructions remain [at the pre-publication revision](https://github.com/theenduser009/Oscal-mapping-strategy/blob/94e41f8896d73cd6ed191c6030efb7f31c7d206b/notebooks/cells/README.md). Its old replacement lists, counts, and suggested SAP/AR runs are not current instructions.
