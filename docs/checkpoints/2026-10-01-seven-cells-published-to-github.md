# Matching seven cells published to GitHub

Date: October 1, 2026
Repository: theenduser009/Oscal-mapping-strategy
Branch: simplify-metadata-boundary
Initial inspected code revision: 94e41f8896d73cd6ed191c6030efb7f31c7d206b
Publication parent: 847c9544de9f3efc273d194da5d4037d33bea286
Publication revision: the commit introducing this checkpoint and the files in the adjacent publication manifest.
Status: REPOSITORY RUNTIME PUBLICATION OF A LOCALLY TESTED CANDIDATE. NOT A SNOWFLAKE DEPLOYMENT OR PRODUCTION APPROVAL.

## Owner request and continuity

The owner explicitly requested publishing all seven already-delivered October 1 cells and keeping status/context in GitHub. Read 00_START_HERE and the dated coverage supplement, inspected the candidate report and actual repository/ref, and preserved accepted mapping/safety decisions. Prior handoff/counts are historical; no full/current registry or original complete workbook is inferred.

This publication supersedes only the earlier October 1 candidate checkpoint's statement that the new runtime existed solely in attachments. That earlier documentation-only commit remains an accurate record of its time. This is not another redesign or a new business-mapping approval.

Immediately before publication, the branch had gained commit 847c9544, which adds only connection-test.txt. The comparison against 94e41f8 confirmed no runtime or status collision. The new file's exact blob bbf25794258b724564e99d0b641252001f276810 and its commit are preserved; publication uses a normal fast-forward, not a force update.

## Files and exactness

All seven notebooks/cells/*.py files match the delivered candidate bytes. Their notebooks/cells_v2 counterparts use the same blobs. The combined NB_ARCHER_OSCAL_MAPPER_V1.py was regenerated with the unchanged repository generator; its executable sections match all seven cells. Its repository wrapper differs from the delivered combined-file wrapper only. The parsed-JSON reader matches the delivered reader.

The companion JSON manifest gives every runtime blob SHA and size. All replaced code files are nonempty. No unrelated empty file, placeholder, mapping CSV, registry, DDL, test fixture, existing checkpoint, or CI workflow was removed or changed.

Current status, project handoff, root README, AGENTS, and both cell indexes were refreshed so older Profile/SAP instructions are not presented as the current task. Their complete previous text remains linked at the immutable inspected revision. Existing evidence and history remain available.

## Implemented changes, unchanged from the delivered candidate

1. Configuration retains sources/models/storage and safe defaults with a matching release label.
2. Inputs retain actual joined-child Content ID separately from the parent join ID.
3. Compiler derives ambiguous-output and joined-source attribution from approved metadata, with a mapping fingerprint and matching plan version.
4. Transforms capture assigned contributions on surviving objects, use one property constructor, reject mixed impact cardinality, and omit explicitly empty user/group selections.
5. Graph attaches grouped source-field/target-path props to exact owners. Joined contributions carry child provenance. Repeated targets described from an ancestor require their existing validated native payload UUID; otherwise a gap is reported.
6. Loader keeps existing safeguards and blocks COMMIT on unresolved attribution gaps.
7. Orchestrator defaults to PREVIEW, checks matching versions, reports fingerprints/lineage, and checks all routes for gaps before any COMMIT.

Compiler/helpers: lean-csv-registry-v5-lineage. Loader: oscal-lean-daily-v3.2-lineage.
CONFIG.EXECUTE_WRITES=False. OSCAL_LOAD_MODE=PREVIEW.

Native values stay native; approved business extensions use approved props owners. Unmapped/TBD/DEFERRED/EXCLUDED fields are not automatically approved or dumped into props. No lineage table, duplicate CSV row, or per-field toggle. FIPS/Legacy labels, source-null policy, and native identity seeds remain unchanged from the delivered candidate. No group resolver or href generation was added.

## Validation performed again before publication

- Candidate seven files checked against their manifest and matching local code under test.
- python run_tests.py: 73 PASS, 0 FAIL, 0 ERROR, exit 0.
- python -m unittest test_first_pass test_lineage_release -v: 53 tests passed, exit 0.
- python check_native_parity.py: NATIVE_PARITY_PASS across five synthetic models and six routes, 12 records per source. 384 native non-lineage nodes and 312 edges match the pinned baseline; only known lineage and audit fields excluded.
- Existing tools/sync_notebook_cells.py and --check: synchronized. Generated Python compiles; mirrors match maintained bytes.
- Git blob creation responses matched local expected hashes before publication-tree construction.

The 126 checks use the delivered candidate's disclosed test contracts, not an unchanged run of the original broad-lineage 73-case file. Earlier candidate documentation explains changed target/group assertions and the synthetic requirement-props registration. Independent missing-registration cases still block COMMIT.

These are limited Python/SQLite local-adapter checks. They are not official Snowpark/native Snowflake tests. The full maintained repository suite, production CSV/current registry, native SQL/grants/types, concurrency/scale, and complete OSCAL export conformance were not validated by this publication. Inspect GitHub Actions separately; 126 local passes are not full CI acceptance. No target DML or native readback occurred.

## Evidence continuity

The recreatable test archive remains attached to the OSCAL Project conversation as OSCAL_Seven_Cell_Test_Evidence_2026-10-01.zip, SHA256 67088e22d4dab4f80051287eb880fed667c6d4089ab0fcc24ff40b6157c7bb43. The delivered seven-cell archive SHA256 is 3ebbadc9bb5d2f9553bcb4fd37d16c71dbc4ccff7466bcbb54562edcb0a06232. This commit publishes runtime, reader, hashes, and status; it does not claim the entire external local lab/database is installed in the repository.

Prior evidence is retained in 2026-09-30-local-sqlite-test-lab-executed.md, 2026-09-30-props-contract-and-seven-cell-roadmap.md, and 2026-10-01-seven-cell-contribution-candidate.md. Earlier 64/8/1 baseline and 68/5/0 first-pass counts remain valid for their own versions.

## Remaining gates and next action

Native integration and production approval remain pending. Development namespace governance and consumer access to versioned mappings must be resolved. Unchanged-run tests do not implement contributor removal: obsolete broad lineage and removed contributors still require controlled reconciliation, without truncation or weakened guards. Graph consistency does not imply full OSCAL/FIPS conformance. Do not infer AR32/daily-loss/SAP/POAM acceptance from older checkpoints or this publication.

Next action: validate this exact published set against maintained repository/SDK compatibility gates, accounting for actual CI failures, before bounded authorized native Dev integration. No new Snowflake debugging run is requested solely to reproduce locally covered defects. Verify remote branch/tree and critical files before reporting publication complete; distinguish GitHub readback from native database verification.
