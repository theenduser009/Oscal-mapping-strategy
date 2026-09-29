# Archer RequestedObject record metadata identified

Date: September 29, 2026
Status: New owner-provided RAW_DATA screenshot reviewed. Read-only identity reconciliation SQL published and repository read-back verified. No Matillion/Snowflake write performed.

## New source evidence

The screenshot shows record-level metadata under RequestedObject outside FieldContents. The visible structure includes:
- Id
- Identity.BaseContentId
- Identity.Locators[]
- LastUpdated
- LevelId
- SequentialId
- UpdateInformation.CreateDate
- UpdateInformation.CreateLogin
- UpdateInformation.UpdateDate
- UpdateInformation.UpdateLogin
- Version

In the one shown sample, RequestedObject.Id, Identity.BaseContentId and locator identities for ARCHER and SYS_REF visibly carry the same numeric value. A SYS_WF locator carries a different workflow-style identity. This is one-sample evidence only and must not be generalized without a source-wide check.

The screenshot shows Version as numeric 709. It should not be restated as 7.9 without separate evidence.

## What the current Matillion candidate does and does not do

The current combined candidate already reads RequestedObject.Id and RequestedObject.LevelId for conversion/control logic.

It does not currently preserve the full RequestedObject record metadata above inside CURATED_JSON. It also still derives stored CONTENT_ID through the historical ID_SOURCE_JSON fallback chain before using RequestedObject.Id as final fallback.

Therefore the project has not yet proved that the fallback chain is the correct semantic definition of Archer Content ID, even though earlier full-source evidence showed zero current stored/source CONTENT_ID mismatches.

## New read-only check

Published and read back:
- Path: sql/READ_ONLY_ARCHER_REQUESTED_OBJECT_IDENTITY_RECONCILIATION.sql
- Publication commit: 3983ddadb50e06907433a6d71e10fe656a16c696
- Blob: dde9fe1bfaf3bbba43f281ee532c0946809a4e76

The query returns aggregate-only checks comparing:
- stored CONTENT_ID vs RequestedObject.Id;
- Identity.BaseContentId vs RequestedObject.Id;
- ARCHER locator identity vs RequestedObject.Id;
- SYS_REF locator identity vs RequestedObject.Id;
- presence of SYS_WF locator identities;
- population of LevelId, SequentialId, Version, LastUpdated and UpdateInformation fields.

A second result set inventories locator aliases and counts without exposing raw IDs.

## Decision boundary

Do not change the one-update Matillion CONTENT_ID rule or add all record metadata to CURATED_JSON until the source-wide identity reconciliation is reviewed.

The current combined write candidate remains committed/read-back verified in Git, but this new source evidence creates a pre-run identity checkpoint. Run the read-only reconciliation first.

After that result:
- if RequestedObject.Id is confirmed as the authoritative row/content identity across the source, simplify CONTENT_ID to RequestedObject.Id and treat other locator/business IDs as separate metadata;
- decide separately whether record metadata should be persisted into CURATED_JSON, separate columns, or a reporting/audit structure;
- do not treat SYS_WF identity, SequentialId, or LevelId as interchangeable with Content ID without explicit evidence.
