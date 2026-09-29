# Curated JSON lookup SQL publication

Date: September 29, 2026
Status: SQL committed and repository read-back verified. No Snowflake execution.

## Owner direction

Publish every OSCAL SQL statement the owner is asked to run in this GitHub repository first, then provide a direct copy-ready file link. A chat code block or sandbox attachment alone is not sufficient delivery. Verify the published file by reading it back. If publication fails, report that failure rather than claiming the SQL was posted.

This supersedes chat-only/sandbox-only delivery as the primary route for runnable OSCAL SQL. It does not authorize unrequested database execution, broaden write scopes, or change mapping approvals.

## Repository evidence

- Branch: `simplify-metadata-boundary`.
- Pre-publication head verified: `9217ad6746a08177450d0230b01bbc966039d72e`.
- SQL publication commit: `2d85095bd45f5e52c188cfb62ab1ff065a823608`.
- SQL path: `sql/READ_ONLY_ARCHER_META_LOOKUP_COLUMNS.sql`.
- SQL blob returned by branch read-back: `9a88a1dafdd30d474946638d095ec636d9795641`.

## What changed

Published the existing discovery SELECT for Archer metadata columns. It reads `RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS`, scoped to `ES_ESC_GRC`, for candidate user/group metadata objects plus `ARCHER_META_FIELD` and `ARCHER_META_VALUE`.

The SELECT body is unchanged from the preceding QA conversation. Added explanatory comments and a date. No mapper, mapping CSV, registry, existing SQL file, or Matillion UPDATE was modified.

## Validation actually performed

Read the target branch head and SQL directory before publication. The proposed SQL path returned Not Found; a new file was created through the GitHub connector. Fetched the complete file from the branch after creation and compared its returned text with the intended publication.

Repository publication/read-back is not a Snowflake PREVIEW, SQL execution, database COMMIT, or database read-back. None of those occurred. No live lookup columns, rows, join uniqueness, or user/group resolution outcomes were established.

## Remaining gaps and next action

The revised CURATED_JSON enrichment UPDATE remains unimplemented. Exact Meta User and Meta Group table/column contracts still need verification. The next action is to copy the published SQL, run it in Dev, and return its column-definition result. Results are limited to the queried schema and current-role visibility; an omitted table is not proof that it does not exist elsewhere.

Preserve original Archer IDs and handle UserList/GroupList separately when designing enrichment. Existing non-null CURATED_JSON update scope, source Content ID correctness, and downstream mapper consumption remain separate validation concerns; this discovery query changes none of them.
