# Project handoff - read this before resuming

## Current action - field rules moved to the mapping CSV

No owner approval is pending. The owner reviewed the compilation and authorized
the simplification; earlier approval prompts were stale.

Executable field rules now live in [ARCHER_OSCAL_MAPPINGS.csv](../Mapping/ARCHER_OSCAL_MAPPINGS.csv),
with [readable columns](../Mapping/MAPPING_COLUMNS.md). The 147 original source
occurrences retain exact field names, labels, paths, types, Notes and provenance.
One additional, explicitly labelled existing populated-value guard is preserved.
There are 60 approved rules, one guard, 85 deferred rows and two excluded helpers.
Compilation review did not approve unresolved mappings or unseen source rows.

The deployed settings no longer contain field rules, source-field path rewrites
or exclusions. They still contain structural/source/lookup/destination settings
that the current registry does not fully hold. **The JSON dependency is not yet
removed.** The old input compatibility branch also remains in Cell Three.
This is the completed field-rule migration, not the final catalog-free release.

All 593 local tests pass. Regression checks preserve all 61 execution contracts, the accepted SSP
graph fingerprint, all eleven CIA mappings and AR17 output. Original Notes
conflicts and accepted/deferred boundaries remain unchanged. Source input now
preserves UTF-8 Notes and literal N/A labels. V2 and combined notebook pages are
generated from the maintained cells. No new Snowflake run has been accepted.

**Next:** retire the older field-rule input branch and consolidate the remaining
structural settings without introducing guessed identities or a second
hand-maintained mapping catalog. No additional owner approval is needed for the
authorized refactor. No notebook rerun, normal write, reload or registry mutation
is requested during that work. Normal writes remain disabled.

Earlier SSP persisted scope, AR17 in-memory-only acceptance and the unexplained
old-row reduction remain unchanged. Prior run instructions and requests for
the full CSV or repeated approval below are superseded.

## Current action - reviewed compilation; simplify accepted rules

The owner reviewed the [147-entry compiled workbook](../Mapping/REVIEW.md),
confirmed the blank-path control entries, and authorized continuing. The eight
source documents are partial transcriptions, not the full original 608-row sheet.
Compilation review does not approve new paths or rules. Do not request the
original CSV again as a blanket blocker; use the supplied documents and existing
accepted evidence, leaving unseen and unresolved rows out of scope.

The [interim cleanup](checkpoints/2026-09-12-mapper-simplification-audit.md) removes
Cell Three's unused metadata upload, three unused helpers and one ignored
argument. **567 local tests pass**, including accepted SSP/AR parity and whole-cell
no-upload regressions. V2 and combined pages are synchronized. The JSON catalog
is still required; this is not the final simplified release or live acceptance.

**Next:** migrate the known accepted rules to readable mapping metadata, preserve
accepted/deferred boundaries and reconcile specific Notes conflicts. All accepted
SSP source fields, including the eleven CIA fields, and all seventeen accepted AR
fields are present. The missing reject-populated guard remains preserved. Do not
replace accepted CIA rules with the draft's conflicting shared note.

No notebook rerun, new field approval, registry change or database write is
requested. Normal writes remain disabled. Prior persisted SSP scope, AR17
in-memory acceptance and the unexplained old-row reduction remain unchanged.
Earlier run advice and requests for the complete CSV below are superseded.

Last reconciled: **2026-09-11**. Purpose: durable context requested by the owner, so the cell roles, completed work and pending decisions do not need to be retold.

## Resume here

**Latest owner direction and current blocker:** simplify the existing seven cells
against the original design, using one maintained Excel/CSV mapping source and
the registry; do not add another duplicate JSON contract. The current JSON
dependency is still present, so do not claim the requested redesign is complete.
[Current simplification audit](checkpoints/2026-09-12-mapper-simplification-audit.md)
records the original README revisions and the missing complete 608-row CSV.
Request that actual notebook mapping file with full Notes before guessing a
catalog-free rule translation. Cell Three's unused metadata upload is removed;
three dead helpers and one ignored argument are removed. All 567 local tests
pass, and all eleven CIA routes match accepted behavior. No live acceptance or
database changes. **No rerun is requested; the older preview advice below is
superseded while the final mapping-input reconciliation is pending.**

