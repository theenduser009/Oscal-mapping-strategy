# Project handoff - read this before resuming

## Current action - eight-hour delivery candidate

The owner authorized continued changes while away and requested tested code on
GitHub within eight hours. All **769 local tests pass**; **2,209 metadata** and
**729 linked-identity differential cases** match supported behavior. Generated
notebooks are synchronized. The preceding checkpoint af639853 passed GitHub CI;
verify this candidate's own remote commit and checks before claiming publication.

The current cells contain **3,700 physical / 3,263 nonblank, noncomment lines**,
159 physical lines below this task's start and 562 below the earlier 4,262-line
draft. The larger simplification target remains unmet. Do not call this a major
lean rewrite or production acceptance.

Fixed malformed CSV row loss, quoted source bindings, stale party data after a
failed build, and incorrect commit/failure attribution. Removed repeated registry
validation, repeated identity scans and the unused mapping upload. Conflicting
latest source payloads now block instead of selecting a JSON-hash winner; equal
latest duplicates still collapse after configured technical ordering.

**Next action:** verify the final GitHub publication/CI, continue meaningful
remaining simplification from this tested checkpoint, and perform live acceptance
in the intended Snowflake environment before enabling writes. The deadline check
is scheduled for September 13 at 08:04 America/New_York. See the
[eight-hour delivery checkpoint](checkpoints/2026-09-13-eight-hour-delivery.md).

No Snowflake connection was available and no database action occurred. Registry
setup and daily persistence/readback acceptance remain pending; normal writes
stay false and AR has no verified destination. Historical SSP/AR evidence and
the unresolved old/new SSP row difference are unchanged.

## Previous action - review the tested seven-cell candidate

All **749 local tests pass**, and **2,209 differential cases** match the supported
CSV/registry behavior. An independent review found no blocking issue after the
cached-plan upgrade fix. Generated split and combined cells are synchronized.

The current notebook has **3,720 physical / 3,290 nonblank, noncomment lines**:
139 / 126 fewer than the start of this task, and 542 physical lines below the
earlier 4,262-line draft. Mapping is still 905 lines and transforms 1,207 lines.
The larger lean-rewrite target is not met; do not inflate the size improvement.

Removed duplicate runtime state and obsolete catalog/default/controlled-field
execution. Those retired options now reject explicitly. Versioned cached plans
and matching-cell checks prevent silent loss after an upgrade. Accepted SSP/CIA11/
AR17 outputs and metadata-only future-model behavior remain covered; frozen
historical engines and expected outputs are unchanged.

**Next action:** review the tested candidate and decide the remaining simplification
scope, then run live acceptance in the intended Snowflake environment before writes.
See the [tested candidate checkpoint](checkpoints/2026-09-13-tested-seven-cell-candidate.md).
No Snowflake connection was available and no database action occurred. Normal
writes stay false, daily persistence/readback acceptance remains pending, and AR
has no verified destination. Historical SSP/AR evidence and the unresolved old/new
SSP row difference remain unchanged.

## Previous action - tested cleanup across all seven cells

The owner authorized continued simplification across all seven cells while away
and asked for full testing. The current draft removes duplicate runtime state,
reads each mapping CSV once, builds registry reference groups directly, shares
loader result setup and simplifies the runner. All **739 local tests pass**;
**2,209 differential mapping cases** match the prior behavior. Generated cells
are synchronized. A pinned GitHub workflow checks the same suite and packaging.

This pass is modest: **3,859 to 3,817 total lines** (42 fewer), with **3,383
nonblank/noncomment lines**. Mapping remains 939 lines and transformations
1,270 lines. The owner's larger readability/size target is not yet met; do not
present this cleanup as the requested lean rewrite or production certification.

**Next action:** continue the larger simplification from the tested draft,
then perform live Snowflake verification before enabling writes. See the
[verification checkpoint](checkpoints/2026-09-12-seven-cell-cleanup-and-testing.md).
No live Snowflake connection is available here and no database action occurred.
Normal writes remain false, the daily writer's live acceptance is pending,
and the Assessment Results destination remains unverified. Historical accepted
SSP/AR results and the unresolved old/new SSP row difference are unchanged.

