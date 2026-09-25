# Existing C2S published view contract captured from owner screenshots — 2026-09-25

The owner supplied screenshots of the existing published view:
RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_PUBLISHED.C2S_AUTHORIZATION_PACKAGE_ALL

Visible legacy columns include:
- ARCHER_AUTHORIZATION_PACKAGE_DATA_CONTENT_ID
- AUTHORIZATION_PACKAGE_NAME
- LEGACY_SAP_ID
- BUSINESS
- BUSINESS_NAME
- OPERATIONAL_STATUS
- POAMS
- POAM_ID
- POAM_NAME
- POAM_ID_NAME
- WORKFLOW_STATUS
- AUTHORIZATION_PACKAGE_SUBMIT_DATE
- ATOIATO_EXPIRATION_DATE
- SYSTEM_ADMINISTRATOR_SA and ID/name variants
- ALTERNATE_SYSTEM_ADMINISTRATOR_SA and ID/name variants
- INFORMATION_OWNER_IO and ID/name variants
- AUTHORIZING_OFFICIAL_AO and ID/name variants
- ENTITY
- ENTITY_NAME
- ATOIATO_DATE
- AUTHORIZATION_DECISION
- ACRONYM
- CONFIRMEDINARCHER

The visible SQL derives these through legacy curated Archer tables, including
Business, POA&M, Workday LDAP user and Entity tables.

This is not the same contract as the new OSCAL POC. Do not overwrite the
existing consumer view until parity and gap decisions are complete.

Current OSCAL mappings can directly support several old business fields
(AUTHORIZATION_PACKAGE_NAME, OPERATIONAL_STATUS, ATOIATO_DATE,
AUTHORIZATION_DECISION, ACRONYM), and provide richer graph-native information
(components, implemented requirements, AR observations/properties, POA&M items,
Assessment Plan tasks, UUIDs, and relationship-integrity metrics).

Several legacy display fields do not currently have equivalent OSCAL-only
semantics, especially Business/Entity/LDAP display-name columns and legacy
POA&M name fields. Do not silently alias these.

Added QA:
sql/qa/C2S_OLD_VIEW_VS_OSCAL_VIEW_2026-09-25.sql

Next:
1. create/recreate C2S_OSCAL_AUTHORIZATION_PACKAGE_ALL POC;
2. run old-vs-new parity QA;
3. decide unsupported legacy columns;
4. only then plan replacement/cutover of C2S_AUTHORIZATION_PACKAGE_ALL.
