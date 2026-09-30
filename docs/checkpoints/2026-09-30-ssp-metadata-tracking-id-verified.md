# SSP metadata TRACKING_ID verification

Date: September 30, 2026
Status: Owner-run Snowflake output reviewed. No mapper change made.

## Owner-run evidence

For the sampled rows from sql/qa/SSP_METADATA_TRACKING_ID_SOURCE_CHECK.sql:
- CONTENT_ID was present;
- Archer TRACKING_ID was populated;
- OSCAL metadata.document-ids[].identifier matched the Archer TRACKING_ID for the displayed rows.

## Interpretation

TRACKING_ID -> system-security-plan.metadata.document-ids[].identifier is verified end-to-end for the owner-reviewed sample.

## Metadata fields verified so far

- metadata.title <- AUTHORIZATION_PACKAGE_NAME: source/target sample matched.
- metadata.published <- FIRST_PUBLISHED for current snapshot: matched.
- metadata.last-modified <- LAST_UPDATED for current snapshot: matched.
- metadata.document-ids[].identifier <- TRACKING_ID: matched.
- metadata.version and metadata.oscal-version are support/config values and were present in target.

Remaining metadata review is primarily responsible-party mappings.
