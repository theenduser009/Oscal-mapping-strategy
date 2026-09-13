# Restore direct sensitivity mapping after live value reconciliation

The owner's [corrected live value report](2026-09-13-ssp-read-only-value-reconciliation.md)
resolves the two differences found in the accepted SSP preview:

- All 36 changed impact nodes reproduce their retained source values. Each of
  the three objectives changes stored `low` to candidate `Low`; all are
  `CASE_ONLY`. The published one-line Cell Two lowercase lookup correction
  addresses that casing difference.
- All 1,958 removed sensitivity members have populated direct-text
  `SECURITY_CATEGORY` source values. The helper's resolved source labels match
  the stored values. Its source-label comparison strips surrounding whitespace;
  the report does not prove that every raw string is already trimmed.

The owner asked to retain the existing FIPS mapping and use the straightforward
direct transformation. Restore the existing documented CSV row from
`SECURITY_CATEGORY` to
`system-security-plan.system-characteristics.security-sensitivity-level`
with `TRANSFORM_ID = direct`. This copies the source value without deriving it
from CIA values or recommended categories. The metadata-only change adds no
runtime code. The FIPS correction and original transform fixtures remain intact.

The restored row raises executable coverage from 47 to 48 SSP rules; AR remains
17. CSV row count remains 151. The previously accepted 1,403 transform cases
and SSP/AR business fixtures remain checked against immutable evidence, with
separate coverage for the restored row. This restores an existing stored member;
it does not establish full OSCAL conformance or approve target writes.

## Next action

1. Replace the notebook Files copy of `ARCHER_OSCAL_MAPPINGS.csv` with the
   corrected CSV and replace Cell Two with its published version.
2. Keep the existing deployment settings, `EXECUTE_WRITES = False` and Cell
   Seven in `PREVIEW`. Run Cells One through Seven once so the corrected graph
   gets a fresh run identifier.
3. Inspect the new aggregate report. With equivalent inputs and no other
   differences, the two corrections should remove the explained 1,994 updates.
   This is an expectation to verify, not a claimed live result. Raw whitespace,
   other records and changed source/target data can produce remaining changes.

The extended value review is complete and need not be repeated. This new
preview is necessary because the earlier candidate does not contain these
corrections. No registry reset, schema work or full-table reload is required.
Daily COMMIT and committed readback remain pending.
