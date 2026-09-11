-- Copy this entire file into one Snowflake SQL cell. No replacements needed.
-- Read-only: retrieves existing failures; does not rerun the Python write pilot.
-- Uses the current user's most recent 1,000 queries within the last two hours.
-- Client-generated statements are included to expose Snowpark failures.
-- Share ERROR_MESSAGE for the row matching the pilot attempt, not raw query text.
-- Keep the pilot paused. This SQL has not been executed against your Snowflake account.

SELECT
    START_TIME,
    QUERY_TYPE,
    ROLE_NAME,
    DATABASE_NAME,
    SCHEMA_NAME,
    ERROR_CODE,
    ERROR_MESSAGE
FROM TABLE(
    RTX_ENTERPRISESERVICES_DEV.INFORMATION_SCHEMA.QUERY_HISTORY_BY_USER(
        END_TIME_RANGE_START => DATEADD('hour', -2, CURRENT_TIMESTAMP()),
        RESULT_LIMIT => 1000,
        INCLUDE_CLIENT_GENERATED_STATEMENT => TRUE
    )
)
WHERE ERROR_CODE = 2003
ORDER BY START_TIME DESC
LIMIT 5;
