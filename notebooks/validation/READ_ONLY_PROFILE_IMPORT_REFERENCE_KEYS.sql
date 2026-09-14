-- Profile discovery only: identify RAW JSON fields that may carry Profile / Import Profile references.
-- Motivated by Archer relationship diagrams showing Profile and Import Profile nodes.
-- Read-only. Returns field names only; no source values, record IDs, or target writes.
WITH source AS (
    SELECT TRY_PARSE_JSON(TO_VARCHAR(CURATED_JSON)) AS payload
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
)
SELECT DISTINCT
    f.key::STRING AS FIELD_NAME
FROM source,
LATERAL FLATTEN(INPUT => payload) f
WHERE UPPER(f.key::STRING) LIKE '%PROFILE%'
   OR UPPER(f.key::STRING) LIKE '%IMPORT%'
ORDER BY FIELD_NAME;
