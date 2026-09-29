# Matillion raw-to-curated SQL change comparison

Date: September 29, 2026
Status: Repository comparison completed. No Snowflake or Matillion change performed.

## What was compared

1. Historical screenshot-transcription checkpoint added September 11, 2026:
   commit `ab07a7484e4b83a0699e8f3cb64cb4f588c5d5a4`,
   file `docs/raw_curated_json_update_sql_checkpoint.md`.
2. Null-key retention candidate added later the same day:
   commit `2a5f8562d696a23eb17a05e93bb373587af1d1aa`,
   file `sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql`.
3. Current branch version of that candidate on `simplify-metadata-boundary`.

The candidate blob at its original September 11 commit and the current branch blob are both:
`89793be25352cdd5292a7ab512403bd074ce9830`.

Therefore the GitHub candidate file itself has not changed since it was created on September 11.

## Changes from the older transcription to the candidate

The September 11 original transcription built:

`OBJECT_AGG(SQL_KEY, TYPED_VALUE) AS CURATED_JSON`

and derived CONTENT_ID from values inside CURATED_JSON.

The later candidate changed only the intended null-preservation/identity-isolation boundary:

1. CURATED_JSON now retains named SQL-null values as JSON null:
   `OBJECT_AGG(SQL_KEY, COALESCE(TYPED_VALUE, PARSE_JSON('null'))) AS CURATED_JSON`.

2. A second internal aggregate was added:
   `OBJECT_AGG(SQL_KEY, TYPED_VALUE) AS ID_SOURCE_JSON`.

3. The CONTENT_ID fallback chain now reads from `ID_SOURCE_JSON` rather than the null-preserving `CURATED_JSON`, so retaining null keys cannot accidentally change the existing identity-selection behavior.

4. `ID_SOURCE_JSON` is passed through the inner SELECT but is not written to the target table.

The field extraction, ARCHER_META_FIELD join, row-precedence logic, type conversions, recursive nested extraction, UNION, source table variable, and both `CURATED_JSON IS NULL` predicates were intentionally preserved.

## Current evidence boundary

The current owner screenshots supplied September 29 visibly show the null-preserving aggregate and ID_SOURCE_JSON pattern, so the visible portions are consistent with the repository candidate.

However, GitHub still labels the candidate as derived from screenshots rather than a byte-for-byte export of the live Matillion component. This comparison does not prove that no additional unshared Matillion edits exist outside the visible screenshots.

## Next action

Use the current candidate as the known baseline for adding the approved Meta User enrichment, but compare the resulting replacement once against the actual Matillion component before deployment.
