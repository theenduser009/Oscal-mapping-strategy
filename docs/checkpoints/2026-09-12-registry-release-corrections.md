# Corrected registry-backed seven-cell release - 2026-09-12

## Result

All **685 local tests pass**, with zero failures, errors, skips or expected
failures. The six failing cases recorded in the
[additional-testing checkpoint](2026-09-12-registry-release-additional-tests.md)
now pass. The earlier hold is superseded for this corrected version.

The owner requested updated notebooks and approved scoped edits/publication.
No live registry setup, notebook execution, DIM/FACT write or Matillion run was
performed. Live setup and preview remain pending.

## Corrections

| Area | Correction | Unchanged behavior |
| --- | --- | --- |
| Cell Three | Known inactive, disabled and unselected registry paths block approved descendants instead of falling through to a parent. | Legitimate sibling prefixes, active duplicates, source/model isolation and deferred/excluded rows. |
| Cell Five | Empty canonical dataframes receive an explicit typed schema. | Populated rows retain existing type inference; empty sources and invalid graphs still fail before loading. |
| Registry SQL | Pre-DDL path, root, collection and strict-parent validation; validated dynamic UPDATE result count. | Original nine columns, 18 added metadata columns, seed values, conflict protection and transaction boundaries. |

A deleted registry path cannot automatically be distinguished from a legitimate
nested payload member. The routing fix closes **known** non-executable boundaries;
it does not invent absent registry metadata.

Cell Seven already calls the same mapping and persistence functions per
source/model context. No additional SSP/AR wrappers, selector, standalone cell,
field mapping or duplicate execution path was added.

## Verification

- Complete local suite: 685 tests, all pass.
- All six original failing boundary assertions remain; no skipped/expected-fail
  annotations or weakened output expectations were introduced.
- Seven additional disabled-path isolation tests, eight typed-transport tests,
  and four additional migration tests pass.
- Accepted SSP/CIA graph and AR17 payload/key parity pass against frozen
  independent baselines. Those fixtures were not changed.
- All seven cells execute in local AR preview tests with fake Snowpark inputs:
  zero/false values, missing/null values and repeat-key stability are preserved.
- Older root-only test fixtures now use the same strict typed transport stub;
  their mapping assertions are unchanged.
- Source/V2/combined synchronization check passes.

Snowpark and SQL transport assertions use local stand-ins and source-bound
predicate checks. They are **not** live Snowflake syntax/execution evidence.

The empty-frame implementation follows the
[Snowpark dataframe schema interface](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/snowpark/api/snowflake.snowpark.Session.create_dataframe).
Dynamic DML result capture is supported by Snowflake's
[RESULTSET example](https://docs.snowflake.com/en/developer-guide/stored-procedure/stored-procedures-calling-references);
the count column follows the official [UPDATE output](https://docs.snowflake.com/en/sql-reference/sql/update).

## Files and next action

Maintain code only in source Cells Three and Five and the registry SQL; generated
V2 pages and combined notebook carry the same changes. The mapping CSV, all
other cell logic, historical fixtures and accepted stored data are unchanged.

Use the [corrected setup instructions](../REGISTRY_METADATA_SETUP.md).
First run only the one-time DEV registry SQL in a fresh SQL worksheet and share
its aggregate result. After setup is verified, use the matching seven V2 cells
and mapping CSV in PREVIEW with writes disabled. No JSON upload is needed.

Do not rerun the accepted full DEV SSP reload. It remains 2,813 sources,
70,102 DIM rows and 67,289 FACT rows. The previous row reduction remains
unexplained; AR17 is still in-memory accepted only, not persisted.

Reproduce local checks:
`python -B -m unittest discover -s tests`
and `python -B tools/sync_notebook_cells.py --check`.
