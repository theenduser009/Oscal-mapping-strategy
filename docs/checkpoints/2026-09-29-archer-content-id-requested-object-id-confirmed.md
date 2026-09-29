# Archer Content ID rule owner-confirmed

Date: September 29, 2026
Status: Owner/SME confirmation accepted and current combined Matillion candidate updated. No Snowflake/Matillion execution performed.

## Confirmed identity rule

The owner reports Grady confirmed that Archer record identity / Content ID is RequestedObject.Id. The owner also inspected additional records and found the same RequestedObject identity structure repeating across rows.

This is owner/SME evidence. It supersedes the older historical fallback assumption that application/business identifiers such as ssp_uuid, AUTH_PKG_TRACKING_ID, HRTN_ID, TRACKING_ID or a field-level CONTENT_ID should take precedence over RequestedObject.Id for the stored raw-table CONTENT_ID.

## Current combined candidate

Path:
- sql/matillion/CANDIDATE_raw_curated_with_meta_user_enrichment.sql

Update commit:
- 0b6fc75e923a9ff4edfa33d07501c9c83cae3d3f

Read-back blob:
- 1a118817e1d3d04020d6ed9d1785910c9f998fe8

The final identity assignment is now:

curated.REQ_OBJ_ID::string AS CONTENT_ID

where REQ_OBJ_ID is extracted from RequestedObject.Id.

The earlier application-field COALESCE fallback chain is no longer used for CONTENT_ID selection in the combined candidate.

## Preserved logic

Read-back confirms the combined candidate still contains:
- current source-side TRY_TO_NUMBER FIELD_ID safety;
- ARCHER_META_FIELD field-name mapping;
- current type conversions and nested extraction;
- JSON-null key preservation;
- Meta User enrichment from UserList[].Id through ARCHER_META_USER;
- no Meta Group enrichment;
- existing pending-row CURATED_JSON IS NULL boundaries.

The internal ID_SOURCE_JSON aggregate remains present for now but is no longer used to choose CONTENT_ID in the combined candidate. It can be removed later as cleanup after runtime acceptance; removing it is not required for this identity correction.

## Record-level metadata

RequestedObject also exposes Identity.BaseContentId, Identity.Locators, LevelId, SequentialId, Version, LastUpdated and UpdateInformation. Their presence is now recognized, but this checkpoint does not decide whether all of those fields belong in CURATED_JSON, separate technical columns, or a separate audit/reporting structure.

## Next action

Use the updated combined candidate for DEV. After execution, verify:
- target CONTENT_ID equals RequestedObject.Id;
- CURATED_JSON field names/values remain preserved;
- UserList retains original Id/permission flags and gains ResolvedUser where lookup succeeds;
- GroupList remains unchanged.

No database run/read-back exists yet for this updated identity rule.
