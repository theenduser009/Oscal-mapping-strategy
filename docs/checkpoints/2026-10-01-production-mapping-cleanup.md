# Production mapping cleanup and minimal lineage prop — 2026-10-01

Base inspected: theenduser009/Oscal-mapping-strategy / simplify-metadata-boundary at 5590ac35c24cb691f9476b50f2f925f25bcb5bbc.

Implemented:
- runtime CSV reduced from 27 to 18 columns
- all 155 rows retained; operational settings preserved
- one canonical OSCAL_ELEMENT_PATH; INFORMATION_SYSTEM_TYPE normalized to props[]
- pre-cleanup CSV archived verbatim
- production header enforced for the configured Source One profile
- RUNTIME_TARGET_PATH and CSV RULE_ID removed from execution logic
- LINEAGE_REQUIRED compiled directly
- lineage prop simplified to name + ns + value; no class
- one lineage prop per contributing source field/host
- cells_v2 and combined notebook synchronized
- validator 17 and focused lineage tests updated
- production CSV contract test added

Unchanged intentionally: namespace urn:company:oscal:lineage:v1, 12 Y mappings,
transforms, null policies, role/reference behavior, graph containment, loader
safety, and destination schemas.

Evidence boundary:
The earlier live PREVIEW with 3,581 four-key lineage props belongs to the
superseded runtime. This repository change performs no Snowflake DML and does not
prove the new three-key payload live.

Next action:
Upload the cleaned CSV and matching seven cells, run SSP PREVIEW, then run
notebooks/validation/17_ssp_selective_lineage_contract_validation.py. No COMMIT
until the fresh PREVIEW and validator are reviewed.


## Repository validation actually performed

Code commit: `f5e5755d3e4eaeb733452fd1b65352def49188e0`

GitHub Actions run: `36897565862`

Confirmed:
- generated notebook synchronization check passed
- `test_production_mapping_contract` passed
- all 9 selective-lineage focused tests in `test_universal_lineage_props` passed
- the production CSV has 155 rows, exactly 18 runtime columns, and 12 LINEAGE_REQUIRED=Y rows
- read-back inspection confirmed Cell 5 no longer emits a lineage `class`

The full historical `tests/lean` suite remains red: 270 tests ran with 38
failures and 96 errors. The log includes known historical/fixture compatibility
issues, stale expectations for removed provenance/RULE_ID columns and older
153-row counts, plus local end-to-end fixtures that do not provision newer
Source One lookup tables. This full-suite failure is **not** being treated as a
successful production release.

No live Snowflake PREVIEW has yet been run for the new three-key lineage payload.


## NOTES retained for transition review

Owner decision on 2026-10-01: keep `NOTES` for a while as a human review aid. The clean CSV therefore has 19 columns. Execution does not read NOTES; Cell 2 accepts it only as an explicitly optional column. All other retired provenance/history columns remain removed.


## Seven-cell release-marker correction

A fresh Snowflake PREVIEW attempt failed before commit with `Run the matching Cell 5 before Cell 7`. Root cause was a repository packaging mismatch introduced during the v7 cleanup: Cell 5 advertised `lean-csv-registry-v7-production-clean` while Cell 7 still checked for `lean-csv-registry-v6-lineage-required`.

Corrected and read back on 2026-10-01. Current head after the fix: `8e7129b77e2f56dd7395888b3bc2b02041dcdec0`. A dedicated release-marker test was added so Cells 3/4/5/7 cannot silently drift again. No Snowflake DML occurred; the failed run was `FAILED_BEFORE_COMMIT` with `writes_executed=false` and `commit_attempted=false`.


## Fresh Snowflake SSP PREVIEW after cleanup

Owner-provided live notebook evidence on 2026-10-01 after loading the cleaned CSV and matched seven-cell release:

- pipeline status: `PREVIEW_COMPLETE`
- model/source: `SSP / source-one`
- `writes_executed=false`
- `persisted=false`
- `committed=false`
- `target_dml_attempted=false`
- `pre_write_validation_passed=true`
- `validation_passed=true`
- `storage_verified=true`
- source records: `2813`
- candidate nodes: `550380`
- candidate edges: `547567`
- DIM expected changes: `3581 inserts / 0 updates / 546799 unchanged`
- FACT expected changes: `3581 inserts / 0 updates / 543986 unchanged`
- `LINEAGE_PROPS=3581`
- `LINEAGE_GAPS=0`
- `LINEAGE_COMPLETE=true`
- load status: `PREVIEW_PASSED_NO_TARGET_DML`
- temporary cleanup: `REMOVED`

Interpretation: the cleaned mapping contract and matched seven-cell release now build and validate successfully in live Snowflake PREVIEW. This proves the candidate graph/storage checks and no-DML safety for this run. It does **not yet** prove that every lineage payload has exactly the new minimal `name + ns + value` shape; run validation helper 17 next before any COMMIT.


## Namespace removed from selective lineage — 2026-10-01

