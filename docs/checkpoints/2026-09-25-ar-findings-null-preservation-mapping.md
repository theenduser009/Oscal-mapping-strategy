# Source One Assessment Results FINDINGS null-preservation mapping — 2026-09-25

## Evidence
Owner explicitly approved mapping FINDINGS even when null.

Live Source One profile on 2026-09-25:
- SOURCE_ROWS = 2,813
- JSON_NULL_ROWS = 2,813
- no current non-null finding payload is present.

## Decision
FINDINGS is now APPROVED as a source-preservation mapping under:

assessment-results.results[].props[]

Transform: direct
NULL_POLICY: preserve
Property identity: existing result-level SOURCE_FIELD_NAME policy
Property name: findings

This deliberately does NOT instantiate native:
assessment-results.results[].findings[]

because the current source provides no finding identity/content. A null result property preserves the current source state without fabricating finding UUIDs or relationships.

## Assessment Results mapping status
After this change:
- APPROVED = 45
- DEFERRED = 0
- Total Source One Assessment Results mapping rows = 45

RISK_ASSESSMENT_REPORT was separately approved earlier on 2026-09-25 as a canonical JSON-text result property preserving the attachment-ID array.

## Repository
- Branch: simplify-metadata-boundary
- FINDINGS mapping commit: cade4163c4f503e3b1335275b9fc4b79677ee049
- Mapping CSV blob: a425d53efbbbf5590fb34588acfccc7bb4326c54

## Validation actually performed
- Exact FINDINGS CSV row changed from DEFERRED to APPROVED.
- Null preservation uses existing Cell 3 / Cell 4 property behavior; no new code or registry change was required for FINDINGS.
- Read-back status count verifies all 45 Source One Assessment Results rows are now APPROVED.
- No Snowflake PREVIEW/COMMIT has yet been performed for the combined RISK_ASSESSMENT_REPORT + FINDINGS changes.

## Next action
Refresh latest mapping CSV, Cell 3 and Cell 4, then run Source One ASSESSMENT_RESULTS in PREVIEW.

Expected qualitative behavior:
- RISK_ASSESSMENT_REPORT produces one result property for each currently populated source array.
- FINDINGS produces one null-preserved result property per Source One record.
- Native findings[] remains empty because there is no current finding identity data.

If PREVIEW passes, COMMIT and capture read-back verification.
