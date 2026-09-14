-- Read-only discovery: follow the ALLOCATED_CONTROLS relationship shape.
-- Prior read-back showed ALLOCATED_CONTROLS contains arrays of objects such as
-- {"ContentId": 573480, "LevelId": 355}, while the other inspected candidate fields were null in those rows.
-- This query extracts the referenced ContentId/LevelId pairs without target writes.

SELECT DISTINCT
    r.CONTENT_ID AS AUTHORIZATION_PACKAGE_CONTENT_ID,
    f.value:ContentId::STRING AS REFERENCED_CONTENT_ID,
    f.value:LevelId::STRING AS REFERENCED_LEVEL_ID
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r,
LATERAL FLATTEN(INPUT => r.CURATED_JSON:ALLOCATED_CONTROLS) f
WHERE f.value:ContentId IS NOT NULL
ORDER BY REFERENCED_LEVEL_ID, REFERENCED_CONTENT_ID
LIMIT 100;