Owner decision: remove `urn:company:oscal:lineage:v1` entirely. The selective lineage payload is now only `{"name":"source-field","value":"<ARCHER_FIELD_NAME>"}`. Traceability does not depend on a namespace: the lineage DIM row carries `SOURCE_RECORD_ID` (the Archer Content ID), the property `value` carries the exact Archer source field name, the mapping CSV resolves that source field to `OSCAL_ELEMENT_PATH`, and the FACT containment edge ties the lineage prop to the corresponding OSCAL graph context. This supersedes the earlier three-key namespace-bearing lineage payload. Fresh PREVIEW is required before COMMIT because the live 3,581-prop validation was for the superseded namespace-bearing payload.


## Live trace helper check after namespace removal

Owner-provided Snowflake screenshots on 2026-10-01 show `notebooks/validation/18_ssp_lineage_trace_sample.py` executing and resolving lineage source fields to their canonical OSCAL targets. Visible examples include OPERATIONAL_STATUS -> system-security-plan.system-characteristics.status.state and the confidentiality/integrity/availability override fields -> their corresponding security-impact-level objective paths. The helper is also coded to print ARCHER_CONTENT_ID from SOURCE_RECORD_ID, but the uploaded screenshots crop the leftmost output, so the actual Content ID values are not independently readable from this evidence. This confirms the trace mechanism structure, not yet a full v8 PREVIEW acceptance.


## Namespace-free v8 live lineage validation PASS

Owner-provided Snowflake output on 2026-10-01 from the current namespace-free validator confirms:
- EXPECTED LINEAGE FIELDS = 12
- LINEAGE NODES = 3581
- REPORTED LINEAGE PROPS = 3581
- INVALID LINEAGE PROPS = 0
- DUPLICATE LINEAGE PROPS = 0
- LINEAGE_CONTRACT_VALIDATED = True

The current Git validator was read back at branch head bb74552529044cf800777781551a0cb6b8b490c3 and contains no lineage namespace requirement. Therefore this live result proves the namespace-free two-key custom property shape (name + value) for all 3,581 candidate lineage props. The populated source-field counts remain OPERATIONAL_STATUS 2771 and the availability/confidentiality/integrity override fields 270 each; the remaining eight configured lineage fields are absent in this source snapshot.

This completes the namespace-free SSP PREVIEW lineage gate. No target COMMIT/read-back has yet been performed for v8.


## Namespace-free v8 lineage validator PASS

Owner-provided Snowflake output on 2026-10-01 confirms the current namespace-free validator passed across all candidate SSP lineage properties: EXPECTED LINEAGE FIELDS=12, LINEAGE NODES=3581, REPORTED LINEAGE PROPS=3581, INVALID LINEAGE PROPS=0, DUPLICATE LINEAGE PROPS=0, and LINEAGE_CONTRACT_VALIDATED=True. The populated source-field counts remain OPERATIONAL_STATUS=2771 and the availability/confidentiality/integrity override fields=270 each; the other eight configured fields produced no lineage rows in this source snapshot. This validates the v8 two-key lineage payload (name + value) in PREVIEW. No target COMMIT/read-back has yet been performed for v8.


## Namespace-free v8 SSP COMMIT and read-back verification

Owner-provided Snowflake COMMIT output on 2026-10-01 shows:
- pipeline status: COMMITTED_AND_VERIFIED
- source/model: source-one / SSP
- writes_executed=true
- persisted=true
- committed=true
- target_dml_attempted=true
- pre_write_validation_passed=true
- validation_passed=true
- storage_verified=true
- source_records=2813
- nodes=550380
- edges=547567
- expected DIM changes before commit: 3581 inserts / 0 updates / 546799 unchanged
- expected FACT changes before commit: 3581 inserts / 0 updates / 543986 unchanged
- post-commit verification DIM: 0 inserts / 0 updates / 550380 unchanged
- post-commit verification FACT: 0 inserts / 0 updates / 547567 unchanged
- load status: COMMITTED_AND_VERIFIED
- temporary_cleanup=REMOVED

Interpretation: the committed target state matches the namespace-free v8 candidate graph and is read-back verified. The post-commit zero-insert/zero-update verification establishes immediate idempotency for this exact graph. Any later mapping CSV cleanup is a new version and must go through a fresh PREVIEW before another COMMIT.


## Verified Archer meta-value resolution for FIPS candidate

Owner-confirmed live lookup on 2026-10-01: Archer SELECT_VALUE_ID 162407 resolves to SELECT_VALUE_NAME `Legacy LOE C` in `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE`.

For the inspected Content ID 867022, the populated confidentiality, integrity, and availability override fields each carried `ValuesListIds:[162407]`; the committed OSCAL security-impact members therefore contain `Legacy LOE C`. This is consistent with the current `security-objective` transform and the mapping CSV's reviewed legacy allowed-values contract. This checkpoint confirms the ID-to-label resolution step for that concrete value; it does not imply all FIPS candidate IDs have been individually verified.


## FIPS payload-to-Archer-field live trace

