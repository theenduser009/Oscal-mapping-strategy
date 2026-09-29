# Combined Matillion post-run validation passed

Date: September 29, 2026
Status: Owner reports the whole-table post-Matillion validation returned POST_MATILLION_ACCEPTANCE_PASSED. Per-field UserList coverage screenshots were also reviewed. This is owner-posted Snowflake evidence; ChatGPT did not execute Snowflake.

## Repository baseline

- Branch before checkpoint: simplify-metadata-boundary
- Head: e31f632e0be078e933cb387432a70cec38014b50
- Validation SQL: sql/matillion/READ_ONLY_POST_COMBINED_MATILLION_VALIDATION.sql

## Accepted validation result

The first validation result set returned:
- POST_MATILLION_ACCEPTANCE_PASSED

That acceptance status means the validation query found no blocking condition among:
- CURATED_JSON null rows;
- missing RequestedObject.Id rows;
- missing stored CONTENT_ID rows;
- CONTENT_ID != RequestedObject.Id mismatches;
- UserList members missing original Id;
- UserList members missing ResolvedUser;
- ResolvedUser contract mismatches;
- missing/unexpected lookup status;
- GroupList members accidentally carrying ResolvedUser or ResolvedGroup.

## Per-field UserList evidence

The owner-posted field-level grid shows:
- original UserList Ids preserved (zero MEMBERS_MISSING_ID in the visible rows);
- MEMBERS_WITH_RESOLVED_USER equals USER_MEMBER_OCCURRENCES across the visible rows;
- MEMBERS_WITH_EXPECTED_CONTRACT equals USER_MEMBER_OCCURRENCES across the visible rows;
- MATCHED_MISSING_EEID is zero in the visible rows.

Known unresolved users remain explicit as USER_NOT_FOUND in the same four fields previously identified:
- RESPONSIBLE_PARTY: 164
- CURRENT_ACTOR: 164
- RESPONSIBLE_PARTY_DELEGATE: 164
- RCD_CREATOR: 54

Total USER_NOT_FOUND occurrences: 546.

Those four fields are outside the current runtime mapping CSV, so this does not block the approved OSCAL mapped scope. No user identity was fabricated.

## Current status

Implemented and persisted upstream:
- RequestedObject.Id -> CONTENT_ID;
- current FIELD_ID mapping and TRY_TO_NUMBER safety;
- null-key preservation;
- UserList Meta User enrichment in CURATED_JSON;
- GroupList left unchanged.

Still pending downstream:
- OSCAL mapper does not yet emit ResolvedUser EEID/name into party payloads;
- GroupList / Meta Group support remains pending;
- Archer Dev Field ID traceability column remains a separate QA item.

## Next action

Run the OSCAL mapper in PREVIEW/read-only mode against the freshly enriched CURATED_JSON before any downstream commit. Confirm graph counts/integrity and verify that the upstream ResolvedUser additions did not re-key or alter existing party/reference relationships.
