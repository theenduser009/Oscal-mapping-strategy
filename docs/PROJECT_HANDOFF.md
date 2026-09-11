# Project handoff — read this before resuming

Last reconciled: **2026-09-11**. Purpose: durable context requested by the owner, so the cell roles, completed work and pending decisions do not need to be retold.

## Resume here

**The full SSP DEV reload is accepted. Do not rerun it.** The next engineering work is to complete and verify the **existing daily loading path in Cells 6-7**, reusing the physical-storage and transactional checks already proved by the separate persistence cells. This is not a request to build another mapper from scratch.

This checkpoint update changes documentation/instructions only. No new notebook run, database write, scheduler or daily-loader implementation was performed by saving it.

The old-versus-new SSP row-count difference remains a separate unresolved audit. AR has 17 accepted in-memory mappings, but no accepted database load. Keep those distinctions when reporting progress.

## The pipeline and every cell's responsibility

| Step | Existing file / component | What it does |
| --- | --- | --- |
| Upstream Matillion | [Null-preserving UPDATE](../sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql) | Converts raw field IDs to field names and writes CURATED_JSON on the Archer RAW table. Retains named nulls. Not part of notebook Cells 1-7. |
| Cell 1 | [Configuration](../notebooks/cells/01_initialization_and_configuration.py) | Snowpark/configuration, source/registry/target settings, model and identity policy. Baseline EXECUTE_WRITES is false and initialization rejects true. |
| Cell 2 | [Inputs](../notebooks/cells/02_source_mapping_registry_inputs.py) | Reads CONTENT_ID and existing CURATED_JSON from the configured source, mapping artifact, live registry and approved lookups. Resolves duplicate source IDs by the configured technical ordering, not arbitrary deduplication. |
| Cell 3 | [Mapping contract](../notebooks/cells/03_canonical_mapping_contract.py) | Normalizes and routes the approved mappings and registry ownership. |
| Cell 4 | [Helpers](../notebooks/cells/04_parsing_transform_payload_helpers.py) | Parses values, applies approved transforms, constructs payloads and deterministic identity. |
| Cell 5 | [Graph builder](../notebooks/cells/05_registry_graph_builder.py) | Builds model-specific nodes and parent-child edges for selected source records using the registry. Does not invent populated collections. |
| Cell 6 | [Validation and guarded loader](../notebooks/cells/06_validation_and_guarded_loader.py) | Already defines validate_and_load_oscal, MERGE generation, and verify_oscal_load. It can insert/update DIM and FACT when enabled; accepted normal runs used writes disabled. |
| Cell 7 | [Orchestrator](../notebooks/cells/07_mapper_orchestrator.py) | Calls graph construction, validation/loader and mapping coverage; produces final_nodes_df, final_edges_df and run_result. |
| Owner's current Cell 8 | [Separate full DEV reload](../notebooks/persistence/RELOAD_ALL_SSP_DEV.py) | Replaces both entire SSP DEV target tables from the accepted graph. This was the accepted one-time full reload, not the finished daily loader. |

The consolidated seven-cell source is [NB_ARCHER_OSCAL_MAPPER_V1.py](../notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py); keep it synchronized with split cells when code changes. Separate AR, assembly, diagnostic and persistence cells are identified by filename, not a fixed notebook number.

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

**Already exists:** Cell 6 generates primary-key-based insert/update MERGEs; Cell 7 invokes it. The corrected explanation is not “nothing loads in Cells 1-7,” but “their normal write branch has not been accepted end to end against these physical targets.”

**Remaining before enabling daily writes:**

- Reuse the proven physical conversions: existing 32-hex hashes to BINARY(16) without rehashing; canonical UUIDs to the physical 32-character representation; parsed VARIANT payloads. Normal Cell 6 currently passes logical values through.
- Put DIM and FACT mutations in a shared explicit transaction with rollback handling. The current normal loader has no such transaction.
- Compare actual saved payloads, PK/FK/UUID links and record-scoped hierarchy, not only matched key counts.
- Define an unchanged-business-value policy; current MERGE updates matched non-PK columns, including audit fields.
- Agree obsolete node/edge and deleted source-record handling. A missing row in a partial input is not authorization to delete target data.
- Prove repeatability with independently rebuilt inputs, changed/new records and failure cases. Re-merging a frozen staging snapshot alone does not prove the whole daily pipeline.
- Reconcile enablement with Cell 1's deliberate false-only baseline; do not merely tell the owner to flip its flag.

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

This is durable project documentation, not a promise of unlimited conversational memory or an active Snowflake session. Work in this repository should read it before giving the next run instruction. The root instructions use the project mechanism documented in [official OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