Owner-provided Snowflake result on 2026-10-01 for Content ID 867022 shows the committed `security-impact-level` payload repeated alongside all 11 reviewed Archer candidate fields. The visible committed OSCAL payload has confidentiality, integrity, and availability objective members populated as `Legacy LOE C`. The three visible populated Archer source fields are `AVAILABILITY_CONTROL_CATEGORY_OVERRIDE`, `CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE`, and `INTEGRITY_CONTROL_CATEGORY_OVERRIDE`; each carries `ValuesListIds:[162407]`. The other reviewed candidate rows shown are null for this record. This corroborates the earlier verified Archer meta-value resolution `162407 -> Legacy LOE C` and demonstrates the payload-to-source-field trace for the inspected Content ID.


## CIA/FIPS semantic reconciliation — 2026-10-01

Fresh review of the actual source note, current mapper code, and historical acceptance shows two distinct rules that must not be conflated. The original SSP System Characteristics source note says all security-impact values must normalize to FIPS 199 low/moderate/high. The current mapper does resolve Archer select IDs through ARCHER_META_VALUE and normalizes labels already recognized as low/moderate/high, but it also preserves explicitly allowed Legacy LOE strings from the mapping CSV. Historical project guidance explicitly recorded that full FIPS normalization was not established and that no Legacy LOE -> FIPS equivalence should be invented without evidence. Therefore the currently committed v8 payload is technically read-back verified, but Legacy LOE values inside security-objective-* are not proof of source-note FIPS normalization. No runtime change is made by this checkpoint. Next evidence step is read-only inventory of actual select IDs/labels across the 11 CIA candidate fields using sql/validation/SSP_CIA_SOURCE_VALUE_AUDIT.sql, followed by an owner-approved crosswalk only if noncanonical legacy labels must be converted.


## Matillion meta-reference enrichment candidate — 2026-10-01

Owner-provided live metadata evidence now confirms:
- `ARCHER_META_VALUES` resolves `VALUEID -> VALUENAME`; the owner reports these values include the canonical CIA labels such as High/Low.
- `ARCHER_META_GROUP` exposes `GROUP_ID`, `GROUP_NAME`, and `GUID` (owner screenshot).

A new DEV-only Matillion candidate is committed at
`sql/matillion/CANDIDATE_enrich_curated_json_users_values_groups.sql`.
It preserves original Archer IDs and enriches existing `CURATED_JSON` with:
- `UserList[].ResolvedUser`
- field-level `ResolvedValues[]` from `ValuesListIds[]`
- field-level `ResolvedGroups[]` from `GroupList[]`

A matching read-only post-run validator is committed at
`sql/matillion/READ_ONLY_POST_META_REFERENCE_ENRICHMENT_VALIDATION.sql`.

Validation performed here: repository source inspection, branch/head verification, exact file creation, and Git read-back. No Snowflake/Matillion execution was performed from chat. The existing user-only Matillion candidate remains historical and is not proof that value/group enrichment has executed.

Next action: place/run the new candidate in Matillion DEV after the existing raw-to-CURATED_JSON conversion, then run the read-only validator and capture its result before simplifying notebook-side Archer meta lookups. Do not remove the notebook fallback until the Matillion enrichment is persisted and read-back verified.


## CORRECTION — Matillion meta-reference contract — 2026-10-01

This section supersedes the immediately earlier Matillion meta-reference candidate note where the value table/columns were recorded incorrectly.

Owner correction and live evidence:
- Value lookup table is `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE`.
- Value key is `SELECT_VALUE_ID`.
- Resolved label is `SELECT_VALUE_NAME`.
- Example owner-provided value ID: `80664`; its business label is read from `SELECT_VALUE_NAME`.
- Group lookup table is `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_GROUP`.
- Group key is `GROUP_ID`.
- Resolved group label is `GROUP_NAME`.
- The Matillion enrichment does not require `GUID` for the current group-resolution contract.

The current Git candidate and matching read-only validator were corrected to those exact contracts. The earlier commit using `ARCHER_META_VALUES / VALUEID / VALUENAME` is superseded and must not be run. No Matillion or Snowflake execution was performed from chat.

Next action remains: run the corrected DEV Matillion candidate, then run the corrected read-only post-enrichment validator. Keep notebook-side lookup fallback until that persisted enrichment is read-back verified.


## Post-enrichment validator result — value/group enrichment not yet present — 2026-10-01

Owner-provided Snowflake screenshots from `READ_ONLY_POST_META_REFERENCE_ENRICHMENT_VALIDATION.sql` show:
- USER_MEMBER_OCCURRENCES = 55,782
- USER_MEMBERS_RESOLVED = 55,782
- VALUE_ID_OCCURRENCES = 185,440
- RESOLVED_VALUE_OCCURRENCES = 0
- MATCHED_VALUE_OCCURRENCES = 0
- VALUE_NOT_FOUND_OCCURRENCES = 0
- VALUE_IDENTITY_MISMATCHES = 185,440
- GROUP_ID_OCCURRENCES = 192,141
- RESOLVED_GROUP_OCCURRENCES = 0
- MATCHED_GROUP_OCCURRENCES = 0
- GROUP_NOT_FOUND_OCCURRENCES = 0
- BAD_GROUP_STATUS_OCCURRENCES = 0
- GROUP_IDENTITY_MISMATCHES = 192,141
- STATUS = REVIEW_BEFORE_OSCAL

