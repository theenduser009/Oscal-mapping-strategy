-- READ ONLY: see how SSP security-impact-level appears in the DIM table.
SELECT SOURCE_RECORD_ID,
       OSCAL_UUID,
       METADATA_JSON:"security-objective-confidentiality"::STRING AS CONFIDENTIALITY,
       METADATA_JSON:"security-objective-integrity"::STRING AS INTEGRITY,
       METADATA_JSON:"security-objective-availability"::STRING AS AVAILABILITY,
       METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE ELEMENT_TYPE = 'security-impact-level'
ORDER BY SOURCE_RECORD_ID
LIMIT 50;
