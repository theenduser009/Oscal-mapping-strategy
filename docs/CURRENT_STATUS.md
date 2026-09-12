# Current Status


## Current action - live preview blocked by scalar/collection metadata conflict

The owner-provided Snowflake screenshot shows Cell Three failing during
`decode_registry_model_contracts(...)` with:

```text
ValueError: Scalar object operator cannot define collection identity metadata
```

The failure occurs before `compile_mapping_contexts(...)` completes. No graph
build, persistence stage or target DML is established by this evidence. The
screenshot does not expose the offending model or registry path.

**Next action:** perform only a read-only inspection of active registry rows to
identify any scalar-object operator carrying collection identity metadata.
Report the exact model, node path, operator, collection flag, instance-key rule,
item path and parent-instance identity setting. Do not weaken the decoder guard,
update metadata or enable writes. See the
[dated failure checkpoint](checkpoints/2026-09-12-scalar-object-collection-identity-failure.md).

This runtime failure supersedes the earlier instruction to proceed directly
with the matching seven-cell preview. The corrected local release and its 685
passing tests remain local evidence; this screenshot is the current live
checkpoint.


## Current action - remove retired DEV registry columns

The maintained mapper has been changed locally to use the mapping CSV, the
original nine registry columns, and only three sparse registry rules:
`OPERATOR`, `UUID_POLICY` and `REQUIRED_MEMBERS`. The other fifteen experimental
columns are no longer read. The revised setup SQL never drops them if an earlier
DEV attempt created them.

Cell One and Cell Three are updated. Cell Four now consumes Cell Three's
normalized registry contract instead of parsing it again. Cell Six drops its
SSP-only compatibility constants and consolidates repeated physical projection
helpers while retaining the public writer API, transaction, rollback, integrity,
idempotency and read-back checks. The maintained cells, V2 pages and combined
notebook are synchronized. All **697 local tests pass**, including the
exact accepted SSP graph digest, all eleven CIA transforms, all seventeen
accepted Assessment Results outputs, metadata-only third-model execution,
routing boundaries, migration bindings, PK/FK safeguards and loader behavior.

Executable LOC is 209 / 149 / 896 / 1,468 / 151 / 804 / 160 by cell, 3,837
total. This is 119 fewer executable lines than the pre-audit lean candidate.
Static closure found no additional unused top-level Cell Four functions; its
remaining size is tested transformation, hydration, identity and integrity code.

No Snowflake statement was run and no registry, DIM or FACT data changed. This
is local verification, not live acceptance. Normal writes remain disabled. The
accepted SSP DEV reload, unresolved old-versus-new SSP row difference and AR17
in-memory-only status are unchanged.

The owner has now approved physical cleanup of the fifteen retired experimental
DEV columns. The guarded cleanup preflights the exact schema, preserves a full
row fingerprint, uses one `RESTRICT` drop, and verifies exactly the original
nine plus three active columns afterward. It does not access DIM/FACT.

**Next action:** run the complete
[registry cleanup SQL](../sql/registry/CLEANUP_UNUSED_OSCAL_MAPPER_METADATA_COLUMNS.sql)
once in a fresh DEV worksheet and share its single returned object. Do not run
the notebook yet. See the
[cleanup checkpoint](checkpoints/2026-09-12-registry-column-cleanup.md).
See the [lean runtime checkpoint](checkpoints/2026-09-12-lean-registry-runtime.md).

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

Last reconciled: 2026-09-11

## Previous action - mapping-input search (superseded)

The owner requires the original simple seven-cell interface and Excel/CSV plus
registry as the maintained mapping metadata, without a second duplicate JSON
catalog. The [simplification audit](checkpoints/2026-09-12-mapper-simplification-audit.md)
records the recovered original design, current dependencies and exact cleanup.
Cell Three's unused Snowpark metadata upload is removed, along with three unused
helpers and one ignored compatibility argument. All **567 tests pass**, including
whole-cell initialization checks. The existing JSON dependency has **not** been
removed; this is not the final Excel-only release or a live accepted run.

The eleven CIA mappings remain intact and match the accepted implementation.
The complete 608-row source mapping CSV is absent from both the current GitHub
tree and the saved earlier checkout/history. Next: obtain the actual mapping
CSV from notebook Files, including full Notes, and finish the rules/dependency
reconciliation before finalizing simplified code. No new notebook run, mapping
approval, database write or reload is requested. Accepted SSP/AR scope is unchanged.

## Previous action - registry-first routing correction (run advice superseded)

**Implemented and regression-verified:** the same seven-cell workflow now excludes the old SSP/AR engines from deployed Cell Four; their original code is frozen for tests only. One compiled metadata plan controls mapping decisions. Optional declarative constraints cover cardinality, required/absent-value policy, type, enum and numeric bounds. Cell Five, Six and Seven retain the shared graph, guarded writer and runner. Original split cells are the maintained source; a developer-only generator keeps V2/combined copies synchronized.

All **564 local tests pass**, including exact accepted SSP fixture parity, AR17 standalone-output parity, metadata-only new field/third-model execution, the complete posted 459-row failure pattern, mixed 608-row routing, and constraint failure checks. This is implementation evidence, not live Snowflake acceptance. No source, registry or target data was written.

