# OSCAL party name enrichment from persisted ResolvedUser

Date: September 29, 2026
Status: Mapper change implemented in GitHub, generated notebook mirrors synchronized, focused lean tests added. Snowflake PREVIEW for this party-payload change has not yet been run. GitHub CI rerun is in progress after correcting a duplicate test-module packaging issue.

## Repository baseline

Branch before implementation:
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
- Cell 4 blob after update: aa36ffc7d83057fe286fa2109bd56a057ae04a3d

Generated mirrors synchronized:
- cells_v2 Cell 4 commit cd226ce2a0717a847ec0e0a70a75939a292cd02f
- monolithic notebook commit 1679982f6d004603e461bcc47bb764a1e8a05e8a
- monolithic blob 8e660c82849ac627e732a70f8e2072385352ccaf

## EEID handling

OSCAL 1.2.3 supports party external-ids, but each external ID requires a scheme expressed as an absolute URI.

The project does not yet have an owner-approved enterprise EEID scheme URI. Therefore:
- name enrichment is active;
- EEID remains safely persisted upstream in ResolvedUser;
- EEID is emitted into OSCAL external-ids only if configuration ARCHER_EEID_SCHEME is explicitly supplied as a valid absolute URI;
- no scheme is invented by this change.

This preserves the prior decision not to fabricate enterprise identifier semantics.

## Identity / idempotency boundary

The following are unchanged:
- party UUID seed;
- responsible-party party-uuid references;
- collection instance key;
- DIM node-key formula;
- FACT edge-key formula.

Expected Snowflake behavior after replacing Cell 4 and rerunning SSP PREVIEW:
- no DIM inserts from party identity;
- no FACT inserts/updates from responsible-party identity;
- DIM updates only for party nodes whose METADATA_JSON gains a name;
- all other graph identity relationships remain stable.

A second PREVIEW after any eventual COMMIT should return zero delta if source data is unchanged.

## Tests

Focused tests were added under:
- tests/lean/test_resolved_user_party_payload.py

Coverage:
- name enrichment preserves party identity;
- external-id emission is gated by an explicit absolute URI scheme;
- USER_NOT_FOUND stays identity-only;
- conflicting names for the same party identity fail closed.

An initial CI run failed before executing the tests because the same module filename existed in both tests/ and tests/lean/. That duplicate root test was removed in commit:
- b6a14f22d26d9212bc62b94741915d91599ec031

A fresh Mapper checks run is now queued/in progress. Do not treat CI as passed until that run completes successfully.

## Immediate next action

After GitHub CI passes:
1. replace only Cell 4 in the Snowflake notebook with the current maintained Cell 4;
2. run Cell 4;
3. run Cell 7 in PREVIEW;
4. inspect expected DIM updates and confirm FACT remains zero-delta before any COMMIT.

Do not configure ARCHER_EEID_SCHEME until the enterprise naming-system URI is approved.
