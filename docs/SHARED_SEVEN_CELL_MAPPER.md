# Shared seven-cell mapper: Source One → SSP and Assessment Results

Status: implemented; all 473 repository tests pass, including 65 focused multi-model checks. Split/combined notebook synchronization and whitespace checks pass. No shared-workflow Snowflake run or AR database load is accepted yet.

This is the owner-approved consolidation, not a new mapping batch. The seven existing cells now route Source One through a common graph builder and guarded persistence API. The accepted SSP mappings and 17 accepted AR fields are the parity baseline. The blocked 34-field AR candidate is not enabled.

## One run, two configured model routes

| Cell | Responsibility |
| --- | --- |
| 1 | Explicit source profiles, enabled models, mapping-file bindings, model policies and verified storage contracts. |
| 2 | Read each source separately; freeze a session-local snapshot reused by its model routes; read mapping rows, registry and approved lookups. |
| 3 | Compile source/model contexts; preserve original paths and Notes; report selected, excluded, deferred and blocked rows. |
| 4 | Shared value/identity helpers and approved model policies. Existing SSP rules and AR score rules live here, not in separate graph loops. |
| 5 | One registry traversal and one node/edge builder, with explicit source/model/parent context. |
| 6 | One guarded writer using the selected storage contract; logical graph-only validation when no target is verified. |
| 7 | Preflight all selected routes, build their graphs and report each outcome. Default PREVIEW. |

The registry does not supply missing business transformations. A new model reuses the engine but still needs approved mappings, registry identity/parent rules, any genuinely new reusable value policy, and a verified destination contract. The other six source tables have not been named or enabled by assumption.

A source profile can supply explicit `MODEL_STORAGE_CONTRACTS` overrides per model when its approved destination/provenance differs. A source must not borrow another source's verified identity contract. A shared mapping file requires explicit source-column/value binding; model selection is not a substitute for source selection.

Source snapshots use Snowpark [cache_result](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/1.35.0/snowpark/api/snowflake.snowpark.DataFrame.cache_result). These are temporary session tables, not writes to RAW data or OSCAL DIM/FACT. Keep the same session open; the input dictionaries retain the cache handles. Snapshots of different tables are captured separately, not as a cross-table transaction. Finish upstream ingestion before the notebook run.

## Next authorized run: preview only

1. Replace the existing seven Python cells with the corresponding seven sections of [the complete notebook](../notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py). This revision changes the interfaces across all seven, so do not mix old and new cells.
2. Keep Cell 1 `CONFIG["EXECUTE_WRITES"] = False` and Cell 7 `OSCAL_LOAD_MODE = "PREVIEW"`.
3. Run Cells 1–7 once, in order, using the existing approved mapping CSV. No additional standalone execution cell.
4. Share only the printed `OSCAL_PIPELINE_REPORT`; keep raw values and source IDs in Snowflake.

Expected successful preview: `PREVIEW_WITH_TARGET_CONTRACTS_PENDING`, with one Source One/SSP group and one Source One/Assessment Results group. SSP must pass its target-aware preview. AR must select exactly the accepted 17 fields and report `MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING`, `storage_verified=false`, and no writes. This validates AR graph structure, not saved AR data or full OSCAL schema conformance.

If routing or mapping contracts fail, the run stops with aggregate context and no target writes. Do not switch to COMMIT to bypass an error. Do not rerun the accepted full reload, pilots, or expanded standalone AR candidate.

## Persistence boundary

The actual SSP destination contract is configured from accepted physical-schema evidence. AR destination names and column types remain unverified; its contract is explicitly empty and cannot inherit SSP table names. Every selected route needs a verified storage contract before Cell 7 accepts COMMIT.

Future authorized commits use per-source/model transactions, not one distributed transaction across every model. The runner validates all routes first; a later commit failure preserves the reports of earlier committed groups and stops without an automatic retry. An unknown commit outcome or failed post-commit readback requires investigation.

The writer inserts new keys, updates changed business values, and preserves audit fields on unchanged rows. It verifies saved values, primary/foreign keys, UUID links and record-scoped hierarchy. Its second merge pass must make no changes. Obsolete keys inside selected records block the write; records absent from the input are preserved. No DELETE, TRUNCATE, guessed deletion rule, permanent backup creation or privilege changes are included.

## What remains unchanged or pending

- SSP full DEV reload remains accepted: 2,813 records, 70,102 DIM nodes, 67,289 FACT edges. No reload is needed for this code consolidation.
- The reduction from the old SSP tables remains unexplained. This release does not classify removed rows as duplicates or resolve that audit.
- AR remains 17 runtime-accepted mappings in memory, not persisted. Candidate, rejected and deferred rows remain excluded.
- Full SSP/AR document conformance is not established by graph parity or database key checks.
- Matillion raw-ID-to-CURATED_JSON conversion is upstream and unchanged.
- Daily deployment/scheduling is not performed here. Matillion should execute a reviewed, deployed notebook version; new data is not permission to download new code automatically.
