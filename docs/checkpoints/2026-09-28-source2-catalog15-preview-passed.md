# Source Two Source-level Catalog preview passed — September 28, 2026

## Repository basis
Repository: theenduser009/Oscal-mapping-strategy.
Branch: simplify-metadata-boundary.
Head inspected before this documentation update: 6af5cc7b25ac89d6e95a78fd02bfce1747754494.

Files actually retrieved at that head:
- Mapping/sources_source_runtime.csv, header and 15 Catalog rules; blob 9f8c84d59fbbaa43ceb9cf638e07063511713276.
- notebooks/cells/07_mapper_orchestrator.py, complete; blob 78166e558cf99600d75e2995a7bae4144dad9534.
- docs/checkpoints/2026-09-17-source2-catalog-source-commit-readback-verified.md; blob 676dfe8d1655f1d9c93de434210bcf117f78b197.
- AGENTS.md, current text through line 120. Older Profile/SAP/AR instructions are historical, not a replacement for the current owner-selected Source Two task.

## New owner-provided Snowflake evidence
The September 28 screenshot shows one OSCAL_PIPELINE_REPORT group:
- source: source-two-source.
- model: CATALOG.
- release: oscal-lean-daily-v3.1.
- overall mode: PREVIEW.
- overall status: PREVIEW_COMPLETE.
- source_records: 148.
- nodes: 1697.
- edges: 1549.
- validation_passed: true.
- storage_verified: true.
- pre_write_validation_passed: true.
- writes_executed, persisted, committed and target_dml_attempted: false.
- route status: PREVIEW_PASSED_NO_TARGET_DML.
- temporary_cleanup: REMOVED.
- overall writes_executed and commit_attempted: false.

| Proposed changes | Inserts | Updates | Unchanged |
| --- | ---: | ---: | ---: |
| DIM | 148 | 0 | 1549 |
| FACT | 148 | 0 | 1401 |

This is owner-provided live PREVIEW evidence. It is not a database COMMIT or readback report. No private screenshot, record identifier or source payload is published here.

## Reconciliation with the retained mapping and earlier checkpoint
The September 17 accepted 14-rule Catalog batch contained 148 source records, 1549 nodes and 1401 edges. The current CSV has 15 approved Source-level Catalog rules, including SOURCE_TRACKING_ID -> catalog.metadata.props[] with PROPERTY_NAME=tracking-id, TRANSFORM_ID=direct and RULE_ID=catalog:SOURCE_TRACKING_ID:property. Its recorded readiness evidence was 148/148 populated integers.

The new preview proposes exactly 148 additional nodes and 148 additional edges, with all 1549 earlier candidate nodes and 1401 earlier candidate edges unchanged. This is consistent with one tracking-id property and its containment edge per source record. It is an aggregate reconciliation, not independent proof of the field identity/value for each inserted row. The screenshot does not show Cell Three's selected-rule count or per-field payloads; do not infer that those were separately inspected.

This supersedes the fresh Catalog preview-pending status in the September 28 Source Two resume discussion and project checkpoint. The older 14-rule COMMIT/readback remains historical acceptance for its batch; it does not certify this new additive load.

## Immediate next action
In the same unchanged notebook session, keep SELECTED_MODELS=("CATALOG",) and the shared CONFIG EXECUTE_WRITES=False. Change only Cell Seven's OSCAL_LOAD_MODE to "COMMIT" and run Cell Seven once, with other Catalog writers paused. Do not Run All, execute historical diagnostic cells below it, truncate tables, change mapping/registry, or select another model.

Code location: notebooks/cells/07_mapper_orchestrator.py on simplify-metadata-boundary.

The reviewed orchestrator rebuilds and previews the route from its retained inputs, then invokes the guarded loader with writes enabled internally. If the earlier session/inputs have changed, do not rely on stale contexts; rebuild the matching preview first.

Expected, not yet observed: source-two-source / CATALOG COMMITTED_AND_VERIFIED, 148 DIM and 148 FACT inserts with zero updates when the previewed state remains unchanged, and post-commit verification with zero remaining inserts/updates and 1697 DIM / 1549 FACT unchanged. An error or unknown transaction outcome requires report review, not an automatic retry.

## Scope and remaining QA
This checkpoint accepts the Source-level Catalog preview only. It does not establish completed Topic/Section/Sub-Section hierarchy, policies, or Control Standard relationships. Preserve the owner's September 28 clarification that Control Standard connects to both Topic and Policy; do not silently collapse those associations into one parent-child edge.

After the additive commit, inspect the committed readback and run separate Catalog whole-table structural QA and tracking-id source/value coverage before claiming this increment fully accepted. The shared loader's previously recorded whole-table orphan-detection limitation remains open; this preview does not fix it. The passed POAM rebuild is unrelated and needs no repeated run.

## Validation and changes in this update
Performed: read owner screenshot, current branch, relevant CSV, orchestrator, prior accepted Catalog checkpoint and repository instructions; compare the visible counts and statuses. Only this dated documentation file is added. No runtime/SQL/CSV/registry changes, no new synthetic tests or CI run, and no Snowflake operation by this chat.

State: current Source-level Catalog mapping published; new additive PREVIEW passed; additive COMMIT/readback pending; whole-table and field-level acceptance pending; wider Source Two hierarchy/relationship work remains separate.
