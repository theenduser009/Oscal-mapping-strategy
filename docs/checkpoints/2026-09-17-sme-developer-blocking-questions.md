# Checkpoint — SME developer-blocking questions

Date: 2026-09-17
Repository: `theenduser009/Oscal-mapping-strategy`
Branch: `simplify-metadata-boundary`
Implementation baseline reviewed before question write: `e802f04d3c0767b2d0eea28934699366e0f18559`
Question-list commit: `f603edcad399415125fb08c95a6059e7ed440ab6`

## Change

Added `questions/SME_DEVELOPER_BLOCKING_QUESTIONS_2026-09-17.md` as a short, email-ready list of only the mapping decisions that currently prevent a developer from completing a safe mapping.

The list was derived from the current repository mapping documents and deferred/ambiguous rows, then checked against NIST OSCAL references for SSP Control Implementation, Profile, Assessment Results, Catalog, and Component Definition.

## Included blockers

- Allocated Controls -> SSP implemented-requirement source fields and grain.
- Control Implementation rows with no exact OSCAL path.
- Profile import href/control-selection source.
- ADD_OVERLAY routing among Profile import/merge/modify semantics.
- AUTHORIZATION_DECISION collision with SSP operational status.
- Assessment Results rows whose source mapping gives alternative representations.
- Source 2 SOURCE_DESCRIPTION / INFORMATION collision on Catalog metadata remarks.
- Source 2 CONTROL_PROCEDURES ambiguity between Catalog and Component Definition.
- Request for original untruncated mapping rows where screenshot transcription is clipped.

## Deliberately excluded

Generic ContentId/LevelId routing, system/helper fields, timestamp/timezone questions, routine link/back-matter mechanics, and already-resolved implementation mechanics were intentionally left out of this concise SME email list.

## Validation actually performed

- Re-read the current project handoff before changing repository material.
- Verified branch head at `e802f04d3c0767b2d0eea28934699366e0f18559` before the write.
- Read current `questions/SME_OPEN_QUESTIONS.md` and current mapping review files.
- Read current deferred/ambiguous rows in `Mapping/ARCHER_OSCAL_MAPPINGS.csv`.
- Reviewed NIST OSCAL references for the relevant model semantics.
- Read back the newly created question file from GitHub after commit.

No Snowflake query, PREVIEW, COMMIT, registry change, mapper-code change, or runtime CSV change was performed for this checkpoint.

## Remaining gap / next action

Owner should review the short question list for wording and send the accepted questions to the SME/mapping owner. SME answers should then be recorded against the exact source field and intended OSCAL model/path before any corresponding deferred mapping is promoted to executable metadata.
