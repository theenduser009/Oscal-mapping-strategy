# Lean release tests

Run the current release suite from the repository root with Python 3.12:

```powershell
python -m pip install "pandas==2.3.3" "snowflake-snowpark-python[localtest]==1.55.0"
$env:REQUIRE_SNOWPARK_TESTS = "1"
python -m unittest discover -s tests/lean -v
python tools/sync_notebook_cells.py --check
git diff --check
```

On other shells, set `REQUIRE_SNOWPARK_TESTS=1` in the environment before running
the same Python commands. This makes a missing Snowpark dependency fail instead
of silently skipping the package smoke tests. No database credentials are
required, and these tests do not connect to Snowflake.

Tests load fresh definitions from `notebooks/cells` by default. Set
`LEAN_CELLS_DIR` only when checking a candidate directory before promotion.
The test helper omits notebook I/O and supplies an explicit local transport; it
never fills missing functions from an older active mapper.

## What the checks establish

- CSV/registry compilation, source selection, required values, transforms,
  collection identity, parent relationships and pipeline failure reporting.
- Accepted SSP and AR17 outputs against frozen independent evidence, including
  precision, source isolation and metadata-only new-field/third-model execution.
- The restored Direct `SECURITY_CATEGORY` mapping is checked separately for
  source-text preservation, absent/null/empty-string omission and unchanged
  graph keys, UUIDs and edges. All earlier 1,403 transform cases remain intact.
- `test_ar30_extension.py` compares the 13 added AR fields with the earlier
  standalone oracle, including decimal precision, zero/false, null omission,
  parent links and preservation of the original AR17 identities. Original
  CSV source names, paths, Notes and provenance remain unchanged; parked
  reference/multi-value fields and workflow rows stay deferred. The two exact-name
  AR threshold additions are checked separately for zero preservation, unchanged
  AR30 keys/payloads and no fallback to underscore-prefixed names.
- Batched component hydration, selected lookup validation and retained partial
  component behavior.
- Loader preview, insert/update/unchanged behavior, rollback, unknown commit
  outcomes and post-commit readback reporting. Relational checks execute against
  SQLite with an explicit MERGE adapter; this is not a Snowflake SQL engine.
- Actual `snowflake-snowpark-python` local-emulator behavior for projections,
  snapshots, ranking, deduplication, typed graph frames and row collection.
  `test_snowpark_local.py` adapts only the emulator's unsupported transaction
  query and string-filter boundaries and describes those substitutions.
- `test_notebook_end_to_end.py` executes every statement of all seven cells
  using the actual CSV, synthetic values for every approved field, installed
  Snowpark frames and the local relational adapter. It covers SSP preview,
  commit and unchanged retry; SSP/AR route selection; and 32-record isolation.
  The emulator's unsupported `TRIM` uses the documented `mock.patch` hook;
  SQL and target writes use the explicit SQLite/MERGE adapter.
- The gap suites cover source mutation, typed-value collisions, failed output
  materialization, empty CSV bindings, nullable registry inputs, audit lineage
  and temporary-table cleanup. Unknown outcomes retain inspection data.
- `test_preview_update_review.py` covers the separate read-only comparison
  helper: JSON member differences, aggregate counts, drift, privacy and guards.
  Its value reconciliation checks controlled transitions, frozen source values,
  ambiguous selections, sensitivity-source presence and unchanged contexts.
  Its installed Snowpark test preserves duplicate and missing binary-key
  matches. The emulator's unsupported SQL-string projections are explicitly
  adapted; those expressions still require live Snowflake execution.
- `test_fips_normalization.py` loads the actual lookup code and checks that
  picklist IDs and direct labels produce the same lowercase FIPS value across
  all eleven approved objective mappings. It preserves general Archer labels
  and all eight approved legacy exceptions without inventing severity values.

The package smoke tests exercise an installed Snowpark implementation, but no
local emulator proves the live schema, roles, transactions, MERGE semantics or
persisted Snowflake values. Those require the intended environment's registry
verification and daily-loader acceptance. Full OSCAL document conformance is
also distinct from validation of the currently mapped graph.

## Frozen evidence and historical tests

`tests/fixtures/legacy_cell4_pre_declarative.py` and related historical fixtures
preserve earlier accepted behavior. `tests/fixtures/pre_lean_cells` contains the
unchanged pre-rebuild Cell Three/Four source used as an independent transform
oracle; `test_transforms.py` checks their SHA-256 hashes before comparing the
original 1,403 mapping/value cases and 299 cases for the AR additions. These files are test-only and must never be imported by the
deployed notebook or edited to make a comparison pass.

The older tests directly under `tests/` include historical private APIs,
retired policy catalogs, old reports and earlier migration workflows. They are
retained as historical coverage and fixture providers; they are **not the current
release suite**. The former 769-test result belongs to the prior implementation
and is not reported as validation of this rewrite. The release command is
`python -m unittest discover -s tests/lean`, with the required Snowpark dependency
gate enabled for CI.
