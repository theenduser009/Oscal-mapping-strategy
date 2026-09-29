# One-update Matillion raw-to-CURATED_JSON plus Meta User enrichment

Date: September 29, 2026
Status: Combined one-UPDATE candidate committed and repository read-back verified. Not compiled or executed in Snowflake/Matillion.

## Repository version

- Branch baseline before combined publication: simplify-metadata-boundary at 0cdfd4e6e8a22222b5fa068ce5ab88ce4d1eca16.
- Combined SQL path: sql/matillion/CANDIDATE_raw_curated_with_meta_user_enrichment.sql.
- Initial publication commit: 5f9bc70210291e7203aec5db822a33ab004f81c9.
- A text-generation substitution issue in the first publication was detected before user delivery and corrected.
- Corrected commit: 85ad741cf3ae782c671d29d9c9e87f2573117b54.
- Corrected blob after full read-back: ebcd0a2442d06f0a703841abfb79e3796650cd86.

The initial broken publication must not be used. The corrected blob above supersedes it.

## Agreed normal flow

1. COPY/source load into RAW; CURATED_JSON starts SQL NULL for the new load.
2. Run one Matillion UPDATE that performs:
   - FIELD_ID -> ARCHER_META_FIELD.SQL_FIELD_NAME;
   - owner-confirmed source-side TRY_TO_NUMBER FIELD_ID safety;
   - type conversion and nested extraction;
   - JSON-null key preservation;
   - ID_SOURCE_JSON-based CONTENT_ID selection;
   - UserList[].Id -> ARCHER_META_USER.ARCHER_USER_ID enrichment;
   - final CURATED_JSON and CONTENT_ID persistence.
3. Run the OSCAL mapper.

There is no second Meta User UPDATE in the preferred normal-load design.

## User enrichment contract

- Preserve every original UserList member key including Id and permission flags.
- Add ResolvedUser containing ContractVersion, LookupStatus, EEID, FIRST_NAME, MIDDLE_NAME and LAST_NAME.
- Valid unmatched IDs remain present as USER_NOT_FOUND; no EEID/name is invented.
- MATCHED_MISSING_EEID remains explicit when applicable.
- Malformed/ambiguous user enrichment does not block raw-to-curated conversion for the record; that record falls back to the un-enriched candidate JSON.
- GroupList is not changed. Meta Group enrichment waits for the authoritative group lookup contract.

## Meta Value scope

ARCHER_META_VALUE resolution is not duplicated into this Matillion candidate. The existing OSCAL mapper already owns select-value label resolution. This is an explicit current design decision, not a completed upstream Meta Value enrichment.

## Read-back checks performed

The corrected repository file was fetched in full. It contains:
- the current TRY_TO_NUMBER(f.FIELD_ID) behavior in the ordering and top-level join;
- TRY_TO_NUMBER(nf.FIELD_ID) in the nested join;
- the verified UserList[].Id regex/key extraction;
- ARCHER_META_USER lookup;
- ResolvedUser construction;
- no ARCHER_META_GROUP or ResolvedGroup enrichment;
- the original pending-row CURATED_JSON IS NULL source and target predicates.

No Snowflake SQL compilation, Matillion run, PREVIEW, UPDATE execution, COMMIT or database read-back has been performed for the combined statement.

## Next action

Use only the corrected combined file for DEV:
sql/matillion/CANDIDATE_raw_curated_with_meta_user_enrichment.sql

Replace the existing Matillion raw-to-curated UPDATE with this candidate in DEV, run the normal COPY + UPDATE flow, then inspect the persisted CURATED_JSON for a small responsible-party sample before running the downstream OSCAL mapper.

The standalone user-enrichment UPDATE remains historical/test scaffolding and is superseded as the preferred normal-load design by this one-update candidate.
