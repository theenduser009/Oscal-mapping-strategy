# Project continuity instructions

## Start here on every task

1. Read [docs/PROJECT_HANDOFF.md](docs/PROJECT_HANDOFF.md), then the current-action section of [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md).
2. Before advising a run or claiming acceptance, inspect the relevant current code and linked live run evidence. Check for newer owner-posted GitHub evidence when status is requested. A transcript, old README paragraph, local test pass, or prepared release is not proof of a successful database write.
3. Read [docs/ARCHITECTURE_CONTEXT.md](docs/ARCHITECTURE_CONTEXT.md) for design contracts and [docs/MAPPING_PROGRESS.md](docs/MAPPING_PROGRESS.md) for field-level scope. Historical run instructions do not override the dated current checkpoint.
4. If evidence is unavailable, state what is unverified; do not ask the owner to repeat context already stored here.

## Active scope - AR32 metadata extension; POAM preview accepted

The owner requested the remaining AR mapping changes discussed in the other
chat. Enable the exact unprefixed CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD and
CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD fields as scalar-score observations at
assessment-results.results[].observations[]. This supersedes only the previous
source-name deferral for those two rows. Preserve the existing 30 AR rows and
their IDs, SSP sensitivity, and the POAMS reference mapping. Thirty-two AR
rows are enabled and thirteen remain deferred. Original spreadsheet path/Notes
are provenance; approved RUNTIME_TARGET_PATH contains one exact full path.
No runtime, registry or table changes accompany this extension.
Follow docs/AR_NEXT_RUN.md for a fresh AR32 preview; added-field live coverage
is not accepted from synthetic tests or the previous aggregate AR load.
Relevant private excerpts do not contain the new exact threshold fields;
report that gap and never invent values or publish private source data.

The owner-posted POAM preview is accepted in main commit
f5677398faf9da2c9919e6fa29d0db0264816d4e: 2,813 source records, 2,821 DIM
inserts, eight FACT inserts, no updates, all validation/storage checks passed,
and no target writes or commit. The owner was given the Cell Seven COMMIT step;
its actual outcome remains pending verification. Do not repeat registry or
schema setup, ask table names again, or claim POAM persisted without the report.
Keep the same Source One POAMS reference scope and package-scoped UUIDs.

The existing SSP and AR mapped-graph COMMIT/readback acceptance stands.
AR tables are populated; no replacement DDL or unchanged rerun is requested.
This material update is CSV-only; all seven runtime cells remain unchanged.

## Latest shared AR COMMIT accepted

The owner-posted AR COMMIT is COMMITTED_AND_VERIFIED for 2,813 records,
73,189 DIM inserts and 70,376 FACT inserts. All validation/write/commit flags
passed and committed readback matched every inserted row; cleanup is REMOVED.
See docs/checkpoints/2026-09-13-assessment-results-commit-completed-and-verified.md.
The prior AR schema mismatch is superseded by this successful storage run.
AR tables are now populated. Do not rerun sql/ddl, recreate tables, reset the
registry or request another unchanged run. Retain the accepted SSP checkpoint.
Advance the owner's next POA&M work without adding a separate runtime engine.
Thirty AR metadata rows remain enabled and fifteen deferred. Aggregate graph
persistence does not establish every field's populated coverage or full OSCAL
conformance. Continue using relevant private screenshot excerpts alongside
synthetic tests without publishing source values.

## Non-negotiable metadata-driven architecture

- Current code is JSON-free. Mapping/ARCHER_OSCAL_MAPPINGS.csv maintains the
  147 reviewed occurrences, existing guard and three existing support rules.
  These support rows are not new Excel approvals. Cell One holds deployment
  settings; the original nine registry columns own hierarchy and identity.
  Only OPERATOR, UUID_POLICY and REQUIRED_MEMBERS are active sparse execution
  extensions. No field-specific execution branch or duplicate catalog is
  allowed.
- The earlier eighteen-column registry design is superseded. The lean setup SQL
  adds or verifies only the three active extension columns and never drops any
  legacy DEV columns. Registry setup and cleanup must not be repeated: the
  owner posted an accepted live SSP PREVIEW, recorded in
  docs/checkpoints/2026-09-13-oscal-lean-daily-v3.1-preview-accepted.md.
  The completed live value reconciliation is recorded in
  docs/checkpoints/2026-09-13-ssp-read-only-value-reconciliation.md: all 36 impact
  nodes are case-only low-to-Low changes, and 1,958 removed sensitivity members
  match direct SECURITY_CATEGORY text after diagnostic trimming. The documented
  Direct CSV mapping and corrected lowercase FIPS lookup are implemented. The
  corrected live SSP PREVIEW is accepted in
  docs/checkpoints/2026-09-13-ssp-preview-no-target-changes.md, posted in main
  commit 9d08e8978cbb5894239b688743880b75accadeea: 2,813 source records,
  70,102 nodes and 67,289 edges, with zero DIM/FACT inserts or updates. All
  validation/storage checks passed; that preview's write/commit flags are false.
  The subsequent live SSP COMMIT is accepted in
  docs/checkpoints/2026-09-13-ssp-commit-completed-and-verified.md, posted in main
  commit a53c16aff842cde044f7bda2efb64a2198ac3117. It reports
  COMMITTED_AND_VERIFIED for the same counts, with target DML attempted and
  writes/persisted/committed true. Expected changes and committed readback both
  show zero inserts/updates; all rows are unchanged and cleanup is REMOVED.
  This accepts the live no-change commit and readback, superseding the earlier
  daily-COMMIT-pending status. It does not prove changed-row persistence.
  Retain this accepted checkpoint; do not repeat an unchanged run, diagnostics,
  registry work or the full reload. Use the existing seven cells for the next
  intended SSP run and record changed-row counts/readback when source changes
  arrive. Keep shared EXECUTE_WRITES false; Cell Seven selects PREVIEW/COMMIT.
  Direct sensitivity preserves source text; CIA mappings normalize recognized
  low/moderate/high values but retain explicitly approved legacy strings.
  Changed-row acceptance, AR storage, deployment/scheduling and full OSCAL/FIPS
  conformance remain separate. Run tests/lean, not the retired private-API suite.
