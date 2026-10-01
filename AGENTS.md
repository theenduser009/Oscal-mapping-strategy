# Project continuity instructions

Updated October 1, 2026. Current scope: publication and release validation of the matching contribution-aware seven-cell candidate on `simplify-metadata-boundary`.

## Start every task with actual repository context

1. Read `docs/PROJECT_HANDOFF.md` and `docs/CURRENT_STATUS.md`, then the latest dated checkpoint relevant to the task. In the OSCAL ChatGPT Project, read `00_START_HERE.txt` first, but treat its September 14 code/counts as a dated snapshot.
2. Verify the actual branch HEAD and relevant source files before changes. Recheck capabilities rather than assuming a database connection or local files. Context is not a live Snowflake session.
3. Use the mapping CSV for exact source fields, approved paths, transforms, and null policy; registry for hierarchy/identity; Cell 1 for source/model/storage bindings. Preserve all accepted field names, statuses, unresolved questions, and native identity seeds.
4. Do not ask the owner to reconstruct context already stored here. The coverage/historical-support supplement identifies gaps: partial screenshot-derived review Excel is not the original complete workbook; historical collection-only registry rows are not a current full export.

## Current implementation and evidence

The seven maintained runtime files are in `notebooks/cells`. Generated copies are in `notebooks/cells_v2` and `notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`. Matching releases are `lean-csv-registry-v5-lineage` and `oscal-lean-daily-v3.2-lineage`. See `docs/checkpoints/2026-10-01-seven-cells-published-to-github.md` and its manifest for exact content hashes.

All seven match the delivered locally tested October 1 candidate. Publication is not native execution or production approval. The fresh local 126-test pass uses synthetic inputs and a limited Python/SQLite adapter. Do not call it full repository CI, official Snowpark compatibility, full production mapping coverage, or complete OSCAL conformance.

## Owner decisions

- Keep one universal metadata-driven mapper and seven cells. No per-field or per-model special-case lineage branches, duplicate mapping rows, new lineage fact table, or manual lineage switches.
- Native approved values stay native. Approved non-native business values use the approved props owner. Needed source attribution uses grouped props from actual surviving contributions, with exact owner/child context. Unknown/TBD/DEFERRED/EXCLUDED fields are not automatically put into props.
- A direct mapping is not automatically self-describing. Unique one-to-one attribution relies on the matching versioned mapping. Namespace approval and availability of mapping definitions to exported-document consumers remain unresolved release requirements.
- Keep FIPS/Legacy classification separate; never invent a crosswalk or precedence. Preserve actual JSON null for approved null-preserving warehouse mappings; absent keys remain absent. A warehouse null does not prove schema-valid exported OSCAL.
- Do not add guessed hrefs, source aliases, field display names, group resolution, business-unit equivalences, or registry entries merely to fill gaps.

## Writes, tests, and publication

Keep shared `CONFIG["EXECUTE_WRITES"]` false. Cell 7 selects PREVIEW/COMMIT; preview can use temporary tables but does not write target DIM/FACT. Transactions are per route, not globally atomic across models. Preserve schema/PK/FK/UUID, record/instance ownership, rollback, readback, and obsolete-row guards. Unknown commit outcome or failed post-commit readback means inspect; do not automatically retry. No truncation, reset, rekey, registry mutation, or new database write is authorized by a GitHub publication request.

Before recommending another SAP/POAM or other owner run, check newer owner-provided evidence. Historical AR30 does not prove later AR32, and historical SSP acceptance does not prove later daily-loss or lineage. A setup script is not proof it executed. Respect current release blockers.

Maintain source only in `notebooks/cells`; run the existing `tools/sync_notebook_cells.py` and `--check` for copies. Keep tests outside the production seven cells. Freeze expected behavior independently, preserve failures, and separate local fixtures from actual source/run evidence. Do not replace failed production checks with success stubs or label changed assertions as an unchanged test run.

## Durable status and privacy

For every material update, update CURRENT_STATUS and PROJECT_HANDOFF and add a dated checkpoint identifying inspected/published revision, changed files, validation actually performed, remaining gaps, and one next action. Publish authorized code/deliverables in the repository, then verify the remote tree/file content before claiming completion. Keep artifacts attached to the OSCAL Project when supported. Do not claim a Source was updated without an actual supported write.

Keep current docs concise and link dated history. Refresh source links when code changes and mapping inventories only when mappings change. Do not present old run instructions or old line counts as current. Do not delete unrelated empty files or placeholders without inspecting purpose and dependencies.

Never publish private source rows, screenshots, credentials, or identifying personal/company narrative. Existing operational table/field identifiers in the approved code are preserved; test examples must be synthetic. Keep unknown exception payloads out of public logs.

The full previous instruction/history file remains available [at the pre-publication revision](https://github.com/theenduser009/Oscal-mapping-strategy/blob/94e41f8896d73cd6ed191c6030efb7f31c7d206b/AGENTS.md). Its historical active Profile/SAP sections do not override this current scope.