The sample CIA/FIPS result also shows populated `ValuesListIds` (examples include 80654, 162409, 162411, 162405) while `ResolvedValues` is NULL.

Interpretation: the previously deployed UserList enrichment is present, but the new ValuesListIds/GroupList enrichment is not persisted in the inspected CURATED_JSON. This result does not prove a lookup failure: if the corrected candidate had executed and merely missed a lookup, it is designed to emit VALUE_NOT_FOUND/GROUP_NOT_FOUND rows rather than zero resolved arrays. Do not simplify notebook lookups yet.

Next action: execute the corrected DEV Matillion candidate `sql/matillion/CANDIDATE_enrich_curated_json_users_values_groups.sql` and capture the Matillion affected-row/result status. Then rerun the same read-only validator. If the Matillion component reports zero rows updated or the validator remains unchanged, stop and inspect candidate eligibility/blocking rather than retrying blindly.


## Matillion raw-load incident diagnosis and integrated replacement — 2026-10-01

Owner reported that a pipeline run populated RAW_DATA but left CURATED_JSON null. Repository inspection found the exact cause: the recently supplied file
`sql/matillion/CANDIDATE_enrich_curated_json_users_values_groups.sql`
is a **post-CURATED enrichment** statement. Its source predicate requires
`TYPEOF(r.CURATED_JSON) = 'OBJECT'` and its target predicate also requires
`TYPEOF(tgt.CURATED_JSON) = 'OBJECT'`. Therefore it cannot create CURATED_JSON
for newly loaded rows where CURATED_JSON is SQL NULL. Used in the raw-load
Matillion component, it updates zero such rows.

A new integrated replacement is committed:
`sql/matillion/CANDIDATE_raw_curated_with_meta_user_value_group_enrichment.sql`.

This new statement starts from the previously accepted raw -> CURATED_JSON SQL,
preserves source-side `TRY_TO_NUMBER(FIELD_ID)` safety, existing type conversion,
nested extraction, JSON-null key preservation, RequestedObject.Id -> CONTENT_ID,
and both `CURATED_JSON IS NULL` pending-row guards. It then enriches the newly
built candidate JSON with UserList, ValuesListIds, and GroupList metadata.
Malformed/ambiguous enrichment falls back to the un-enriched newly built
CURATED_JSON for that record rather than preventing raw-to-curated conversion.

Validation performed in chat: current branch/source inspection and Git read-back
of the integrated file. No Matillion/Snowflake execution of the integrated
replacement has yet been observed. The post-CURATED enrichment file remains
valid only for already-populated CURATED_JSON and must not be used as the
raw-load conversion component.

Next action: replace the raw-load Matillion SQL with the integrated replacement,
run once in DEV, and verify CURATED_JSON is populated before any notebook
simplification.


## Matillion metadata enrichment spot checks — 2026-10-01

Owner-confirmed live spot checks after running the integrated raw->CURATED_JSON enrichment:
- ValuesListIds enrichment is working; example value ID 80654 resolves with LookupStatus=MATCHED and ValueName=Low.
- GroupList enrichment is also working; owner confirmed the group-ID resolution result is good.

These are field-level live confirmations of both value and group enrichment. They do not by themselves replace the full aggregate validator summary; retain the overall post-enrichment validation gate before removing notebook-side fallback lookups.


## v9 notebook consumes Matillion-resolved values — 2026-10-01

Owner-confirmed upstream evidence now supports moving the select-value resolution boundary into Matillion:
- value ID 80654 is persisted in CURATED_JSON with ResolvedValues LookupStatus=MATCHED and ValueName=Low;
- GroupList enrichment is also owner-confirmed good; the posted sample shows GroupId 268 resolving to GroupName `Global Archer: Read Access` for populated group-list fields.

Repository implementation:
- new matched mapper release: `lean-csv-registry-v9-matillion-resolved-meta`;
- Cell 1 no longer configures `ARCHER_META_VALUE_TABLE`;
- Cell 2 no longer queries `ARCHER_META_VALUE`; production lookup maps are empty compatibility containers only;
- Cell 4 consumes `ResolvedValues[]` from CURATED_JSON first, verifies source-ID/cardinality/status identity, and normalizes matched Low/Moderate/High labels for security-objective mappings;
- unresolved, mismatched, malformed, or cardinality-conflicting ResolvedValues fail closed;
- reviewed Legacy LOE labels remain governed by the existing mapping CSV allowed-values contract; no new LOE-to-FIPS equivalence is invented;
- Cells 3/4/5/7 use the same v9 release marker;
- maintained cells, cells_v2, and the combined notebook are synchronized;
- the 155-row/19-column mapping CSV is unchanged.

