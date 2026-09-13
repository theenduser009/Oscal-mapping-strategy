# Expanded validation of the lean mapper

The owner requested an end-to-end check for missing behavior after the initial
108-test release. Three independent reviews examined inputs/metadata,
transforms/graph construction and persistence. The resulting fixes add only
36 runtime lines: **1,838 lines across the seven cells**, still **50.3% below
the 3,700-line version**. Mapping CSV rows and approved scope are unchanged.

## Reproduced gaps and fixes

| Boundary | Previous behavior | Corrected behavior |
| --- | --- | --- |
| Source configuration | Duplicate source keys could survive Cell 1 and fail after reading a source. | The existing uniqueness check rejects the duplicate before ingestion. |
| CSV source binding | A mistyped configured binding selected zero mapping rows. | A configured binding must select rows; a typo cannot become an empty plan. |
| Registry input | Blank optional ITEM_PATH differed from SQL NULL. | The existing text normalizer handles both consistently. |
| Nested mapping | A nested assignment could mutate the source object and invent a later source value. | Assigned values are copied. |
| Conflicting values | Python treated false/0 and nested equivalents as equal. | Conflict checks use the same JSON representation as graph output. |
| Property names | A punctuation-only field could emit a blank property name. | Existing text validation rejects the empty normalized name. |
| Output reporting | A failed DataFrame creation could report outputs as published. | Publication is recorded only after both frames are created. |
| Audit lineage | Nullable target audit columns allowed missing lineage to commit. | Verified-storage graphs require populated run ID and timestamps before DML. |
| Temporary snapshots | Successful runs left six temporary tables, including full target copies. | Confirmed preview, commit and verified rollback clean up their own tables. Cleanup failure does not change the recorded transaction result. |
| Source coverage | Boolean/float counts could compare equal to an integer count. | Coverage accepts Python/NumPy integer counts and rejects booleans/floats. |
| Stored root type | A non-root using the root's element type passed preview but failed after MERGE. | Verified-storage preview rejects this ambiguous physical representation. |

The paired loader/runner release is `oscal-lean-daily-v3.1`; use matching cells.
Unknown commit outcomes and failed post-commit readback retain temporary data
for inspection. No automatic retry or deletion policy was added.

## Test coverage

**All 158 tests pass in [GitHub CI #10](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/34758711257)**
for code commit [ae90082b](https://github.com/theenduser009/Oscal-mapping-strategy/commit/ae90082bc89029f6731872e1d89253c178f087e5).
The run used Python 3.12, pandas 2.3.3 and Snowpark 1.55.0 and completed the
suite in 9.554 seconds without skips. It includes the original five Snowpark
API smoke tests and three new complete-notebook tests. The expanded local
suite passes 150 tests; its two unavailable Snowpark classes are explicitly
skipped rather than represented as executed locally.

The full-cell runs exposed a source-count compatibility regression in the
new coverage check. `numbers.Integral` now accepts NumPy integer counts from
Snowpark while still rejecting booleans and floats. Both the focused
regressions and complete-notebook runs pass. No further runtime changes
followed this passing code commit.

The complete-notebook tests execute every statement in all seven cells with
the maintained CSV and synthetic values for every approved FIELD mapping:

1. SSP preview, commit, readback and an unchanged retry that preserves audit values.
2. SSP/AR preview and refusal to commit either route when the selected AR destination is absent.
3. Exact coverage and record-scoped parent links across 32 source records.

The tests use installed Snowpark frames for source, registry, lookup and graph
operations. SQL and target writes use the explicit SQLite/MERGE adapter.
Snowpark's local emulator does not implement `TRIM`; the test supplies the
documented `mock.patch` hook. The adapter's target schema includes the reviewed
column nullability. These are declared test-environment substitutions, not
changes to the production notebook. See
[Snowflake's local testing documentation](https://docs.snowflake.com/en/developer-guide/snowpark/python/testing-locally).

Existing acceptance evidence remains covered: the exact SSP fingerprint,
independent AR17 output, 1,403 frozen transform comparisons, metadata-only new
fields/models, lookup batching, required values, linked identities, stable
hashes, source-order selection, rollback and unknown transaction results.
Generated split and combined notebooks must pass synchronization checks.

## What remains unverified or incomplete

- Live Snowflake registry verification and daily preview/MERGE/rollback/readback
  have not run for this release because no live connection is available.
  Emulator and SQLite tests do not prove roles, live SQL execution, warehouse
  behavior or live data quality.
- AR has no verified destination contract and remains graph-preview only.
- This is the approved mapped scope, not a complete OSCAL document. Unapproved
  fields and full-document schema/constraint conformance remain separate work.
- The historical unexplained SSP row-count reduction is unchanged.

The remaining deployment step is live acceptance in the intended environment,
starting with the existing registry prerequisite and PREVIEW. Pause other
target writers for COMMIT; baseline comparison is not a concurrency lock.
