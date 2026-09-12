# Project continuity instructions

## Start here on every task

1. Read [docs/PROJECT_HANDOFF.md](docs/PROJECT_HANDOFF.md), then the current-action section of [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md).
2. Before advising a run or claiming acceptance, inspect the relevant current code and linked live run evidence. Check for newer owner-posted GitHub evidence when status is requested. A transcript, old README paragraph, local test pass, or prepared release is not proof of a successful database write.
3. Read [docs/ARCHITECTURE_CONTEXT.md](docs/ARCHITECTURE_CONTEXT.md) for design contracts and [docs/MAPPING_PROGRESS.md](docs/MAPPING_PROGRESS.md) for field-level scope. Historical run instructions do not override the dated current checkpoint.
4. If evidence is unavailable, state what is unverified; do not ask the owner to repeat context already stored here.

## Non-negotiable metadata-driven architecture

- The owner's prime requirement is metadata-driven execution, not merely metadata validation of hardcoded field rules.
- Excel/CSV governs approved source-to-target mappings; the registry governs hierarchy/identity; the reviewed deployment catalog supplies executable transforms, parameters, operators, source bindings and storage contracts.
- Active source/model routes must use the compiled metadata engine. Do not add source-field or model-name branches to the graph builder, writer or active dispatch.
- A new approved field or model using existing operators must work through metadata changes alone. Add reusable Python only for genuinely new behavior, with tests and explicit scope.
- Preserve one public model selector and the same seven cells. Maintain code only in notebooks/cells; generate V2 split and combined notebook with tools/sync_notebook_cells.py and verify --check. This is a developer packaging tool, not an extra Snowflake cell.
- Prove accepted SSP and AR17 output parity and metadata-only new-field/third-model execution before publishing changes. Historical compatibility engines live only in tests/fixtures/legacy_cell4_pre_declarative.py; never import that fixture into production or edit it to make parity pass.
- The single compiled plan is generated from approved rows, registry and catalog supplements. The catalog is not automatically generated from Excel; do not claim it is. Prefer executable mapping columns for new rules, and reject conflicting duplicated metadata rather than silently choosing a winner.
- Blank or ambiguous metadata is not approval. Keep rejected/deferred rows separate; never silently fall back from partial executable metadata to an older rule.

## Keep these boundaries explicit

- Matillion converts raw field-ID JSON to the Archer RAW table's CURATED_JSON column. The OSCAL notebook reads that column; it does not perform that upstream conversion.
- Cells 1-5 configure/read/normalize/transform/build. Cell 6 already defines validation, insert/update MERGE loading, and load verification. Cell 7 orchestrates them. Do not say the notebook has no loader.
- Normal Cells 1-7 runs used writes disabled. The separate full DEV reload was accepted; the existing Cells 6-7 daily persistence path is not yet end-to-end accepted.
- User notebook cell numbers after seven are session-local. Identify a separate cell by its file and purpose, not by assuming every Cell 8 is the same program.
- Registry governs hierarchy and identity. Excel/CSV source field, model, exact element path, mapping type and Notes govern field mappings. Registry presence is not proof of complete mapping.
- Separate implemented, candidate-only, runtime-accepted in memory, persisted/read-back verified, deferred, blocked, and full OSCAL conformance. Do not turn one status into another.

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
