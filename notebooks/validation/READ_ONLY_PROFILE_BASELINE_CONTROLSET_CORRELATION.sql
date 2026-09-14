-- Profile discovery only: correlate baseline recommendation with observed control-set/version selections.
-- Reads stored RAW versions; counts are not the mapper's deduplicated current snapshot.
-- No record IDs and no target writes. Keep source-value results private.
WITH source AS (
    SELECT TRY_PARSE_JSON(TO_VARCHAR(CURATED_JSON)) AS payload
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
)
SELECT
    payload:BASELINE_RECOMMENDATION AS BASELINE_RECOMMENDATION,
    payload:CONTROL_SET_VERSION_NUMBER AS CONTROL_SET_VERSION_NUMBER,
    payload:CONTROL_SET_VERSION_NUMBER_HRC AS CONTROL_SET_VERSION_NUMBER_HRC,
    COUNT(*) AS STORED_VERSION_COUNT
FROM source
GROUP BY ALL
ORDER BY STORED_VERSION_COUNT DESC
LIMIT 50;
