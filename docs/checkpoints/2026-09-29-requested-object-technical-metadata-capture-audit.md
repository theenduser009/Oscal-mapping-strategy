# Archer RequestedObject technical metadata capture audit

Date: September 29, 2026
Status: Current Matillion candidate and current OSCAL source-input code inspected. No runtime write performed.

## Confirmed current capture

- RequestedObject.Id is now the owner-confirmed Archer record identity and is persisted as raw-table CONTENT_ID in the combined Matillion candidate.
- RequestedObject.LevelId is extracted and used internally in the Matillion field-metadata precedence logic.
- The OSCAL mapper reads CONTENT_ID as SOURCE_RECORD_ID plus CURATED_JSON.
- Warehouse DW load timestamps are separate pipeline/load timestamps; they are not Archer CreateDate/UpdateDate.

## Not currently persisted into CURATED_JSON

The current combined Matillion candidate does not add these RequestedObject record-level attributes into CURATED_JSON:
- Identity.BaseContentId
- Identity.Locators[]
- SequentialId
- Version
- LastUpdated
- UpdateInformation.CreateDate
- UpdateInformation.CreateLogin
- UpdateInformation.UpdateDate
- UpdateInformation.UpdateLogin

LevelId is used during conversion but is not emitted as a CURATED_JSON property by the current SQL.

These attributes remain present in RAW_DATA, so they are not lost at the raw layer; however, the downstream OSCAL mapper does not currently consume them because its source input selects CONTENT_ID and CURATED_JSON.

## Design recommendation

Do not treat these technical/source-record attributes as OSCAL business fields by default.

Preserve a small source-record metadata envelope for lineage/audit/change tracking, separate from the OSCAL semantic mappings. Highest-value candidates are:
- Archer record Id / CONTENT_ID (already handled)
- LevelId
- Version
- LastUpdated
- UpdateInformation timestamps/logins
- Identity.BaseContentId and Locators where cross-system traceability is useful

SequentialId should be preserved only as source metadata unless an Archer owner gives it a specific semantic use.

A concrete storage shape (dedicated columns vs CURATED_JSON metadata object vs separate audit table) is not yet approved. Do not add these fields to the combined Matillion write until that storage decision is made.
