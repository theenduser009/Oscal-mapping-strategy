# Validation 05 repair and seven-cell contract checkpoint

Date: **2026-09-15**  
Branch: `simplify-metadata-boundary`  
Original repair baseline: `9c28ab11fd9cdb4cfe0697da0f0ce0fbe3b70202`  
Validator implementation commit: `6ca52a18dedfecdc4734f9307dfd0f86ab8b30a7`  
Regression-test commit: `87ec6d77d6a5453dab2150cf142e39568d717355`  
Repository head inspected before recording the owner result: `564b77543c1b70df05ad87976d5214ecad8b5d24`

## Current outcome — owner-run Validation 05 PASS

**New evidence received 2026-09-15:** the owner supplied the completed Snowflake notebook report for validator version `2026-09-15-r2`. It reports `STATUS: PASS`, `FAILURE_COUNTS: {}`, and `WRITES_PERFORMED_BY_VALIDATOR: false`.

This supersedes the earlier **live Validation 05 result pending** statement for the corrected r2 validator and this reported preview only. Earlier failed validator attempts remain invalid test results; they are not retroactively passed. This update does not turn the known timestamp failure into a pass or establish full SSP conformance.

Evidence type: **owner-provided screenshot of an executed notebook report**, not an independent assistant connection/query to Snowflake. The screenshot's validator version and visible report format match the repository r2 validator; the screenshot is not a cryptographic attestation of all notebook source bytes. The frozen source snapshot's ingestion/as-of time is not supplied in this report.

### Aggregate output transcribed from the screenshot

```json
{
  "VALIDATION": "05_SSP_METADATA_GRAPH_AND_SELECTED_PAYLOADS",
  "VALIDATOR_VERSION": "2026-09-15-r2",
  "STATUS": "PASS",
  "SOURCE_RECORDS": 2813,
  "METADATA_BRANCH_NODES": 33696,
  "NODE_COUNTS_BY_PATH": {
    "system-security-plan.metadata": 2813,
    "system-security-plan.metadata.document-ids[]": 2813,
    "system-security-plan.metadata.parties[]": 9382,
    "system-security-plan.metadata.responsible-parties[]": 9344,
    "system-security-plan.metadata.roles[]": 9344
  },
  "SCALAR_VALUES_CHECKED": {
    "title": 2813,
    "version": 2813,
    "oscal-version": 2813
  },
  "METADATA_RELATED_EDGES": 33696,
  "RESPONSIBLE_PARTY_NODES": 9344,
  "PARTY_REFERENCES_CHECKED": 9477,
  "ROLE_PARTY_REFERENCE_COVERAGE": "EXERCISED",
  "FAILURE_COUNTS": {},
  "TIMESTAMPS": "KNOWN_FAILED_LEXICAL_CHECK_REMEDIATION_DEFERRED_SME",
  "NOT_TESTED": [
    "Full OSCAL schema conformance",
    "Business approval of field meaning",
    "Complete source-to-party assignment reconciliation",
    "Target persistence",
    "Document-ID equality/uniqueness (separate Validation 04)"
  ],
  "WRITES_PERFORMED_BY_VALIDATOR": false,
  "SOURCE_KEY": "source-one"
}
```

Only aggregate results are published. The private screenshot and its run identifier remain in the project conversation; no private source identifiers, payloads, or people names are reproduced here. Party/role counts are graph instances across SSP records, not a count of globally distinct people.

### What now has owner-run evidence

Within the implemented checks, the report supports:

- Exactly one Metadata node for each of the 2,813 source records.
- Metadata `title`, `version`, and `oscal-version` are nonblank strings matching the values selected by their compiled source/configuration rules; 2,813 values of each were checked.
- Candidate node/instance identity checks, compiled parent paths, one incoming parent edge per Metadata-branch node, record ownership, and edge endpoint UUID equality passed.
- Basic role and party payload checks passed. Responsible-party roles and all 9,477 checked party references resolved **within the same SSP**, rather than merely somewhere in another SSP's graph.
- The configured payload UUID-emission checks passed. A graph `OSCAL_UUID` and a JSON payload `uuid` remain distinct concepts.
- Role/party checks were actually exercised, not skipped due to empty data.

