# C2S legacy-view requirement gap plan — 2026-09-25

Owner-provided screenshots establish 35 output columns in the existing
C2S_AUTHORIZATION_PACKAGE_ALL consumer contract.

Current assessment:
- 7 columns are directly supported from current OSCAL data:
  CONTENT_ID, AUTHORIZATION_PACKAGE_NAME, OPERATIONAL_STATUS,
  WORKFLOW_STATUS, ATOIATO_DATE, AUTHORIZATION_DECISION, ACRONYM.
- 5 columns have a related OSCAL concept but cannot yet reproduce the exact
  legacy consumer value without additional preservation/hydration:
  LEGACY_SAP_ID, POAMS, INFORMATION_OWNER_IO, AUTHORIZING_OFFICIAL_AO,
  CONFIRMEDINARCHER.
- 23 columns are not currently reproducible from the OSCAL-only published view.
  Most are legacy enrichment/display fields sourced from Business, POA&M detail,
  Workday/LDAP user, or Entity datasets, plus unmapped submit/expiration dates.

This is a consumer-contract gap, not evidence that the existing approved OSCAL
mappings are mechanically incorrect.

Required plan:
1. profile the missing source-like fields in Authorization Package RAW;
2. discover the actual current lookup/raw objects for Business, POA&M detail,
   Entity and Workday/LDAP;
3. preserve external party IDs in metadata.parties[] and hydrate party names
   where an approved user lookup exists;
4. hydrate POA&M item IDs/names rather than exposing only UUID references;
5. determine whether LEGACY_SAP_ID equals SAP_ID or is a separate identifier;
6. map/preserve submit and expiration dates if current source evidence exists;
7. ingest/map Business and Entity relationships if the published view contract
   must be satisfied entirely from OSCAL;
8. update the OSCAL published view only after these mappings are committed and
   old-vs-new parity is validated.

Do not silently map SYSTEM_ADMINISTRATOR_SA to ISA or LEGACY_SAP_ID to SAP_ID
without evidence that those semantics are identical.
