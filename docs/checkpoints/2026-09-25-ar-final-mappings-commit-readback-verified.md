# Source One Assessment Results final mappings COMMIT/read-back verified — 2026-09-25

## Repository basis
- Branch: simplify-metadata-boundary
- Head inspected before checkpoint: 17c2ba46ed45a1767ec9daebadfcbbe8806413fa

## Owner-provided Snowflake COMMIT evidence
Source One / ASSESSMENT_RESULTS:
- mode = COMMIT
- status = COMMITTED_AND_VERIFIED
- source_records = 2,813
- nodes = 109,630
- edges = 106,817
- writes_executed = true
- persisted = true
- committed = true
- target_dml_attempted = true
- pre_write_validation_passed = true
- validation_passed = true
- storage_verified = true

Expected changes before write:
- DIM: INSERTS 3,129 / UPDATES 0 / UNCHANGED 106,501
- FACT: INSERTS 3,129 / UPDATES 0 / UNCHANGED 103,688

Post-commit verification:
- DIM: INSERTS 0 / UPDATES 0 / UNCHANGED 109,630
- FACT: INSERTS 0 / UPDATES 0 / UNCHANGED 106,817

## Final AR mapping scope
All 45 Source One Assessment Results CSV rows are now APPROVED.

The final two source-preservation mappings are:
- RISK_ASSESSMENT_REPORT -> results[].props[] via canonical json-text
- FINDINGS -> results[].props[] with explicit null preservation

Native findings[] is still not instantiated because current source contains no finding identity/content.

## Next Source One work
Remaining non-Profile DEFERRED rows are:
- 1 SSP Metadata field
- 12 SSP Control Implementation fields

These are the next closeout batch. They had no populated value in the last profile (Control Implementation) or previously recorded no-current-value evidence (metadata confirmation). Do not invent relationships for them; use source-preservation semantics only where approved.
