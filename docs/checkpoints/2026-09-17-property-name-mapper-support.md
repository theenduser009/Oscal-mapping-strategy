# Optional property-name mapper support — 2026-09-17

## Repository checkpoint

Branch immediately before this checkpoint: `simplify-metadata-boundary` at `8c876e77cd70a3a352e73c7845775645f3bcc46a` (`Add optional property name mapping support`).

## Why this change was needed

The reviewed Source 2 Source runtime batch contains Catalog metadata properties whose approved target names do not always equal a slug of the Archer source field. Examples include `NUMBER_OF_CONTROL_STANDARDS_SOURCE_LEVEL -> control-count`, `COUNT_OF_CONTROLS -> total-controls`, `SOURCE_CRITICALITY_VALUE -> criticality-value`, `AUTH_SOURCES_FILTER -> filter-category`, and `OFFICIAL_RETIREMENT_DATE -> retirement-date`.

The pre-change shared mapper always generated a property name from `SOURCE_FIELD_NAME`. That was correct for existing mappings but could not express these reviewed Source 2 names without changing their semantics.

## Implemented change

Commit `8c876e77cd70a3a352e73c7845775645f3bcc46a` adds one optional flat runtime metadata column:

`PROPERTY_NAME`

Behavior:

- For `properties` and `observations`, a nonblank `PROPERTY_NAME` is validated and compiled into `REPRESENTATION_PARAMS.property_name`.
- Cell 4 uses that explicit name when present.
- When `PROPERTY_NAME` is absent or blank, the existing source-field-slug behavior is unchanged.
- `PROPERTY_NAME` is rejected for other operators.
- Unsupported whitespace/characters are rejected.

Maintained/generated artifacts updated by the tested commit:

- `notebooks/cells/03_canonical_mapping_contract.py`
- `notebooks/cells/04_parsing_transform_payload_helpers.py`
- synchronized `notebooks/cells_v2/` copies
- `notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`
- `Mapping/MAPPING_COLUMNS.md`
- `tests/lean/test_property_name_override.py`

## Validation actually performed

GitHub Actions run `35242927438` completed successfully before the code was committed.

- New property-name tests: **4/4 passed**.
- Relevant maintained mapper regression modules: **113/113 tests passed**.
- Total tests in this guarded change workflow: **117/117 passed**.
- `tools/sync_notebook_cells.py --check`: **passed**.
- `git diff --check`: **passed**.
- Tested code was then committed by the workflow as `8c876e77cd70a3a352e73c7845775645f3bcc46a`.
- Branch read-back after the workflow confirms that commit is the branch head at the time of this checkpoint preparation.

The repository-wide `mapper-checks` workflow was not used as the acceptance gate for this change because the branch already has unrelated historical validation-helper gaps recorded elsewhere. This checkpoint claims only the targeted/relevant suite above plus generated-file and whitespace checks.

## Owner-reported live Catalog registry state

On 2026-09-17, after the guarded registry extension was run, the owner reported these live Catalog paths:

1. `catalog` — singleton
2. `catalog.metadata` — singleton
3. `catalog.metadata.props[]` — collection, `INSTANCE_KEY_RULE = SOURCE_FIELD_NAME+VALUE`, `ITEM_PATH = '$'`, `OPERATOR = properties`

This owner report supersedes the earlier state in which only `catalog` and `catalog.metadata` were present.

`$` in this registry contract means the current/whole transformed collection item value for the property operator. It is mapper item-path notation, not a Snowflake column and not an OSCAL JSON path.

## Source 2 execution status

- Full `sources_source` review: **implemented/published**.
- 14-row Source runtime batch (`Mapping/sources_source_runtime.csv`): **committed/read-back verified**.
- Source 2 Catalog Cell 1 (`notebooks/pilots/source2_catalog_source_cell1.py`): **committed/read-back verified; PREVIEW configuration**.
- Catalog root/metadata/props registry branch: **owner-reported live**.
- Optional `PROPERTY_NAME` capability: **implemented, tested, committed and read-back verified**.
- Seven-cell Source 2 PREVIEW: **not yet run/read-back verified**.
- Catalog DIM/FACT DML from this Source 2 batch: **none yet**.

## Next action

Run the Source-level Catalog batch in Snowflake PREVIEW only using the current maintained seven-cell mapper, `Mapping/sources_source_runtime.csv`, and `notebooks/pilots/source2_catalog_source_cell1.py`. Keep `EXECUTE_WRITES = False`. Review the resulting pipeline/graph report before any COMMIT decision.

This PREVIEW is a warehouse graph/mapping validation checkpoint; it is not yet a claim of a complete NIST-valid Catalog document because remaining native Catalog metadata requirements and deferred Source-tab semantics are tracked separately.
