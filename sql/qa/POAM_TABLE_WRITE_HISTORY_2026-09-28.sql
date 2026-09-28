-- POAM TABLE WRITE-HISTORY CANDIDATES - 2026-09-28
-- SELECT ONLY. Run the entire file as-is. At most 21 rows: summary + 20 events.
-- Reviewed branch: simplify-metadata-boundary
-- Reviewed head: 946411bc44ee89620a16d83134dd0718900db973
-- Purpose: inspect retained history, not repeat current-DIM matching tests.
--
-- Requires existing access to SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY.
-- On an authorization error, stop and report the error; do not grant privileges.
-- Searches the preceding 90 days; history can lag by up to 45 minutes.
-- This is a query-text candidate search, NOT authoritative object lineage.
-- It recognizes common table-target syntax, including quoted/qualified names.
-- Other schemas with the same table names can match. Comments, strings, dynamic
-- identifiers, renames, truncated query text, and indirect operations limit it.
-- DATABASE_NAME/SCHEMA_NAME are compilation context, NOT proven target identity.
-- A successful statement / affected-row count does NOT prove a later COMMIT.
-- Transaction IDs are retained for follow-up; transaction outcomes are not inferred.
-- Successful zero-row INSERT/UPDATE/DELETE/MERGE statements are counted in the
-- summary but omitted from the event display so no-op loads do not hide changes.
-- More than 20 candidates: OLDER_EVENTS_NOT_SHOWN reports the display truncation.
-- No query text, payloads, user names or private record IDs are returned.
-- No source tables, target tables, registry or mapping rules are changed.
-- Documentation reviewed 2026-09-28:
-- https://docs.snowflake.com/en/sql-reference/account-usage/query_history

