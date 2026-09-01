SELECT
    SOURCE_RECORD_ID,
    METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE SOURCE_RECORD_ID = '565189'
  AND ELEMENT_TYPE IN (
      'system-characteristics',
      'authorization-boundary',
      'status',
      'system-ids',
      'security-impact-level',
      'props'
  )
ORDER BY ELEMENT_TYPE;