**Verified cause:** the [posted diagnostic](OSCAL_PIPELINE_ROUTING_FAILURE_2026-09-12.md#unknown-model-label-diagnostic) accounts for all 459 blocked rows: 454 placeholder model labels and five Profile/Security Assessment Plan rows. One of those five also has a placeholder path. The earlier label-first gate blocked these before proper classification. The 58 missing-approved-metadata rows are part of the 60 deferred rows, not additional blockers.

**Correction:** Cell Three derives ownership from active registry paths for any model; known label/path conflicts still block. Catalog-declared placeholders stay deferred. Registered other-model paths are excluded from the selected route without enabling another model. If an unreviewed row has no registered owner, it remains deferred under the existing policy rather than being approved by inference. An executable approved row with unknown ownership still blocks. The real SSP path marked TBD remains unresolved. Issue samples now include original model labels and paths.

**Next action:** replace the notebook Files copy of mapper_contract.v1.json and replace only Cell Three from V2. In the existing active session, run Cell One to reload the catalog, then Cell Three, then Cell Seven in PREVIEW; preserve the model selector and keep writes disabled. If the session has restarted, run the matching seven-cell set in order. Post the complete pipeline report. No additional diagnostic, standalone mapper, registry change or DEV reload is needed. Live acceptance remains pending.

The catalog preserves the existing SSP rules and 17 accepted AR fields. New approved mappings using supported behavior can be added through metadata alone; new field-specific Python is not required. Missing approval, unknown transformations and contradictory contracts stop execution. Rejected/deferred AR rows do not become approved automatically.

AR still lacks verified target names/types and is graph-preview-only. Shared daily runtime/writer acceptance and AR persistence remain pending. The other source tables/models are not inferred or enabled.

The prior full SSP DEV reload remains committed/read-back verified: **2,813 source records, 70,102 DIM elements, 67,289 FACT dependencies**. [Accepted live report](SSP_FULL_DEV_RELOAD_2026-09-11.md). The reduction from 126,453 old DIM / 122,939 old FACT remains unexplained: 56,351 fewer DIM and 55,650 fewer FACT rows. No durable before-copy was retained; do not call those removed rows duplicates or stale without evidence.

Matillion raw-ID conversion, persisted SSP data, field acceptance counts and unresolved work are unchanged. [Durable handoff](PROJECT_HANDOFF.md). Historical entries below retain earlier incidents; superseded run requests are not the current action.

## Active incident - Matillion raw-to-curated null field loss

### Latest checkpoint - owner confirms full preview passed

On 2026-09-11 the owner explicitly confirmed the full read-only preview ran
successfully and mapped the fields as expected. This is **owner-reported preview
acceptance**, not independently observed execution of the Matillion UPDATE.
No preview rerun is requested.

Next action: replace the existing Matillion raw-to-curated component SQL with
the [complete corrected UPDATE](../sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql),
retaining its existing `${jv_raw_table_name}` job variable, then run the pipeline.
The UPDATE retains named nulls and preserves content-ID selection. It still
selects only rows with SQL-null CURATED_JSON; already-curated records are skipped
and need a separately scoped repair if required. Matillion pipeline execution
and persisted readback remain pending. No SQL logic changes or new test run
were made for this handoff. Earlier requests to rerun the preview below are
superseded by this confirmation.


**Immediate requested action: view the complete corrected JSON, not another null-only report.**
[Run the full conversion preview SELECT](../sql/matillion/READ_ONLY_authorization_package_full_conversion_preview.sql)
with no edits or inputs. The configured authorization-package raw table is filled
in. Inspect RAW_FIELD_CONTENTS, CURRENT_CURATED_JSON and PROPOSED_CURATED_JSON to
compare raw field IDs/values with mapped names, populated values and retained nulls.
No write or Matillion change occurs. Published without a test run as requested;
live Snowflake verification and deployment remain pending. Earlier null-only
reports are optional, not the required next action.

**SSP write pilot paused by owner; it has not run.** The current priority is the
reported production field-ID/name loss in the upstream Matillion conversion.
The [incident diagnosis and bounded candidate](RAW_CURATED_NULL_FIELD_FIX.md)
identify one confirmed mechanism in the uploaded SQL: SQL-null typed values are
omitted by the final JSON aggregation. A candidate retains named nulls while
preserving the original content-ID input and both pending-row update filters.

Status: **candidate prepared; not live-verified or deployed**. Read-only regression
and collision preflight are provided. Missing metadata, nested extraction and
key collisions are separate unresolved cases, not silently changed. Existing
non-null curated rows are not repaired by this candidate; no bulk reset/backfill
is authorized. An affected table/record and before-after evidence are needed for
a bounded repair. Accepted SSP/AR work and all deferred mappings are unchanged.

A [one-record values preview](../sql/matillion/READ_ONLY_raw_curated_values_preview.sql)
now shows raw fields, stored/proposed curated JSON, content IDs and key counts
using SELECT only. Set the actual table and requested-object ID before running.
It can inspect existing curated rows without changing them; duplicate rows/keys
block the proposal. Preview runtime acceptance is pending; no production write
or deployment has occurred. Keep sensitive result values inside Snowflake.

For the owner's requested flat list, use the
[one-step null-field-name query](../sql/matillion/READ_ONLY_authorization_package_null_field_names.sql).
The authorization-package RAW table is filled in from Cell 1; set only the raw
requested-object ID. Output is field name plus null value, with explicit blocked
or no-null status. No previous-result query or data write is needed.

Latest owner request: provide a **copy/paste/run, no-input query across the table**
and publish without testing. The
[all-record null-field-name SQL](../sql/matillion/READ_ONLY_authorization_package_all_null_field_names.sql)
is provided with the configured authorization-package RAW table hard-coded. It
returns field names and affected-record counts, SELECT only. No test run was
performed for this new file, and Snowflake runtime acceptance remains pending.
The earlier single-record inputs and result-scan step are not needed for this file.

## Paused action - approved one-record SSP DEV write pilot

The owner approved testing persistence now, rather than postponing every write
until all mappings are complete. The [separate one-record pilot](SSP_WRITE_PILOT.md)
is prepared and locally tested; **live write, rollback and readback acceptance
are still pending**. Use its separate COMMIT mode for the approved pilot while
keeping the normal mapper's `EXECUTE_WRITES = False`.

Scope is one complete record from the accepted SSP graph (70,102 nodes / 67,289
edges overall), written only to the configured SSP DEV DIM/FACT tables. The cell
checks live table schemas, rehearses and verifies rollback, then commits and
reads back the same frozen record. It does not alter accepted mapping code,
write AR or registry rows, delete existing rows, or authorize a bulk load.

AR remains **17 accepted + 15 candidate-only + 2 parked rejections + 7 workflow
deferred + 2 duplicate-score deferred + 2 remaining review = 45 rows**.
The parked/deferred history below remains in force; no unchanged AR rerun is
requested. Persistence is a distinct pending milestone, not a new mapped field.

## Current direction - workflow fields and duplicate score deferred

On September 11, the owner confirmed **skip the seven workflow audit fields for
now**, then also directed us to **defer both Average Security Compliance Score
row occurrences** because their duplicate-field meaning is unresolved.
Neither duplicate is counted as complete. These workflow fields target
`assessment-results.results[].props[]`; they are deferred, not implemented or
complete. This is separate from the two parked value-conversion blockers,
`RISK_ACCEPTANCE_RBDS` and `RISK_ASSESSMENT_REPORT`.

| Remaining Archer field | Row occurrences | Exact Excel target | Current issue |
| --- | ---: | --- | --- |
| `AVG_SECURITY_COMPLIANCE_SCORE` | 2 | `assessment-results.results[].observations[]` | **Deferred by owner, 2026-09-11.** Duplicate meaning unresolved. Both original rows are preserved; no rename, deduplication or output is inferred. Reopen only after source-field identity is clarified. |
| `TOTAL_PACKAGE_INHERENT_RISK` | 1 | `assessment-results.results[].observations[]` | CSV says observation; earlier owner Notes evidence differs. Confirm the governing original row before selecting its contract. |
| `FINDINGS` | 1 | `assessment-results.results[].findings[]` | Notes require linking finding UUIDs; referenced finding identity/source and parent association are not established. |

**No action or notebook run is requested for the deferred score.**
The two remaining non-deferred rows are Total Package Inherent Risk and Findings,
with the unresolved contracts shown above. No code is changed by this status update.

Inventory is **45 row occurrences = 17 accepted + 15 implemented candidate-only
+ 2 parked after rejection + 7 workflow rows deferred + 2 duplicate score rows deferred
+ 2 remaining rows under review**.
Deferred rows remain in the inventory and are not completed mappings.

The [two-field diagnostic](https://github.com/theenduser009/Oscal-mapping-strategy/blob/ac3e8b348eabc708960ccdd51f00e3a0383613dc/docs/ssp_mapping_progress_checkpoint.md#assessment-results-rejected-value-shape-diagnostic--2026-09-11)
is complete and matched the blocked run: 2,813 records, zero parse failures,
1 reference-shaped rejection and 99 multi-number-array rejections, zero writes.
The field meanings and output rules remain parked. No rerun is requested.
The blocked 34-field batch is not accepted. SSP, mapper code, registry and the
original CSV remain unchanged.

## Latest AR run - v3 blocked; no repeat run yet

The [posted thirty-four-field run](https://github.com/theenduser009/Oscal-mapping-strategy/blob/c4279208c3d13554c5fe667755f0e8a2b6cabba5/docs/ssp_mapping_progress_checkpoint.md) confirms the new release ran.
Mapping and registry contracts passed; all 2,813 source records were valid and
unique. Two source fields were rejected by the existing scalar-value conversion:
`RISK_ACCEPTANCE_RBDS` has 1 invalid value and `RISK_ASSESSMENT_REPORT` has 99.
This establishes handler rejection, not that the underlying Archer data is bad
or that either field contains a particular object/reference shape.

All 34 per-field totals reconcile to 2,813 records. Candidate observations total
67,782, producing 73,408 candidate nodes and 70,595 candidate edges with zero
duplicate keys or dangling edges. `OUTPUTS_PUBLISHED = false` and
`WRITES_EXECUTED = false`: these are not accepted/published outputs.
The previous seventeen-field acceptance remains the baseline; its per-field
coverage matches this attempt. None of the seventeen additions is promoted to
runtime accepted from this blocked batch.

**Follow-up complete:** the shape diagnostic above explains both rejections.
The owner parked their conversion decisions and moved to the remaining eleven.
No registry insertion is needed for the parked observation fields.
**Do not rerun the unchanged AR cell.**

Three added fields have no populated evidence in this source:
`PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD`,
`PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD` and `INITIAL_RISK_ASSESSMENT`.
They are source-coverage gaps, not the cause of the blocked status; their upstream
cause is not established. The two underscore-prefixed threshold fields each have
one populated value. See [field-by-field candidate evidence](MAPPING_PROGRESS.md#approved-alternative-path-additions--pending-live).

**Short current summary: [SSP - done and next](SSP_DONE_AND_NEXT.md).**
**Current direction:** SSP leftovers are parked while other Excel models are
reviewed. The [model/path progress and clarification queue](MAPPING_PROGRESS.md#modelpath-status-and-clarification-queue)
separates status, evidence/reason, and information needed for each scope.
**Assessment Results: seventeen mappings are live accepted; seventeen more are
implemented and pending live; eleven row occurrences remain not enabled.** The [September 11 uploaded run](https://github.com/theenduser009/Oscal-mapping-strategy/blob/05fdb9e25bd7e28661f6fbd2d868d360c8d9e0bd/docs/ssp_mapping_progress_checkpoint.md#assessment-results-mapped-scope-checkpoint--2026-09-11)
confirms `ar-observation-scores-v2-17-fields` at
`assessment-results.results[].observations[]`: 2,813 source records,
46,960 emitted observations, 52,586 nodes, 49,773 edges and 2,813 partial
documents. Mapping/registry errors, invalid source records, duplicate keys and
dangling edges are zero. No database writes occurred.

All seventeen selected fields have populated evidence. Ten fields cover every
record; seven have missing source values, including 267 missing risk grades and
541 missing average operating-environment scores. These are omitted field values,
not dropped records or invented defaults. The report does not establish whether
the values were missing in Archer or during upstream curation. See the
[per-field register](MAPPING_PROGRESS.md#assessment-results-field-register).

**The accepted v2 release needs no repeat run.** The separate AR mapper now
implements the approved seventeen alternative-path additions as cumulative v3.
That expanded run is now blocked on the two value-conversion cases above;
[exact field list and current blocker](ASSESSMENT_RESULTS_START_HERE.md).
SSP code and its accepted graph/assembly are unchanged. Required registry paths were present in the actual Snowflake table
when the accepted runs passed; no outstanding registry insertion is identified
for those accepted scopes. This is recorded-run evidence, not a fresh full-registry
audit or proof that every future path exists. Keep `EXECUTE_WRITES = False`.

**Current build:** the owner approved one observation per field with a named
inline property for the seventeen rows whose original path says observations
or props. The v3 release checks those exact original field/path/Notes contracts,
retains the accepted seventeen mappings, and uses the same three registry paths.
There is no new registry insertion. The expanded runtime report is recorded as
blocked; source-shape evidence is needed before a correction.

**Remaining work:** 11 AR row occurrences are not enabled (duplicate and
conflicting Notes rows, conditional workflow properties and finding references). A shared cross-model engine with one entry
point has been discussed, but the consolidation is **not implemented**. Do not
represent that design discussion as a completed refactor or silently change the
accepted pipelines. Full-model completeness and OSCAL schema validation are also
pending. [Current AR scope and remaining decisions](ASSESSMENT_RESULTS_START_HERE.md).

The clearer Excel review identifies a skipped `HELPER_PTA_CALC` property and
a `PACKAGE_TYPE` property-name mismatch. Both are pending corrections under
System Characteristics; Control Implementation is parked. Those SSP corrections
remain uncoded and no SSP rerun is required for the separate AR release.
Historical checkpoints below retain
their original scope and do not establish completeness against the new evidence.

## Resume checkpoint - preserve passed, failed and pending work

Use this page, [Mapping Progress](MAPPING_PROGRESS.md), and the linked live
checkpoints before choosing new work. Compare the code release and source scope
with the recorded accepted release. Do not request a repeat run simply because
the conversation or notebook session restarted; rerun only when changed code,
inputs or the next task actually requires rebuilding in-memory outputs.

- **Passed:** accepted SSP mapped-scope graph/assembly, plus the seventeen-field
  AR release. These are not full-model/schema-valid claims.
- **Failed attempts:** the earlier SSP registry-schema, reference-container and
  mapping-dispatch failures remain documented below and in dated checkpoints.
  Later accepted runs supersede those failures for their corrected releases;
  do not treat old failed-run instructions as today's next action.
- **Not completed:** seventeen AR additions pending live plus eleven excluded AR
  row occurrences, the parked SSP corrections
  and source gaps, full-model conformance, persistence, and the proposed
  shared-engine consolidation remain distinct unfinished work.

Original evidence is preserved in Git history. The initial AR result is pinned
to [its original snapshot](https://github.com/theenduser009/Oscal-mapping-strategy/blob/683b0de290334cdc82675cda302f4244b10c9e0e/docs/ssp_mapping_progress_checkpoint.md#assessment-results-mapped-scope-checkpoint--2026-09-10); the expanded result is pinned to
[its accepted snapshot](https://github.com/theenduser009/Oscal-mapping-strategy/blob/05fdb9e25bd7e28661f6fbd2d868d360c8d9e0bd/docs/ssp_mapping_progress_checkpoint.md#assessment-results-mapped-scope-checkpoint--2026-09-11), so replacing an uploaded status file cannot
erase the earlier proof.

## Verified notebook

- Current live Snowflake notebook: `NB_ARCHER_OSCAL_MAPPER_V2`.
- Keep `EXECUTE_WRITES = False` while validating.
- Repository conformance target: NIST OSCAL SSP `1.2.3`, pinned in authoritative Cell 1.

## Verified mapper checkpoint

```text
Graph nodes: 70102
Graph edges: 67289
Duplicate node keys: 0
Duplicate edge keys: 0
Dangling source edges: 0
Dangling target edges: 0
PRE-WRITE VALIDATION PASSED
EXECUTE_WRITES = False
```

The earlier partial component hydration run is accepted. It retained 67,671 nodes and
64,858 edges, loaded 1,435 approved hydration rows (7 software and 1,428
interconnections), and found 7 software plus 968 interconnection descriptions.
Every structural key check passed and no DIM/FACT write occurred. The durable
[component hydration checkpoint](checkpoints/2026-09-10_ssp_component_hydration_run.md)
records the full output. The preceding component identity/type release and the
earlier metadata and system-characteristics releases remain accepted.

The existing-registry `system-characteristics` collection-contract release is
now runtime-accepted. All 114 repository tests pass, and the live rerun kept
the same healthy 67,683-node / 64,870-edge graph with no writes. The durable
[system-characteristics checkpoint](checkpoints/2026-09-09-ssp-system-characteristics-contract-run.md)
records the result.

## Minimum-required-scope checkpoint

The previous minimum-contract audit established:

```text
Required paths in minimum contract: 13
Required paths present in registry: 8
Required paths missing from registry: 5
Required paths with mapping owner: 6
Required paths without mapping owner: 7
Records meeting current minimum contract: 0
Result: NOT READY
```

Missing registry branches identified were `import-profile`, `system-information`, `information-types[]`, `control-implementation`, and `implemented-requirements[]`.

## Latest required-source readiness audit - EXECUTED 2026-09-09

The read-only OSCAL SSP 1.2.3 required-source readiness audit was executed successfully in the live Snowflake notebook.

### Safety / identity gates

```text
Session CONFIG OSCAL version: 1.2.3
Cell 7 graph validation passed: True
Cell 7 pre-write validation passed: True
Writes executed: False
Source rows: 2813
Unique source records: 2813
Unique graph records: 2813
Source/graph identity reconciled: True
Source parse errors: 0
Source path resolution errors: 0
```

### Required path action classification

The audit reviewed 13 required paths and classified them as:

```text
ADD_STRUCTURAL_REGISTRY_PATH: 3
DESIGN_COLLECTION_REGISTRY_AND_INSTANCE_MAPPING: 2
SOURCE_CANDIDATE_COLLISION_REVIEW: 1
STRUCTURE_CARDINALITY_COVERED: 7
```

Key findings:

- `system-security-plan`: registry present, 2813 generated nodes, cardinality valid for all 2813; no artifact rows required for the structural root.
- `metadata`: registry present, artifact rows=5, executable rows=4, skipped rows=1; generated coverage=2813.
- `import-profile`: registry missing, artifact rows=0, executable rows=0, generated nodes=0. Action: `ADD_STRUCTURAL_REGISTRY_PATH`.
- `system-characteristics`: registry present, artifact rows=6, executable rows=6, generated coverage=2813.
- `system-information`: registry missing, no mapping candidates. Action: `ADD_STRUCTURAL_REGISTRY_PATH`.
- `status`: registry present, artifact rows=3, executable rows=2, skipped=1; generated coverage=2813.
- `authorization-boundary`: registry present and generated coverage=2813.
- `system-implementation`: structural cardinality covered for 2813.
- `control-implementation`: registry missing. Action: `ADD_STRUCTURAL_REGISTRY_PATH`.
- `system-ids[]`: registry present; one executable candidate; generated coverage/cardinality valid for all 2813.
- `information-types[]`: registry missing. Action: `DESIGN_COLLECTION_REGISTRY_AND_INSTANCE_MAPPING`.
- `components[]`: registry present, artifact/executable rows=6, six unique source candidates; generated nodes=4804 but generated record coverage only 944. Candidate records zero=1869. Action: `SOURCE_CANDIDATE_COLLISION_REVIEW`.
- `implemented-requirements[]`: registry missing. Action: `DESIGN_COLLECTION_REGISTRY_AND_INSTANCE_MAPPING`.

Important: collection multiplicity/extra nodes are not being treated as duplicate graph-key defects. Graph duplicate keys remain zero.

### Required payload field action classification

The audit reviewed 18 required payload fields:

```text
ADD_REGISTRY_AND_MAPPING_SOURCE: 4
ADD_REGISTRY_CONFIG_VALUE_REQUIRED: 1
CONFIG_INJECTION_OR_SHAPING_REQUIRED: 1
GENERATED_VALID_FULL_COVERAGE: 3
MAPPING_SOURCE_AND_SHAPING_REQUIRED: 1
MAPPING_SOURCE_REQUIRED: 5
SOURCE_COMPLETENESS_REQUIRED: 3
```

Confirmed full generated coverage:

```text
system-characteristics.system-name: 2813
system-ids[].id: 2813
metadata.last-modified: 2813
```

For `metadata.last-modified`, **2813 means nonblank string/output presence
only**. It does not prove RFC 3339-with-timezone normalization, transformed
value equality, source precedence, or semantic completion. Two artifact rows
converge on that singleton field:
`ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED` and `LAST_UPDATED`.
Cell 4 now has a source-preserving timestamp resolver. It keeps one populated
source string unchanged, accepts identical populated candidates, and fails
closed when populated candidates differ instead of allowing mapping order to
overwrite a value. It does not infer a timezone. A live rerun is pending.

Confirmed source-completeness gaps:

```text
system-characteristics.description: candidate zero=33; generated valid=2780
status.state: candidate zero=42; generated valid=2771
authorization-boundary.description: candidate zero=294; generated valid=2520
```

These are source completeness issues, not observed mapper-loss discrepancies.

Metadata/config findings:

- `metadata.title`: no executable mapping source; action `MAPPING_SOURCE_REQUIRED`.
- `metadata.version`: no executable mapping source; action `MAPPING_SOURCE_REQUIRED`.
- `metadata.oscal-version`: controlled config `OSCAL_VERSION` is injected by
  Cell 5; the updated graph ran successfully and the exact aggregate payload
  validation passed for all 2,813 metadata nodes. The durable checkpoint
  records every failure count at zero and no writes.
- `import-profile.href`: registry absent, no mapping source, and no configured profile href; action `ADD_REGISTRY_CONFIG_VALUE_REQUIRED`.

Missing branch/field design findings include:

- `control-implementation.description`: `ADD_REGISTRY_AND_MAPPING_SOURCE`.
- `information-types[].title`: `ADD_REGISTRY_AND_MAPPING_SOURCE`.
- `information-types[].description`: `ADD_REGISTRY_AND_MAPPING_SOURCE`.
- `implemented-requirements[].control-id`: `ADD_REGISTRY_AND_MAPPING_SOURCE`.

Component hydration findings:

```text
components[].type: MAPPING_SOURCE_REQUIRED
components[].title: MAPPING_SOURCE_REQUIRED
components[].description: MAPPING_SOURCE_REQUIRED
components[].status.state: MAPPING_SOURCE_AND_SHAPING_REQUIRED
```

The current component collection remains reference-oriented and needs source/instance design before production OSCAL assembly.

### Composite record-level readiness

The audit reports:

```text
system-security-plan: generated nodes satisfy cardinality/all required fields = 2813
metadata: candidate sources cover all required fields = 0; generated nodes satisfy all required fields = 0
import-profile: 0 / 0
system-characteristics: candidate source completeness=2780; generated valid=2780
system-information: 0 / 0
status: candidate/generated valid=2771
 authorization-boundary: candidate/generated valid=2520
system-implementation: generated structural coverage=2813
control-implementation: 0 / 0
system-ids[]: candidate/generated valid=2813
information-types[]: 0 / 0
components[]: candidate/generated all-required-field coverage=0
implemented-requirements[]: 0 / 0
```

Candidate-source coverage for collections is explicitly record-level evidence only and does not prove that values correlate to the same collection member instance.

### Import-profile decision gate

```text
Registry path present: False
Artifact rows for href: 0
Executable rows for href: 0
Currently owner-aligned rows for href: 0
Candidate records with one populated value: 0
Candidate records with multiple populated values: 0
SSP_IMPORT_PROFILE_HREF configured: False
```

Decision from the audit:

> Provide the approved profile URI for `CONFIG['SSP_IMPORT_PROFILE_HREF']`; no default was invented.

This is a controlled configuration/business-governance input, not something the mapper should fabricate.

### Audit result

```text
RESULT: MAPPING-BACKLOG EVIDENCE ONLY
```

The audit never authorizes writes. Assembled OSCAL JSON schema and constraint validation remain mandatory after the minimum-contract gaps are resolved.

## Latest mapping-artifact progress audit - EXECUTED 2026-09-09

The repository now records the filtered screenshot evidence from
`archer_to_oscal_mapping.xlsx`. The visible filter reports 103 of 609 records
and confirms SSP mappings across metadata, system characteristics, extension
properties, security-impact candidates, responsible parties, components, and
control implementation.

The complete loaded-artifact
[progress audit](checkpoints/2026-09-09_SSP_MAPPING_ARTIFACT_PROGRESS_AUDIT.md)
has now been executed. Its aggregate result is:

```text
Loaded artifact rows: 608
Screenshot-reported rows: 609
Artifact identity/version/provenance reconciled: False
Explicit STATUS column: False
SSP rows retained: 104
Unique SSP row fingerprints: 104
Exact duplicate SSP rows: 0
MORE_INFORMATION_REQUIRED: 80
PRESENCE_RECONCILED: 17
NO_SOURCE_DATA: 5
NOT_APPLICABLE: 2
Artifact rows explicitly marked complete: 0
Global completion claim allowed: False
```

The 608-versus-609 baseline difference remains unresolved. The estimate that
roughly 20 items are complete cannot be treated as a governed project count:
17 rows have output-presence reconciliation, but the artifact declares none
complete and presence is not transformed-value equality.

The user's implementation priority is now explicit:

1. Use the complete Excel Archer-to-OSCAL crosswalk as the daily SSP work
   queue.
2. Preserve each concrete `OSCAL_Element_Path`, mapping type, transformation
   rule, and declared status.
3. Process unresolved mappings root-to-leaf without reworking rows already
   proven complete.
4. Use the pinned OSCAL contract for final conformance and for resolving
   ambiguity, not as a substitute for the mapping artifact.

The audit selected the first implementation-ready root-to-leaf target as:

```text
NEXT ROOT-TO-LEAF TARGET: system-security-plan.metadata.last-modified
NEXT TARGET SELECTION BASIS: IMPLEMENTATION_READY
NEXT TARGET CLASS: MORE_INFORMATION_REQUIRED
NEXT TARGET REASON: TRANSFORM_HANDLER_MISSING
```

The read-only
[metadata last-modified audit](checkpoints/2026-09-09_SSP_METADATA_LAST_MODIFIED_READINESS_AUDIT.md)
was executed. The package-prefixed candidate is empty for all 2,813 records;
`LAST_UPDATED` is populated and is the current generated value for all 2,813.
Every populated value is parseable but timezone-naive. The user chose to keep
that source value unchanged. Cell 4 therefore resolves the source cluster
without normalizing the timestamp or inferring a timezone. This remains a
final OSCAL-conformance gap, but it no longer permits silent mapping-order
overwrite.

The next safe branch change is implemented in the repository: Cell 5 injects
the controlled `CONFIG["OSCAL_VERSION"]` value into the one
`system-security-plan.metadata` payload for each source record. It copies the
payload rather than mutating mapping output, rejects missing configuration,
and fails closed if an existing mapped value conflicts with the configured
version. The authoritative notebook and split Cell 5 are synchronized. This
change has now run successfully in Snowflake.

## Latest mapper rerun - EXECUTED 2026-09-09

The user-provided
[Cell 7 + Cell 8 checkpoint](checkpoints/2026-09-09_CELL7_CELL8_OUTPUT_CHECKPOINT.md)
records the full rerun after replacing Cell 5:

```text
Graph nodes: 51500
Graph edges: 48687
Duplicate node keys: 0
Duplicate edge keys: 0
Dangling source edges: 0
Dangling target edges: 0
PRE-WRITE VALIDATION PASSED
EXECUTE_WRITES = False
```

The unchanged graph cardinality is expected because this patch changes the
metadata payload, not graph topology. Successful Cell 5 execution proves that
the configured-version, conflict, and singleton guards did not fail. The
checkpoint does not print a field-level version count, so exact 2,813-record
payload verification required a separate small check. That check is now
recorded `PASSED`: all 2,813 metadata nodes contain the configured value, every
failure count is zero, and no writes occurred. The repeated Cell 8 timestamp
conclusion is historical audit output; it does not supersede the later user
decision to preserve those timestamps unchanged.

## Locked metadata branch boundary

The Excel artifact defines 15 metadata rows. This is the fixed work slice; do
not restart discovery for each field:

| Target | Rows | Current disposition |
| --- | ---: | --- |
| `metadata.last-modified` | 2 | Source-preserving collision-safe resolver ran successfully; timezone gap retained |
| `metadata.published` | 2 | Same collision-safe resolver ran successfully; no populated-source conflict raised |
| literal `metadata.props` | 1 | `TBD`, source-empty, and not an active collection registry path |
| `metadata.document-ids[].identifier` | 1 | Exact source/output equality passed for 2,813/2,813 records |
| `metadata.responsible-parties[]` | 9 | Five executable assignments now close to generated role and `person` party objects; four `TBD` rows remain excluded |

The pinned contract additionally requires `metadata.title`,
`metadata.version`, and `metadata.oscal-version`. The approved completion rule
now reuses `AUTHORIZATION_PACKAGE_NAME` for the metadata title, sets the SSP
document version to controlled value `1.0`, and retains OSCAL version `1.2.3`.
The source field already generated `system-name` for all 2,813 records in the
accepted baseline, so no fallback title is invented.

## Security-impact production assembly - LIVE RERUN PASSED

The recorded source/runtime evidence separates the optional assembly states:

```text
No populated objective values: 2453
Partial confidentiality/integrity/availability assemblies: 90
Complete confidentiality/integrity/availability assemblies: 270
```

Cell 4 now treats
`system-security-plan.system-characteristics.security-impact-level` as one
atomic optional assembly. It emits the singleton only when all three required
security-objective strings are populated. Empty and partial assemblies are
omitted; the mapper does not invent or default a missing objective.

Cell 5 now recognizes that same path as an optional singleton and does not
recreate an omitted assembly as an empty structural node. Other structural
singleton and collection behavior is unchanged. The split cells and
authoritative notebook are synchronized, and focused tests cover complete,
empty, and partial inputs plus the structural fallback.

The read-only Snowflake rerun passed. Graph nodes and edges each fell by exactly
2,543, which equals the 2,453 empty plus 90 partial assemblies identified by
the earlier aggregate evidence. Duplicate and dangling key counts remained
zero, pre-write validation passed, and no DIM/FACT write occurred. The 270
complete security-impact assemblies remain the expected emitted population.

## Metadata completion release - IMPLEMENTED; REGISTRY RETRY PENDING

The five approved responsible-party source fields already emit role
assignments, but the prior party UUID included the source role field. That
could give one Archer party a different UUID for every role and would prevent
later creation of one reusable OSCAL party object.

Cell 4 now derives party UUIDs from the source system, SSP record, and stable
Archer party identifier without including the role field. The same party in
multiple roles therefore reuses one UUID. Duplicate source references are
removed in source order. Reference objects must expose `Id`, `UserId`, or
`ContentId`; arbitrary dictionaries no longer become identities through JSON
serialization. Missing stable identifiers fail closed with no source values in
the error.

The user approved the five executable source fields as person references.
Cell 4 now emits only referenced role definitions, one reusable `person` party
object per stable party UUID, and one deduplicated assignment per role. Cell 5
uses the party payload UUID as that node's OSCAL UUID and validates, per source
record, that every role ID and every party UUID resolves exactly once. It also
rejects unreferenced role or party objects. The four `TBD` mappings remain
excluded.

The registry remains authoritative. Cell 5 requires active
`system-security-plan.metadata.roles[]`,
`system-security-plan.metadata.parties[]`, and the existing
`system-security-plan.metadata.responsible-parties[]` rows, all parented to
metadata. The guarded setup cell derives unused process orders from the live
SSP registry, inserts only missing role/party paths, and verifies them. It is
read-only by default and never updates an existing governed row.

The first controlled registry setup attempt was blocked by Snowflake before
the new rows were inserted because the original merge omitted non-null
`ELEMENT_TYPE`. The next guarded revision also stopped before DML when its
schema preflight proved that `INSTANCE_KEY_RULE` is mandatory. Neither failed
attempt changed the registry.

The live schema and collection snapshot are now recorded. The registry has
nine columns, and the observed collection vocabulary includes
`SOURCE_FIELD_NAME`, `VALUE`, `SOURCE_FIELD_NAME+ID`, `SOURCE_FIELD_NAME+VALUE`,
and `CONTENT_ID`. Metadata collection rows use process order 3; process order
is hierarchy depth, not a globally unique sequence.

The setup now supplies and verifies the complete nine-column contract. Its
new rows reflect the mapper's actual instance identities:

```text
metadata.roles[]:
  ELEMENT_TYPE=roles
  IS_COLLECTION=TRUE
  INSTANCE_KEY_RULE=SOURCE_FIELD_NAME
  PROCESS_ORDER=3 (derived from existing metadata.responsible-parties[])
  ITEM_PATH=$

metadata.parties[]:
  ELEMENT_TYPE=parties
  IS_COLLECTION=TRUE
  INSTANCE_KEY_RULE=ID
  PROCESS_ORDER=3 (derived from existing metadata.responsible-parties[])
  ITEM_PATH=UserList[]
```

Roles are emitted once per approved source field. Party identity is derived
from each user-list member's stable identifier and is deliberately independent
of source field so the same person can be reused across roles. The schema
preflight remains fail-closed for any unrecognized mandatory column.

The live snapshot contained no ID-only party rule. The user explicitly
approved adding `ID` for this collection rather than reusing
`SOURCE_FIELD_NAME+ID`, which would contradict cross-role party reuse.

Do not rerun Cell 7 against either failed setup attempt. Run the latest setup
cell first and require its final verification message.

The subsequent Cell 7 attempt no longer stopped on missing role/party registry
paths; it reached responsible-party parsing and failed with the sanitized
"reference has no stable identifier" guard. The live registry evidence explains
the source shape: responsible-party values use `ITEM_PATH=UserList[]`, while
Cell 4 previously unwrapped other Archer containers but not `UserList`.

Cell 4 and the authoritative notebook now unwrap that exact governed container
before applying the existing stable `Id`, `UserId`, or `ContentId` checks. It
does not accept arbitrary dictionaries, invent an identity, print a source
value, or alter registry/DIM/FACT data. Focused wrapper and full metadata tests
pass, and the complete suite is green.

## Current engineering interpretation

The graph engine is no longer the primary problem. Its structural integrity remains clean. The backlog is now separated into four concrete categories:

1. **Structural registry additions** - `import-profile`, `system-information`, `control-implementation`.
2. **Collection design + instance mapping** - `information-types[]` and `implemented-requirements[]`.
3. **Component collection/source collision + hydration design** - current `components[]` coverage is 944/2813 records and six candidate source mappings need deliberate reconciliation.
4. **Required field sourcing/configuration** - import-profile href, component fields, plus known source-completeness gaps of 33/42/294 records.

The Excel mapping artifact is now the primary sequencing source for that
backlog. The minimum-contract findings remain valid final-completeness gates,
but they do not determine which spreadsheet-defined mapping should be worked
next when an earlier root-to-leaf row is still unresolved.

Do not patch individual records. Do not invent required controlled values. Do not enable writes.

## System-characteristics collection integrity release - RUNTIME ACCEPTED

The accepted live registry snapshot already defines the two collection
contracts needed for this increment:

```text
system-characteristics.props[]:
  INSTANCE_KEY_RULE=SOURCE_FIELD_NAME+VALUE
  ITEM_PATH=$

system-characteristics.system-ids[]:
  INSTANCE_KEY_RULE=VALUE
  ITEM_PATH=$
```

Cell 4 now converts every emitted property value to a canonical nonblank
string. Boolean values become lowercase JSON-style strings, finite scalar
values become trimmed strings, and unresolved objects, nested lists, blanks,
or non-finite values fail closed without exposing source values.

Property instance identity now derives from source field plus normalized
value, rather than list position. System-ID identity now derives from its
normalized value, rather than the generic `singleton` key. Identical governed
identities are deduplicated; a conflicting payload for one identity fails
closed. Reordering a multi-value property no longer changes its node identity.

Cell 5 now retains and verifies the live registry collection flag,
`INSTANCE_KEY_RULE`, and `ITEM_PATH` for these two paths before graph
construction. No registry DML is required.

The singleton aggregator no longer lets canonical mapping row order choose a
winner when two populated mappings target the same field. Identical
transformed values are accepted; distinct values fail closed with a sanitized
error. This applies the policy-free collision rule to the multiple
security-impact candidates without inventing recommended-versus-override
precedence. Security objective text is limited to normalized FIPS values and
the eight reviewed legacy LOE labels.

The known source-owned gaps remain unchanged: 33 records lack a system
description, 42 lack a status state, and 294 lack an authorization-boundary
description. `system-information` and `information-types[]` are not part of
this release because the checked-in evidence has neither governed registry
paths nor source mappings for them.

The post-release Cell 7 run completed with 67,683 nodes and 64,870 edges, zero
duplicate node or edge keys, zero dangling source or target edges, passed
pre-write validation, and `EXECUTE_WRITES = False`. The unchanged counts are
accepted evidence that the governed collection identities caused no data loss
for this source population. No further system-characteristics rerun is needed.

## Component source contract - EXECUTED; IDENTITY/TYPE RELEASE IMPLEMENTED

The next root-to-leaf branch is
`system-security-plan.system-implementation.components[]`. The parent
`system-implementation` singleton already has full 2,813-record structural
coverage. The live registry snapshot gives an exact contract for
`components[]`: parent `system-implementation`, collection true, instance rule
`CONTENT_ID`, and item path `$`. Cell 5 now verifies that contract without
changing any registry row.

Six executable Archer `Reference` mappings target the collection: subsystems,
software, hardware, and three interconnection sources. Current generic
collection handling uses source field plus list position and therefore cannot
be promoted as the component implementation. The checked-in artifacts also do
not prove the live reference-container shape or show whether title,
description, and status are carried inside each reference.

The one-time aggregate
[component source-contract checkpoint](checkpoints/2026-09-09-ssp-component-source-contract.md)
is complete. It reconciled all 4,804 populated references: 4,452 explicit
`ContentId` object members and 352 scalar content-ID members. The object shape
is exactly `ContentId,LevelId`; no object carries title, description, or
status. Seven SSP records contain cross-field overlap, covering 12 governed
IDs. No source identifier or value was printed, and no data was changed.

Cell 4 now implements the six proved `Reference` mappings. It requires each
mapping's declared component-type signal, accepts only the two observed source
shapes, canonicalizes `ContentId` to a string, uses it as member identity, and
emits the proved component type. Identical content ID and type pairs collapse
to one node; a content ID with conflicting types fails closed without printing
the ID. Cell 5 adds the node's deterministic OSCAL UUID to its component
payload and verifies the recorded parent, collection flag, `CONTENT_ID` rule,
and `$` item path. No registry DML is required.

The read-only post-release Cell 7 run is accepted. It completed with **67,671
nodes** and **64,858 edges**, zero duplicate node or edge keys, zero dangling
source or target edges, passed pre-write validation, and
`EXECUTE_WRITES = False`; no DIM or FACT changes were made. Relative to the
previous accepted graph, both counts decreased by exactly 12. That matches the
12 governed component IDs already proved to overlap across source fields, so
the change is the intended identity deduplication rather than data loss.

This is a component identity/type release, not full component hydration. The
source references do not contain the required title, description, or status,
and Cell 2 currently loads no referenced component table. Those remaining
fields need an approved lookup source keyed by `ContentId`; they are not
invented here.

The subsequent aggregate-only
[component lookup discovery](ssp_component_lookup_discovery_2026-09-10.md)
completed successfully with zero profiling failures and no writes. It
reconciled 4,792 component occurrences to 1,436 distinct IDs and proved that
all 1,436 appear in at least one candidate object. The three generic
`ARCHER_META_CONTENT` layers match every ID but expose no recognized hydration
fields, so they are identity evidence only-not title, description, or status
sources. The interconnections-named RAW object matches 1,428 IDs and the
software-named RAW object matches seven. The remaining one governed ID is the
hardware reference; table-to-Excel-field ownership is not inferred from those
object names.

The evidence is not yet a hydration contract. Interconnections have complete
`INTERCONNECTION_NAME` coverage, only 968 populated `DESCRIPTION` values, a
small third-party-name/description subset, and no observed status field.
Software has two possible title fields and four possible status fields for all
seven records. Hardware has no proved type-specific source. No source, field,
precedence, or status transformation has been approved.

## Component source-routing audit - EXECUTED; ROUTES PROVED

The Excel-driven routing audit completed read-only and reproduced the accepted
baseline exactly:

```text
Canonical Excel component mapping rows: 6
Reference occurrences: 4804
Distinct source-record/component/type pairs: 4792
Graph component nodes: 4792
Distinct component IDs: 1436
Invalid reference members: 0
Cross-type component IDs: 0
Source pairs missing from graph: 0
Graph pairs missing from source: 0
Invalid graph component nodes: 0
Lookup source profiling failures: 0
Accepted-baseline drift checks: 0
Writes executed: False
```

The source routing is now evidence-backed rather than inferred from object
names. All seven software IDs match only
`ARCHER_CONTENT_SOFTWARE_RAW`. All 1,405 primary interconnection IDs and all
82 connecting-information-system IDs match only
`ARCHER_CONTENT_INTERCONNECTIONS_RAW`. The one hardware ID matches neither
hydration-bearing candidate. The two inactive Excel fields have no runtime
references.

The run printed `Unexpected non-array reference roots: 15632`, but that count
is a reporting defect rather than proved source-shape failure: SQL `IS NOT
NULL` also includes a VARIANT containing JSON `null`. It did not affect array
extraction, route matching, field coverage, or graph reconciliation. The cell
now reports JSON-null roots separately and treats only other non-array values
as unexpected. The count reconciles exactly: 2,813 records x six fields =
16,878 roots; the prior source-contract audit proved 1,246 populated array
roots; 16,878 - 1,246 = 15,632 absent JSON-null roots. No repeat run is
required for the accepted routing evidence.

The remaining real blockers are field-contract or source-data decisions:

- Software: source route complete; `SOFTWARE_NAME` versus `BUSINESS_NAME` and
  four status candidates require a governed choice. `DESCRIPTION` is complete.
- Interconnections: source route complete; `INTERCONNECTION_NAME` is complete,
  `DESCRIPTION` is populated for only 968 of 1,428 IDs, alternate third-party
  fields cover small subsets, and no status candidate was found.
- Hardware: its one reference has no proved hydration source.

## Partial component hydration - RUNTIME ACCEPTED

The owner approved this evidence-backed increment:

```text
software:
  source = ARCHER_CONTENT_SOFTWARE_RAW
  title = SOFTWARE_NAME
  description = DESCRIPTION
  status = deferred pending approved field/value crosswalk

interconnection:
  source = ARCHER_CONTENT_INTERCONNECTIONS_RAW
  title = INTERCONNECTION_NAME
  description = DESCRIPTION when populated; preserve missing-source gap
  status = deferred because no source candidate exists

hardware:
  retain current UUID/type only until its source is supplied
```

The release is now implemented in the authoritative notebook and synchronized
split Cells 2, 4, and 5. Cell 2 opens only the two exact approved RAW lookup
sources. Cell 4 validates the exact six Excel component mappings, extracts only
the three approved hydration routes server-side, joins by canonical
`ContentId`, and collects only routed ID/title/description rows. It rejects
ambiguous physical columns, blank or duplicate lookup IDs, missing approved
lookup rows, malformed lookup JSON, missing or non-text titles, incomplete
software descriptions, populated non-text interconnection descriptions, and
cross-type identities before graph construction. No identifier or source value
is printed.

Component assembly is source-field gated. `SOFTWARE`, `INTERCONNECTIONS`, and
`INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM` can hydrate. `SUBSYSTEMS`,
`HARDWARE`, and `SAP_INTAKE_FORM_INTERCONNECTIONS` retain UUID/type-only
behavior even if an identically named lookup record exists. A component seen
in both an approved and deferred interconnection field is emitted once and is
hydrated from the approved occurrence. Node keys, instance keys, UUID policy,
and containment edges are unchanged. Cell 5 also rejects any unapproved
component status field.

The live read-only Cell 7 run completed successfully with 1,435 hydration
lookup rows: 7 software rows with 7 descriptions and 1,428 interconnection
rows with 968 descriptions. The graph remained 67,671 nodes and 64,858 edges,
with zero duplicate keys, zero dangling edges, pre-write validation passed,
and `EXECUTE_WRITES = False`. This is the expected result because hydration
changes payload content without changing node or edge identity.

## Immediate next action

### Active implementation - Assessment Results; SSP corrections parked

The owner chose to pause remaining SSP work and continue matching Assessment
Results score mappings. The cumulative seventeen-field release is live accepted.
The newly approved seventeen alternative-path additions are implemented in the
34-field v3 release. That run has now completed in blocked state; do not repeat
it unchanged. Resolve the two rejected-value source shapes first. The
[progress register](MAPPING_PROGRESS.md) separates seventeen accepted fields,
seventeen additions pending live, eleven excluded rows and recorded source gaps.
Shared-engine consolidation remains a proposal, not completed work.
No SSP mapper configuration, registry, DIM or FACT changes are part of this release.

### Parked Excel review - two System Characteristics corrections, not coded

Model **SSP**, target `system-security-plan.system-characteristics.props[]`:
map `HELPER_PTA_CALC` according to row 35's Calculated/custom-property Notes,
and reconcile `PACKAGE_TYPE` to the example property name
`authorization-package-type`. The distinct `PACKAGE_TYPE_HELPER_CALC` remains
excluded by its explicit do-not-map Notes. See the
[short summary](SSP_DONE_AND_NEXT.md). No code change or notebook rerun yet.

### Parked - control-count correction proposed, not coded

Model: **SSP**. The new Control Implementation screenshots do contain a
detailed Option 1 example in Notes for
`COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS`. The earlier generic
summary omitted it. Its proposed `control-implementation.props[]` location
conflicts with the pinned standard model; no custom extension was approved.

Recommended mapping-owner review: use
`system-security-plan.metadata.props[]` for the SSP-wide summary, with property
name `controls-missing-implementation-details-count`. Copying the existing
Archer count is proposed, not yet confirmed. The namespace also needs approval.
Keep the original Excel evidence unchanged. The
[one-row correction proposal](checkpoints/2026-09-10_ssp_control_count_mapping_proposal.md)
contains the observed Notes, standard-model evidence and exact decisions.
**No mapper/registry code changes or Snowflake run are needed until the row is approved.**
No new mapping has been counted as complete. The existing accepted graph and
assembly remain valid for their recorded scope.

### Current checkpoint - mapped-scope SSP assembly ACCEPTED

The newest [live result](live-snowflake-results.md) completes the date/property
release: **70,102 nodes, 67,289 edges, zero duplicate or dangling keys,
pre-write validation passed, writes false**. Hydration remains 1,435 lookup
rows, with 7 software and 968 interconnection descriptions. This is now the
accepted graph-runtime baseline, not final SSP conformance or per-field equality
proof. The prior failure is resolved at this checkpoint.

**Model: SSP. Assembly root: `system-security-plan`.** The assembly includes
all currently mapped branches, including the active component branch
`system-security-plan.system-implementation.components[]`.

The latest posted result confirms **2,813 documents and 2,813 roots assembled**,
consuming **70,102 nodes and 67,289 edges**. Result:
`MAPPED-SCOPE ASSEMBLY PASSED`; writes false; complete SSP claim false;
OSCAL schema-valid claim false. The component release's graph-to-JSON step is
now accepted. [Assembly checkpoint](checkpoints/2026-09-10_ssp_mapped_scope_assembly_accepted.md).

**No repeat notebook, registry, report or assembly run is required.** Keep
`EXECUTE_WRITES = False`. Documents are transient in the notebook session, not
persisted to DIM/FACT or exported. This does not add mapping rows or establish
complete SSP conformance. Each next mapping handoff identifies the OSCAL model,
exact target path, source field and transformation rule.

Separately, the user requested ten additional Excel-defined SSP rows. The earlier
review considered the available concrete contracts implemented; that conclusion
is superseded by the two clearer-screenshot discrepancies above. Other candidates
include 50 blank-target control rows and TBD mappings. The full current
workbook/CSV is not present in the repository.

For a complete ten-row backlog, use a current SSP mapping export with Archer field, OSCAL model, approved
target path, mapping type and Notes. To build ten genuinely new mappings it
must contain ten additional executable rows, or the owner must supply their
missing targets/rules. No target paths will be invented or existing work counted
again. Details and count reconciliation:
[accepted checkpoint](checkpoints/2026-09-10_ssp_date_property_run_accepted.md).

The assembly step is complete. The two evidenced property corrections can move
forward without waiting for a full workbook export; additional rows still need
their own approved contracts and source evidence.

### Previous implementation handoff - superseded by successful run above

The latest [live report](live-snowflake-results.md) inspected **54 canonical
SSP mappings** and identified two unsupported contracts. It supplied the exact
`ATOIATO_DATE`  `system-security-plan.system-characteristics.date-authorized`
rule: type `Transform`, Notes `Convert timestamp to DateDatatype`.
The second row is `RECOMMENDED_SECURITY_CATEGORY` with Notes `All Nulls`.
These are contract counts, not populated-record counts or completed mappings.

Cell 4 now implements the authorization-date rule for valid ISO date/timestamp
strings and native dates: emit `YYYY-MM-DD` on the existing parent singleton,
retain the source calendar day, and make no timezone shift. The parser checks
calendar/time/offset validity; ambiguous locale strings, epochs and wrappers
require source evidence instead of guessing. Existing `published` and
`last-modified` values are unchanged. The all-null row is also unchanged:
absent values skip, populated values fail without an approved contract.

The now-completed run instruction was to replace only
[Cell 4](../notebooks/cells/04_parsing_transform_payload_helpers.py), then run
**4, 5, 6, 7** in the existing session with `EXECUTE_WRITES = False`.
If the session restarted, run all seven. No registry setup or contract-report
rerun is needed. Post Cell 7's complete output. Run the mapped-scope assembler
only if Cell 7 succeeds.

203 local tests pass, including date conversion, invalid dates/offsets,
unchanged metadata timestamps and canonicalization-to-graph regressions.
The successful run above now establishes runtime acceptance for this release;
exact field-level coverage remains distinct from that acceptance.
See the [date release checkpoint](checkpoints/2026-09-10_ssp_authorization_date_mapping.md).

The new [mapping register](MAPPING_PROGRESS.md) tracks source field, OSCAL
model/path, implementation, live acceptance, payload proof and remaining gaps.
[Today's report](daily/2026-09-10.md) is ready for manager review; it has not been
sent to the manager. Daily reporting in this task is scheduled for **5 PM
Eastern**. Keep the computer and app running for scheduled local-file work.

### Previous correction - property routing (retained for context)

The accepted component hydration run remains the baseline. The newest
[live result](live-snowflake-results.md) is a **Cell 7 mapper failure**, not a
recorded failure of the standalone dispatcher diagnostic. Hydration loaded
1,435 rows successfully before the mapper rejected `INFORMATION_SYSTEM_TYPE`
as an `extension-property` owned by `system-security-plan.system-characteristics`.
The recorded target-field text is truncated; its exact suffix is not assumed.

**Cause and correction:** Cell 3 used registry-prefix matching alone and left
the approved property on the parent. Cell 4 correctly requires property
instances to belong to `props[]`. Cell 3 now routes the eight explicitly
screenshot-confirmed property sources into that existing collection. Original
artifact paths/explicit targets remain available, with a separate
`CANONICAL_ELEMENT_PATH` for ownership. No source values, unknown transforms,
other branches, timestamp rules, or registry definitions are changed.

The prior instruction was to replace Cell 3 and rerun the graph. That run
reached the authorization-date failure, now addressed in the release above.
Both the Cell 4 run and older report instructions are now superseded by the
successful checkpoint; no repeat run is required.

All **189 local tests** pass, including eight new regressions through actual
Pandas canonicalization and existing property/graph logic. The graph test
checks one parent per source record, deduplicated property payloads and
within-record parent/child keys. Snowflake transport and unrelated component
lookup I/O are faked locally; **live acceptance is pending**, and this does not
prove all externally loaded Excel rows are supported. See the
[routing correction checkpoint](checkpoints/2026-09-10_ssp_property_routing_fix.md).

