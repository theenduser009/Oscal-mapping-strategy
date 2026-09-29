# Latest Matillion CURATED_JSON user-enrichment candidate

Date: September 29, 2026
Status: New candidate SQL committed and repository read-back verified. No Snowflake or Matillion execution has occurred.

## Baseline

- Branch before this change: simplify-metadata-boundary at 6b99d82541bd6dbc3ef637090151658ff15c2323.
- Current raw-to-curated baseline already includes:
  - JSON-null key preservation;
  - ID_SOURCE_JSON isolation for CONTENT_ID selection;
  - owner-confirmed TRY_TO_NUMBER on source-side FIELD_ID ordering and metadata joins.

## New candidate

Path:
- sql/matillion/CANDIDATE_enrich_curated_json_users.sql

Publication commit:
- ad256ab16f35ef33582227eea4e0468a8ad909de

Read-back blob:
- 9f571642b592793ef2d05893705e8bd2bac923cd

## Intended Matillion flow

1. Run the existing raw-to-CURATED_JSON conversion.
2. Run the new Meta User enrichment step.
3. Run the OSCAL mapper.

The enrichment step resolves UserList[].Id through RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER.ARCHER_USER_ID and adds ResolvedUser with ContractVersion, LookupStatus, EEID, FIRST_NAME, MIDDLE_NAME and LAST_NAME.

Original UserList member Id and HasRead/HasUpdate/HasDelete values are preserved. Unmatched users remain present with USER_NOT_FOUND rather than being dropped or assigned a fabricated identity.

GroupList remains unchanged. No group-name enrichment is implemented because the authoritative Meta Group lookup table/columns are still unavailable.

## Why this is a separate Matillion step

Keeping user enrichment separate from the already-corrected raw-to-curated converter makes the new responsibility isolated and reversible. It also allows enrichment of already-populated CURATED_JSON without changing the converter's existing NULL-only processing boundary.

This supersedes the earlier idea of folding all user-enrichment CTEs directly into the main conversion UPDATE as the preferred implementation shape. The business result remains the same: resolved user attributes are persisted in CURATED_JSON before the OSCAL mapper reads it.

## Validation performed

- Repository branch/version checked before creating the file.
- Candidate created in GitHub and fetched back in full.
- Read-back confirms:
  - UserList[].Id is the only user lookup key;
  - original member payload is retained and only ResolvedUser is inserted/refreshed;
  - GroupList is never modified;
  - unmatched/invalid users receive explicit status without invented identity;
  - foreign ResolvedUser contracts block a record rather than being overwritten;
  - source-row matching uses RequestedObject.Id, consistent with the current converter.

No Snowflake compilation, PREVIEW, Matillion run, UPDATE, COMMIT or database read-back has been performed.

## Next action

Review the SQL in GitHub. Before enabling this write step in Matillion, run a read-only preview of the same full-scope enrichment output against Dev or convert this candidate temporarily to SELECT-only for final aggregate counts.

Downstream OSCAL party payload changes remain separate: the current mapper still needs an explicit reviewed change to consume ResolvedUser EEID/name and expose the desired reporting lineage in DIM/Power BI.
