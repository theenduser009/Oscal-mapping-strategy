# POAM orphan UUID result and other-model trace - 2026-09-28

## Repository basis
- Branch: simplify-metadata-boundary.
- Head inspected before this work: 91e25c8bbdc73767274e14d6411986a3fa470be7.
- New SQL commit: d0766b3744385aa4cd99d1c0f320d097fe15c9f7.
- New SQL path: sql/qa/POAM_ORPHAN_OTHER_MODEL_TRACE_2026-09-28.sql.
- Read-back SQL blob: 9b0e1dd42840110cfe8c393f0b8c6a0b905bf496, matching the locally tested file.

## Owner-provided live result
The screenshot of POAM_ORPHAN_UUID_DIAGNOSTIC_2026-09-28.sql shows QA_EXECUTED_AT 2026-09-28 13:22:35.148 -0400 and all ten rows:

| QA_CHECK | OBSERVED_COUNT |
| --- | ---: |
| FACT_ROWS_READ | 2583 |
| FACT_ROWS_WITH_MISSING_HASH_ENDPOINT | 2575 |
| UUID_INVALID_OR_MISSING | 0 |
| UUID_AMBIGUOUS | 0 |
| BOTH_UUIDS_UNIQUE_SAME_OWNER | 0 |
| BOTH_UUIDS_UNIQUE_OWNER_CONFLICT_OR_MISSING | 0 |
| SOURCE_UUID_ONLY | 0 |
| TARGET_UUID_ONLY | 0 |
| NEITHER_UUID_FOUND | 2575 |
| CLASSIFICATION_COUNT_DIFFERENCE | 0 |

This is table-wide evidence, not a selected Content ID count. The prior endpoint-bucket result established that the same 2,575 FACT rows have both hash endpoints absent and eight FACT rows have both hash endpoints present.

For all 2,575 inspected orphan FACT rows, neither normalized endpoint UUID was found in the current POAM DIM. UUID_INVALID_OR_MISSING=0 means the query's normalized 32-hex format check passed; it is not full semantic/RFC UUID validation. CLASSIFICATION_COUNT_DIFFERENCE=0 proves bucket accounting, not repair or data-integrity sign-off.

## Supersession and remaining gap
This result supersedes the UUID-diagnostic-pending status in docs/checkpoints/2026-09-28-poam-both-endpoints-missing-confirmed.md. There is no current POAM DIM candidate from that diagnostic for a UUID-based endpoint re-link.

It does not establish that rows are stale, disposable, misrouted, generated incorrectly, or associated with deleted historical nodes. POAM table-wide relationship QA remains open. Historical committed/read-back verified batches and the upstream RAW_DATA-to-CURATED_JSON saved-reference match remain separate, dated evidence; neither clears these current orphan facts.

The September 14 current-action text still visible in AGENTS.md, PROJECT_HANDOFF.md and CURRENT_STATUS.md is historical and does not override the September 25-28 checkpoints or this active QA task.

## Next read-only diagnostic prepared
The new single SELECT checks the current SSP, Assessment Results, and Assessment Plan tables for:
- any matching endpoint BINARY hash in that model's DIM;
- any matching normalized endpoint UUID in that model's DIM;
- an identical complete six-column FACT row in that model's FACT.

It returns eleven aggregate rows including current total/orphan POAM row counts. All namespaces in the three searched model tables are included, with no source-record filter. No private identifiers or payloads are returned. DISTINCT membership indexes prevent duplicate lookup rows from multiplying counts; they do not certify uniqueness. Source FACT row multiplicity is retained. Counts overlap across tests and models and must not be added as unique orphan counts.

This tests a possible routing/copy explanation without assuming it. Matches are candidates requiring further lineage review, not proof of intended ownership or permission to move/rekey/delete facts. No matches would not prove the facts are obsolete. Historical tables, Time Travel, STG, catalog and other schemas are not searched by this query.

## Validation actually performed
- Read current branch, actual UUID diagnostic, current table/key bindings, AGENTS.md and handoff/current-status sections.
- Created the new SQL locally; static checks confirm one SELECT-only statement without DDL/DML. The initial static test was corrected to ignore semicolons inside string literals; no SQL change was required.
- Executed the SQL using SQLite 3.46.1 with qualified-table-name and CURRENT_TIMESTAMP adapters plus a local REGEXP_LIKE function.
- Five synthetic cases passed: mixed candidates, duplicate source and lookup rows, UUID formatting, nulls and nonidentical copied facts; empty FACT; fully resolved POAM facts; no other-model matches; duplicate POAM DIM keys.
- Each case returned eleven rows matching independent Python membership counts. SQLite write operations were denied during query execution and table row counts stayed unchanged.
- SQL committed and read-back blob matched the tested local file.
- No Snowflake dialect parser, live compilation or live execution of the new trace was performed. No new mapper tests or CI run are claimed.
- No runtime mapper, CSV, registry, loader or database changes. No repair authorized or executed.

## Immediate next action
Run sql/qa/POAM_ORPHAN_OTHER_MODEL_TRACE_2026-09-28.sql as-is in Snowflake and share its eleven aggregate result rows. Use that evidence before choosing any repair or further lineage search. Do not repeat column discovery, upstream reconciliation or the OSCAL mapper.
