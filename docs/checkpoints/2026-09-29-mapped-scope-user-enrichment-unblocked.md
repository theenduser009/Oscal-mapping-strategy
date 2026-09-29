# Unmatched user/group references are outside the current runtime mapping artifact

Date: September 29, 2026
Status: Current repository mapping CSV rechecked after owner clarification. This changes the interpretation of the full-source enrichment gaps; no database or mapper write was performed.

## Repository evidence

- Branch inspected: `simplify-metadata-boundary`.
- Branch head before this checkpoint: `2ceef28a7e4cc99779a9bbedb13970d28487a579`.
- Actual runtime artifact inspected: `Mapping/ARCHER_OSCAL_MAPPINGS.csv` from that branch.
- Exact source-field searches were performed against the complete file content, not a screenshot-derived workbook.

## Important correction

The four fields that account for all 546 unmatched UserList occurrences in the full-source enrichment scan are **not present anywhere in the current runtime mapping CSV**:

- CURRENT_ACTOR
- RCD_CREATOR
- RESPONSIBLE_PARTY
- RESPONSIBLE_PARTY_DELEGATE

The three fields carrying the visible 192,141 GroupList member occurrences are also **not present anywhere in the current runtime mapping CSV**:

- DEFAULT_RECORD_PERMISSIONS
- HRTN_DEFAULT_RP_AUTOMATIC
- NETWORK_SECURITY_ENGINEER_NSE

Therefore these full-source unresolved references do **not** currently block the approved OSCAL source-to-target mappings. They remain source-curation/reporting data-quality items if the project chooses to enrich every access-control field in CURATED_JSON, but they are outside the current runtime mapping artifact.

This supersedes the earlier interpretation that the 546 unmatched references had to be explained before current OSCAL user enrichment could proceed.

## Current mapped responsible-party scope

The current mapping CSV contains approved responsible-party mappings including the SSP Metadata responsible-party fields and the approved Security Control Assessor / Alternate Security Control Assessor mappings. The full-source field breakdown supplied by the owner showed zero unmatched user occurrences for those currently mapped responsible-party fields.

This supports moving forward with user enrichment for the current OSCAL mapped scope while preserving any unmatched nonmapped UserList members unchanged or explicitly unresolved in generic CURATED_JSON enrichment.

## Group lookup

The absence of a verified Meta Group lookup still means group IDs cannot yet be translated to group names. Because the three group-heavy fields identified by the full-source scan are not in the current runtime mapping CSV, the missing group lookup does not currently block the approved OSCAL mapping scope. Preserve GroupList IDs and permission flags unchanged until the authoritative group lookup contract arrives.

## Owner clarification on screenshots and STG

Earlier payload screenshots were examples only and were not an exhaustive representation of all source data. ARCHER_META_USER_STG is the same user source for this purpose and is not an independent fallback. Do not repeat the STG diagnostic.

## Next implementation action

Proceed to integrate the accepted ARCHER_META_USER enrichment logic into the current Matillion CURATED_JSON conversion for UserList members, preserving original Id and permission flags. For a user lookup miss outside mapped OSCAL scope, preserve the original member and explicit unresolved status rather than dropping or substituting an identity.

Do not invent Meta Group enrichment. Do not change Content ID, OSCAL UUIDs, DIM/FACT keys, or mapping approvals as part of this upstream change.

The production Matillion statement was supplied as owner screenshots, not as an exact text file in the repository. Any full replacement SQL derived from those screenshots must be identified as screenshot-derived and compared against the actual Matillion component before deployment.
