# Expanded Source One published OSCAL views — 2026-09-25

## Repository
- Branch: simplify-metadata-boundary
- Head before checkpoint: 625bf9ddee3d49ed83236232735ca1bb6f489a8d
- Expanded ALL view commit: cace90436c4cdbfae26b19772f036e3f1e108e8a
- Refreshed ACTIVE view commit: 625bf9ddee3d49ed83236232735ca1bb6f489a8d

## Existing published views
- RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_PUBLISHED.C2S_OSCAL_AUTHORIZATION_PACKAGE_ALL
- RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_PUBLISHED.C2S_OSCAL_AUTHORIZATION_PACKAGE_ACTIVE

## What changed
The ALL view remains one row per Source One SOURCE_RECORD_ID and now exposes substantially more OSCAL information while avoiding child-to-child fanout.

Added/expanded:
- strict Source One namespace filtering on all four OSCAL DIM models;
- SSP metadata published/last-modified/document ids/metadata properties;
- all responsible-party roles plus full responsible-party array;
- roles and parties arrays;
- full system-id array;
- all system-characteristics extension properties as one VARIANT object;
- authorization-decision scalar exposure;
- system implementation component count + structured component array;
- control implementation implemented-requirement count + structured control array;
- per-record SSP node/edge counts and relationship-integrity status;
- Assessment Results node/edge counts, observation count, native-finding count,
  structured observation array and result-property object;
- POA&M node/edge counts, item count and item array;
- Security Assessment Plan node/edge counts, task count, task array and property object;
- cross-model coverage and overall relationship-integrity status.

The ACTIVE view remains a thin SELECT * over ALL with the existing acronym filter.
Its SQL was refreshed so it can be recreated after the expanded ALL view.

## Design decision
Cross-model integration uses SOURCE_RECORD_ID. FACT foreign keys remain model-local.
One-to-many collections are aggregated before the final join to preserve one row
per Authorization Package and avoid Cartesian multiplication.

## Validation actually performed
Repository read-back verified:
- ALL view contains Source One filters;
- component aggregation is present;
- implemented-requirement aggregation is present;
- Assessment Results observation aggregation is present;
- POA&M item aggregation is present;
- Assessment Plan task aggregation is present;
- overall relationship-integrity output is present;
- ACTIVE remains SELECT * over ALL.

No live Snowflake CREATE VIEW has been executed by the assistant, and no live
query result has yet validated Snowflake compilation or row counts for this revision.

## Next action
Execute in Snowflake, in this order:
1. sql/published/C2S_OSCAL_AUTHORIZATION_PACKAGE_ALL_POC.sql
2. sql/published/C2S_OSCAL_AUTHORIZATION_PACKAGE_ACTIVE_POC.sql

Then validate:
- COUNT(*) of ALL = expected Source One package count;
- one row per ARCHER_AUTHORIZATION_PACKAGE_DATA_CONTENT_ID;
- CROSS_MODEL_COVERAGE = PASS;
- OVERALL_RELATIONSHIP_INTEGRITY = PASS;
- spot-check one CONTENT_ID's structured component/control/AR/POAM/SAP columns.

If Snowflake reports a compilation error, use that exact error as the next checkpoint; do not simplify or remove data blindly.
