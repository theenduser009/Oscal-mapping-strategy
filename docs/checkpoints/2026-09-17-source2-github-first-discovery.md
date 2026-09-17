# Source 2 GitHub-first discovery checkpoint

Date: 2026-09-17
Repository: `theenduser009/Oscal-mapping-strategy`
Branch: `simplify-metadata-boundary`
Reviewed starting commit: `5379fcf4e3fadcd1cfb1fddc8f1f636e82aa70c2`
SQL publication commit: `614cee85b217b7f19f30b2169162984cd3e9e94c`

## Owner instruction and retained scope

The owner explicitly requested that each next runnable step be posted to GitHub. Publish the exact SQL/code on the working branch, verify the published contents, and give the owner its link before asking them to run it. Repository publication does not execute Snowflake or authorize unrelated database changes.

The current pilot remains Source 2 Source -> Catalog Metadata, beginning with the review candidates `SOURCE_NAME -> catalog.metadata.title` and `SOURCE_VERSION -> catalog.metadata.version`. Doubtful rows and the recorded SME questions remain pending. Source 1 is not being added to the Source 2 workbook. No second mapper or seven-cell rewrite is proposed.

## Published next action

[sql/SOURCE2_SOURCE_READ_ONLY_DISCOVERY.sql](../../sql/SOURCE2_SOURCE_READ_ONLY_DISCOVERY.sql)

This is one SELECT over `RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES` and `COLUMNS`. It lists visible candidate Source-level object names, table types and physical column definitions in `ES_ESC_GRC`. The literal name fragment is a discovery filter, not an approved source binding. This initial search location comes from the existing RAW environment; it does not prove that Source 2 is delivered there.

The query returns no business record values and executes no DDL, DML, temporary-table materialization, registry change, or mapper run. An empty result only means no matching object is visible in this search scope; it does not prove nonexistence elsewhere. A wide table and a RAW table must not be treated as interchangeable merely because their names are similar.

## Evidence and validation actually performed

Read the relevant project handoff and coverage sections, actual branch head, existing source configuration, Source mapping rows 2-3, SQL directory and the Source 2 source-binding/decision-register sections. No newer Source 2 live discovery result was established by this review.

The SQL file was created at the commit above and fetched back at that exact commit. Its returned Git blob `717ba5d0a989cb6676498455c5dd9b3b33ec53a6` matches the locally computed blob for the prepared 1,731-byte UTF-8 file. SHA-256: `b8c03b7b57c3d2e6f70f459e261b6185b2599ebb5e60e733e355af838ef7bd98`.

Validation is static review and GitHub readback only. No Snowflake execution or SQL-engine validation has been performed. No Source 2 runtime rows, source/model configuration, registry rows or DIM/FACT data have been implemented by this publication. No PREVIEW or database COMMIT/readback is claimed.

## Remaining gaps and next step

Run the published SELECT in a Snowflake SQL worksheet and return the result for review. Do not run the seven cells or repeat the Catalog table-creation script for this step. Review candidate table/column evidence before posting the focused one-record check for `SOURCE_NAME` and `SOURCE_VERSION`; do not guess a physical `_RAW` object, key column, source values or a duplicate-selection rule.

Catalog destination execution/definition evidence, registry readiness, model configuration and exact source JSON shapes remain separate gates. This checkpoint turns the previously requested manual sample into a GitHub-first discovery step; it does not supersede the Source 2 mapping decisions, deferred statuses or historical Source 1 evidence.

Reference: [SME_OPEN_QUESTIONS.md](../../questions/SME_OPEN_QUESTIONS.md), particularly S2-06 through S2-10. Keep business record values and private screenshots out of public GitHub.
