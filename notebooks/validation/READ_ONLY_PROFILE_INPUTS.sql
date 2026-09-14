-- Profile discovery only: distinct values across the RAW table's stored versions.
-- These counts are NOT the mapper's deduplicated current source snapshot.
-- No record IDs or target writes. Keep source-value results private.
WITH source AS (
    SELECT TRY_PARSE_JSON(TO_VARCHAR(CURATED_JSON)) AS payload
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
)
SELECT
    IS_OBJECT(payload) AS IS_OBJECT_DOCUMENT,
    TYPEOF(payload:ADD_OVERLAY) AS ADD_OVERLAY_TYPE,
    payload:ADD_OVERLAY AS ADD_OVERLAY,
    TYPEOF(payload:BASELINE_RECOMMENDATION) AS BASELINE_RECOMMENDATION_TYPE,
    payload:BASELINE_RECOMMENDATION AS BASELINE_RECOMMENDATION,
    COUNT(*) AS STORED_VERSION_COUNT
FROM source
GROUP BY ALL
ORDER BY STORED_VERSION_COUNT DESC
LIMIT 30;
