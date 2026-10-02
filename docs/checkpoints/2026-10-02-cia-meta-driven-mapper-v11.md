# 2026-10-02 CIA Meta-Driven Mapper v11

## Repository checkpoint
- Branch: `simplify-metadata-boundary`
- Code head before this checkpoint: `e0b49f183faed3f61dc108a0b53e4533352fedfd`
- Release: `lean-csv-registry-v11-meta-driven-security-objectives`

## Owner-approved change
Live Snowflake validation showed that populated CIA select-value IDs resolve cleanly through
`ARCHER_META_VALUE.SELECT_VALUE_ID -> SELECT_VALUE_NAME`, including both canonical
`Low` and source-native `Legacy LOE ...` labels. The failure-only validation returned
zero rows.

The mapper therefore no longer uses a manually maintained CIA Legacy-LOE allowlist from
`Mapping/ARCHER_OSCAL_MAPPINGS.csv`.

## Implemented
- Cleared `ALLOWED_VALUES` for all 11 `security-objective` mapping rows.
- Cell 3 no longer compiles `approved_legacy_values` for `security-objective`.
- Cell 4 now requires one resolved Archer-meta label; it lowercases only
  `Low/Moderate/High` to `low/moderate/high` and otherwise preserves the exact
  resolved meta label.
- Bumped matching mapper release guards to
  `lean-csv-registry-v11-meta-driven-security-objectives`.
- Updated the maintained source cells, copy-ready `cells_v2` mirrors, and combined
  `NB_ARCHER_OSCAL_MAPPER_V1.py`.
- Updated CIA validation terminology from `REVIEWED_LEGACY_OCCURRENCES` to
  `NONCANONICAL_META_LABEL_OCCURRENCES`.
- Updated seven-cell READMEs to the v11 release.

## Validation actually performed
Repository read-back checks after the edits confirmed:
- all seven maintained cells are byte-equivalent to their `cells_v2` mirrors;
- all seven cell sections in the combined notebook match the maintained source cells;
- exactly 11 `security-objective` mapping rows remain;
- zero of those 11 rows retain the manual Legacy-LOE allowlist;
- `approved_legacy_values` is absent from the maintained seven-cell source;
- no maintained source cell retains the v10 release string;
- the expected v11 release guards are present.

## Evidence boundary
- No Snowflake PREVIEW or COMMIT was executed from ChatGPT after the v11 code change.
- The earlier live meta-value verification proves the upstream Archer labels, not the
  execution of the newer v11 mapper.
- Do not treat this checkpoint as target-table write verification.

## Next action
1. Refresh/use the matching v11 seven-cell mapper.
2. Run SSP in PREVIEW only.
3. Re-run `notebooks/validation/19_ssp_cia_resolved_values_validation.py`.
4. Confirm zero source/target conflicts and zero mismatches.
5. Separately continue the field-lineage drill-down: `ELEMENT_TYPE` identifies the OSCAL
   node; exact Archer source-field attribution comes from selective `source-field` props
   plus the mapping row that identifies the target member.
