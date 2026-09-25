-- C2S LEGACY VIEW REQUIREMENT GAP PROFILE
-- Date: 2026-09-25
-- READ ONLY.
--
-- Purpose:
-- Identify whether legacy C2S view requirements that are not currently
-- reproduced by the OSCAL-backed view are:
--   A) present in Authorization Package RAW but unmapped,
--   B) absent from Authorization Package RAW and require another source/lookup,
--   C) derived display fields requiring lookup hydration.
--
-- No values are returned; only counts/shapes and candidate object names.


-- 01. Profile source-like legacy requirements inside current Authorization Package RAW.
WITH fields(FIELD_NAME) AS (
  SELECT COLUMN1 FROM VALUES
    ('LEGACY_SAP_ID'),
    ('BUSINESS'),
    ('AUTHORIZATION_PACKAGE_SUBMIT_DATE'),
    ('ATOIATO_EXPIRATION_DATE'),
    ('SYSTEM_ADMINISTRATOR_SA'),
    ('ALTERNATE_SYSTEM_ADMINISTRATOR_SA'),
    ('ENTITY'),
    ('CONFIRMEDINARCHER'),
    ('ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER')
),
src AS (
  SELECT CURATED_JSON
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
),
p AS (
  SELECT
    f.FIELD_NAME,
    GET(s.CURATED_JSON,f.FIELD_NAME) V
  FROM src s CROSS JOIN fields f
)
SELECT
  FIELD_NAME,
  COUNT(*) SOURCE_ROWS,
  COUNT_IF(V IS NULL) SQL_NULL_OR_MISSING,
  COUNT_IF(IS_NULL_VALUE(V)) JSON_NULL_ROWS,
  COUNT_IF(V IS NOT NULL AND NOT IS_NULL_VALUE(V)) POPULATED_ROWS,
  COUNT_IF(TYPEOF(V)='ARRAY') ARRAY_ROWS,
  COUNT_IF(TYPEOF(V)='OBJECT') OBJECT_ROWS,
  COUNT_IF(TYPEOF(V)='VARCHAR') TEXT_ROWS,
  COUNT_IF(TYPEOF(V) IN ('INTEGER','DECIMAL','DOUBLE','NUMBER')) NUMBER_ROWS
FROM p
GROUP BY FIELD_NAME
ORDER BY FIELD_NAME;


-- 02. Discover candidate RAW/structured lookup objects for legacy enrichments.
-- Do not infer ownership from names alone; this only tells us what exists.
WITH objects AS (
  SELECT TABLE_NAME OBJECT_NAME,'TABLE' OBJECT_TYPE
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
  WHERE TABLE_SCHEMA='ES_ESC_GRC'
  UNION ALL
  SELECT TABLE_NAME,'VIEW'
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.VIEWS
  WHERE TABLE_SCHEMA='ES_ESC_GRC'
)
SELECT OBJECT_NAME,OBJECT_TYPE
FROM objects
WHERE OBJECT_NAME ILIKE '%BUSINESS%'
   OR OBJECT_NAME ILIKE '%POAM%'
   OR OBJECT_NAME ILIKE '%ENTITY%'
   OR OBJECT_NAME ILIKE '%WORKDAY%'
   OR OBJECT_NAME ILIKE '%LDAP%'
   OR OBJECT_NAME ILIKE '%USER%'
ORDER BY OBJECT_NAME;


