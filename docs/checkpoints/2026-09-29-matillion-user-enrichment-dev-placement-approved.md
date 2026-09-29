# Matillion Meta User enrichment approved for DEV placement

Date: September 29, 2026
Status: Owner approved proceeding with a separate Matillion enrichment step after raw-to-CURATED_JSON conversion. SQL committed and repository read-back verified. No Snowflake/Matillion execution has been performed by ChatGPT.

## Current SQL

Path:
- sql/matillion/CANDIDATE_enrich_curated_json_users.sql

Latest hardening commit:
- 85578e2997b1d476955a0988d6a8e97b24e22dcd

Read-back blob:
- 425e6b8b4bbcaa93590f6294b28ee6a7cbb2328b

## Agreed flow

1. Existing raw-to-CURATED_JSON conversion runs first.
2. Meta User enrichment runs next.
3. OSCAL mapper consumes the enriched CURATED_JSON.

The user confirmed CURATED_JSON starts null on the normal initial load, so the first conversion step fills it before the enrichment step executes.

## Enrichment contract

- UserList[].Id -> ARCHER_META_USER.ARCHER_USER_ID.
- Preserve original Id and permission flags.
- Add ResolvedUser with contract version, lookup status, EEID, first/middle/last name.
- Valid unmatched IDs remain present with USER_NOT_FOUND.
- GroupList is unchanged until Meta Group lookup is available.
- No Content ID, UUID, DIM/FACT key, raw payload or mapping approval is changed.

## Hardening before DEV run

The write candidate now skips rather than silently correcting:
- duplicate physical source records for one RequestedObject.Id;
- stored CONTENT_ID mismatches;
- malformed non-array UserList values;
- invalid user IDs;
- duplicate lookup IDs;
- foreign/conflicting ResolvedUser contracts;
- member-count mismatches.

The current full-source evidence previously showed zero source-ID mismatch, zero duplicate source identities, zero blocking user members and zero invalid UserList/GroupList shapes for Source One. Those are owner-posted read-only results, not proof of this UPDATE execution.

## Next action

Add this SQL as the second Matillion SQL step immediately after the existing raw-to-CURATED_JSON update in DEV and run the normal pipeline. Then read back CURATED_JSON for a small sample and confirm ResolvedUser is present while original Id/permission flags and GroupList remain intact.

Do not add group-name enrichment until the authoritative Meta Group lookup contract is supplied.
