# POAM other-model trace negative; loader-scope gap and history review

Evidence date: September 28, 2026.
Repository: theenduser009/Oscal-mapping-strategy.
Branch inspected: simplify-metadata-boundary.
Head before this work: 946411bc44ee89620a16d83134dd0718900db973.
New SQL commit: 29e0883976299aeb2079c34e589a8ad965414ad4.
SQL path: sql/qa/POAM_TABLE_WRITE_HISTORY_2026-09-28.sql.
SQL Git blob read back: eef0a6d9cb6269aa144f90a5fcbf3dae8de118f2.
That blob matches the locally tested file.

## Owner-provided result
The latest screenshot of POAM_ORPHAN_OTHER_MODEL_TRACE_2026-09-28.sql shows all eleven rows:
- POAM FACT_ROWS_READ: 2,583.
- POAM FACT_ROWS_WITH_MISSING_HASH_ENDPOINT: 2,575.
- SSP: ANY_ENDPOINT_HASH_FOUND = 0, ANY_ENDPOINT_UUID_FOUND = 0, EXACT_STORED_FACT_ROW_FOUND = 0.
- ASSESSMENT_RESULTS: the same three checks are all 0.
- SECURITY_ASSESSMENT_PLAN: the same three checks are all 0.

This supersedes the other-model-trace-pending status in docs/checkpoints/2026-09-28-poam-uuid-no-matches-and-other-model-trace.md. It establishes no matches in the three current model DIM/FACT tables searched, not that the facts never belonged to those models historically or that every schema was searched.

Earlier September 28 results remain: the same 2,575 rows have BOTH_ENDPOINTS_MISSING in current POAM DIM, and NEITHER_UUID_FOUND there; eight FACT rows have both hash endpoints present. The cross-model result does not clear the POAM defect or authorize disposal of any fact. Root cause and original ownership remain unverified.

The upstream RAW_DATA-to-CURATED_JSON MATCHED_SAVED_REFERENCE result is a separate gate. Historical committed/readback-verified loads remain evidence for their batches, not proof of clean current whole-table relationships. No original complete workbook or current registry export was inferred from the historical handoff supplement.

## New actual-code finding: scope-based validation can miss disconnected FACT rows
Inspected notebooks/cells/06_validation_and_guarded_loader.py, lines 210-270, at the pinned head above. Blob: a206e316427b3aac7d20f4bb25c9af73c3a54c0b.

_load_scope includes target FACT rows only when their primary key matches a candidate FACT or either endpoint belongs to the scoped/candidate DIM-key set. _load_preflight performs its orphan check on that returned scope. Therefore a fully disconnected FACT whose own key is not a candidate can fall outside this orphan check. Global null/duplicate-key checks do not cover this relationship defect.

A local synthetic SQL test of the exact membership predicate confirmed that a noncandidate both-endpoints-missing FACT was excluded, while a candidate FACT and a FACT touching a selected parent were included.

This is a confirmed code-coverage limitation and explains how a batch-scoped COMMITTED_AND_VERIFIED report can coexist with current table-wide orphan failures. It does NOT establish when the 2,575 facts appeared or what operation created the discrepancy. No mapper or loader patch was made. Adding a full-table orphan gate is a proposed follow-up, distinct from repairing existing data.

## Next read-only artifact
POAM_TABLE_WRITE_HISTORY_2026-09-28.sql queries SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY over the preceding 90 days. It looks for common DML/DDL table-target syntax naming the POAM DIM or FACT and returns one summary plus at most twenty recent candidate events. Counts of successful explicitly zero-row DML and older omitted events are included.

It returns event times, statement types, row-change counts, query IDs, transaction IDs and compilation context. It does not return raw query text, user names or payloads. It changes no database objects/data.

Limitations:
- Access to ACCOUNT_USAGE must already exist; permission failure is a specific access gap, not no history.
- QUERY_HISTORY can lag by up to 45 minutes. No recent complete-through guarantee is inferred.
- Table-name text matching is candidate evidence, not an object-ID lineage proof. Names in other schemas, comments/strings, quoted-case semantics, indirect/dynamic operations, renames and truncated query text limit coverage.
- No match does not prove no earlier mutation. The search window and any display truncation remain explicit.
- A successful statement and affected-row count do not independently prove the transaction committed.
- No Time Travel, restoration, deletion, truncation, rekeying or reload is performed or authorized.

Snowflake official reference reviewed September 28, 2026:
https://docs.snowflake.com/en/sql-reference/account-usage/query_history

## Validation actually performed
- Read the current branch, owner screenshot, AGENTS.md, historical POAM guide and current loader scope/preflight source.
- Verified public QUERY_HISTORY columns, retention and latency against Snowflake documentation.
- Executed four local SQLite relational cases: mixed DML/DDL/failed/quoted/qualified events and source-only exclusions (18 fixtures); empty history; zero-row-DML-only history; 25-event truncation accounting. All passed with write operations denied while the diagnostic ran.
- The first local run exposed a POSIX-class translation error in the Python regex adapter. Corrected that adapter only, then reran successfully; the published SQL did not require modification for that test failure.
- Tested the reviewed loader scope predicate separately on three synthetic FACT rows; the disconnected noncandidate was excluded as described above.
- No Snowflake dialect parser was installed. Local SQLite and Python regex behavior do not certify a live Snowflake compile or run.
- SQL committed and full content/blob read-back verified. No new CI run, live Snowflake history result, mapper execution or database write is claimed.

## Immediate next action
Run sql/qa/POAM_TABLE_WRITE_HISTORY_2026-09-28.sql as-is with the user's existing Snowflake role. Share the result, or the exact authorization error. Do not repeat the three already-completed endpoint matching diagnostics or reload the mapper.
