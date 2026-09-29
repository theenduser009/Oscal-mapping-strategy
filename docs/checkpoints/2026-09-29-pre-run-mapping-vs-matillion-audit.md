# Pre-run mapping-vs-Matillion audit before combined DEV update

Date: September 29, 2026
Status: Current runtime mapping CSV, current mapper helpers, current combined Matillion candidate, and the historical review workbook were compared. No Snowflake/Matillion execution performed.

## Source precedence

The uploaded ARCHER_OSCAL_MAPPING_REVIEW.xlsx is historical/partial review material, not the current executable contract. The current runtime source of truth is Mapping/ARCHER_OSCAL_MAPPINGS.csv on simplify-metadata-boundary.

Current runtime CSV readback:
- 155 rows total
- 139 APPROVED
- 13 EXCLUDED
- 2 DEFERRED
- 1 BLOCKED_IF_POPULATED

The historical workbook has 147 listed entries and contains older TBD states that have since been superseded by owner-approved runtime mappings.

## Pre-run findings

### 1. Archer record Version vs OSCAL/document version — separated correctly

Current mapping CSV contains support mappings:
- OSCAL_VERSION -> system-security-plan.metadata.oscal-version from CONFIG
- SSP_DOCUMENT_VERSION -> system-security-plan.metadata.version from CONFIG

RequestedObject.Version is not a runtime source-field mapping. Do not map Archer RequestedObject.Version into OSCAL metadata.version. If retained, keep it namespaced as Archer/source-record metadata.

### 2. RequestedObject.LastUpdated must not collide with mapped LAST_UPDATED fields

Current CSV has both:
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED -> metadata.last-modified
- LAST_UPDATED -> metadata.last-modified

These are FieldContents mappings. RequestedObject.LastUpdated is separate record-level technical metadata and is not currently placed into CURATED_JSON.

If record-level metadata is added later, store it under a namespaced source-metadata envelope rather than adding a top-level LAST_UPDATED key that could collide with current mappings.

### 3. CONTENT_ID correction is aligned

Combined Matillion candidate now uses RequestedObject.Id as CONTENT_ID per owner/SME confirmation. TRACKING_ID remains an approved OSCAL document-id source field and is no longer treated as record identity.

### 4. User enrichment does not break current responsible-party extraction

Current mapper _extract_reference_ids follows UserList and then _party_reference_identifier reads the original Id/UserId/ContentId from each member. The new ResolvedUser child is therefore ignored by the current identity/hash path, while original Id is preserved.

This means the combined Matillion change should not re-key existing OSCAL party UUIDs.

### 5. But the mapper does not yet consume ResolvedUser EEID/name

Current responsible-party payload builder still creates parties as uuid/type and assignments as role-id/party-uuids. It does not yet emit EEID, first/last name, or source-field lineage from ResolvedUser.

Therefore a successful Matillion enrichment proves upstream persistence, but it does not by itself complete the downstream OSCAL/Power BI person attributes.

### 6. GroupList remains a future gap

Current helper explicitly prefers UserList and has no GroupList branch. Meta Group lookup is also unavailable. The combined Matillion candidate intentionally leaves GroupList unchanged.

Do not claim group-based responsible-party hydration is complete until Meta Group and mapper GroupList handling are implemented.

### 7. ARCHER_META_VALUE remains intentionally downstream

Current runtime mapping contains 15 archer-select transforms. The OSCAL mapper already resolves those through ARCHER_META_VALUE. The combined Matillion candidate does not duplicate value-label resolution upstream.

This is intentional and preserves the existing mapping contract.

### 8. Archer Dev Field ID traceability column is still absent

The current runtime CSV headers do not contain an Archer Dev Field ID column. This is a QA/lineage requirement from the September 29 review, not a blocker for the raw-to-curated Matillion update itself.

## Run decision

No new mapping mismatch was found that requires changing the combined Matillion SQL before a DEV raw-to-curated run.

Safe boundary:
1. Run COPY/load to RAW.
2. Run the combined Matillion update in DEV.
3. Validate persisted CONTENT_ID and CURATED_JSON UserList/ResolvedUser.
4. Do not treat downstream OSCAL EEID/name or GroupList support as complete yet.

The RequestedObject technical metadata envelope remains a separate design decision because all of those values remain available in RAW_DATA and are not lost by this run.
