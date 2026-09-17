# Source 2 SME question register — publication checkpoint

Date: 2026-09-17
Repository: `theenduser009/Oscal-mapping-strategy`
Branch: `simplify-metadata-boundary`
Reviewed implementation baseline: `64cfe17782500db73f636280540f37b29d5a63e0`
Question-register publication: `1b3db602f777c71c23e0d1ca80bf9e4cd0e29320`
Question-register blob: `3d64a67735f6ae80186d32f455bf4f17bf6764a2`

## Owner request and scope

The owner requested consolidation of the Source 2 mapping questions and suggestions in the existing SME question area, and objected to rewriting all seven cells merely to introduce Source 2. This is a documentation-only update. It does not authorize implementation of a proposal, mapping approval, registry changes, a new mapper, or a Snowflake run.

## Changes actually published

Updated the existing [questions/SME_OPEN_QUESTIONS.md](../../questions/SME_OPEN_QUESTIONS.md), retaining the five earlier questions and their September 15 evidence. Changed its update date and appended Source 2 issue IDs S2-01 through S2-13.

S2-01 through S2-10 preserve the ten issues discussed with the owner: property names; description/information collision; publication and last-modified ownership; review-to-runtime mapping; Catalog configuration/storage; registry/identity/null policies; physical source binding; clipped/ambiguous text; and the four-table hierarchy. S2-11 through S2-13 capture the related previously raised technical/helper/permission, alternative-model/reference, and Back Matter questions.

Each entry identifies the evidence, decision owner, question, proposed handling and whether it concerns the first Metadata pilot or later work. The existing timezone question is cross-referenced, not declared resolved.

Recorded the owner's September 17 clarification: SOURCE_DESCRIPTION describes the authoritative source and its Note also allows a Back Matter resource description; INFORMATION is additional information about the source. The prior suggestion to use remarks for SOURCE_DESCRIPTION and a property named information for INFORMATION remains a proposal, dependent on source content and SME agreement. No CSV destination was changed.

## Actual inspection and validation

- Read the project 00_START_HERE handoff and dated coverage material; retained their evidence boundaries rather than treating September 14 as the current branch state.
- Re-fetched the actual working branch: baseline `64cfe17782500db73f636280540f37b29d5a63e0`.
- Located the existing questions directory and read the full pre-update question register (blob `5d13106ed510bf11010bd4be60e90fb5751961ee`).
- Re-read the Source review CSV; inspected the relevant current Cell 3 compilation logic, Cell 4 singleton/property construction, Cell 6 CROSS_RECORD_EDGE guard, and the committed Catalog DDL. Other pinned cell excerpts and the four-sheet transcription checkpoint had already been retrieved in this project conversation.
- Published the question register and fetched all its content back in ranges at commit `1b3db602f777c71c23e0d1ca80bf9e4cd0e29320`; the returned blob matches the update response. Checked the earlier five questions, the complete Source 2 section, proposals and evidence references.
- Compared baseline to question publication: exactly one modified file, `questions/SME_OPEN_QUESTIONS.md`, with 188 additions and one deletion. The existing questions remain; the single prior-line replacement is the update date.
- No mapper tests, Snowflake PREVIEW, database COMMIT or database read-back was performed. This is GitHub documentation read-back, not database verification.

This checkpoint is the additional documentation file accompanying the verified question publication. Its presence does not change the implementation baseline.

## Supersession and unchanged decisions

The earlier blanket statement that Source 2 would never need any cell changes is superseded by the scoped assessment in the register. The seven-cell framework is retained. Cell 1 source/model configuration is a future integration task; optional PROPERTY_NAME support in Cells 3/4 is only an engineering proposal requiring approval and regression tests. Full cross-table Catalog assembly is not proven by source-profile configuration alone.

No runtime CSV, four review CSVs, notebook cell, registry SQL, target DDL, source data or Source 1 identity/behavior was modified by these documentation updates. No new execution statuses were assigned. Catalog DDL is committed/readable; its live execution is not established here.

Historical AR30 acceptance does not prove later AR32 changes; historical SSP acceptance does not prove the later daily-loss mapping. September 16 Validation 11 supports its recorded Source 1 component PREVIEW scope, not Source 2, a later COMMIT or full OSCAL schema conformance. Existing SAP/POAM evidence gaps are not reopened as rerun requests by this update.

## Remaining gaps and immediate next action

Obtain SME decisions for S2-02, S2-03 and S2-04, together with the existing timezone question: where the two text fields belong and which date fields own published/last-modified. Keep mapper changes paused while those decisions are recorded. Engineering source, table-definition and registry checks remain distinct from business approval. Request only the specific missing result or cell text when needed, not another upload of the already accessible four CSVs.

After relevant decisions and source contracts are verified, prepare a scoped Source/Catalog Metadata pilot using the existing engine; separately review/test any necessary generic capability, and retain PREVIEW before authorized COMMIT/read-back.
