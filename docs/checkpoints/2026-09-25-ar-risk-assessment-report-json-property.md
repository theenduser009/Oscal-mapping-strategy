# Source One Assessment Results final populated field mapping — 2026-09-25

## Evidence
Owner-provided Snowflake profile on 2026-09-25 shows:
- FINDINGS: 2,813 source rows; 2,813 JSON-null rows; therefore no current finding payload to instantiate.
- RISK_ASSESSMENT_REPORT: 2,813 source rows; 316 populated roots; all 316 populated roots are arrays; 742 total items; all 742 items are INTEGER; zero text/object/nested-array/other-number items.

## Decision
RISK_ASSESSMENT_REPORT is now APPROVED as:
assessment-results.results[].props[]

Transform: json-text.

Each source array is preserved as one canonical JSON string property value. This keeps all attachment IDs, supports multiple IDs per result, and preserves the existing SOURCE_FIELD_NAME identity policy for result properties. It intentionally does NOT invent:
- a URL or URN,
- an OSCAL back-matter resource,
- a resource UUID,
- an attachment download location,
- or a resolved document relationship.

FINDINGS remains DEFERRED because the current source is entirely JSON null. No finding identity, title, description, target, or relationship is fabricated.

## Runtime changes
- Added reusable transform id json-text to maintained Cell 3 and cells_v2 Cell 3.
- Added stable JSON serialization implementation to maintained Cell 4 and cells_v2 Cell 4.
- Updated one CSV row: RISK_ASSESSMENT_REPORT.
- No registry change.
- No target DML performed by this repository update.

## Validation actually performed
- Read-back verified maintained/v2 Cell 3 equality.
- Read-back verified maintained/v2 Cell 4 equality.
- Read-back verified json-text registration and implementation are present.
- Read-back verified RISK_ASSESSMENT_REPORT is APPROVED with json-text to results[].props[].
- No live Snowflake PREVIEW/COMMIT has yet been performed for this mapping.

## Next action
Refresh the latest Cell 3, Cell 4, and mapping CSV, then run Source One ASSESSMENT_RESULTS in PREVIEW. If clean, COMMIT and capture read-back.

Expected qualitative effect:
- no new result roots,
- one additional result property for each of the 316 source records with a populated RISK_ASSESSMENT_REPORT array,
- no FINDINGS nodes.
Do not hard-code an exact DIM/FACT delta until PREVIEW confirms the current persisted target state.
