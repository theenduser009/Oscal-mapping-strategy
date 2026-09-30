# SSP security-impact all-field validation harness

Date: September 30, 2026
Status: Code/documentation committed and read-back verification pending in this checkpoint. No Snowflake execution claimed.

## Current executable inventory

The historical 13-row Security Impact section contains:
- 11 active candidate mappings into the three security-impact-level objectives;
- SECURITY_CATEGORY, which maps separately to security-sensitivity-level;
- FULL_CONTROL_ASSESSMENT_HELPER, which is excluded.

Current mapper behavior:
- Low / Moderate / High labels normalize to lowercase;
- explicitly approved Legacy LOE labels are preserved;
- conflicting populated candidate values for one singleton objective fail closed;
- no precedence hierarchy is implemented.

## Added

- docs/guides/SSP_SECURITY_IMPACT_FIPS199_END_TO_END.md
- sql/qa/SSP_SECURITY_IMPACT_ALL_FIELDS_END_TO_END.sql

## Validation status

Repository changes only. The new SQL has not yet been owner-run in Snowflake. Current source/target conclusions remain limited to the earlier confidentiality/integrity owner checks and historical read-only checkpoints.

## Next action

Owner runs Query 1 from SSP_SECURITY_IMPACT_ALL_FIELDS_END_TO_END.sql and reviews VALIDATION_STATUS, especially any CONFLICTING_SOURCE_CANDIDATES, MISMATCH, MISSING_TARGET, or UNRESOLVED_OR_UNAPPROVED_SOURCE_LABEL rows.