**Prime requirement: metadata-driven execution, not model-specific Python mapping branches.** The owner authorized all necessary changes. The active seven-cell workflow now loads a reviewed metadata catalog and compiles Excel/CSV mappings plus registry ownership into reusable operators. A new approved field/model using supported behavior does not require field-specific Python. One model selector remains.

Cell One reads [mapper_contract.v1.json](../notebooks/metadata/mapper_contract.v1.json); Cell Three compiles approved executable rows; Cell Four runs generic transforms/operators. Cells Five through Seven reuse the existing common graph/writer/runner. The historical SSP/AR engines are now removed from the deployed cells and frozen under tests only. Cell Four requires a compiled metadata context; it cannot fall back to the older mapper.

All **564 local tests pass**. Independent parity checks match the accepted SSP fixture exactly and the AR17 standalone business output. New-field and third-model tests run through the actual shared builder with legacy classifiers unavailable. The registry-first tests reconstruct the complete posted 459-row label pattern and a 608-row mixed workbook. These are local regressions, not new live counts. Cardinality, required/null policy and simple typed/enum/range validation are declarative constraints. Cell Four remains roughly half its previous size.

**The live routing cause is now evidenced and corrected in code.** [Posted diagnostic](OSCAL_PIPELINE_ROUTING_FAILURE_2026-09-12.md#unknown-model-label-diagnostic) accounts for all 459 blockers: 416 TBD, 37 N/A - Calculated, one Multiple - See Notes, two Profile and three Security Assessment Plan. The old label-first gate incorrectly blocked placeholders and other-model rows across the workbook. The 58 missing-approval rows plus two explicitly deferred rows explain the existing 60 deferred total; the checkpoint's severity label for those 58 is inconsistent with the counts.

Cell Three now derives model ownership dynamically from all active registry paths and uses labels only to detect known conflicts. Placeholder decisions are catalog metadata, not field/model-specific Python fixes. Unregistered, unreviewed rows remain deferred; unknown ownership on executable approved rows still blocks. No new model or field is enabled, no target path is translated, and the TBD row with a real SSP security-impact-level path remains unresolved.

**Next: one changed-code PREVIEW, not a repeat diagnostic or DEV reload.** Replace the uploaded catalog with the updated mapper_contract.v1.json and replace only Cell Three with the updated V2 file. In the same active session with existing Cells Two/Four/Five/Six and their inputs, run Cell One (reload catalog), then Cell Three, then Cell Seven with PREVIEW. Keep the user's model selection and writes-disabled configuration. If the session has ended, run the matching seven-cell set in order instead. Post the complete printed pipeline report. Live acceptance remains pending; do not claim a local reconstruction proves new live counts or request COMMIT.

Maintain code once in notebooks/cells and generate V2/combined pages with tools/sync_notebook_cells.py. The owner still uses the same seven V2 pages, no extra runtime dependency or cell. Only Cell Three and the catalog routing metadata change in this correction; transforms, graph builder and writer are unchanged. The executable plan is generated from the sheet/registry/catalog; the catalog itself is not automatically synchronized from Excel. [Metadata contract and limitations](../notebooks/metadata/README.md).

**The full SSP DEV reload stays accepted; do not rerun it.** Source One SSP and the 17 previously accepted AR mappings are preserved. AR target names/types remain unverified, so AR cannot COMMIT or inherit SSP destinations. Other sources/models and candidate/rejected/deferred AR rows are not enabled by assumption.

No database write, registry change, Matillion execution or new mapping acceptance occurred in this refactor. The unexplained old-versus-new SSP row reduction remains unresolved.

## The pipeline and every cell's responsibility

| Step | Existing file / component | What it does |
| --- | --- | --- |
| Upstream Matillion | [Null-preserving UPDATE](../sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql) | Converts raw field IDs to field names and writes CURATED_JSON on the Archer RAW table. Retains named nulls. Not part of notebook Cells 1-7. |
| Cell 1 | [Configuration](../notebooks/cells/01_initialization_and_configuration.py) | Loads reviewed metadata for source/model bindings, executable rules and verified storage contracts; one model selector. Baseline EXECUTE_WRITES is false and initialization rejects true. |
| Cell 2 | [Inputs](../notebooks/cells/02_source_mapping_registry_inputs.py) | Reads source-local CONTENT_ID and CURATED_JSON snapshots, each bound mapping artifact, registry and approved lookups; model routes reuse the same source snapshot. Resolves duplicate source IDs by the configured technical ordering, not arbitrary deduplication. |
| Cell 3 | [Mapping contract](../notebooks/cells/03_canonical_mapping_contract.py) | Compiles isolated source/model contexts, preserving paths/Notes and reporting selected, excluded, deferred and blocked rows. |
| Cell 4 | [Helpers](../notebooks/cells/04_parsing_transform_payload_helpers.py) | Shared helpers/operators execute the compiled plan; legacy field-specific engines are test fixtures only. |
| Cell 5 | [Graph builder](../notebooks/cells/05_registry_graph_builder.py) | One generic graph loop builds nodes/edges for each explicit source/model context using the registry. Does not invent populated collections. |
| Cell 6 | [Validation and guarded loader](../notebooks/cells/06_validation_and_guarded_loader.py) | Shared validate_and_load_oscal and verify_oscal_load use an immutable verified storage contract; targetless AR gets logical graph validation only. Conditional upserts, transaction/readback and obsolete-row blocking remain. |
| Cell 7 | [Orchestrator](../notebooks/cells/07_mapper_orchestrator.py) | Preflights all source/model routes, builds each through the shared engine and emits OSCAL_PIPELINE_REPORT. MODEL_GRAPHS retains scoped graphs; compatibility outputs refer only to the configured default route. |
| Owner's current Cell 8 | [Separate full DEV reload](../notebooks/persistence/RELOAD_ALL_SSP_DEV.py) | Replaces both entire SSP DEV target tables from the accepted graph. This was the accepted one-time full reload, not the finished daily loader. |

The maintained source is [notebooks/cells](../notebooks/cells/README.md); the [combined notebook](../notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py) and V2 pages are generated from it. Separate AR, assembly, diagnostic and persistence cells are identified by filename, not a fixed notebook number.

A new Python cell in the same Snowflake session can reuse in-memory inputs. A new Snowflake session cannot. Rebuilding inputs may be necessary for a future authorized run, but the chat history alone does not keep dataframes or temporary snapshots alive.

## Accepted evidence — preserve, do not repeat

| Milestone | Verified scope | Evidence |
| --- | --- | --- |
| SSP mapped graph and mapped-scope assembly | 2,813 source records/documents; 70,102 nodes / 67,289 edges in the accepted graph before full reload. Not full-model/schema completeness. | [Graph checkpoint](checkpoints/2026-09-10_ssp_date_property_run_accepted.md), [assembly checkpoint](checkpoints/2026-09-10_ssp_mapped_scope_assembly_accepted.md) |
| One-record DEV reconciliation | Replacement committed; rollback rehearsal, saved values and keys, repeat-write checks passed. No permanent backup under owner-approved DEV scope. | [One-record live result](SSP_ONE_RECORD_RECONCILIATION.md#live-transaction-only-reconciliation-result--2026-09-11) |
| Ten additional DEV records | Committed/read-back verified; 289 DIM / 279 FACT rows; repeat inserts zero; first record unchanged. Eleven records proved before full reload. | [Ten-record checkpoint](SSP_TEN_RECORD_DEV_BATCH_2026-09-11.md) |
| Full SSP DEV reload | COMMIT; PERSISTED true; 2,813 source records, 70,102 DIM / 67,289 FACT rows. Saved graph, payload/key and hierarchy checks passed; second pass inserted zero rows. | [Full reload live checkpoint](SSP_FULL_DEV_RELOAD_2026-09-11.md) |
| AR score mapping | 17 mappings accepted in memory across 2,813 source records; no database writes. The later 34-field candidate is not accepted. | [AR accepted run and inventory](ASSESSMENT_RESULTS_START_HERE.md) |
| Upstream null correction preview | Owner confirmed complete conversion preview preserves expected field names and values, including nulls. Actual Matillion UPDATE/pipeline execution is not independently verified. | [Current incident checkpoint](CURRENT_STATUS.md#active-incident---matillion-raw-to-curated-null-field-loss), [fix explanation](RAW_CURATED_NULL_FIELD_FIX.md) |

The full reload used transaction-only recovery and no permanent backup. It replaced the earlier eleven records too. Local tests supported publication; the owner-posted live report, not those tests, establishes persistence acceptance.

## Row-count reduction — still unexplained

| Table | Before full reload | After full reload | Fewer rows |
| --- | ---: | ---: | ---: |
| SSP DIM elements | 126,453 | 70,102 | 56,351 |
| SSP FACT dependencies | 122,939 | 67,289 | 55,650 |

The loaded tables exactly matched the accepted new graph. That does **not** establish why every old row disappeared, whether every old source record was retained, or whether the old rows were duplicates/stale. Element counts are not source-record counts. Do not infer an old root count by subtracting edges from nodes.

Next audit, when requested: compare old and new source-record/path coverage read-only, reporting only differences. The reload created temporary before-snapshots; whether the same Snowflake session remains open is not confirmed. Do not promise those snapshots survive a restart or that durable recovery exists. Leave the accepted targets unchanged while this is unresolved.

## Daily SSP loading — existing code and remaining work

The owner needs a repeatable daily process, not a fresh one-off cell for each run.

**Implemented in this revision:**

- The existing Cell 6 public loader APIs remain. Proven binary/UUID/VARIANT projection and live schema checks are integrated.
- Unique temporary staging is created before the shared DIM/FACT transaction. Staging is not dependent on an earlier pilot cell.
- Same-key business changes update; new keys insert. The three audit columns do not trigger changes, and unchanged rows retain their existing stored fields.
- Preflight checks obsolete keys, provenance, PK/FK/UUID links, graph hierarchy and selected source count. Obsolete in-scope rows block the whole write; absent input records are preserved.
- Both MERGEs run twice inside one transaction; the second pass must report zero inserts and zero updates. Exact business values, updated audit fields, unchanged stored values and graph links are checked before commit and again afterward.
- Rollback, unknown commit and failed post-commit readback have different reports. No automatic retry or false success.
- Cell 7 checks for the updated Cell 6 function, rejects missing source IDs before stringification, computes coverage before writes, and clears stale run outputs.
- Cell 1 stays unchanged with global EXECUTE_WRITES false. Cell 7's explicit SSP_LOAD_MODE defaults to PREVIEW and changes only a per-run configuration copy.

**Still pending:** live Snowflake preview and approved commit/readback acceptance; automatic obsolete-node/source-deletion policy; operational daily scheduling and production review. Local tests include independently reconstructed logical inputs and audit-only reruns, but do not prove Snowflake compilation or actual daily-source behavior. An all-unchanged live run would not prove a changed-row write was exercised.

No extra execution cell was added. See [the daily-loader guide](SSP_DAILY_LOADING.md). Keep concurrent target writers paused for an approved commit; snapshot comparisons do not establish an exclusive lock.

Idempotent means the same source and mapping rules yield the same business data and deterministic keys without duplicates. Audit run IDs/timestamps may have a separate policy. A complete validated full refresh can also be idempotent; daily truncation is not required. The accepted DEV full-reload cell uses snapshot-specific acceptance checks and is not a ready-to-schedule daily job.

## SSP field mapping scope and parked work

The register records **43 distinct Archer fields / 44 implemented source-to-target mappings**: 11 metadata, 27 system-characteristics, 6 component-reference routes. This is an implementation count, not 44 individually complete/schema-valid mappings or all workbook rows.

- Metadata and all six approved component-reference routes have accepted mapped-scope evidence.
- System-characteristics work is implemented with exceptions. PTA helper is still skipped despite Notes describing a custom property; its rule requires reconciliation. Do not confuse it with the package-type helper, which stays excluded as transient.
- Package type's current property name differs from the Notes example; naming correction is parked.
- Recommended security category has an “All Nulls” rule and no approved populated-value conversion. Other security-category row questions remain in the register.
- Control Implementation is parked: its proposed property placement/rule has not been approved as a standard-conforming mapping. Do not invent a custom extension or redirect its path.
- The six approved System Implementation rows stop at components[]. A separate component status mapping is not evidenced by those Excel rows.
- Missing source descriptions, unproved hardware hydration and incomplete/absent CIA data remain explicit gaps. Generated support nodes do not add completed Excel rows.

See [SSP done and next](SSP_DONE_AND_NEXT.md), [mapping register](MAPPING_PROGRESS.md) and [pinned conformance contract](OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md). SSP model conformance is pinned to 1.2.3; mapped-scope DEV persistence is not certification of a full schema-valid SSP.

## AR and other models

There are **45 AR row occurrences / 44 distinct Archer fields** in the posted transcription, not the complete original workbook:

- 17 runtime-accepted in memory.
- 15 additional implemented candidate-only rows.
- 2 parked rejected fields: Risk Acceptance (one reference-shaped object), Risk Assessment Report (99 multi-number lists). Their meaning/conversion must not be guessed.
- 7 workflow audit properties deferred by the owner.
- 2 duplicate Average Security Compliance Score occurrences deferred.
- 2 under review: Total Package Inherent Risk and Findings reference/UUID association.

The accepted pattern is one observation per populated source field, with a named inline property. The required root/result/observation registry entries were checked; inline properties did not require extra registry nodes. The published expanded AR cell remains a blocked candidate, not a safe replacement for the accepted 17-field write scope.

No AR database load is accepted. Before AR persistence, confirm actual AR target schemas and reuse the shared writer for accepted mappings only; never repoint an SSP full-reload cell to AR. POA&M and other models have not been completed by this work.

## Fixed identities and targets

- Source: RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
- Registry: RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
- DIM: RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
- FACT: RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY
- Source identity: Archer CONTENT_ID; model SSP; version v1_registry_path_instance.
- Physical PK/FK hashes: BINARY(16). Physical UUID columns: VARCHAR(32). DIM METADATA_JSON: VARIANT. Load timestamps: TIMESTAMP_TZ(9).

Use current schema evidence before changes; these facts do not grant permissions. The registry owns hierarchy/identity and Excel owns approved field mapping. Neither registry population nor graph integrity alone proves every Excel row is complete.

## Past failures and current recovery boundary

Schema-type rejection, temporary staging failure, extra existing rows with nonmatching keys, and no eligible unstored record blocked earlier pilots. A permanent-backup privilege failure then blocked reconciliation. These were not successful writes and are not instructions to retry old cells.

The owner authorized a one-record DEV replacement without permanent backup, then ten records, then the full DEV reload. Those runs now have accepted reports above. Prior approvals are scoped history, not standing permission to truncate tomorrow or change production. The full reload has no durable before-copy from this workflow after commit.

For future uncertain commit/readback failures: inspect first; never auto-rerun. For source conversion, the Matillion correction only selects SQL-null CURATED_JSON rows; already-curated rows need a separately authorized repair.

## How this memory stays current

Project startup guidance is in [AGENTS.md](../AGENTS.md). Update this handoff, CURRENT_STATUS and affected field statuses after verified milestones and decisions, preserving linked historical evidence. State whether evidence is code review, local test, owner-reported output or live readback.

This is durable project documentation, not a promise of unlimited conversational memory or an active Snowflake session. Work in this repository should read it before giving the next run instruction. The root instructions use the project mechanism documented in [official OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).## Daily loading - shared implementation, live acceptance pending

The normal path is the seven-cell workflow, not the one-time full DEV reload.
See [shared workflow](SHARED_SEVEN_CELL_MAPPER.md) and [SSP daily policy](SSP_DAILY_LOADING.md).

Cell Seven defaults to OSCAL_LOAD_MODE=PREVIEW and global EXECUTE_WRITES remains
false. Every selected route must have a verified storage contract before COMMIT.
The current AR route does not, so the shipped two-model selection is preview-only.

The writer inserts new keys, updates changed business values and leaves
unchanged rows/audit values alone. PK/FK, UUID, payload, source scope and hierarchy
checks remain. Each source/model has its own DIM/FACT transaction. All graphs
are preflighted first, but commits across models are not one transaction.
A later failure records already committed groups and must not automatically retry.

Obsolete in-scope keys block writes; absent source records are preserved.
No DELETE, TRUNCATE, permanent backup or assumed deletion policy. Live shared
preview/commit acceptance, daily scheduling and production review remain pending.
An unchanged live run alone would not prove a changed-row write.

## SSP field mapping scope and parked work

The register records **43 distinct Archer fields / 44 implemented source-to-target mappings**: 11 metadata, 27 system-characteristics, 6 component-reference routes. This is an implementation count, not 44 individually complete/schema-valid mappings or all workbook rows.

- Metadata and all six approved component-reference routes have accepted mapped-scope evidence.
- System-characteristics work is implemented with exceptions. PTA helper is still skipped despite Notes describing a custom property; its rule requires reconciliation. Do not confuse it with the package-type helper, which stays excluded as transient.
- Package type's current property name differs from the Notes example; naming correction is parked.
- Recommended security category has an “All Nulls” rule and no approved populated-value conversion. Other security-category row questions remain in the register.
- Control Implementation is parked: its proposed property placement/rule has not been approved as a standard-conforming mapping. Do not invent a custom extension or redirect its path.
- The six approved System Implementation rows stop at components[]. A separate component status mapping is not evidenced by those Excel rows.
- Missing source descriptions, unproved hardware hydration and incomplete/absent CIA data remain explicit gaps. Generated support nodes do not add completed Excel rows.

See [SSP done and next](SSP_DONE_AND_NEXT.md), [mapping register](MAPPING_PROGRESS.md) and [pinned conformance contract](OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md). SSP model conformance is pinned to 1.2.3; mapped-scope DEV persistence is not certification of a full schema-valid SSP.

## AR and other models

There are **45 AR row occurrences / 44 distinct Archer fields** in the posted transcription, not the complete original workbook:

- 17 runtime-accepted in memory.
- 15 additional implemented candidate-only rows.
- 2 parked rejected fields: Risk Acceptance (one reference-shaped object), Risk Assessment Report (99 multi-number lists). Their meaning/conversion must not be guessed.
- 7 workflow audit properties deferred by the owner.
- 2 duplicate Average Security Compliance Score occurrences deferred.
- 2 under review: Total Package Inherent Risk and Findings reference/UUID association.

The accepted pattern is one observation per populated source field, with a named inline property. The required root/result/observation registry entries were checked; inline properties did not require extra registry nodes. The published expanded AR cell remains a blocked candidate, not a safe replacement for the accepted 17-field write scope.

No AR database load is accepted. Before AR persistence, confirm actual AR target schemas and reuse the shared writer for accepted mappings only; never repoint an SSP full-reload cell to AR. POA&M and other models have not been completed by this work.

## Fixed identities and targets

- Source: RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
- Registry: RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
- DIM: RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
- FACT: RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY
- Source identity: Archer CONTENT_ID; model SSP; version v1_registry_path_instance.
- Physical PK/FK hashes: BINARY(16). Physical UUID columns: VARCHAR(32). DIM METADATA_JSON: VARIANT. Load timestamps: TIMESTAMP_TZ(9).

Use current schema evidence before changes; these facts do not grant permissions. The registry owns hierarchy/identity and Excel owns approved field mapping. Neither registry population nor graph integrity alone proves every Excel row is complete.

## Past failures and current recovery boundary

Schema-type rejection, temporary staging failure, extra existing rows with nonmatching keys, and no eligible unstored record blocked earlier pilots. A permanent-backup privilege failure then blocked reconciliation. These were not successful writes and are not instructions to retry old cells.

The owner authorized a one-record DEV replacement without permanent backup, then ten records, then the full DEV reload. Those runs now have accepted reports above. Prior approvals are scoped history, not standing permission to truncate tomorrow or change production. The full reload has no durable before-copy from this workflow after commit.

For future uncertain commit/readback failures: inspect first; never auto-rerun. For source conversion, the Matillion correction only selects SQL-null CURATED_JSON rows; already-curated rows need a separately authorized repair.

## How this memory stays current

Project startup guidance is in [AGENTS.md](../AGENTS.md). Update this handoff, CURRENT_STATUS and affected field statuses after verified milestones and decisions, preserving linked historical evidence. State whether evidence is code review, local test, owner-reported output or live readback.

This is durable project documentation, not a promise of unlimited conversational memory or an active Snowflake session. Work in this repository should read it before giving the next run instruction. The root instructions use the project mechanism documented in [official OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
