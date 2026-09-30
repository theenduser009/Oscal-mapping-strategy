# Executed local SQLite mapper test lab

Date: 2026-09-30
Branch: simplify-metadata-boundary
Code commit tested: cbf0de7b5ccd5674a4ad3c73d9179a6c5ed81cc2
Status: EXECUTED LOCALLY; NOT A CLEAN RELEASE; NO LIVE SNOWFLAKE EXECUTION.

## Scope and continuity

The owner requested an isolated local database and sample-data validation rather than repeated debugging runs in their Snowflake account. The prior handoff and coverage supplement remain historical. This checkpoint adds executed evidence for the specific cases below, superseding static-only review of those cases. It does not supersede live acceptance or prove every production mapping.

All seven maintained source files were materialized and verified against the pinned Git blob hashes before execution. No mapper, production CSV, registry, or database in the owner's environment was changed. The lab executes the current cell code with synthetic source records, synthetic mapping rows, synthetic registry rows, and a custom limited Python/SQLite transport. Model selection and mapping-file locations are test inputs. The full production mapping CSV and the entire existing repository test suite were not exercised.

Python 3.13.5; SQLite 3.46.1. The official Snowpark local-test package could not be installed in the sandbox. The custom adapter is based in part on the repository's existing tests/lean/test_loader.py SQLite/MERGE approach. It is not the official Snowpark emulator, a Snowflake service, or proof of native Snowpark API compatibility. No account credentials were used.

## Executed results

73 new scenarios: 64 PASS, 8 FAIL, 1 ERROR. The runner returns exit status 1; failed cases were not relabeled as expected passes. The packaged kit was extracted into a separate temporary directory and rerun successfully, reproducing exactly the same counts and exit status.

A separate file-backed demonstration database uses 12 synthetic records in each of two sources. Five models execute across six source/model routes because Assessment Results uses both sources. The database contains:

| Model | DIM | FACT |
|---|---:|---:|
| SSP | 336 | 324 |
| Assessment Results, both sources | 96 | 72 |
| Assessment Plan | 84 | 72 |
| POAM | 24 | 12 |
| Catalog | 36 | 24 |
| Total | 576 | 504 |

PREVIEW left target tables empty. Local insertion and readback succeeded. An unchanged rerun produced zero inserts and updates for all routes. SQLite integrity_check returned ok. The database was closed, reopened, and the 73 stored test-result records read back. All COMMITTED_AND_VERIFIED labels in the packaged reports refer to the local transport only.

## Reproduced issues: nine cases in six groups

1. Mixed impact picklists: Low plus an unknown ID, and Low plus an approved Legacy LOE label, are silently reduced to Low instead of rejecting mixed input. This does not authorize inventing a Legacy-to-FIPS crosswalk.
2. False lineage: attribution is emitted for a suppressed incomplete object, a skipped transform, and a picklist whose resolved list is empty. Raw presence is not a surviving target contribution.
3. Redundant attribution: one-to-one output still receives a lineage prop. This fails the newer narrower owner requirement; it is not a regression from the originally broad behavior.
4. Preview retrieval: compact JSON text predicates find zero props where parsed-key inspection finds 12 in the same sample.
5. Joined children: two native control records are emitted, but their expected child-field attribution is absent. A separate wrong-outer-context case correctly triggers parent ambiguity rejection; do not weaken that guard.
6. Empty UserList/GroupList wrapper: the mapper raises Responsible-party reference has no stable identifier before any commit. Explicit empty-wrapper behavior requires correction or a confirmed contract; malformed populated identities must still be rejected.

## Passed local behavior

All five model route fixtures and the combined six-route fixture completed. Standard impact normalization, reviewed Legacy-label preservation, disagreeing candidates, unresolved singleton-ID rejection, zero/false/null behavior, native assembly, party-name resolution, record-scoped UUIDs, software lookup, and joined native control identities passed their scenarios.

Persistence tests passed for native-value update without key/edge changes, unchanged and audit-only reruns, rollback after an injected failure between DIM and FACT MERGEs, and a simulated lost response after local COMMIT being marked unknown/do-not-retry. Duplicate/orphan/cross-record graph guards, schema mismatch, open-transaction checks, and obsolete-row blocking passed. Obsolete-row blocking is not automatic contributor-removal support.

## Artifacts attached to this conversation

- OSCAL_Local_Test_Kit_2026-09-30.zip: source snapshot, adapter, fixtures, scripts, detailed reports, logs, and database.
- OSCAL_Local_Test_Report_2026-09-30.md.
- OSCAL_Local_Test_Lab_2026-09-30.sqlite.
- OSCAL_Local_Test_Results_2026-09-30.json.

ZIP SHA256: f5bc1e847ac7acb880c7f0ff2801a85020b146660dd09455b79da5f99ef005c4

The archive contains a file manifest and all seven Git blob hashes. These artifacts are attached, not uploaded as repository runtime files. No private screenshots or real source-record data are included. This is a downloadable/re-creatable lab, not a permanently hosted database.

## Boundaries

Not established: native Snowflake SQL compilation, grants, actual VARIANT/collation/timestamp behavior, concurrent writers, production performance, full live registry coverage, all production CSV mappings, full OSCAL schema conformance, or Matillion enrichment. The synthetic input is already enriched. Model fragments are not complete OSCAL documents.

Official local-test scope reference: https://docs.snowflake.com/en/developer-guide/snowpark/python/testing-locally

## Next action

Use these failing fixtures to correct shared contribution capture, exact child/owner attribution, and parsed-JSON inspection; address mixed-picklist validation separately without changing approved business labels. Rerun the local suite before requesting another owner Snowflake debugging run. Native integration remains a later separate gate. No production code fix or new Snowflake run is claimed by this checkpoint.