Repository validation actually performed:
- generated notebook synchronization check passed in GitHub Actions;
- all five focused Matillion-resolved FIPS tests pass: canonical Low/Moderate/High normalization, direct-text compatibility, fail-closed identity/status/cardinality checks, removal of the runtime meta-value-table dependency, and reviewed Legacy LOE preservation;
- the historical full lean suite is still red: 272 tests ran with 30 failures and 102 errors. The remaining failures are dominated by pre-existing stale 153-row, retired RULE_ID/provenance, old routing/registry fixture, and historical persistence expectations. This is not being treated as a green full-suite release.

Evidence boundary:
No Snowflake execution of the v9 seven-cell mapper has yet been observed. The namespace-free v8 COMMIT/readback remains the persisted baseline; it does not prove v9 candidate values.

Next action:
Load the matched v9 Cells 1-7 in Snowflake, keep `EXECUTE_WRITES=False`, run SSP PREVIEW only, and post the full pipeline/group report. Do not COMMIT v9 until that fresh PREVIEW is reviewed.


## Cell 2 blocked by missing source identity — 2026-10-01

Owner-provided Snowflake screenshot shows the v9 run stopping in Cell 2 at
`load_source_input` with:
`ValueError: Source contains missing record identities`.

Fresh repository read-back confirms Cell 2 intentionally rejects any source row
whose configured `CONTENT_ID` is SQL NULL or blank before deduplication/model
fan-out. This is an upstream source-integrity gate, not a mapper transform error.
Do not weaken Cell 2 by filtering or inventing a source identity.

The exact upstream cause is not yet proven. A new read-only diagnostic is
committed at:
`sql/matillion/READ_ONLY_SOURCE_IDENTITY_CURATED_GAP.sql`.

It reports whole-table missing CONTENT_ID / CURATED_JSON counts, RAW_DATA physical
types, RequestedObject.Id coverage, identity mismatches, and only the affected
problem rows. No Snowflake DML is performed.

Next action: run that diagnostic and inspect all three result sets before making
another Matillion or notebook change. The v9 PREVIEW has not started; v8 remains
the last committed/read-back verified OSCAL target baseline.


## v10 curated-resolved-only notebook cleanup — 2026-10-01

Owner decision: for the current Source One snapshot, rows with both missing CONTENT_ID and SQL-NULL CURATED_JSON are treated as empty source shells and skipped so the run can proceed. Populated curated rows without identity still fail closed. The two owner-inspected shell records have empty Archer FieldContents and no curated business payload.

Implemented release: `lean-csv-registry-v10-curated-resolved-only`.

Runtime changes:
- Cell 2 no longer carries Archer select/FIPS lookup maps at all.
- `load_source_lookups` now loads only component and joined-record hydration inputs.
- Cell 2 reports `NULL_SOURCE_SHELLS_SKIPPED` and excludes only missing-identity rows whose CURATED_JSON is SQL NULL; a populated CURATED_JSON with missing identity remains a blocking error.
- Cell 4 uses Matillion `ResolvedValues[]` as the production select-value source, verifies ValueId/source-ID identity, MATCHED status and cardinality, then maps the resolved label.
- Low/Moderate/High handling is now only OSCAL CIA normalization of an already-resolved label. There is no ARCHER_META_VALUE/FIPS lookup in the notebook runtime.
- The reviewed Legacy LOE fallback contract remains in mapping metadata; no new LOE-to-FIPS crosswalk was introduced.
- Mapping CSV remains unchanged at 155 rows / 19 columns.
- Cells 1/3/4/5/7 share the v10 release marker; cells_v2 and the combined notebook are synchronized.

Repository validation actually performed:
- GitHub generated-notebook synchronization gate passed.
- Focused source-shell test passed: null identity + null curated payload is skipped and counted.
- Populated curated payload with missing identity still fails closed.
- Focused resolved-value tests pass for canonical Low/Moderate/High normalization, direct text compatibility, fail-closed resolved-value identity/status/cardinality checks, removal of runtime ARCHER_META_VALUE dependency, and reviewed Legacy LOE preservation.
- Historical full lean suite remains red: 273 tests ran with 31 failures and 105 errors, dominated by existing stale RULE_ID/153-row/routing/persistence fixture expectations. This is not a green full-suite release.

Evidence boundary:
No live Snowflake v10 PREVIEW has yet been observed. v8 remains the last target COMMIT/read-back baseline.

Next action:
Replace Snowflake notebook Cells 1-7 with the matched v10 files and run Cell 2 first. Expected Source One selection report for the currently observed snapshot is RAW_ROWS=2812, NULL_SOURCE_SHELLS_SKIPPED=2, SELECTED_ROWS=2810 (subject to source changes). If Cell 2 succeeds, continue Cells 3-7 in PREVIEW with EXECUTE_WRITES=False and review the resulting CIA/security-impact payload and DIM/FACT delta before any COMMIT.


