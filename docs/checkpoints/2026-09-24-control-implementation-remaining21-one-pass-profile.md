# Remaining Control Implementation fields — one-pass shape profile

Date: 2026-09-24

## Repository
- Branch: simplify-metadata-boundary
- SQL commit: 9d0a0dbf39ded617a4b021e0cc14a3c79cdfe3fe

## Current accepted status before this profile
Owner-provided Snowflake evidence shows the corrected SSP snapshot committed and
read-back verified at 250,844 DIM nodes / 248,031 FACT edges for 2,813 source
records. Current Control Implementation CSV counts are 13 APPROVED, 10 EXCLUDED,
21 DEFERRED. Of the 13 approved rows, 11 are package-level summaries and 2 are
Level-355 control-detail fields (CONTROL_NUMBER and IMPLEMENTATION_DETAILS).

## Why this query exists
The next mapping must be driven by actual remaining Excel fields. CONTROL_OWNER_CO
and SECURITY_CONTROL_ASSESSOR_SCA are present in the review workbook, but the
workbook does not establish their physical source location or Archer serialization.
The remaining bullet candidates likewise have no supplied individual path/type.

Rather than run 21 separate diagnostics, one SELECT-only query compares all 21
remaining fields across Authorization Package and the matched Level-355 dataset.
It returns only aggregate presence/type/reference-shape counts; no source values,
record IDs, user names or payload text are returned.

## Next action
Run sql/validation/2026-09-24_control_implementation_remaining21_shape_profile.sql
once and return the result grid. Use that single result to classify the remaining
fields into direct property, select/property, role/reference, relationship, empty,
or workflow/helper buckets before changing the CSV.

No mapping, registry, notebook runtime or target DIM/FACT change is made by this
checkpoint.
