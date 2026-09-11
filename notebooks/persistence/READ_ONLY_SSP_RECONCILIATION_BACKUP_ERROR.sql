-- Copy this whole file into ONE Snowflake SQL cell. No replacements.
-- Read-only: retrieve the real error hidden by the Python reconciliation wrapper.
-- Do NOT rerun the replacement, old pilot, or Cells 1-7 for this check.
-- Current user's latest 10,000 queries within four hours; client SQL included.
-- Empty results mean no matching visible history in that window, NOT success.
-- Inspect QUERY_TEXT in Snowflake. Share ERROR_MESSAGE, ROLE_NAME and QUERY_ID;
-- do not publish unrelated query text, source data or credentials.
-- Documentation: https://docs.snowflake.com/en/sql-reference/functions/query_history

SELECT
    QUERY_ID,
    START_TIME,
    QUERY_TYPE,
    ROLE_NAME,
    DATABASE_NAME,
    SCHEMA_NAME,
    ERROR_CODE,
    ERROR_MESSAGE,
    QUERY_TEXT
FROM TABLE(
    RTX_ENTERPRISESERVICES_DEV.INFORMATION_SCHEMA.QUERY_HISTORY_BY_USER(
        END_TIME_RANGE_START => DATEADD('hour', -4, CURRENT_TIMESTAMP()),
        RESULT_LIMIT => 10000,
        INCLUDE_CLIENT_GENERATED_STATEMENT => TRUE
    )
)
WHERE ERROR_CODE = 3001
  AND CONTAINS(UPPER(QUERY_TEXT), 'BACKUP_SSP_RECONCILE_')
  AND NOT CONTAINS(UPPER(QUERY_TEXT), 'QUERY_HISTORY_BY_')
ORDER BY START_TIME DESC
LIMIT 5;
