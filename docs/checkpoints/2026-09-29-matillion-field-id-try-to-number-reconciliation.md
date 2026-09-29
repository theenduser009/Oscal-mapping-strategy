# Matillion FIELD_ID TRY_TO_NUMBER reconciliation

Date: September 29, 2026
Status: Owner-provided current Matillion screenshots reconciled to the repository candidate. No Snowflake or Matillion execution was performed.

## Confirmed differences

The current Matillion screenshots show three source-side FIELD_ID changes that were missing from the stored candidate:

1. ROW_NUMBER ordering: TO_NUMBER(f.FIELD_ID) -> TRY_TO_NUMBER(f.FIELD_ID)
2. Top-level metadata join: TO_NUMBER(amf.FIELD_ID) = TRY_TO_NUMBER(f.FIELD_ID)
3. Nested metadata join: TO_NUMBER(amf.FIELD_ID) = TRY_TO_NUMBER(nf.FIELD_ID)

The metadata-table side remains TO_NUMBER(amf.FIELD_ID).

## Repository updates

Branch: simplify-metadata-boundary

Updated and read back:
- sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql
- sql/matillion/READ_ONLY_raw_curated_null_preflight.sql
- tests/test_matillion_null_key_patch.py
- docs/RAW_CURATED_NULL_FIELD_FIX.md

Candidate update commit: 638ca4d1ae7a4643a8939f9deb590f59b64a4c21
Preflight update commit: f9a8cb7f33cebf83d07cbab8646b35f088427634
Test update commit: 0774dcc84be845cd693c3153ba01671d761a4e29
Guide update commit: 6f9cb840947578d671ff48d3f1b58d09cad3a587

Current candidate blob after read-back: 5bbc3f2e9186c2c20c21a5315586594ce2b51064.

Text verification found exactly two TRY_TO_NUMBER(f.FIELD_ID) occurrences and one TRY_TO_NUMBER(nf.FIELD_ID) occurrence in the candidate, with no remaining strict source-side TO_NUMBER join forms.

## Meaning

Nonnumeric source FIELD_ID values no longer throw at those three source-side conversion points; they convert to NULL for matching/ordering and can remain unresolved instead. This does not approve or invent mappings for nonnumeric keys.

The existing null-preserving CURATED_JSON and ID_SOURCE_JSON behavior remains unchanged.

## Next action

Use this synchronized candidate as the baseline for Meta User enrichment. Before deployment, compare the final enriched SQL once against the actual Matillion component because screenshots are not a byte-for-byte export.