## Cell 7 component-hydration failure — 2026-10-01

Owner-provided Snowflake Cell 7 screenshot shows v10 PREVIEW stopping before any
group publication/commit:
- mode = PREVIEW
- status = FAILED_BEFORE_COMMIT
- groups = []
- writes_executed = false
- commit_attempted = false
- failed_route = source-one / SSP
- error_type = ValueError
- error_message = Component hydration lookup record is missing

Fresh code/history review confirms this is not part of the Matillion select-value
or FIPS cleanup. It is the previously accepted SSP component-hydration contract.
The mapper intentionally fails closed if a hydrated SOFTWARE or INTERCONNECTION
reference ContentId is absent from its configured lookup table.

Current executable component hydration bindings remain:
- SOFTWARE -> ARCHER_CONTENT_SOFTWARE_RAW (title + required description)
- INTERCONNECTIONS -> ARCHER_CONTENT_INTERCONNECTIONS_RAW
- INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM -> ARCHER_CONTENT_INTERCONNECTIONS_RAW
The other approved component reference fields do not currently request hydration.

Historical evidence dated 2026-09-09/10 showed the component source contract and
a successful read-only hydration run for the then-current 2,813-record snapshot.
That historical acceptance does not prove the current daily snapshot still has
complete lookup coverage.

No mapper behavior was changed in response to this failure. A new read-only
diagnostic is committed at:
sql/validation/READ_ONLY_SSP_COMPONENT_HYDRATION_GAP.sql

It reports:
1) coverage/missing counts by hydrated Archer source field,
2) exact current missing component references and parent SSP record,
3) lookup-table identity/null/duplicate health.

Next action: run the three SELECTs from that file. If the gap is current lookup
coverage or lookup-table raw-load health, repair/reload the corresponding
upstream component source. Do not remove the hydration guard or skip component
records merely to make PREVIEW pass.


## Component hydration root cause confirmed — lookup tables empty — 2026-10-01

Owner-provided live Snowflake results from
`sql/validation/READ_ONLY_SSP_COMPONENT_HYDRATION_GAP.sql` establish the
current failure cause.

Coverage summary:
- `INTERCONNECTIONS`: 4,444 reference occurrences / 1,405 distinct referenced IDs; 0 matched; all 4,444 missing.
- `INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM`: 352 occurrences / 82 distinct IDs; 0 matched; all 352 missing.
- `SOFTWARE`: current diagnostic shows populated references but 0 matched.

Lookup-table health proves why all hydration misses:
- `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_SOFTWARE_RAW`: 0 rows.
- `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_INTERCONNECTIONS_RAW`: 0 rows.

Therefore Cell 7's `Component hydration lookup record is missing` is not a
v10 FIPS/ResolvedValues regression and should not be bypassed in notebook code.
The accepted component hydrator is correctly failing closed because the two
configured upstream lookup sources are empty in the current DEV snapshot.

Historical September component-hydration acceptance used populated lookup
sources and cannot be used as proof for the current daily snapshot.

Next action:
reload/populate the two component lookup raw tables through their normal
Matillion/source ingestion path, then rerun only the lookup-table health query
and the component coverage summary. Once lookup rows are present and coverage
returns matched IDs, rerun Cells 1-7 in PREVIEW with writes disabled. Do not
remove the hydration guard or fabricate component title/description values.


## v10 Cell 7 reached target preflight and hit obsolete-row guard — 2026-10-01

Owner-provided Snowflake screenshot shows the current SSP PREVIEW progressed past
source loading, Matillion-resolved values, graph construction, and component
hydration, then stopped in loader PREPARATION with:
- mode = PREVIEW
- status = FAILED_BEFORE_COMMIT
- groups = []
- writes_executed = false
- commit_attempted = false
- failed_route = source-one / SSP
- error_type = LoadError
- error_message = OBSOLETE_TARGET_ROWS_BLOCKED
- loader release = oscal-lean-daily-v3.2-lineage
- target_dml_attempted = false
- pre_write_validation_passed = false
- lineage_gaps = 0

This is the loader's existing anti-delete/daily-loss guard. It means at least
one target DIM/FACT row inside the current source-record scope is absent from
the candidate stage. The guard fires before MERGE and therefore no target DML
occurred.

Do not weaken the guard or rerun Cell 7 before inspecting the failed PREVIEW's
temporary stage tables. Existing read-only helper:
`notebooks/validation/12_ssp_obsolete_target_rows_diagnostic.py`
was designed for this exact condition and must be run in the SAME Snowflake
notebook session immediately after the failure. Preparation failures retain the
TMP_OSCAL_* stage set for diagnosis.

Next action: run that helper as the next cell and capture its OBSOLETE SUMMARY,
DIM BY ELEMENT TYPE, classification, top affected source records, and FACT BY
DEPENDENCY TYPE. Use those results to distinguish intended identity changes
from real source-data loss before any loader/mapping change.


