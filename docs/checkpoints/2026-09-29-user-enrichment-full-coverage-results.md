# Full-source user enrichment coverage reviewed; unresolved-user and group gaps isolated

Date: September 29, 2026  
Status: Owner-posted Dev full-scope read-only result reviewed. User enrichment is not yet authorized for persistence because unresolved user references remain and group-name enrichment still lacks an approved lookup contract.

## Repository version and SQL

- Branch reviewed before this checkpoint: `simplify-metadata-boundary` at `be45c1832792a56cabd85de161d04848dcc6793c`.
- Full coverage SQL run by owner: `sql/READ_ONLY_ARCHER_USER_ENRICHMENT_FULL_COVERAGE.sql`; published commit `9753a98de4842a5988f85438b594f0ac2b9882e0`; blob `11b159c7bfcc247cefb0f0a6a62885bde6f99b58`.
- New gap-diagnostic SQL: `sql/READ_ONLY_ARCHER_REFERENCE_ENRICHMENT_GAPS.sql`; publication commit `3f9979074b26f4be20e76df028b73e006683cb3f`; blob `c4e247317a92add202b28b7bb6a9af4569086cf7`.
- Both SQL artifacts are read-only. No UPDATE, Matillion change, mapper run, database COMMIT or database read-back is claimed.

## Owner-posted full-source results

Visible ALL-row results from the three screenshots:

| Metric | Result |
| --- | ---: |
| SOURCE_ROWS | 2813 |
| DISTINCT_STORED_CONTENT_IDS | 2813 |
| UNSUPPORTED_RAW_SHAPE_ROWS | 0 |
| SOURCE_ID_MISSING_ROWS | 0 |
| CONTENT_ID_MISMATCH_ROWS | 0 |
| FIELD_OCCURRENCES | 40819 |
| FIELDS_WITH_USERS | 34936 |
| USER_MEMBER_OCCURRENCES | 55782 |
| MATCHED_USER_MEMBERS | 55236 |
| MISSING_EEID_USER_MEMBERS | 0 |
| UNMATCHED_USER_MEMBERS | 546 |
| BLOCKING_USER_MEMBERS | 0 |
| FIELDS_WITH_GROUPS | 5883 |
| GROUP_MEMBER_OCCURRENCES | 192141 |
| FIELDS_WITH_BOTH | 0 |
| INVALID_USERLIST_SHAPES | 0 |
| INVALID_GROUPLIST_SHAPES | 0 |

The rightmost INVALID_GROUP_MEMBER_IDS value was not visible in the supplied images, so it is not inferred.

The 546 unmatched user-member occurrences are concentrated in four source fields:

| Source field | Unmatched occurrences visible |
| --- | ---: |
| CURRENT_ACTOR | 164 |
| RCD_CREATOR | 54 |
| RESPONSIBLE_PARTY | 164 |
| RESPONSIBLE_PARTY_DELEGATE | 164 |
| Total | 546 |

All other displayed source fields have zero unmatched-user occurrences.

The visible group-member population is concentrated in three source fields:

| Source field | Field occurrences with groups | Group member occurrences |
| --- | ---: | ---: |
| DEFAULT_RECORD_PERMISSIONS | 2813 | 127409 |
| HRTN_DEFAULT_RP_AUTOMATIC | 2813 | 64475 |
| NETWORK_SECURITY_ENGINEER_NSE | 257 | 257 |
| Total | 5883 | 192141 |

No field in the displayed result has both a populated UserList and GroupList at the same time (`FIELDS_WITH_BOTH = 0`).

## Interpretation

The full-source run strongly supports the proposed UserList extraction and `ARCHER_META_USER` join shape: 55,236 of 55,782 user-member occurrences resolve with EEID, no displayed matched user is missing EEID, no blocking user-member condition is reported, and no invalid UserList/GroupList shape is visible.

It is **not** a clean whole-source user-enrichment acceptance because 546 user-member occurrences do not resolve in the authoritative `ARCHER_META_USER` snapshot used by the preview. Those references must be preserved and explained; they must not be dropped or reassigned.

The group workload is material (192,141 member occurrences). Source group Id/flags are structurally available, but the authoritative group-ID-to-name lookup remains unverified. Group-name enrichment cannot be claimed complete.

The source identity checks shown are clean for this Source One snapshot: 2,813 rows and 2,813 distinct stored Content IDs, with zero visible unsupported raw shapes, missing raw RequestedObject IDs, or Content-ID mismatches. This does not retroactively prove older loads or other sources.

## New gap diagnostic

`sql/READ_ONLY_ARCHER_REFERENCE_ENRICHMENT_GAPS.sql` contains two read-only statements:

1. For the 546 unmatched user occurrences, report aggregate/per-field distinct counts and whether those IDs are present in `ARCHER_META_USER_STG`, including whether STG has a nonblank EEID. STG is diagnostic only; it is not silently promoted to the production lookup.
2. Discover accessible group-related tables/columns in `RTX_RAW_DEV.ES_ESC_GRC` so the actual group lookup candidate can be reviewed with the Archer SME instead of guessed.

No IDs, names, EEIDs or Content IDs are returned by the first diagnostic. The second query returns schema metadata only.

## Next action

Run both statements from `sql/READ_ONLY_ARCHER_REFERENCE_ENRICHMENT_GAPS.sql` in Dev and return the result grids. If the unmatched users are explained and an authoritative group lookup contract is established, the next implementation step is a reviewed Matillion CURATED_JSON enrichment UPDATE that preserves original Id/flags and adds resolved user/group attributes without changing Content IDs or existing OSCAL UUIDs.

Do not clear or truncate existing CURATED_JSON as part of this work. Existing non-null JSON persistence/backfill remains an explicit deployment decision after the enrichment contract is accepted.
