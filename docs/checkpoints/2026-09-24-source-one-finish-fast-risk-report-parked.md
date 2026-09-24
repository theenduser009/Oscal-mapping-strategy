# Source One finish-fast decision — RISK_ASSESSMENT_REPORT parked — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before this checkpoint: `f6f169d61a48578d809daff58584785da1e96496`

## Owner-provided live Snowflake evidence
The current RISK_ASSESSMENT_REPORT discovery returned:
- Source records: 2,813
- Archer metadata: FIELD_TYPE_ID 11, LEVEL_ID 353, MODULE_ID 547
- current repository candidates by name:
  - ARCHER_CONTENT_DOCUMENT_REPOSITORY_RAW
  - ARCHER_CONTENT_EVIDENCE_REPOSITORY_RAW
- both candidate tables expose RAW_DATA-style payloads rather than the CURATED_JSON contract used by the current attachment diagnostic
- no attachment-ID resolution was established by the diagnostic
- result = ATTACHMENT_IDS_NOT_RESOLVED_IN_CURRENT_CANDIDATE_RAW_TABLES

## Decision
Do not spend more sprint time reverse-engineering attachment storage right now.

RISK_ASSESSMENT_REPORT remains an explicit documented Source One exception:
- OSCAL representation is not promoted
- no href/URN is invented
- no historical structured/STG table is used as runtime proof
- no DIM/FACT DML is required for this field

This is a source/runtime-contract blocker, not unfinished mapper coding.

## Source One finish-fast priority
The current runtime Source One routes are SSP, ASSESSMENT_RESULTS, POAM and
SECURITY_ASSESSMENT_PLAN.

Current evidence:
- SSP: fresh 2026-09-24 PREVIEW is zero-delta at 89,629 nodes / 86,816 edges.
- Assessment Results: 2026-09-21 COMMIT/read-back verified.
- POAM: current repository contains no newer COMMITTED_AND_VERIFIED checkpoint.
- Security Assessment Plan: current repository contains no newer COMMITTED_AND_VERIFIED checkpoint.

Therefore the fastest remaining execution checkpoint is a combined read-only
PREVIEW of POAM + SECURITY_ASSESSMENT_PLAN.

## Next action
In Cell 1 set:
`SELECTED_MODELS = ("POAM", "SECURITY_ASSESSMENT_PLAN")`

In the same notebook session, run:
1. Cell 1
2. Cell 2
3. Cell 3
4. Cell 7 with OSCAL_LOAD_MODE = "PREVIEW"

Cells 4-6 do not need to be rerun if their definitions are still loaded.

Use that one report to determine whether either remaining route needs a commit.
