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
