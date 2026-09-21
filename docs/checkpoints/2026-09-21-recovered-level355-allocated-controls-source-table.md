# Recovered Level-355 Allocated Controls source-table conclusion — 2026-09-21

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before this checkpoint: `49a81850c785e8676487db9cee424d10794dfc4c`

## Recovered prior project conclusion
From the September 15, 2026 OSCAL project discussion, the expected Archer RAW
table for the Level-355 `CONTROL` records under module `ALLOCATED CONTROLS`
was identified as:

`ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`

The naming conclusion came from:
- Level 355 -> `CONTROL`
- Module 549 -> `ALLOCATED CONTROLS`
- Archer ingestion naming convention using module + level for this multi-level module

The owner subsequently confirmed that this was the intended table name and also
stated that the Allocated Controls dataset/table was not yet delivered/ingested
into the Snowflake environment available to this project.

## Current September 21 evidence
Today's live owner-run search:
- confirmed Level 355 = CONTROL
- confirmed Module 549 = ALLOCATED CONTROLS
- sampled 100 Level-355 ContentIds from Source One `ALLOCATED_CONTROLS`
- found no matching current RAW table among the 45 current `*_RAW` tables with
  both `CONTENT_ID` and `CURATED_JSON`

This current evidence is consistent with the earlier September 15 conclusion
that the expected `ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW` source has
not been ingested/available in the current Snowflake inventory.

## Status distinction
- Expected source table name: recovered from prior project work and owner-confirmed historically.
- Presence in current Snowflake: NOT established; current search evidence points to absent/not ingested.
- Level-355 business identity: live-confirmed on 2026-09-21.
- SSP Control Implementation implementation: blocked on missing current source dataset for the referenced control records.
- Historical structured/STG tables remain discovery-only and are not approved runtime sources.

## Consequence
Do not continue broad RAW-table guessing or map package-level count/helper fields
as substitutes for the missing Level-355 control records.

The correct next project action is to report/request ingestion of:
`ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`
(or the current platform-equivalent RAW dataset if ingestion naming has changed),
then resume implemented-requirements[] mapping from the actual control records.
