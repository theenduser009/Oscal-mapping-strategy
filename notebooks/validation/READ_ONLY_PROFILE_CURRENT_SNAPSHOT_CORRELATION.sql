-- Profile discovery only: correlation on the mapper-style latest source snapshot.
-- This reduces historical stored-version noise before deciding Profile semantics.
-- Read-only. No target writes. Keep source-value results private.
WITH raw AS (
    SELECT
        CONTENT_ID::STRING AS SOURCE_RECORD_ID,
        TRY_PARSE_JSON(TO_VARCHAR(CURATED_JSON)) AS payload,
        DW_LOAD_TIMESTAMP_TZ,
        DW_LOAD_TIMESTAMP,
        UPDATED_DATE,
        LAST_UPDATED_DATE,
        MODIFIED_DATE,
        CREATE_DATE
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
), ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY SOURCE_RECORD_ID
            ORDER BY
                DW_LOAD_TIMESTAMP_TZ DESC NULLS LAST,
                DW_LOAD_TIMESTAMP DESC NULLS LAST,
                UPDATED_DATE DESC NULLS LAST,
                LAST_UPDATED_DATE DESC NULLS LAST,
                MODIFIED_DATE DESC NULLS LAST,
                CREATE_DATE DESC NULLS LAST
        ) AS rn
    FROM raw
)
SELECT
    payload:BASELINE_RECOMMENDATION AS BASELINE_RECOMMENDATION,
    payload:CONTROL_SET_VERSION_NUMBER AS CONTROL_SET_VERSION_NUMBER,
    payload:CONTROL_SET_VERSION_NUMBER_HRC AS CONTROL_SET_VERSION_NUMBER_HRC,
    COUNT(*) AS CURRENT_RECORD_COUNT
FROM ranked
WHERE rn = 1
GROUP BY ALL
ORDER BY CURRENT_RECORD_COUNT DESC;
