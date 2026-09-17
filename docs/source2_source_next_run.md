# Source 2 Source -> Catalog Metadata: next PREVIEW run

Prepared: 2026-09-17

Current prerequisite checkpoint: optional `PROPERTY_NAME` mapper support committed as `8c876e77cd70a3a352e73c7845775645f3bcc46a`; targeted property-name and relevant mapper regression workflow completed successfully before that commit.

Owner-reported live registry paths:

- `catalog` — `SINGLETON`
- `catalog.metadata` — `SINGLETON`
- `catalog.metadata.props[]` — collection, `SOURCE_FIELD_NAME+VALUE`, `ITEM_PATH='$'`, `OPERATOR='properties'`

For the `properties` operator, `$` is mapper item-path notation meaning the current/whole transformed item value. It is not a Snowflake column and not an OSCAL JSON path.

## Exact PREVIEW steps

1. In the Snowflake notebook Files area, upload `Mapping/sources_source_runtime.csv` with the notebook-visible filename exactly `sources_source_runtime.csv`.
2. Use `notebooks/pilots/source2_catalog_source_cell1.py` as Cell 1.
3. Use the current maintained `notebooks/cells/02_source_mapping_registry_inputs.py` as Cell 2.
4. Use the current maintained `notebooks/cells/03_canonical_mapping_contract.py` as Cell 3. This contains the tested optional `PROPERTY_NAME` compiler support.
5. Use the current maintained `notebooks/cells/04_parsing_transform_payload_helpers.py` as Cell 4. This emits the explicit property name when supplied and preserves source-field-slug behavior otherwise.
6. Use the current maintained Cells 5 and 6 unchanged.
7. Use current Cell 7 with `OSCAL_LOAD_MODE = "PREVIEW"` unchanged.
8. Confirm Cell 1 still has `EXECUTE_WRITES = False`.
9. Run Cells 1 through 7 in order.
10. Capture the printed `OSCAL_PIPELINE_REPORT`. Do not switch to `COMMIT` yet.

## Expected safety behavior

- PREVIEW validates graph and storage behavior but performs no target DIM/FACT writes.
- Cell 7 refuses to run if shared `EXECUTE_WRITES` is not `False`.
- No Source 1 route is selected by the Source 2 Cell 1.
- This run tests the 14 reviewed Source -> Catalog Metadata mappings in `sources_source_runtime.csv`.

## Review after run

Return the full `OSCAL_PIPELINE_REPORT`. If the pipeline completes, also inspect the Catalog graph counts and a small metadata/property sample before any COMMIT decision.

This PREVIEW validates the current warehouse mapping graph. It is not yet a claim that the resulting Catalog is a complete NIST-conformant Catalog document; deferred Source-tab semantics and remaining native Catalog metadata requirements remain separate gates.
