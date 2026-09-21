# Repository cleanup checkpoint — 2026-09-21

## Scope and safety rule
This cleanup removes only clearly completed one-time helper automation and one-time
validation/commit cells from `simplify-metadata-boundary`. Historical context,
mapping artifacts, dated evidence, registry SQL, current mapper cells, tests,
Source One/Source Two mappings, and reusable diagnostics are preserved.

## Repository version
- Branch before cleanup: `c0adc772de9c624ba6f1f7e93861c3b0f8bd2e16`
- Cleanup commit: `1052fa7cd551c06ca98bcacb8f1b4f8591927961`

## Removed
Completed one-time mutation workflows:
- `.github/workflows/apply-property-name-support.yml`
- `.github/workflows/apply-source2-ar-no-defer.yml`
- `.github/workflows/apply-source2-ar-no-defer-v2.yml`
- `.github/workflows/apply-source2-ar-route.yml`
- `.github/workflows/apply-universal-cell1.yml`

Completed one-time patch/helper code:
- `tools/apply_source2_ar_no_defer.py`

Completed Source Two Catalog one-time notebook helpers whose outcomes are already
preserved in dated checkpoints:
- `notebooks/validation/source2_catalog_source_preview_inspection.py`
- `notebooks/validation/source2_catalog_source_commit.py`

## Intentionally retained
- `.github/workflows/mapper-checks.yml`: active reusable CI.
- `.github/workflows/build-source2-workbook.yml` and
  `tools/build_source2_workbook.py`: reusable workbook regeneration path while
  Source Two mapping work is still active.
- `notebooks/validation/10_ssp_curated_json_to_oscal_full_reconciliation.py` and
  `11_ssp_component_payload_reconciliation.py`: reusable Source One reconciliation
  diagnostics while sprint-close mapping work is still active.
- `notebooks/validation/03_ssp_metadata_timestamp_validation.py`: retained
  conservatively because SSP metadata remains part of Source One completion review.
- `notebooks/validation/2026-09-21_source_one_ar_post_preview_compiled_check.py`:
  current read-only validation needed for today's Assessment Results work.
- All `docs/checkpoints/`, mapping provenance, registry/setup SQL, current seven
  mapper cells, tests, and accepted run evidence.
- `notebooks/cells_v2/`: the seven code files are byte-identical to
  `notebooks/cells/`, but they are generated intentionally by
  `tools/sync_notebook_cells.py` as copy-ready pages. They were not deleted in
  this conservative cleanup because doing so would require a packaging-contract
  change rather than simple removal of one-time artifacts.

## Branch audit
Current branch inventory contained:
- `main`
- `simplify-metadata-boundary`
- `noop-temp`, `noop-temp2` ... `noop-temp7`
- `source2-catalog-commit-helper`
- `source2-catalog-commit-helper-final`
- `source2-catalog-commit-helper-v2`
- `source2-catalog-commit-helper-v3`

All seven `noop-temp*` branches point to the same commit
`1c56c954abb0dd5eca2602dcba8df49278f225bb`. The current
`simplify-metadata-boundary` history is 65 commits ahead and 0 behind that
commit, so the temporary branch contains no unique commit not already in the
current working branch.

All four `source2-catalog-commit-helper*` branches point to the same commit
`5752c02c4bd7f9cb5b382746a6c660d3e8743fbd`. The current
`simplify-metadata-boundary` history is 63 commits ahead and 0 behind that
commit, so those helper branches also contain no unique commit not already in
the current working branch.

The only open pull request uses `simplify-metadata-boundary` as its head.
None of the temporary/helper branches is the head of an open PR.

Therefore the 11 temporary/helper branches are safe branch-deletion candidates
from a history-preservation perspective. The available GitHub connector in this
chat does not expose a delete-branch/delete-ref mutation, so this checkpoint does
not claim those branch refs were deleted.

## Read-back verification
After the cleanup commit:
- `.github/workflows/` contains only `build-source2-workbook.yml` and
  `mapper-checks.yml`.
- `notebooks/validation/` contains four retained files:
  `03_ssp_metadata_timestamp_validation.py`,
  `10_ssp_curated_json_to_oscal_full_reconciliation.py`,
  `11_ssp_component_payload_reconciliation.py`, and
  `2026-09-21_source_one_ar_post_preview_compiled_check.py`.
- `tools/` contains only `build_source2_workbook.py` and
  `sync_notebook_cells.py`.

## Next action
Continue Source One Assessment Results verification using the retained
`2026-09-21_source_one_ar_post_preview_compiled_check.py`. Branch-ref cleanup is
administrative only and must not block the sprint-close mapping work.