-- 03. Current legacy-view requirement classification.
-- This is documentation-as-data for team review.
SELECT COLUMN1 LEGACY_COLUMN,COLUMN2 CURRENT_STATUS,COLUMN3 NEXT_ACTION
FROM VALUES
  ('ARCHER_AUTHORIZATION_PACKAGE_DATA_CONTENT_ID','SUPPORTED','SOURCE_RECORD_ID'),
  ('AUTHORIZATION_PACKAGE_NAME','SUPPORTED','Use SSP system-name'),
  ('LEGACY_SAP_ID','NEEDS_PROOF','Compare to SAP_ID; preserve separately if distinct'),
  ('BUSINESS','MISSING_SOURCE/LOOKUP','Ingest/hydrate Business relationship'),
  ('BUSINESS_NAME','MISSING_LOOKUP','Hydrate Business display name'),
  ('OPERATIONAL_STATUS','SUPPORTED','Use SSP status.state'),
  ('POAMS','PARTIAL','POAM relationship exists; preserve/expose original reference IDs if consumer requires old format'),
  ('POAM_ID','PARTIAL/MISSING_DETAIL','Hydrate POAM item source ID'),
  ('POAM_NAME','MISSING_DETAIL','Hydrate POAM item name/title'),
  ('POAM_ID_NAME','MISSING_DETAIL','Derived from POAM ID + name after hydration'),
  ('WORKFLOW_STATUS','SUPPORTED','Use Assessment Results result property'),
  ('AUTHORIZATION_PACKAGE_SUBMIT_DATE','UNMAPPED','Profile and map/preserve if present'),
  ('ATOIATO_EXPIRATION_DATE','UNMAPPED','Profile and map/preserve if present'),
  ('SYSTEM_ADMINISTRATOR_SA','UNMAPPED_ROLE','Profile; map to responsible-party only if semantics prove role'),
  ('SYSTEM_ADMINISTRATOR_SA_ID_ONLY','MISSING_PARTY_EXTERNAL_ID','Preserve source external ID in party payload'),
  ('SYSTEM_ADMINISTRATOR_SA_NAME_ONLY','MISSING_LDAP_HYDRATION','Hydrate party name from approved user lookup'),
  ('SYSTEM_ADMINISTRATOR_SA_ID_NAME','MISSING_LDAP_HYDRATION','Derived after ID/name hydration'),
  ('ALTERNATE_SYSTEM_ADMINISTRATOR_SA','UNMAPPED_ROLE','Profile; map only after role semantics are proved'),
  ('ALTERNATE_SYSTEM_ADMINISTRATOR_SA_ID_ONLY','MISSING_PARTY_EXTERNAL_ID','Preserve source external ID'),
  ('ALTERNATE_SYSTEM_ADMINISTRATOR_SA_NAME_ONLY','MISSING_LDAP_HYDRATION','Hydrate party name'),
  ('ALTERNATE_SYSTEM_ADMINISTRATOR_SA_ID_NAME','MISSING_LDAP_HYDRATION','Derived after ID/name hydration'),
  ('INFORMATION_OWNER_IO','PARTIAL','Responsible-party relationship exists but old raw IDs are not exposed'),
  ('INFORMATION_OWNER_IO_ID_ONLY','MISSING_PARTY_EXTERNAL_ID','Preserve party external ID'),
  ('INFORMATION_OWNER_IO_NAME_ONLY','MISSING_LDAP_HYDRATION','Hydrate party name'),
  ('INFORMATION_OWNER_IO_ID_NAME','MISSING_LDAP_HYDRATION','Derived after ID/name hydration'),
  ('AUTHORIZING_OFFICIAL_AO','PARTIAL','Responsible-party relationship exists but old raw IDs are not exposed'),
  ('AUTHORIZING_OFFICIAL_AO_ID_ONLY','MISSING_PARTY_EXTERNAL_ID','Preserve party external ID'),
  ('AUTHORIZING_OFFICIAL_AO_NAME_ONLY','MISSING_LDAP_HYDRATION','Hydrate party name'),
  ('AUTHORIZING_OFFICIAL_AO_ID_NAME','MISSING_LDAP_HYDRATION','Derived after ID/name hydration'),
  ('ENTITY','MISSING_SOURCE/LOOKUP','Ingest/hydrate Entity relationship'),
  ('ENTITY_NAME','MISSING_LOOKUP','Hydrate Entity display name'),
  ('ATOIATO_DATE','SUPPORTED','Use SSP date-authorized'),
  ('AUTHORIZATION_DECISION','SUPPORTED','Use SSP authorization-decision property'),
  ('ACRONYM','SUPPORTED','Use SSP system-name-short'),
  ('CONFIRMEDINARCHER','PARTIAL/NO_CURRENT_VALUE','Current confirmation mapping exists but current RAW field is missing/unpopulated')
ORDER BY LEGACY_COLUMN;
