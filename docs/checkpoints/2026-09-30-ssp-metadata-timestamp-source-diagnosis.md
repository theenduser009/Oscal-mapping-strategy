# SSP metadata timestamp source diagnosis

Date: September 30, 2026
Status: Owner-run Snowflake output reviewed. No mapper change made.

## Owner-run evidence

For the sampled SSP metadata rows:
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED is null.
- FIRST_PUBLISHED is populated.
- OSCAL metadata.published exactly matches FIRST_PUBLISHED.

Likewise:
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED is null.
- LAST_UPDATED is populated.
- OSCAL metadata.last-modified exactly matches LAST_UPDATED.

## Interpretation

The two package-prefixed mappings are currently dormant for this source snapshot.
The populated generic FIRST_PUBLISHED / LAST_UPDATED fields are the mappings actually supplying the persisted metadata timestamps.

This does not prove the package-prefixed mappings are universally unnecessary; they remain part of the reviewed mapping source and could become populated in a future snapshot.

Current mapper behavior is safe if both mappings ever become populated with conflicting values: singleton target assignment fails closed rather than silently choosing one.

## Current metadata status

Verified so far:
- metadata.title <- AUTHORIZATION_PACKAGE_NAME (support mapping; source and target match in owner-run sample)
- metadata.published <- FIRST_PUBLISHED for current snapshot
- metadata.last-modified <- LAST_UPDATED for current snapshot
- metadata.version = configured SSP document version
- metadata.oscal-version = configured OSCAL version

Next field to inspect:
- TRACKING_ID -> metadata.document-ids[].identifier
