Next, no more code changes yet. We should verify the other two approved Transform mappings that weren’t populated in record 565189:

INFORMATION_OWNER_IO → information-owner

PRIVACY_OFFICER_PO → privacy-officer


Run this against the DIM:

SELECT
    METADATA_JSON:"role-id"::STRING AS ROLE_ID,
    COUNT(*) AS CNT
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
WHERE ELEMENT_TYPE = 'responsible-parties'
  AND METADATA_JSON:"role-id" IS NOT NULL
GROUP BY 1
ORDER BY 1;

Ideally we should see all five implemented roles:

information-owner
system-owner
authorizing-official
system-security-officer
privacy-officer

Run that and show me the result. That tells us immediately whether all 5 architect-approved Transform rows are actually working across the full dataset.