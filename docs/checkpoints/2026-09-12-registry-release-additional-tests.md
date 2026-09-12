# Additional registry-release testing - 2026-09-12

**Historical checkpoint:** the defects below are corrected in the
[subsequent release](2026-09-12-registry-release-corrections.md), which passes
685 local tests. The hold and test failures below describe the earlier version.
Live Snowflake setup and preview are still pending.

## Current decision

**Hold the new registry setup and matching notebook PREVIEW.** Additional tests
found boundary defects after the original 654-test suite passed. This supersedes
the previous setup instructions until corrections and expanded tests pass.
Do not rerun the accepted SSP DEV reload.

This checkpoint is local, not published to GitHub. The user requested continued
testing. No runtime code, migration SQL, mappings, registry, DIM or FACT data
was changed during this testing turn.

## Tested release and passing controls

Published commit
[`1e58f05c9e54bdf4f258ca30be9ede4a0bf1d13a`](https://github.com/theenduser009/Oscal-mapping-strategy/commit/1e58f05c9e54bdf4f258ca30be9ede4a0bf1d13a)
was verified as GitHub main.

- Original 654 local tests pass.
- Expanded full suite: **666 tests, 660 passed, 5 assertion failures and 1 error**.
  All six nonpassing cases are the new regressions described below. There are
  no skipped tests, expected failures or unexpected successes. The 12 added
  tests comprise six passing controls and six defect reproductions.
- Source cells, V2 pages and combined notebook pass synchronization checks.
- New local AR tests execute all seven current cells with fake Snowpark transport:
  zero and false map correctly; missing/null scores preserve the result parent;
  repeat runs preserve business payloads and keys; writes stay disabled.
- Accepted SSP/CIA and AR17 parity passes. A missing CIA objective correctly
  omits the optional assembly when its registry owner is enabled.
- Independent synthetic-model/two-source checks preserve source isolation,
  parent links and deterministic identities.
- These are local tests and source reviews, not live Snowflake acceptance.
  The local runtime has no Snowpark package or live Snowflake connection.

[test_registry_release_boundaries.py](../../tests/test_registry_release_boundaries.py)
asserts required behavior, including normal failing regressions. No skips or
expected-failure markers hide reproduced defects.

Reproduce with `python -B -m unittest discover -s tests`; focused run:
`python -B -m unittest discover -s tests -p 'test_registry_release_boundaries.py'`.
Packaging check: `python -B tools/sync_notebook_cells.py --check`.

## Findings requiring correction

### 1. Disabled/inactive singleton mappings fall through to their parent

Cell Three resolves ownership after filtering selected registry paths. With
`MAPPER_ENABLED=False` or `IS_ACTIVE=False` on
`system-security-plan.system-characteristics.security-impact-level`, all eleven
CIA mappings are still selected under `system-characteristics`.

A missing-objective fixture then emits partial nested CIA values, bypassing
the disabled singleton's complete-only rule. The same fixture omits the
assembly correctly when its owner is enabled. Known disabled/inactive paths
must prevent execution, not become ordinary members of an enabled ancestor.

This is a reproduced configuration-boundary defect, not evidence that the live
registry has this setting or that accepted stored data was lost.

### 2. A future model with no relationships fails dataframe construction

Cell Five calls `session.create_dataframe(edge_rows)` without a schema.
An approved synthetic model producing one root and no edges reaches an empty
list, which Snowpark cannot infer. A strict transport stub reproduces this
requirement. Explicitly typed empty dataframes are needed in the shared builder.

AR17 still produces root/result relationships without score values, so its
missing/null-score controls pass. All-null parent columns are not the issue.
[Snowpark API](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/snowpark/api/snowflake.snowpark.Session.create_dataframe)
and [official empty-data check](https://github.com/snowflakedb/snowpark-python/blob/main/src/snowflake/snowpark/session.py#L3553-L3558)
support the transport requirement. This was not run in Snowflake.

### 3. Migration preflight is weaker than the runtime decoder

The migration checks that an enabled parent exists, but not that it is a strict
path ancestor. A default-enabled SSP singleton with a self-parent or unrelated
enabled parent passes that predicate, then fails the actual Cell Three decoder.

One active null `NODE_PATH` can also avoid the duplicate-path check and vanish
from later equality joins. The decoder rejects it. Active selected paths need
nonblank/non-null checks, and parent/root validation must agree with the decoder
before DDL.

These findings use source-bound SQL predicate simulations and the actual local
decoder, not migration execution. They do not establish malformed live rows.

### Additional reporting risk - not a confirmed live failure

The migration reads `SQLROWCOUNT` after `EXECUTE IMMEDIATE :update_sql`.
Snowflake documents a dynamic-execution case where this variable is null.
Review the UPDATE result set and require a valid count; this account's behavior
has not been established. A null count can omit `UPDATED_ROWS` from the report.
[Snowflake known-issue article](https://community.snowflake.com/s/article/SQLROWCOUNT-returns-NULL-when-executed-by-execute-immediate).

## Next action and preserved scope

Correct these boundaries, rerun expanded regressions and accepted-output parity,
then publish a synchronized correction with one clear setup/run instruction.
No additional diagnostic or unchanged notebook rerun is requested from the
owner now. Corrections and publication were not performed in this testing turn.

Normal writes remain disabled. Accepted SSP DEV reload: 2,813 sources,
70,102 DIM rows and 67,289 FACT rows. Earlier row-count reduction remains
unexplained. AR17 remains accepted in memory only; daily writer and AR
persistence have no new live acceptance.
