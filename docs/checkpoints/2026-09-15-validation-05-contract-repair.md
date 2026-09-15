# Validation 05 repair and seven-cell contract checkpoint

Date: **2026-09-15**  
Branch: `simplify-metadata-boundary`  
Inspected baseline: `9c28ab11fd9cdb4cfe0697da0f0ce0fbe3b70202`  
Validator implementation commit: `6ca52a18dedfecdc4734f9307dfd0f86ab8b30a7`  
Regression-test commit: `87ec6d77d6a5453dab2150cf142e39568d717355`

## Current action

Replace only the previous Validation 05 Python cell with [the updated same file](../../notebooks/validation/05_ssp_metadata_graph_validation.py) and run it in the existing successful SSP PREVIEW session. Do not rerun the mapper or earlier validations merely for this repair. Keep writes false and Cell 7 in PREVIEW. Capture the aggregate `=== SSP VALIDATION 05 ===` report.

The replacement is implemented and locally regression-tested. **Its live Snowflake result is still pending.** No mapper, CSV, registry, source binding, DIM/FACT, or timestamp transformation was changed.

## Superseded errors

Earlier Validation 05 attempts used names that do not exist in the current runtime. Those executions establish validator defects, not SSP defects or passes. This revision supersedes the earlier 05 implementation at the same filename; it does not retroactively validate any failed attempt.

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

All seven maintained files under `notebooks/cells/` were inspected end-to-end. Their current GitHub blob hashes matched the exact local source bytes extracted from the project code bundle; the generated `cells_v2` copies have the same hashes. The older bundle date alone was not used as evidence of current equality.

| Cell | Git blob SHA |
| --- | --- |
| 01 | `bb90243a4397ef0d836ec2481277474c237f422c` |
| 02 | `7a682e4d9cd38c19e12a742daed26b16f81fd100` |
| 03 | `08151f3835a537f2d01552b750bde7dd077b71a0` |
| 04 | `ad72ff385c1bfc9e477ee9c60a4f76e2405321d6` |
| 05 | `896ccc44e1136f723dbb0569de7da9e680b4a4ad` |
| 06 | `a206e316427b3aac7d20f4bb25c9af73c3a54c0b` |
| 07 | `1e6af68af07f66c2fb6bebfb72da2cb40eed9c6a` |

Current mapping CSV blob: `869cc29a07d9def2bdcf3005026caed1bf1248e2`.

Validation 05 blob: `7bc8ec9c09deefd13670e04634a0dedb0738afd6`.
Validation 05 SHA-256: `e84148deee0c4f297e87baaa6d80a79e0656699ad68d058f4af43550c0ad429b`.

## Tests actually performed

Python compilation succeeded. **28 local regression tests passed, zero failures/errors.** The test module is [tests/lean/test_ssp_validation_05.py](../../tests/lean/test_ssp_validation_05.py).

```bash
python -m unittest discover -s tests/lean -p test_ssp_validation_05.py -v
```

The tests use the actual repository configuration, CSV loader, compiler, Metadata assemblers, graph builder, targetless Cell 6 graph validation, and Cell 7 orchestration. They supply two synthetic records and an explicitly synthetic Metadata registry. A minimal dataframe/session adapter replaces Snowflake access; its database read/write entry points reject calls. This is **not** an installed Snowpark SQL-emulator run, full-repository regression run, or live Snowflake acceptance. Source-input selection, target storage/loading, component hydration, and unrelated models were not exercised.

Negative tests include old registry/PK names, malformed payloads, missing Metadata nodes, blank and mismatched titles, wrong document-version values, missing edges, stale run IDs, changed compiled plans, incorrect endpoint UUIDs, unresolved roles, duplicate party references, and a party UUID that exists only in a different SSP. Other tests verify input objects remain unchanged, the validator runs without prior validation imports, and its report does not print private source record values.

## What this validation proves and does not prove

Checks include:

- Metadata appears exactly once for each source record in the existing snapshot.
- Candidate node/instance identities, compiled parent paths, edge parentage, and edge endpoint UUIDs are coherent.
- The generated `title`, `version`, and `oscal-version` are nonblank strings equal to their configured source/config values.
- Role and party payload basics are present; responsible-party `role-id` and `party-uuids` resolve inside the same SSP.
- Payload UUID emission follows the compiled policy.

`PASS` applies only to these checks. Empty optional role/party coverage is labelled `NOT_EXERCISED`, not claimed as exercised. Full source-to-party assignment reconciliation, business appropriateness of each mapping, complete OSCAL schema conformance, document-ID equality/uniqueness, timestamps, and target persistence are outside this validator's scope. The NIST metadata reference describes the role/party reference concepts; the validator is not a replacement for the complete official model/schema validation.

## Prior test evidence remains bounded

- **01:** owner reported registry validation passed; screenshots showed the 19-row inventory and branch/process-order results. This is not full SSP conformance.
- **02:** owner screenshot reported mechanical compilation PASS, with 48 approved SSP rows plus one populated-value guard. This is not field-semantic approval.
- **03:** the observed lexical timestamp test **failed** for 5,626 of 5,626 values. **Remediation is DEFERRED_SME**, not a passing timestamp result. Preserve original timestamps; do not infer UTC from product documentation alone. The extraction timezone question remains in [SME_OPEN_QUESTIONS](../../questions/SME_OPEN_QUESTIONS.md).
- **04:** owner screenshot showed 2,813 document-ID nodes passing that script's scalar/nonblank and within-record duplicate checks. The old script did not prove complete source equality or PK integrity; its displayed PK sample used a nonexistent key. Do not broaden its PASS beyond checks actually executed.
- **05:** previous scripts failed due to validator defects. The replacement needs a fresh owner-run report before any live PASS is recorded.

Profile/import-profile and Control Implementation remain deferred. Do not resume them or enable writes as a consequence of this validator repair.

## Delivery and evidence boundaries

Changes are confined to this validator, its tests, and this checkpoint. GitHub publication is distinct from execution against a Snowflake notebook. The immediate next evidence is the owner's aggregate Validation 05 report, not another mapper rebuild or an assumed live result.
