Yes — you’re right. We already loaded those raw Archer IDs into the OSCAL SSP DIM payload, so first we should use the DIM to show exactly what values are present. Then you can ask the Archer expert, “Where do I resolve these IDs to Low/Moderate/High?”

Run this against the SSP DIM:

SELECT
    ELEMENT_TYPE,
    SOURCE_RECORD_ID,
    METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE METADATA_JSON::STRING ILIKE ANY (
    '%162405%',
    '%162406%',
    '%162407%',
    '%162409%',
    '%162410%',
    '%162411%',
    '%80654%'
)
ORDER BY SOURCE_RECORD_ID;

If you want to focus specifically on the security-impact branch:

SELECT
    SOURCE_RECORD_ID,
    METADATA_JSON
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE ELEMENT_TYPE = 'security-impact-level'
  AND METADATA_JSON IS NOT NULL
ORDER BY SOURCE_RECORD_ID
LIMIT 50;

You should see payloads roughly like:

{
  "security-objective-confidentiality": [162409],
  "security-objective-integrity": [162407],
  "security-objective-availability": [80654]
}

Then the question to your Archer expert is simply:

> “These IDs are coming from Archer into our OSCAL security-impact-level DIM payload — for example 162405, 162406, 162407, 162409, 162410, 162411, and 80654. Where can I look up the corresponding Archer display values so I can normalize them to FIPS-199 low, moderate, or high?”



That is exactly the missing piece for our Direct/Transform mapping.