## v10 SSP PREVIEW passed unchanged against committed target — 2026-10-01

Owner-provided Snowflake Cell 7 screenshot shows a successful live SSP PREVIEW after
the upstream supporting loads completed.

Observed report:
- mode = PREVIEW
- status = PREVIEW_COMPLETE
- source = source-one
- model = SSP
- loader release = oscal-lean-daily-v3.2-lineage
- writes_executed = false
- persisted = false
- committed = false
- target_dml_attempted = false
- pre_write_validation_passed = true
- validation_passed = true
- storage_verified = true
- lineage_gaps = 0
- nodes = 550,380
- edges = 547,567
- source_records = 2,813
- DIM expected changes: INSERTS 0 / UPDATES 0 / UNCHANGED 550,380
- FACT expected changes: INSERTS 0 / UPDATES 0 / UNCHANGED 547,567
- load status = PREVIEW_PASSED_NO_TARGET_DML
- temporary_cleanup = REMOVED
- lineage props = 3,581
- lineage gaps = 0
- lineage complete = true

This is strong live evidence that the current v10 candidate graph is byte/field
equivalent, under the loader's stored comparison contract, to the current committed
SSP target scope: no inserts, no updates, and no obsolete-row block. It also confirms
the prior component-hydration/allocated-control preparation failures were upstream
data-readiness issues rather than a required mapper bypass.

Important boundary: this is PREVIEW/read-only evidence only. It does not constitute a
new COMMIT. The last persisted target remains the previously read-back verified v8
commit, although the v10 candidate currently proposes zero target changes.

Next action: no target write is required for SSP if the intent is only to reconcile the
current target, because PREVIEW proposes zero DML. Before declaring the v10 code release
accepted, review one focused in-memory CIA/security-impact sample from MODEL_GRAPHS to
confirm ResolvedValues are being consumed as intended even though the persisted target
requires no update.


## CIA ResolvedValues validation helper added — 2026-10-01

After the successful unchanged SSP PREVIEW, a focused read-only in-memory validator
was added at:
`notebooks/validation/19_ssp_cia_resolved_values_validation.py`.

Purpose:
- prove the v10 clean boundary from Matillion `ResolvedValues[]` to the
  candidate SSP `security-impact-level` payload;
- compare each populated CIA/security-objective mapping to the actual in-memory
  candidate value;
- report canonical Low/Moderate/High normalization separately from reviewed
  legacy-label occurrences;
- fail on any source-ID / ResolvedValues identity mismatch, cardinality mismatch,
  unresolved status, or source-to-candidate value mismatch.

No database DML/DDL is performed. Live execution is still pending. The helper
must be run in the same notebook session after the successful Cells 1-7 PREVIEW
while `MODEL_GRAPHS` and `SOURCE_INPUTS` are still present.

Acceptance signal:
`MISMATCHES = 0` and `CIA_RESOLVED_VALUES_VALIDATED = True`.


## CIA validation helper corrected for atomic security-impact assembly — 2026-10-02

Owner-provided execution of validation helper 19 showed correct Matillion-resolved traces such as ValueId 80654 -> Low -> OSCAL low and reviewed Legacy LOE labels preserved, but the helper reported a mismatch on a source record with a populated CIA field.

Fresh code/test review established the issue was in the validation helper, not the v10 mapper. The governed security-impact-level object is an atomic optional assembly: its registry REQUIRED_MEMBERS contract requires all CIA objective members before the node is emitted. Historical regression tests/test_ssp_security_impact_atomic_emission.py explicitly verifies that zero, one, or two populated objectives emit no security-impact-level instance, while a complete CIA set emits one singleton.

The original helper incorrectly compared every populated CIA field to a candidate security-impact node, so a valid incomplete source record appeared as a mismatch.

notebooks/validation/19_ssp_cia_resolved_values_validation.py is now corrected to distinguish complete CIA records from incomplete records skipped by design, require no partial node for incomplete records, and compare candidate payload values only for complete CIA records. No production mapper/runtime/mapping CSV code was changed for this correction.

Next action: rerun only helper 19 in the same successful PREVIEW notebook session. Acceptance requires SOURCE_TARGET_CONFLICTS=0, MISSING_COMPLETE_NODES=0, UNEXPECTED_PARTIAL_NODES=0, MISMATCHES=0, and CIA_RESOLVED_VALUES_VALIDATED=True.


## CIA ResolvedValues validation PASSED — 2026-10-02

Owner-provided Snowflake execution of `notebooks/validation/19_ssp_cia_resolved_values_validation.py` completed successfully in the same live PREVIEW session.

