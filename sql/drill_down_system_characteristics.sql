-- Run this in the next SQL cell immediately after
-- show_oscal_path_and_payload.sql.
-- It reuses the prior query result and returns the system-characteristics
-- node plus every child and deeper descendant.

SELECT
    SOURCE_RECORD_ID,
    OSCAL_PATH,
    ELEMENT_TYPE,
    OSCAL_UUID,
    WRITTEN_PAYLOAD,
    PARENT_OSCAL_UUID,
    DEPENDENCY_TYPE
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE
    OSCAL_PATH = 'system-security-plan.system-characteristics'
    OR OSCAL_PATH LIKE 'system-security-plan.system-characteristics.%'
ORDER BY
    REGEXP_COUNT(OSCAL_PATH, '\\.'),
    OSCAL_PATH,
    OSCAL_UUID;

