# Generated copy-ready cells — October 2, 2026

These seven files are byte-identical generated copies of the [maintained source](../cells/README.md). They are not a second engine. Versions: `lean-csv-registry-v11-meta-driven-security-objectives` / `oscal-lean-daily-v3.2-lineage`.

1. [Configuration](01_initialization_and_configuration.py)
2. [Inputs](02_source_mapping_registry_inputs.py)
3. [Mapping compilation](03_canonical_mapping_contract.py)
4. [Transforms and assembly](04_parsing_transform_payload_helpers.py)
5. [Graph and attribution](05_registry_graph_builder.py)
6. [Validation and loading](06_validation_and_guarded_loader.py)
7. [Orchestration](07_mapper_orchestrator.py)

Use all seven together. Keep shared EXECUTE_WRITES false and Cell 7 PREVIEW. The default model remains SSP. [The combined file](../NB_ARCHER_OSCAL_MAPPER_V1.py) contains the same executable sections.

Edit only `notebooks/cells`; regenerate these pages with `python tools/sync_notebook_cells.py`, then run `--check`. The generator is packaging, not another Snowflake cell.

[Current status](../../docs/CURRENT_STATUS.md) distinguishes published/local-tested code from native and production acceptance. [Earlier copy-page instructions](https://github.com/theenduser009/Oscal-mapping-strategy/blob/94e41f8896d73cd6ed191c6030efb7f31c7d206b/notebooks/cells_v2/README.md) remain historical and do not authorize a rerun or table reset.