## Previous action - review the smaller seven-cell notebook

The owner clarified that the target is a substantially easier, smaller notebook
and supplied the complete original: **860 physical lines / 669 nonblank,
noncomment lines**. The previous candidate consolidated responsibility without
reducing total size. This pass removes **403 physical lines / 396 nonblank,
noncomment lines** from that candidate: **4,262 to 3,859 physical lines**.
Cell Four drops from 1,572 to 1,275 physical lines. The seven-cell sequence stays intact.

The implementation shares scalar conversion and lookup validation, removes the
intermediate hydration-plan object and fixed callback dispatch, consolidates
CSV/registry parsing and routing reports, and removes redundant input counts,
storage checks and graph traversal. Mapping CSV and registry SQL are unchanged.

All **736 local tests pass**, including accepted SSP/CIA11/AR17 comparisons,
metadata-only future models, source selection, lookup query behavior, identity,
and guarded writes. Generated V2 cells and combined notebook are synchronized.
Existing frozen fixtures are unchanged; a copy of the previous graph builder
now keeps historical transformer/graph comparisons independent of current code.

**Next action:** review the updated draft
[Reduce notebook bulk and simplify metadata execution](https://github.com/theenduser009/Oscal-mapping-strategy/pull/1).
See the [counts and verification checkpoint](checkpoints/2026-09-12-notebook-bulk-reduction.md).
This is a review candidate, not a merged release or live Snowflake acceptance.
No Snowflake action occurred. Normal writes remain false; the prior release's
live preview and daily writer acceptance remain pending. No live rerun is
requested during review. If adopted, use the matching Cells Two through Six.

## Previous action - review Cells Three and Four metadata cleanup

The owner authorized the first bounded simplification of V2. This candidate
normalizes CSV/registry rows once, resolves reference families once, and puts
compiled-plan validation and operator identity rules in one shared location.
Unchanged compiled plans skip repeated constraint compilation; edited or
independently supplied plans still validate before source rows are read.

All **720 local tests pass**, with no failures, errors or skips. The twenty new
tests cover preparation reuse, reference-family rejection, changed plans,
required/enum enforcement, provenance compatibility and metadata-only edits.
Existing SSP/CIA11/AR17 parity, future-model, identity and guarded-write checks
remain green. Maintained cells, generated V2 pages and the combined notebook
are synchronized. Frozen fixtures, mappings, registry SQL and Cells One, Two,
Five, Six and Seven are unchanged.

**Next action:** review the candidate on `simplify-metadata-boundary` before
adopting it. See the [implementation and validation checkpoint](checkpoints/2026-09-12-metadata-boundary-simplification.md).
This is a review candidate, not a merged release or live Snowflake acceptance.
No notebook or SQL was executed against Snowflake; normal writes remain false.
The prior release's live preview and daily writer acceptance remain pending.
No registry cleanup, DEV reload or unchanged preview rerun is requested here.

The cleanup removes repeated work and rule ownership; it does not materially
reduce total notebook length or complete the other audit suggestions. If
adopted, Cells Three and Four must be replaced together.

## Previous action - CSV-only Cell Three release for preview

Cell Three now uses one flat CSV compiler for executable mappings. The unused
programmatic-format compiler is removed; required CSV rule IDs still undergo
uniqueness checks. Cell Three shrank from 896 to 862 nonblank, non-comment lines.
The maintained source, V2 page and combined notebook are synchronized.

All **700 local tests pass**, with no failures, errors or skips. Six test files
now exercise explicit CSV inputs, including rejection of attempts to bypass that
contract. Frozen historical fixtures are unchanged. Accepted SSP/CIA11/AR17
comparisons, future-model execution, deferred rows, required/null rules and
key/write checks remain intact. Cells One, Two and Four through Seven, mapping
CSV and registry SQL are unchanged. This is a bounded cleanup, not completion of
every suggestion in the external review or acceptance of the daily writer.

**Next action:** use the complete updated
[V2 Cell Three](../notebooks/cells_v2/03_canonical_mapping_contract.py).
If Cell Two has already succeeded in the same active session, replace and run
Cell Three, then run Cells Four through Seven in PREVIEW with
`EXECUTE_WRITES = False`. If the session was restarted, run the matching
[V2 Cells One through Seven](../notebooks/cells_v2/README.md) in order.
Share the aggregate Cell Seven report. Stop if any cell fails; do not enable writes.
No registry setup, cleanup or DEV reload rerun is needed.

The earlier scalar-identity correction remains included. This release is
published, but its Snowflake preview is **not yet accepted**. No database data
was changed during this cleanup. A pending destination-contract status is not
write-readiness approval.

## Previous action - rerun Cell Three preview with scalar legacy fix

The owner confirmed that the guarded registry cleanup completed with fifteen
retired DEV columns removed, twelve columns remaining and an unchanged retained
fingerprint. Do not repeat registry setup or cleanup.

The following V2 run passed Cell Two and stopped in Cell Three before graph
construction or target DML with
`Scalar object operator cannot define collection identity metadata`. The fix is
limited to Cell Three: `INSTANCE_KEY_RULE` and `ITEM_PATH` are interpreted only
for collection rows. Legacy values on a scalar registry row are ignored in the
compiled runtime contract; true collections retain strict identity and item-path
validation. Cell Four consumes that normalized contract.

The maintained Cell Three, V2 page and combined notebook are synchronized. All
**698 local tests pass**, including the new scalar Cell Three-to-Four boundary,
accepted SSP/CIA11/AR17 parity, metadata-only third-model behavior, PK/FK,
idempotency and preview safety. Cells One, Two and Four through Seven have no
runtime logic change. Normal writes remain disabled; this is not live Snowflake
acceptance.

**Next action:** if the session where Cell Two passed is still open, replace only
[V2 Cell Three](../notebooks/cells_v2/03_canonical_mapping_contract.py), run it,
then run the existing Cells Four through Seven with `EXECUTE_WRITES = False`.
If the session restarted, run the matching V2 Cells One through Seven in order.
Share the Cell Seven aggregate report. Do not rerun registry SQL or enable
writes. See the
[fix checkpoint](checkpoints/2026-09-12-cell3-scalar-legacy-identity-fix.md).


## Previous action - remove retired DEV registry columns

The lean runtime is implemented locally. Cell One and Cell Three now compile
the maintained mapping CSV with the original nine registry fields plus only
`OPERATOR`, `UUID_POLICY` and `REQUIRED_MEMBERS`. The other fifteen experimental
registry fields are ignored, not dropped. The revised setup SQL adds, seeds,
conflict-checks and verifies only those three columns.

Exact SSP, CIA11 and AR17 parity is preserved. Multi-source routing and a
metadata-only third model remain supported. Cell Four now relies on Cell Three's
single normalized registry boundary; Cell Six removes SSP-only compatibility
and repeated projection helpers while retaining guarded-write behavior. The
source cells, V2 pages and combined notebook are synchronized; all 697 local
tests pass. Cells Four and Six are 119 executable lines smaller in total. Writes
remain disabled. No Snowflake execution has occurred for this lean change.

The owner explicitly approved removing the fifteen unused experimental columns.
Run only the published
[guarded cleanup SQL](../sql/registry/CLEANUP_UNUSED_OSCAL_MAPPER_METADATA_COLUMNS.sql)
in a fresh DEV worksheet and share its returned object. It preserves all rows
and leaves exactly the original nine plus three active columns. Do not run the
notebook yet. See the
[cleanup checkpoint](checkpoints/2026-09-12-registry-column-cleanup.md).

## Previous action - registry binding correction; superseded

The owner reported a Snowflake statement error at anonymous-block line 270,
position 18: `FLATTEN` received `VARCHAR(17076)` as its `INPUT`. In the
published failing SQL this identifies the first dynamic conflict check, before
this invocation's ALTER or metadata UPDATE. This attempt did not change the
registry or DIM/FACT; it does not establish what existed from older attempts.

The correction serializes the two array bindings to JSON text and explicitly
parses them inside all four dynamic SQL templates (six calls). Native arrays,
original registry columns, metadata seeds, conflict checks and transaction
boundaries remain unchanged. The seven notebook cells and write settings are
unchanged. See the [binding correction checkpoint](checkpoints/2026-09-12-registry-binding-correction.md).

**Next action:** use the complete corrected
[registry SQL](../sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql) in a fresh
Snowflake SQL worksheet with the approved DEV role, no active transaction and
no competing registry writer. Share the aggregate completion report. Keep the
seven-cell preview on hold until registry setup is verified; normal mapper
writes remain disabled.

Local regression checks are not live Snowflake acceptance. The prior suite
missed this bind-transport defect because it used static checks and Python
simulations. The accepted SSP load, unresolved old-row difference and AR17
in-memory-only status are unchanged.

## Previous action - corrected seven-cell release; live setup pending

The three boundary defects are corrected. **All 685 local tests pass**, with
zero failures, errors or skips, including the six formerly failing cases.
The source cells, V2 pages and combined notebook are synchronized.

- Cell Three blocks approved mappings at or beneath known disabled/inactive
  registry paths rather than routing them into an enabled ancestor.
- Cell Five supplies explicit canonical types for empty graph dataframes;
  populated data still uses the existing inference behavior.
- Registry migration rejects null/blank paths and invalid parent/root links
  before DDL; its UPDATE count comes from the executed statement's result.

The existing per-model entrypoint calls the same graph builder and writer.
No model-specific mapper, second selector or new notebook execution cell was
added. CSV mappings, original registry columns/seeds, accepted SSP/CIA/AR17
payloads and identities remain unchanged. Normal mapper writes stay disabled.

**Next action:** use the corrected
[one-time registry SQL](../sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql) in a
fresh Snowflake SQL worksheet with the approved DEV role and no competing
registry writer, then share its aggregate report. Do not run the seven cells
against the old registry. After setup is verified, replace the matching V2
cells and preview in order as described in
[setup instructions](REGISTRY_METADATA_SETUP.md).

This supersedes the additional-testing hold. It is not live Snowflake
acceptance: no SQL migration, DIM/FACT write, Matillion run or daily-loader
acceptance occurred here. The accepted SSP DEV reload, unresolved old-row
difference, AR17 in-memory-only scope and unverified AR targets are unchanged.
See the [correction checkpoint](checkpoints/2026-09-12-registry-release-corrections.md).

## Previous action - additional tests found defects (corrected below)

The owner's request to keep testing exposed boundary defects in the published
registry-backed release. **Do not run the new registry setup or notebook
PREVIEW yet.** This supersedes the previous run instruction below.

The original 654 tests still pass, and accepted SSP/CIA and AR17 parity remains
intact. The expanded suite runs 666 tests: 660 pass, with five assertion failures
and one error in new regression cases (no skips). New tests reproduce
disabled/inactive singleton mappings executing
through their parent and empty-relationship dataframe failure for a future
model. Migration preflight also needs to reject malformed paths and parents
before the runtime decoder encounters them. See the
[additional testing checkpoint](checkpoints/2026-09-12-registry-release-additional-tests.md)
for evidence, limitations and regression files.

**Next action is engineering correction and retesting, not an owner rerun.**
Only local tests and these continuity notes changed during this testing turn.
The hold/checkpoint has not been published to GitHub; runtime code, migration
SQL and database data are unchanged. Normal writes remain disabled. No accepted
field or prior persistence milestone has been reclassified.

## Previous action - registry-backed release, live setup pending (on hold)

The owner approved extending the development registry so the seven cells no
longer require a separate JSON catalog. Code and migration SQL are prepared;
the live registry has NOT been changed by this task.

The maintained [mapping CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv) owns field
rules. It preserves all 147 reviewed occurrences, the existing populated-value
guard, and three explicitly labelled existing support values (metadata title,
OSCAL version and document version). These support rows replace old structural
settings; they are not three newly completed Excel mappings.

The [one-time registry migration](../sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql)
adds 18 sparse, readable metadata columns and fills existing active SSP/AR rows.
It does not insert registry rows, change the original nine columns, or read or
write DIM/FACT. Non-null conflicts block rather than being overwritten.
Schema additions auto-commit; a failed DDL phase can leave nullable columns.
The metadata UPDATE has a separate transaction. No live SQL success is claimed.

Cell One holds visible deployment settings. Cell Three reads the versioned
registry and mapping CSV; Cell Four uses the same reusable operators. The
production JSON is retired; frozen copies exist only under tests/fixtures for
parity. No additional daily cell or model-specific mapper was added.

All **654 local tests pass**, including complete Cells One-to-Three input flow
with the released CSV and extended registry across model selections. Checks
preserve the accepted SSP graph, all eleven CIA mappings, AR17
outputs, original field-rule contracts and source Notes. Required values must
survive conversion; zero and false remain valid. Local tests do not establish
Snowflake execution, daily writer acceptance or complete OSCAL conformance.

**Next action:** run only the one-time registry SQL in a fresh Snowflake SQL
worksheet, with no active transaction or other registry writer, and share its
aggregate report. It needs permission to ALTER and UPDATE the existing DEV
registry, not permanent backup-table creation. Follow [setup and preview
instructions](REGISTRY_METADATA_SETUP.md); do not run the new notebook against
the old registry. Once setup is verified, use the updated CSV and matching V2
Cells One through Seven in PREVIEW. No JSON upload is needed.

No approval is pending for this scoped extension. Normal mapper writes remain
disabled. Do not rerun the accepted DEV reload. SSP persisted scope, the
unexplained old-row reduction, AR17 in-memory-only acceptance, deferred work and
unverified AR targets are unchanged. Historical instructions below are not
current run requests.

## Previous action - reviewed compilation (superseded)

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

## Historical checkpoint (superseded; use current action above)

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
| Cell 1 | [Configuration](../notebooks/cells/01_initialization_and_configuration.py) | Visible source/lookup bindings, version settings, verified storage contracts and one model selector. No JSON file read. Baseline EXECUTE_WRITES is false and initialization rejects true. |
| Cell 2 | [Inputs](../notebooks/cells/02_source_mapping_registry_inputs.py) | Reads source-local CONTENT_ID and CURATED_JSON snapshots, each bound mapping artifact, registry and approved lookups; model routes reuse the same source snapshot. Resolves duplicate source IDs by the configured technical ordering, not arbitrary deduplication. |
| Cell 3 | [Mapping contract](../notebooks/cells/03_canonical_mapping_contract.py) | Compiles isolated source/model contexts, preserving paths/Notes and reporting selected, excluded, deferred and blocked rows. |
| Cell 4 | [Helpers](../notebooks/cells/04_parsing_transform_payload_helpers.py) | Shared helpers/operators execute the compiled plan; legacy field-specific engines are test fixtures only. |
| Cell 5 | [Graph builder](../notebooks/cells/05_registry_graph_builder.py) | One generic graph loop builds nodes/edges for each explicit source/model context using the registry. Does not invent populated collections. |
| Cell 6 | [Validation and guarded loader](../notebooks/cells/06_validation_and_guarded_loader.py) | Shared validate_and_load_oscal and verify_oscal_load use an immutable verified storage contract; targetless AR gets logical graph validation only. Conditional upserts, transaction/readback and obsolete-row blocking remain. |
| Cell 7 | [Orchestrator](../notebooks/cells/07_mapper_orchestrator.py) | Preflights all source/model routes, builds each through the shared engine and emits OSCAL_PIPELINE_REPORT. MODEL_GRAPHS retains scoped graphs; compatibility outputs refer only to the configured default route. |
| Owner's current Cell 8 | [Separate full DEV reload](../notebooks/persistence/RELOAD_ALL_SSP_DEV.py) | Replaces both entire SSP DEV target tables from the accepted graph. This was the accepted one-time full reload, not the finished daily loader. |

The maintained source is [notebooks/cells](../notebooks/cells/README.md); the [combined notebook](../notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py) and V2 pages are generated from it. Separate AR, assembly, diagnostic and persistence cells are identified by filename, not a fixed notebook number.

A new Python cell in the same Snowflake session can reuse in-memory inputs. A new Snowflake session cannot. Rebuilding inputs may be necessary for a future authorized run, but the chat history alone does not keep dataframes or temporary snapshots alive.

## Accepted evidence - preserve, do not repeat

| Milestone | Verified scope | Evidence |
| --- | --- | --- |
| SSP mapped graph and mapped-scope assembly | 2,813 source records/documents; 70,102 nodes / 67,289 edges in the accepted graph before full reload. Not full-model/schema completeness. | [Graph checkpoint](checkpoints/2026-09-10_ssp_date_property_run_accepted.md), [assembly checkpoint](checkpoints/2026-09-10_ssp_mapped_scope_assembly_accepted.md) |
| One-record DEV reconciliation | Replacement committed; rollback rehearsal, saved values and keys, repeat-write checks passed. No permanent backup under owner-approved DEV scope. | [One-record live result](SSP_ONE_RECORD_RECONCILIATION.md#live-transaction-only-reconciliation-result--2026-09-11) |
| Ten additional DEV records | Committed/read-back verified; 289 DIM / 279 FACT rows; repeat inserts zero; first record unchanged. Eleven records proved before full reload. | [Ten-record checkpoint](SSP_TEN_RECORD_DEV_BATCH_2026-09-11.md) |
| Full SSP DEV reload | COMMIT; PERSISTED true; 2,813 source records, 70,102 DIM / 67,289 FACT rows. Saved graph, payload/key and hierarchy checks passed; second pass inserted zero rows. | [Full reload live checkpoint](SSP_FULL_DEV_RELOAD_2026-09-11.md) |
| AR score mapping | 17 mappings accepted in memory across 2,813 source records; no database writes. The later 34-field candidate is not accepted. | [AR accepted run and inventory](ASSESSMENT_RESULTS_START_HERE.md) |
| Upstream null correction preview | Owner confirmed complete conversion preview preserves expected field names and values, including nulls. Actual Matillion UPDATE/pipeline execution is not independently verified. | [Current incident checkpoint](CURRENT_STATUS.md#active-incident---matillion-raw-to-curated-null-field-loss), [fix explanation](RAW_CURATED_NULL_FIELD_FIX.md) |

The full reload used transaction-only recovery and no permanent backup. It replaced the earlier eleven records too. Local tests supported publication; the owner-posted live report, not those tests, establishes persistence acceptance.

## Row-count reduction - still unexplained

| Table | Before full reload | After full reload | Fewer rows |
| --- | ---: | ---: | ---: |
| SSP DIM elements | 126,453 | 70,102 | 56,351 |
| SSP FACT dependencies | 122,939 | 67,289 | 55,650 |

The loaded tables exactly matched the accepted new graph. That does **not** establish why every old row disappeared, whether every old source record was retained, or whether the old rows were duplicates/stale. Element counts are not source-record counts. Do not infer an old root count by subtracting edges from nodes.

Next audit, when requested: compare old and new source-record/path coverage read-only, reporting only differences. The reload created temporary before-snapshots; whether the same Snowflake session remains open is not confirmed. Do not promise those snapshots survive a restart or that durable recovery exists. Leave the accepted targets unchanged while this is unresolved.

## Daily SSP loading - existing code and remaining work

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
- Recommended security category has an "All Nulls" rule and no approved populated-value conversion. Other security-category row questions remain in the register.
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
- Recommended security category has an "All Nulls" rule and no approved populated-value conversion. Other security-category row questions remain in the register.
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