Observed results:
- CIA_MAPPING_FIELDS = 11
- REQUIRED_CIA_MEMBERS = confidentiality, integrity, availability
- SOURCE_RECORDS_CHECKED = 2,813
- SECURITY_IMPACT_NODES = 270
- POPULATED_CIA_FIELD_OCCURRENCES = 901
- RESOLVEDVALUES_OCCURRENCES = 901
- CANONICAL_LOW_MODERATE_HIGH_OCCURRENCES = 110
- REVIEWED_LEGACY_OCCURRENCES = 791
- COMPLETE_CIA_RECORDS = 270
- INCOMPLETE_CIA_RECORDS_SKIPPED_BY_DESIGN = 90
- COMPLETE_TARGET_COMPARISONS = 810
- SOURCE_TARGET_CONFLICTS = 0
- MISSING_COMPLETE_NODES = 0
- UNEXPECTED_PARTIAL_NODES = 0
- MISMATCHES = 0
- final signal: CIA_RESOLVED_VALUES_VALIDATED = True

This is read-only live proof that v10 consumes Matillion `ResolvedValues[]` correctly, preserves the atomic security-impact-level assembly contract, and produces candidate OSCAL CIA member values consistent with the configured transformations. It also confirms 90 source records have incomplete CIA membership and are intentionally omitted rather than emitting partial security-impact-level objects.

Important semantic gap retained: 791 populated CIA occurrences currently resolve to reviewed Legacy LOE labels rather than canonical low/moderate/high. This validation proves transport/mapping consistency; it does not establish a Legacy LOE -> FIPS 199 equivalence. The 110 canonical occurrences are normalized to low/moderate/high as intended.

Combined with the successful unchanged SSP PREVIEW (0 DIM inserts/updates, 0 FACT inserts/updates, 550,380 nodes, 547,567 edges, lineage complete), the v10 runtime behavior is live validated for the current Source One snapshot. No target write is required to reconcile the current persisted target because PREVIEW proposed zero DML.

Next action: decide separately whether the remaining Legacy LOE labels require an owner-approved business/FIPS crosswalk. Do not invent that crosswalk. If no such semantic conversion is currently required, proceed to the next Source One QA/closeout checkpoint without committing SSP target changes.


## CIA ResolvedValues validation accepted — 2026-10-02

Owner-provided Snowflake output from corrected helper 19 passed with the following live results: CIA_MAPPING_FIELDS=11; SOURCE_RECORDS_CHECKED=2813; SECURITY_IMPACT_NODES=270; POPULATED_CIA_FIELD_OCCURRENCES=901; RESOLVEDVALUES_OCCURRENCES=901; CANONICAL_LOW_MODERATE_HIGH_OCCURRENCES=110; REVIEWED_LEGACY_OCCURRENCES=791; COMPLETE_CIA_RECORDS=270; INCOMPLETE_CIA_RECORDS_SKIPPED_BY_DESIGN=90; COMPLETE_TARGET_COMPARISONS=810; SOURCE_TARGET_CONFLICTS=0; MISSING_COMPLETE_NODES=0; UNEXPECTED_PARTIAL_NODES=0; MISMATCHES=0; final signal CIA_RESOLVED_VALUES_VALIDATED=True.

This is live read-only proof that every populated CIA source occurrence observed by the v10 run was supplied through Matillion ResolvedValues, that all 270 complete CIA records emitted exactly one complete security-impact-level object, and that 90 incomplete records emitted no partial object by design. No production mapper change was needed after the helper correction.

Semantic boundary retained: 110 populated occurrences are canonical Low/Moderate/High and normalize to low/moderate/high; 791 occurrences are reviewed Legacy LOE labels and remain preserved. This acceptance proves mapping/runtime consistency, not a Legacy LOE -> FIPS equivalence.

The next Source One validation is the broader exact-path QA required by the September 29 review. Existing helper 14 was refreshed for the current v10 mapping contract: retired RULE_ID/RUNTIME_TARGET_PATH dependencies were removed, a stable current mapping key is derived from model/source/owner/relative target, and CIA atomic value sampling is delegated to accepted helper 19. No runtime mapper or mapping CSV was changed by this QA-helper update.


## Focused SSP props QA introduced — 2026-10-02

Owner rejected the broad Source One QA output as insufficient for closeout because relationship-exception labels and aggregate evidence do not prove each field mapped to its exact OSCAL property. That assessment is accepted: helper 14 remains a triage/inventory report, not final field-by-field proof.

A new root-level read-only helper was added: RUN_SSP_PROPS_ONE_BY_ONE.py. It validates one props[] branch at a time and prints each mapping separately with Archer SQL field name, Archer display field name, FIELD_ID, FIELD_TYPE_ID, LevelId context, exact OSCAL props[] path, exact expected prop name, source present/populated/null counts, target records with that exact prop name, exact transformed-value matches, mismatches, and deterministic sample Content IDs.

The helper intentionally does not use the generic field-type-9/23 relationship-exception shortcut. For a props mapping it compares the exact transformed property value to the exact emitted property name/value.

Default starting scope is system-security-plan.metadata.props[]. Current mapping CSV has one approved mapping in that branch: ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER. After that branch is reviewed, the same helper can be switched by changing QA_PROP_PATH to system-security-plan.system-characteristics.props[].

No production mapper, mapping CSV, or target data was changed by this QA helper. Live execution is pending.
