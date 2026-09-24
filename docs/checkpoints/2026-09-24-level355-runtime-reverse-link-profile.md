# Relationship metadata not exposed; use targeted runtime reverse-link evidence — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `222dc86f3e6f23a0ee65725db014916921079503`

## Owner-provided live Snowflake evidence
The FIELD_GUID trace for Source One ALLOCATED_CONTROLS confirmed:
- FIELD_GUID = E84D64F5-668F-47B5-AC50-89B6F6E67692
- the GUID appears only in ARCHER_META_FIELD and ARCHER_META_FIELD_STG
- no current relationship/reference/xref schema candidate is exposed
- result = RELATIONSHIP_METADATA_NOT_EXPOSED_IN_CURRENT_SCHEMA

## Decision
Stop searching for a relationship metadata table that is not present in this
Snowflake metadata layer.

Use targeted current-runtime evidence instead: profile only Level-355 fields whose
names explicitly describe Authorization Package linkage, plus CONTROL_TO_INHERIT
as a comparison. Compare embedded ContentId references directly to current
Authorization Package CONTENT_ID values.

This is a fallback to empirical source evidence, not a claim that field names by
themselves prove the relationship.

## Next action
Root `RUN_NOW.py` now profiles:
- AUTHORIZATION_PACKAGE
- AUTHORIZATION_PACKAGE_SELECT_CONTROL
- AUTHORIZATION_PACKAGE_ARCHIVED_CONTROLS
- AUTHORIZATION_PACKAGES_ALLOWED_TO_INHERIT
- CONTROL_TO_INHERIT

It reports only aggregate linkage counts and ranks fields by actual Authorization
Package matches. No DML is performed.
