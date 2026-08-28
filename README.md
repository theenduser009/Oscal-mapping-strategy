Aha — this gives us the answer. Do not change the mapper.

For these 20 records:

AUTHORIZATION_BOUNDARY_DESCRIPTION → NULL

CNSS_CONFIDENTIALITY_RATING → NULL

CNSS_INTEGRITY_RATING → NULL

CNSS_AVAILABILITY_RATING → NULL

SECURITY_CATEGORY → populated ("DFARS")


That explains why security-impact-level showed {} even though it owns 12 mappings: the particular mapped fields that belong inside its child structure are null. Meanwhile SECURITY_CATEGORY is mapped at the system-characteristics level as security-sensitivity-level, which is why you already saw:

"security-sensitivity-level": "DFARS"

So that part is behaving correctly.

Next: let's test authorization-boundary properly

Your earlier field-count list says AUTHORIZATION_BOUNDARY_DESCRIPTION has 2,522 populated records, so they definitely exist. Our OR query was just being satisfied first by SECURITY_CATEGORY.

Run only this:

SELECT
    CONTENT_ID,
    CURATED_JSON:AUTHORIZATION_BOUNDARY_DESCRIPTION AS AUTH_BOUNDARY
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
WHERE CURATED_JSON:AUTHORIZATION_BOUNDARY_DESCRIPTION IS NOT NULL
LIMIT 10;

Don't modify anything else yet. Show me that result, and we'll validate authorization-boundary against one of those records.