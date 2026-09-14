-- Profile discovery only: summarize the two reviewed Profile inputs against the now-verified one-row-per-CONTENT_ID RAW snapshot.
-- Purpose: determine whether BASELINE_RECOMMENDATION can identify an OSCAL import resource and whether ADD_OVERLAY contributes any current operation.
-- Read-only. No record IDs and no target writes. Keep source-value results private.
WITH source AS (
    SELECT TRY_PARSE_JSON(TO_VARCHAR(CURATED_JSON)) AS payload
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
), ids AS (
    SELECT
        TRY_TO_NUMBER(payload:BASELINE_RECOMMENDATION:ValuesListIds[0]::STRING) AS BASELINE_ID,
        TYPEOF(payload:ADD_OVERLAY) AS ADD_OVERLAY_TYPE,
        payload:ADD_OVERLAY AS ADD_OVERLAY
    FROM source
)
SELECT
    i.BASELINE_ID,
    b.SELECT_VALUE_NAME AS BASELINE_RECOMMENDATION,
    i.ADD_OVERLAY_TYPE,
    i.ADD_OVERLAY,
    COUNT(*) AS CURRENT_RECORD_COUNT
FROM ids i
LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE b
    ON b.SELECT_VALUE_ID = i.BASELINE_ID
GROUP BY ALL
ORDER BY CURRENT_RECORD_COUNT DESC;