Document-ID nodes are included in the branch graph checks, but their identifier/source equality is not tested by 05. No complete source-to-party assignment reconciliation is inferred from reference integrity alone.

### Current next action

No unchanged Validation 05 rerun is requested. Keep the existing preview and writes disabled. The next proposed test is **Validation 06 — System Characteristics**, beginning with a bounded batch of system-name, short-name, description, and system-ID checks against actual compiled rules and source values. Inspect the current implementation and test the validator locally before publishing it. This checkpoint does not create a Validation 06 script or claim it has run.

Timestamps remain a **known failed lexical check with remediation DEFERRED_SME**. Full schema conformance, semantic approval, remaining source-to-party reconciliation, and target persistence remain separate work. Profile/import-profile and Control Implementation remain deferred.

## Prior repair action — historical, now superseded by the owner report above

The previous action was to replace only the Validation 05 Python cell with [the updated same file](../../notebooks/validation/05_ssp_metadata_graph_validation.py), run it in the existing successful SSP PREVIEW session, and capture the aggregate report. At that point the replacement was implemented and locally regression-tested but its live result was pending. The owner has now supplied that result.

No mapper, CSV, registry, source binding, DIM/FACT, or timestamp transformation was changed for the repair or this report update.

## Superseded errors

Earlier Validation 05 attempts used names that do not exist in the current runtime. Those executions establish validator defects, not SSP defects or passes. The r2 revision supersedes the earlier 05 implementation at the same filename; it does not retroactively validate any failed attempt.

| Incorrect assumption | Verified contract |
| --- | --- |
| `ELEMENT_REGISTRY_DF` | Cell 2 reads `REGISTRY_INPUT_ROWS`; a completed graph carries its compiled registry snapshot in its context. |
| `ctx["ELEMENT_REGISTRY"]` | Cell 3 returns **`ctx["registry_rows"]`**. There is no `ELEMENT_REGISTRY` key. |
| Candidate `PK_ELEMENT_HASH` | Cell 5 emits **`NODE_KEY`**, `ELEMENT_PATH`, `INSTANCE_KEY`, and the other canonical graph columns. Physical DIM key naming is a separate Cell 6 storage contract. |
| Guessed top-level node variables | Cell 7 retains **`MODEL_GRAPHS[(source_key, "SSP")]["nodes"]`**, `edges`, and `context`. |
| UUID policy `omit` removes graph identity | Every canonical node has `OSCAL_UUID`; `omit` controls whether `uuid` is emitted inside `METADATA_JSON`. |
| An edge UUID merely exists somewhere | Validate it against that edge's actual parent/child node. Role/party payload references must resolve inside the same SSP/source record. |

The validator uses the context retained with the graph, checks it against current compilation/run settings, and checks dataframe columns before selecting them. It imports its own standard-library dependencies and does not depend on another validation cell having imported `json`, `re`, or `Counter`.

## Source inspection and version evidence

At the repair checkpoint, all seven maintained files under `notebooks/cells/` were inspected end-to-end. Their GitHub blob hashes matched the exact local source bytes extracted from the project code bundle; the generated `cells_v2` copies had the same hashes. The older bundle date alone was not used as evidence of current equality. The following records that repair's inspection, not a new live byte-for-byte attestation of the owner's notebook.

| Cell | Git blob SHA |
| --- | --- |
| 01 | `bb90243a4397ef0d836ec2481277474c237f422c` |
| 02 | `7a682e4d9cd38c19e12a742daed26b16f81fd100` |
| 03 | `08151f3835a537f2d01552b750bde7dd077b71a0` |
| 04 | `ad72ff385c1bfc9e477ee9c60a4f76e2405321d6` |
| 05 | `896ccc44e1136f723dbb0569de7da9e680b4a4ad` |
| 06 | `a206e316427b3aac7d20f4bb25c9af73c3a54c0b` |
| 07 | `1e6af68af07f66c2fb6bebfb72da2cb40eed9c6a` |

Mapping CSV blob recorded at repair: `869cc29a07d9def2bdcf3005026caed1bf1248e2`.

