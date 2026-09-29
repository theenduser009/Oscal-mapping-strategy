# Persisted UserList enrichment sample verified

Date: September 29, 2026
Status: Owner-posted Snowflake CURATED_JSON sample reviewed after the combined Matillion run. No database action performed by ChatGPT.

## Verified persisted structure

The sample CURATED_JSON shows a source field containing:
- GroupList as an array;
- UserList as an array;
- original user member keys preserved, including Id, HasRead, HasUpdate and HasDelete;
- ResolvedUser added inside the UserList member;
- ResolvedUser.ContractVersion = archer-meta-user-v1;
- ResolvedUser.LookupStatus = MATCHED;
- resolved enterprise identifier and person-name attributes present;
- nullable middle-name retained as null rather than fabricated.

No personal name, EEID, or user ID from the screenshot is copied into this checkpoint.

## Interpretation

This is persisted read-back evidence, not merely preview evidence. It confirms the upstream combined Matillion update physically wrote the expected enrichment shape into CURATED_JSON for at least one matched UserList record.

The sample also shows GroupList preserved independently from UserList. No group enrichment is claimed.

## Current next action

Proceed to the OSCAL mapper in PREVIEW/read-only mode. Verify that the added ResolvedUser child does not change existing deterministic party/reference identities and that graph integrity/counts remain stable before any downstream COMMIT.

A separate mapper enhancement is still required later if EEID/name should be emitted into OSCAL party payloads or Power BI lineage outputs.
