-- Profile discovery only: establish RAW table cardinality before attempting a current-snapshot correlation.
-- The RAW table was read back as containing only CURATED_JSON and CONTENT_ID; there is no load timestamp to rank versions.
-- Read-only. No target writes and no record IDs returned.
SELECT
    COUNT(*) AS RAW_ROW_COUNT,
    COUNT(DISTINCT CONTENT_ID) AS DISTINCT_CONTENT_ID_COUNT,
    COUNT(*) - COUNT(DISTINCT CONTENT_ID) AS EXTRA_ROWS_BEYOND_ONE_PER_CONTENT_ID,
    COUNT_IF(CONTENT_ID IS NULL) AS NULL_CONTENT_ID_COUNT
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW;
