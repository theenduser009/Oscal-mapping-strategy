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
- Batched component hydration, selected lookup validation and retained partial
  component behavior.
- Loader preview, insert/update/unchanged behavior, rollback, unknown commit
  outcomes and post-commit readback reporting. Relational checks execute against
  SQLite with an explicit MERGE adapter; this is not a Snowflake SQL engine.
- Actual `snowflake-snowpark-python` local-emulator behavior for projections,
  snapshots, ranking, deduplication, typed graph frames and row collection.
  `test_snowpark_local.py` adapts only the emulator's unsupported transaction
  query and string-filter boundaries and describes those substitutions.

The package smoke tests exercise an installed Snowpark implementation, but no
local emulator proves the live schema, roles, transactions, MERGE semantics or
persisted Snowflake values. Those require the intended environment's registry
verification and daily-loader acceptance. Full OSCAL document conformance is
also distinct from validation of the currently mapped graph.

## Frozen evidence and historical tests

`tests/fixtures/legacy_cell4_pre_declarative.py` and related historical fixtures
preserve earlier accepted behavior. `tests/fixtures/pre_lean_cells` contains the
unchanged pre-rebuild Cell Three/Four source used as an independent transform
oracle; `test_transforms.py` checks their SHA-256 hashes before comparing 1,403
mapping/value cases. These files are test-only and must never be imported by the
deployed notebook or edited to make a comparison pass.

The older tests directly under `tests/` include historical private APIs,
retired policy catalogs, old reports and earlier migration workflows. They are
retained as historical coverage and fixture providers; they are **not the current
release suite**. The former 769-test result belongs to the prior implementation
and is not reported as validation of this rewrite. The release command is
`python -m unittest discover -s tests/lean`, with the required Snowpark dependency
gate enabled for CI.
