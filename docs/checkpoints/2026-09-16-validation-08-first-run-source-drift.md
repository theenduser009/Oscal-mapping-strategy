# Validation 08 first run — source-table vs CURATED_JSON drift found

Date: **2026-09-16**

Evidence: owner-provided Snowflake notebook screenshots for sample `SOURCE_RECORD_ID = 7344415`.

## First-run result

Validator: `08_SSP_SOURCE_TABLE_TO_OSCAL_SAMPLE_RECONCILIATION`
Validator version: `2026-09-16-r1`
Reported status: **FAIL**

Important interpretation: the reported failure was caused only by `WIDE_TABLE_VS_CURATED_JSON_MISMATCH = 11`. The same run reported:

- APPROVED_SSP_SOURCE_FIELDS: 45
- APPROVED_FIELDS_FOUND_IN_WIDE_TABLE: 45
- APPROVED_FIELDS_MISSING_FROM_WIDE_TABLE: none
- WIDE vs CURATED_JSON:
  - MATCH: 25
  - MISMATCH: 11
  - COMPLEX_REPRESENTATION_NOT_DIRECTLY_COMPARABLE: 9
- OSCAL_OWNER_PATHS_CHECKED: 10
- OSCAL_EXPECTED_INSTANCES: 15
- OSCAL_ACTUAL_INSTANCES: 15

The screenshots did not show an OSCAL expected-vs-actual failure. Therefore this first run does **not** prove that OSCAL mapping is wrong; it proves that the wide source table and the frozen `CURATED_JSON` snapshot are not byte-for-byte equivalent for all sampled approved fields.

## Examples visible in the screenshots

- `ATOIATO_DATE`: wide table `2024-09-13 00:00:00`, CURATED_JSON `2024-09-13` — expected date-shape normalization candidate.
- `AUTHORIZATION_BOUNDARY_DESCRIPTION`: wide form contains escaped markup (`\u003C...`), CURATED_JSON contains decoded `<p>...` — representation normalization candidate.
- `FIRST_PUBLISHED`: wide table second precision vs CURATED_JSON fractional-second precision — precision/representation difference.
- `LAST_UPDATED`: wide table `2026-06-19 13:51:23` vs CURATED_JSON `2026-06-08 12:50:31.320` — material source snapshot difference requiring upstream/source-timing investigation.
- `ACRONYM`: wide value `CCS Hardware` vs CURATED_JSON `CCS Tanjum` — material source difference requiring investigation.
- `AUTHORIZATION_PACKAGE_NAME`: materially different wide and CURATED_JSON text — source normalization/snapshot difference requiring investigation.
- `MISSION_PURPOSE`: wide value null while CURATED_JSON is populated — source snapshot/derivation difference requiring investigation.
- `HARDWARE` and `SOFTWARE`: wide table contains serialized identifiers while CURATED_JSON is null in the sample — complex/source-population difference; these should not be treated as simple scalar equality failures.

## Superseding validator behavior

Validation 08 was revised to `2026-09-16-r2` so that wide-table vs CURATED_JSON differences are diagnostics rather than OSCAL mapping failures. The mapper consumes `CURATED_JSON`, therefore OSCAL pass/fail is determined by:

`CURATED_JSON -> current approved mapping transforms -> expected OSCAL -> actual OSCAL candidate graph`.

Wide-table differences are now categorized separately, including `NORMALIZATION_EQUIVALENT` and `SOURCE_SNAPSHOT_OR_NORMALIZATION_DIFFERENCE`.

## Next action

Run the revised Validation 08 (`r2`) against the same sample record. If OSCAL failures remain empty while source diagnostics persist, preserve the mapping PASS and investigate the source-table/CURATED_JSON differences separately.