- The deployed JSON file is retired. Historical settings and mappings are
  frozen under tests/fixtures for independent parity only, never uploaded or
  loaded in production. Required title/version and AR17 gates remain preserved.
- No owner approval is pending for this scoped implementation. Do not ask the
  owner to reconstruct history or upload the original CSV again as a blanket
  blocker. The reviewed compilation is partial; unseen or blank-path mappings
  remain unresolved.

- The owner's prime requirement is metadata-driven execution, not merely metadata validation of hardcoded field rules.
- Excel/CSV governs approved source-to-target mappings; the registry governs hierarchy/identity; explicit CSV execution columns select reusable transforms; registry columns select operators/assembly policies; Cell One supplies source bindings and verified storage settings.
- Active source/model routes must use the compiled metadata engine. Do not add source-field or model-name branches to the graph builder, writer or active dispatch.
- A new approved field or model using existing operators must work through metadata changes alone. Add reusable Python only for genuinely new behavior, with tests and explicit scope.
- Preserve one public model selector and the same seven cells. Maintain code only in notebooks/cells; generate V2 split and combined notebook with tools/sync_notebook_cells.py and verify --check. This is a developer packaging tool, not an extra Snowflake cell.
- Prove accepted SSP and AR17 output parity and metadata-only new-field/third-model execution before publishing changes. Historical compatibility engines live only in tests/fixtures/legacy_cell4_pre_declarative.py; never import that fixture into production or edit it to make parity pass.
- The single compiled plan is generated from approved CSV rows, versioned registry columns and visible deployment settings. Required source values must survive conversion. Reject conflicting duplicated metadata rather than silently choosing a winner.
- Blank or ambiguous metadata is not approval. Keep rejected/deferred rows separate; never silently fall back from partial executable metadata to an older rule.
- Resolve ownership from active registry paths before executing mappings. Known label/path contradictions block; unknown display labels do not override registered paths. Configured placeholders stay deferred, including TBD rows with real SSP paths. Recognition of another model never enables its execution or storage. Do not reinstate a global unknown-display-label gate over the full workbook.

## Keep these boundaries explicit

- Matillion converts raw field-ID JSON to the Archer RAW table's CURATED_JSON column. The OSCAL notebook reads that column; it does not perform that upstream conversion.
- Cells 1-5 configure/read/normalize/transform/build. Cell 6 already defines validation, insert/update MERGE loading, and load verification. Cell 7 orchestrates them. Do not say the notebook has no loader.
- The live SSP no-change COMMIT and post-commit readback are accepted: 2,813 records, 70,102 nodes and 67,289 edges. Changed-row acceptance is separate; PREVIEW_COMPLETE alone is not a write.
- User notebook cell numbers after seven are session-local. Identify a separate cell by its file and purpose, not by assuming every Cell 8 is the same program.
- Registry governs hierarchy and identity. Excel/CSV source field, model, exact element path, mapping type and Notes govern field mappings. Registry presence is not proof of complete mapping.
- Separate implemented, candidate-only, runtime-accepted in memory, persisted/read-back verified, deferred, blocked, and full OSCAL conformance. Do not turn one status into another.

## Owner-provided example testing

For relevant mapping changes, include tests using readable examples from the
owner's Google Drive screenshots alongside synthetic regression tests. The
private local transcriptions are in the workspace's private/curated-json
folder outside this repository. Exercise only explicitly transcribed values;
never fill omitted screenshot rows or claim a complete dataset was executed.
If the relevant example is absent or unreadable, state that test gap.
Keep screenshots, source values and detailed results out of GitHub and release
packages; publish only aggregate outcomes. Use synthetic source-record IDs
when isolating a source excerpt.

## Work and communication rules

- Preserve accepted mappings and user changes. Inspect existing functions before building another loader or diagnostic.
- State the model, exact OSCAL path, Archer field, and transformation for each new mapping handoff. Follow approved Excel Notes; flag missing/conflicting rules rather than inventing paths, values, namespaces or references.
- Keep responses concise, in English. Ignore background speech the owner identifies as unrelated.
- Do not request unchanged reruns of accepted work. For a necessary run, give one exact file, SQL versus Python, required session inputs, mode, and expected completion signal.
- Keep normal writes disabled until the daily path is explicitly ready and authorized. A past DEV reload or waived backup is not blanket permission for future writes, truncation, schema changes, privilege changes or production actions.
- Unknown commit outcome or failed post-commit readback requires inspection, not an automatic retry. Preserve PK/FK, UUID, payload and record-scoped hierarchy checks.
- Retain the unexplained old-versus-new SSP row difference until evidence reconciles it. Do not call the removed rows duplicates, stale or superseded without proof.
- Keep raw payloads, source identifiers and credentials out of published status; use aggregate evidence.

## Maintain continuity

After a material accepted run, failure, user decision or change of next action, update PROJECT_HANDOFF and the current-action section of CURRENT_STATUS; update the mapping register when field statuses change. Link the exact evidence and preserve historical reports. Record what changed, what is accepted, what is pending/deferred, why, and the single next action. Verify remote publication before saying a change is on GitHub.

These files provide project continuity; they do not preserve a Snowflake session or guarantee memory in unrelated chats. No mapper/database change is authorized merely by reading them.
