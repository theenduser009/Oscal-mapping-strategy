# OSCAL party name enrichment from persisted ResolvedUser

Date: September 29, 2026
Status: Mapper change implemented in GitHub, generated notebook mirrors synchronized, and focused party-enrichment tests passed. Full repository CI remains red because of broader stale/missing test fixtures and expectations unrelated to this feature. Snowflake PREVIEW for the party-payload change is still pending.

## Repository basis

Branch baseline before implementation:
- simplify-metadata-boundary at 9bc4d800d8cb6a15cc12efd871249bf4e7f2aa06

The prior accepted SSP PREVIEW was zero-delta:
- source records 2,813
- nodes 546,799
- edges 543,986
- DIM inserts/updates 0/0
- FACT inserts/updates 0/0
- PREVIEW_PASSED_NO_TARGET_DML

## Change

Maintained Cell 4 now recognizes the persisted Matillion ResolvedUser contract:
- ContractVersion = archer-meta-user-v1
- LookupStatus in MATCHED, MATCHED_MISSING_EEID, USER_NOT_FOUND

For matched person references:
- party UUID seed remains unchanged and still uses the original Archer UserList member Id;
- OSCAL party payload keeps uuid/type and now adds name from FIRST_NAME, optional MIDDLE_NAME, LAST_NAME when available;
- USER_NOT_FOUND retains identity-only party payload;
- same identity seen through enriched and plain references merges without re-keying;
- conflicting enriched data for the same party UUID fails closed.

Implementation commit:
- 370335dee9700f0d19f3388fa130a25df9f83a0d
- Cell 4 blob: aa36ffc7d83057fe286fa2109bd56a057ae04a3d

Generated mirrors synchronized:
- cells_v2 Cell 4 commit cd226ce2a0717a847ec0e0a70a75939a292cd02f
- monolithic notebook commit 1679982f6d004603e461bcc47bb764a1e8a05e8a
- monolithic blob 8e660c82849ac627e732a70f8e2072385352ccaf

## EEID handling

OSCAL party external-ids require an explicit scheme. The project does not yet have an owner-approved enterprise EEID scheme URI.

Therefore:
- name enrichment is active;
- EEID remains safely persisted upstream in ResolvedUser;
- EEID is emitted into OSCAL external-ids only if ARCHER_EEID_SCHEME is explicitly configured with an approved absolute URI;
- no scheme is invented.

## Identity / idempotency boundary

Unchanged:
- party UUID seed;
- responsible-party party-uuid references;
- collection instance key;
- DIM node-key formula;
- FACT edge-key formula.

Expected Snowflake behavior after replacing Cell 4 and rerunning SSP PREVIEW:
- node and edge counts remain stable unless an unrelated source change occurred;
- no DIM inserts caused by party identity;
- no FACT inserts/updates caused by party enrichment;
- DIM updates only for existing party nodes whose METADATA_JSON gains a name.

A later rerun after any accepted COMMIT should be zero-delta when source data is unchanged.

## Test evidence

Focused lean test:
- tests/lean/test_resolved_user_party_payload.py
- commit a53b47c4aefd6e29b89a9452f90013936871ef0e

All four new focused tests passed in GitHub Actions:
- name enrichment preserves party identity;
- EEID external-id is gated by an explicit absolute URI scheme;
- USER_NOT_FOUND remains identity-only;
- conflicting enriched names for one party identity fail closed.

Generated notebook synchronization check also passed.

The full Mapper checks run still failed overall: 260 tests, 27 failures, 57 errors. The visible failure set includes broader repository drift/missing fixtures unrelated to this feature, including:
- tests expecting 153 mapping rows while the runtime CSV now has 155;
- missing validation helper files referenced by older tests;
- local Snowpark test fixtures missing current allocated-controls and Source Two tables;
- pre-existing compiler/input expectations that no longer match the current runtime configuration.

Do not report the broad suite as passed. Do not treat those unrelated failures as evidence that the focused party enrichment failed.

## Immediate next action

In the current Snowflake notebook:
1. replace only Cell 4 with the current maintained Cell 4;
2. run Cell 4;
3. run Cell 7 in PREVIEW;
4. inspect expected DIM changes and verify FACT remains zero-delta before any COMMIT.

Do not configure ARCHER_EEID_SCHEME until the authoritative enterprise scheme URI is approved.
