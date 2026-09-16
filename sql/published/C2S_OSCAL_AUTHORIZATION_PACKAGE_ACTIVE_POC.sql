-- POC ACTIVE view over the OSCAL Authorization Package ALL view.
-- Mirrors the current consumer-side ACTIVE filtering pattern shown in the existing view.
-- Keeps the ACTIVE view thin so every supported OSCAL column from ALL is inherited automatically.

CREATE OR REPLACE VIEW
RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_PUBLISHED.C2S_OSCAL_AUTHORIZATION_PACKAGE_ACTIVE
AS
SELECT *
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_PUBLISHED.C2S_OSCAL_AUTHORIZATION_PACKAGE_ALL
WHERE ACRONYM LIKE '%IPNCCS%'
   OR ACRONYM LIKE '%CCS%'
   OR ACRONYM LIKE '%C2S%';
