# Source One Assessment Results COMMIT and read-back verified — 2026-09-21

## Repository basis
- Working branch: `simplify-metadata-boundary`
- Mapping CSV blob used for the final Source One AR run: `5c6027f09151254a0a070ddaf2f980c953d2f228`
- Prior reconciled-preview checkpoint commit: `1242142b29c251a024a84ee3214e8f19414d7b98`

## Owner-provided live Snowflake COMMIT evidence

The owner ran the guarded Assessment Results pipeline in COMMIT mode after the
final Source One mapping compile, PREVIEW, and insert reconciliation all passed.

### Source One / ASSESSMENT_RESULTS
Observed:
- mode: `COMMIT`
- status: `COMMITTED_AND_VERIFIED`
- source records: `2,813`
- nodes: `106,501`
- edges: `103,688`
- pre-write validation passed: `true`
- validation passed: `true`
- storage verified: `true`
- writes executed: `true`
- persisted: `true`
- committed: `true`
- target DML attempted: `true`
- expected DIM changes before write:
  - inserts: `16,485`
  - updates: `0`
  - unchanged: `90,016`
- expected FACT changes before write:
  - inserts: `16,485`
  - updates: `0`
  - unchanged: `87,203`
- post-commit DIM verification:
  - inserts: `0`
  - updates: `0`
  - unchanged: `106,501`
- post-commit FACT verification:
  - inserts: `0`
  - updates: `0`
  - unchanged: `103,688`
- route status: `COMMITTED_AND_VERIFIED`
- temporary cleanup: `REMOVED`

This is the read-back verification for the September 21 Source One Assessment
Results batch. The earlier PREVIEW-only checkpoints no longer describe the
persistence state of this batch.

### Source Two / ASSESSMENT_RESULTS
The same aggregate COMMIT report also showed Source Two Assessment Results as
`COMMITTED_AND_VERIFIED` with 148 source records, 1,460 nodes and 1,312 edges.
That evidence remains separate from Source One completion status.

## Remaining Assessment Results exceptions
- `RISK_ASSESSMENT_REPORT` remains intentionally DEFERRED. It is an Archer
  attachment field with multi-valued attachment IDs and no approved current-runtime
  attachment identifier/resource contract.
- `FINDINGS` remains a separate deferred Source One reference decision; the
  current reviewed Source One sample was null. Its canonical destination remains
  `assessment-results.results[].findings[]`.

These exceptions are explicit; they are not hidden failures of the committed batch.

## Next Source One area
Move to the remaining SSP Metadata backlog (5 rows) before the larger
Control Implementation backlog:
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER
- SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO
- INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE
- INFORMATION_SYSTEM_ADMINISTRATOR_ISA
- AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR

Start with a read-only shape/metadata comparison against the already-approved
responsible-party fields. No write is authorized by this checkpoint.