Validation 05 blob: `7bc8ec9c09deefd13670e04634a0dedb0738afd6`.
Validation 05 SHA-256: `e84148deee0c4f297e87baaa6d80a79e0656699ad68d058f4af43550c0ad429b`.

The validator was fetched again at repository commit `564b77543c1b70df05ad87976d5214ecad8b5d24` before this report update, and the same blob SHA was returned.

## Tests actually performed

At the repair checkpoint, Python compilation succeeded. **28 local regression tests passed, zero failures/errors.** The test module is [tests/lean/test_ssp_validation_05.py](../../tests/lean/test_ssp_validation_05.py). Those tests were not rerun for this documentation-only update.

```bash
python -m unittest discover -s tests/lean -p test_ssp_validation_05.py -v
```

The tests use the actual repository configuration, CSV loader, compiler, Metadata assemblers, graph builder, targetless Cell 6 graph validation, and Cell 7 orchestration. They supply two synthetic records and an explicitly synthetic Metadata registry. A minimal dataframe/session adapter replaces Snowflake access; its database read/write entry points reject calls. This is **not** an installed Snowpark SQL-emulator run or full-repository regression run. Source-input selection, target storage/loading, component hydration, and unrelated models were not exercised by those local tests.

Negative tests include old registry/PK names, malformed payloads, missing Metadata nodes, blank and mismatched titles, wrong document-version values, missing edges, stale run IDs, changed compiled plans, incorrect endpoint UUIDs, unresolved roles, duplicate party references, and a party UUID that exists only in a different SSP. Other tests verify input objects remain unchanged, the validator runs without prior validation imports, and its report does not print private source record values.

The new owner-run screenshot is separate live execution evidence for 05's reported scope. It does not replace the local test evidence or prove checks not implemented in the validator.

## What this validation proves and does not prove

Checks include:

- Metadata appears exactly once for each source record in the existing snapshot.
- Candidate node/instance identities, compiled parent paths, edge parentage, and edge endpoint UUIDs are coherent.
- The generated `title`, `version`, and `oscal-version` are nonblank strings equal to their configured source/config values.
- Role and party payload basics are present; responsible-party `role-id` and `party-uuids` resolve inside the same SSP.
- Payload UUID emission follows the compiled policy.

`PASS` applies only to these checks. Empty optional role/party coverage is labelled `NOT_EXERCISED`, not claimed as exercised; the new owner report explicitly shows `EXERCISED`. Full source-to-party assignment reconciliation, business appropriateness of each mapping, complete OSCAL schema conformance, document-ID equality/uniqueness, timestamps, and target persistence are outside this validator's scope. The validator is not a replacement for complete official model/schema validation.

## Prior test evidence remains bounded

- **01:** owner reported registry validation passed; screenshots showed the 19-row inventory and branch/process-order results. This is not full SSP conformance.
- **02:** owner screenshot reported mechanical compilation PASS, with 48 approved SSP rows plus one populated-value guard. This is not field-semantic approval.
- **03:** the observed lexical timestamp test **failed** for 5,626 of 5,626 values. **Remediation is DEFERRED_SME**, not a passing timestamp result. Preserve original timestamps; do not infer UTC from product documentation alone. The extraction timezone question remains in [SME_OPEN_QUESTIONS](../../questions/SME_OPEN_QUESTIONS.md).
- **04:** owner screenshot showed 2,813 document-ID nodes passing that script's scalar/nonblank and within-record duplicate checks. The old script did not prove complete source equality or PK integrity; its displayed PK sample used a nonexistent key. Do not broaden its PASS beyond checks actually executed.
- **05:** earlier scripts failed due to validator defects. The corrected `2026-09-15-r2` now has owner-run **PASS** evidence for 2,813 source records and the exact limited checks described above.

## Delivery and evidence boundaries

The repair changed the validator, its tests, and this checkpoint. This subsequent owner-result update changes **this checkpoint only**. It does not alter any executable file or enable a Snowflake write. GitHub publication/read-back of this document is distinct from the owner-run preview report and from target-table commit/read-back verification.

The next action is the bounded System Characteristics validation described above, not another mapper rebuild or rerun of unchanged accepted tests. Preserve all unresolved semantic and source questions.
