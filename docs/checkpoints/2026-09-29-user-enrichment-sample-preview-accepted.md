# User enrichment sample preview accepted; full-scope coverage next

Date: September 29, 2026  
Status: Owner-posted Dev PREVIEW result accepted for the one-record sample. No CURATED_JSON UPDATE, Matillion change, mapper run, database COMMIT, or read-back is claimed.

## Repository version

- Branch: `simplify-metadata-boundary`.
- Pre-coverage branch head inspected: `bc2ab66f7a60f5628ee42b1c270af4a74b73a464`.
- Accepted sample preview SQL: `sql/PREVIEW_ARCHER_CURATED_JSON_USER_ENRICHMENT.sql`, blob `968395ee2f67c4391a510cd58b038a5787502274`.
- New full-scope read-only coverage SQL commit: `9753a98de4842a5988f85438b594f0ac2b9882e0`.
- New SQL path: `sql/READ_ONLY_ARCHER_USER_ENRICHMENT_FULL_COVERAGE.sql`.
- New SQL blob from repository read-back: `11b159c7bfcc247cefb0f0a6a62885bde6f99b58`.

## Owner-posted sample result

The owner reports the one-record preview returned:

- PREVIEW_STATUS = `PREVIEW_BUILT_USER_LOOKUPS_MATCHED`
- USER_MEMBERS = 18
- MATCHED_USERS = 18
- UNMATCHED_USERS = 0
- MISSING_EEID_USERS = 0
- BLOCKED_FIELDS = 0
- GROUP_MEMBERS_UNCHANGED = 32
- GROUP_FIELDS_CHANGED = 0

The supplied before/after screenshots show the original `Id`, `HasDelete`, `HasRead`, and `HasUpdate` values preserved while `ResolvedUser` was added with `ContractVersion`, `EEID`, first/middle/last names, and `LookupStatus = MATCHED`. Multiple-user arrays remain arrays and displayed member order is preserved in the sample.

Privacy note: actual user IDs, EEIDs, names, Content IDs and screenshots are not copied into this repository checkpoint.

## Meaning

This is an accepted **sample PREVIEW**, not a whole-source acceptance and not persistence evidence.

For that selected record, all 18 user-member occurrences resolved successfully to the current `ARCHER_META_USER` snapshot, none were missing EEID, and no field was blocked. The 32 group-member occurrences were deliberately left unchanged because the authoritative Meta Group lookup contract is still unavailable.

`GROUP_FIELDS_CHANGED = 0` means no GroupList field changed in the reconstructed candidate. It is not a separate count of changed group-member rows.

The sample supports the proposed user-enrichment structure. It does not establish coverage for every Source One record, all access-control field shapes, all historical/as-of user identities, or the group lookup.

## Full-scope validation now published

`sql/READ_ONLY_ARCHER_USER_ENRICHMENT_FULL_COVERAGE.sql` performs an aggregate, read-only scan across current Source One rows. It returns no user IDs, EEIDs, names, Content IDs or payloads.

It reports:

- source-row and stored-Content-ID counts;
- unsupported RAW_DATA shapes and missing/mismatching raw RequestedObject IDs;
- reference-field occurrence counts;
- user-member occurrences and matched/missing-EEID/unmatched/blocking counts;
- group-member occurrence counts and invalid group member IDs;
- UserList/GroupList shape issues;
- fields containing both user and group members;
- a per-source-field breakdown.

The group namespace remains structural only; no group-name resolution is invented.

## Next action

Run only the new full-scope read-only coverage SQL in Dev. Review the `ALL / __ALL__` row first.

If the whole-source user gates are clean enough for the agreed policy, use those results to authorize integration of the same enrichment expressions into the existing Matillion CURATED_JSON UPDATE. Existing non-null CURATED_JSON still needs an explicit scoped persistence/backfill decision; do not clear or truncate it.

Meta Group remains a separate follow-up lookup contract. Downstream OSCAL party enrichment and source-field lineage also remain separate mapper/reporting changes after upstream user enrichment is accepted.