WITH
params AS (
    SELECT CURRENT_TIMESTAMP() AS QA_EXECUTED_AT,
           DATEADD(day, -90, CURRENT_TIMESTAMP()) AS SEARCH_START,
           CURRENT_TIMESTAMP() AS SEARCH_END,
           '(INSERT[[:space:]]+INTO|MERGE[[:space:]]+INTO|UPDATE|DELETE[[:space:]]+FROM|COPY[[:space:]]+INTO|TRUNCATE[[:space:]]+(TABLE[[:space:]]+)?|DROP[[:space:]]+TABLE[[:space:]]+(IF[[:space:]]+EXISTS[[:space:]]+)?|UNDROP[[:space:]]+TABLE|ALTER[[:space:]]+TABLE|CREATE[[:space:]]+(OR[[:space:]]+REPLACE[[:space:]]+)?((TEMPORARY|TEMP|TRANSIENT)[[:space:]]+)?TABLE[[:space:]]+(IF[[:space:]]+NOT[[:space:]]+EXISTS[[:space:]]+)?)' AS OP_PATTERN
),
history_mentions AS (
    SELECT q.QUERY_ID, q.START_TIME, q.QUERY_TYPE, q.EXECUTION_STATUS,
           q.ROWS_INSERTED, q.ROWS_UPDATED, q.ROWS_DELETED,
           q.TRANSACTION_ID, q.SESSION_ID, q.DATABASE_NAME, q.SCHEMA_NAME,
           UPPER(REPLACE(q.QUERY_TEXT, '"', '')) AS SQL_TEXT
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q CROSS JOIN params p
    WHERE q.START_TIME >= p.SEARCH_START AND q.START_TIME < p.SEARCH_END
      AND (CONTAINS(UPPER(q.QUERY_TEXT), 'DIM_OSCAL_POAM_ELEMENT')
        OR CONTAINS(UPPER(q.QUERY_TEXT), 'FACT_OSCAL_POAM_DEPENDENCY'))
      AND COALESCE(UPPER(q.QUERY_TYPE), 'UNKNOWN') NOT IN ('SELECT','SHOW','DESCRIBE','EXPLAIN')
),
flags AS (
    SELECT h.*,
           REGEXP_LIKE(h.SQL_TEXT,
               '.*(^|[[:space:];])' || p.OP_PATTERN || '[[:space:]]*([A-Z0-9_$]+[[:space:]]*[.][[:space:]]*){0,2}DIM_OSCAL_POAM_ELEMENT([[:space:];(]|$).*', 's') AS DIM_HIT,
           REGEXP_LIKE(h.SQL_TEXT,
               '.*(^|[[:space:];])' || p.OP_PATTERN || '[[:space:]]*([A-Z0-9_$]+[[:space:]]*[.][[:space:]]*){0,2}FACT_OSCAL_POAM_DEPENDENCY([[:space:];(]|$).*', 's') AS FACT_HIT
    FROM history_mentions h CROSS JOIN params p
),
target_candidates AS (
    SELECT *,
           CASE WHEN UPPER(QUERY_TYPE) IN ('INSERT','UPDATE','DELETE','MERGE')
                  AND LOWER(EXECUTION_STATUS)='success'
                  AND ROWS_INSERTED=0 AND ROWS_UPDATED=0 AND ROWS_DELETED=0
                THEN 1 ELSE 0 END AS SUCCESSFUL_ZERO_ROW_DML
    FROM flags WHERE DIM_HIT OR FACT_HIT
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY START_TIME DESC, QUERY_ID) AS EVENT_ORDER
    FROM target_candidates WHERE SUCCESSFUL_ZERO_ROW_DML=0
),
summary AS (
    SELECT COUNT(*) AS TARGET_SYNTAX_CANDIDATES,
           COALESCE(SUM(SUCCESSFUL_ZERO_ROW_DML),0) AS ZERO_ROW_DML_NOT_SHOWN,
           COUNT(*)-COALESCE(SUM(SUCCESSFUL_ZERO_ROW_DML),0) AS CHANGE_OR_OTHER_CANDIDATES
    FROM target_candidates
),
report AS (
    SELECT 0 AS DISPLAY_ORDER, 'SEARCH_SUMMARY' AS ROW_KIND,
           CAST(NULL AS VARCHAR) AS TABLE_NAME_CANDIDATE,
           CAST(NULL AS TIMESTAMP_LTZ) AS EVENT_TIME,
           CAST(NULL AS VARCHAR) AS QUERY_TYPE,
           CAST(NULL AS NUMBER) AS ROWS_INSERTED,
           CAST(NULL AS NUMBER) AS ROWS_UPDATED,
           CAST(NULL AS NUMBER) AS ROWS_DELETED,
           'HISTORY_SEARCH_NOT_QA_SIGNOFF' AS EXECUTION_STATUS,
           CAST(NULL AS VARCHAR) AS QUERY_ID,
           CAST(NULL AS NUMBER) AS TRANSACTION_ID,
           CAST(NULL AS NUMBER) AS SESSION_ID,
           CAST(NULL AS VARCHAR) AS CONTEXT_DATABASE,
           CAST(NULL AS VARCHAR) AS CONTEXT_SCHEMA
    UNION ALL
    SELECT EVENT_ORDER, 'HISTORY_CANDIDATE',
           CASE WHEN DIM_HIT AND FACT_HIT THEN 'DIM_AND_FACT'
                WHEN DIM_HIT THEN 'DIM_OSCAL_POAM_ELEMENT'
                ELSE 'FACT_OSCAL_POAM_DEPENDENCY' END,
           START_TIME, QUERY_TYPE, ROWS_INSERTED, ROWS_UPDATED, ROWS_DELETED,
           EXECUTION_STATUS, QUERY_ID, TRANSACTION_ID, SESSION_ID, DATABASE_NAME, SCHEMA_NAME
    FROM ranked WHERE EVENT_ORDER<=20
)
SELECT p.QA_EXECUTED_AT, r.ROW_KIND, r.TABLE_NAME_CANDIDATE, r.EVENT_TIME,
       r.QUERY_TYPE, r.ROWS_INSERTED, r.ROWS_UPDATED, r.ROWS_DELETED,
       r.EXECUTION_STATUS, r.QUERY_ID, r.TRANSACTION_ID, r.SESSION_ID,
       r.CONTEXT_DATABASE, r.CONTEXT_SCHEMA,
       s.TARGET_SYNTAX_CANDIDATES, s.ZERO_ROW_DML_NOT_SHOWN,
       s.CHANGE_OR_OTHER_CANDIDATES,
       GREATEST(s.CHANGE_OR_OTHER_CANDIDATES-20,0) AS OLDER_EVENTS_NOT_SHOWN,
       p.SEARCH_START, p.SEARCH_END
FROM report r CROSS JOIN params p CROSS JOIN summary s
ORDER BY r.DISPLAY_ORDER;
