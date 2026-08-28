Yes — now we have a concrete target: Hardware CONTENT_ID = 8243332. Before changing the mapper, I’d validate the entire reference chain in Snowflake.

Run these SQL blocks in order. Do not change any notebook code yet.

-- ================================================================
-- 1. PROVE THE HARDWARE RECORD EXISTS
-- ================================================================

SELECT
    CONTENT_ID,
    CURATED_JSON
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_HARDWARE_RAW
WHERE CONTENT_ID = 8243332;

Expected: 1 row.

Then validate uniqueness and payload:

-- ================================================================
-- 2. HARDWARE RECORD QUALITY CHECK
-- ================================================================

SELECT
    CONTENT_ID,
    COUNT(*) AS ROW_COUNT,
    COUNT_IF(CURATED_JSON IS NULL) AS NULL_JSON_COUNT
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_HARDWARE_RAW
WHERE CONTENT_ID = 8243332
GROUP BY CONTENT_ID;

Expected:

CONTENT_ID   ROW_COUNT   NULL_JSON_COUNT
8243332      1           0

Now inspect the structure of the Hardware JSON:

-- ================================================================
-- 3. INSPECT HARDWARE JSON KEYS
-- ================================================================

SELECT
    CONTENT_ID,
    OBJECT_KEYS(CURATED_JSON) AS JSON_KEYS
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_HARDWARE_RAW
WHERE CONTENT_ID = 8243332;

Next, prove that an Authorization Package actually references 8243332 through INTERCONNECTIONS.

-- ================================================================
-- 4. FIND AUTHORIZATION PACKAGE -> HARDWARE REFERENCE
-- ================================================================

SELECT
    ap.CONTENT_ID AS AUTH_PACKAGE_CONTENT_ID,
    f.value:"ContentId"::STRING AS REFERENCED_CONTENT_ID,
    f.value:"LevelId"::STRING   AS REFERENCED_LEVEL_ID,
    f.value                     AS REFERENCE_JSON
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW ap,
LATERAL FLATTEN(
    INPUT => ap.CURATED_JSON:"INTERCONNECTIONS"
) f
WHERE f.value:"ContentId"::STRING = '8243332';

This is the most important validation.

If it returns a row, we have proven:

Authorization Package
        ↓
INTERCONNECTIONS
        ↓
ContentId = 8243332
        ↓
Hardware RAW

Now validate the actual join:

-- ================================================================
-- 5. PROVE CROSS-TABLE JOIN
-- Authorization Package reference -> Hardware RAW
-- ================================================================

SELECT
    ap.CONTENT_ID AS AUTH_PACKAGE_CONTENT_ID,

    f.value:"ContentId"::STRING AS REFERENCED_CONTENT_ID,
    f.value:"LevelId"::STRING   AS REFERENCED_LEVEL_ID,

    hw.CONTENT_ID AS HARDWARE_CONTENT_ID,
    hw.CURATED_JSON AS HARDWARE_JSON

FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW ap,

LATERAL FLATTEN(
    INPUT => ap.CURATED_JSON:"INTERCONNECTIONS"
) f

LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_HARDWARE_RAW hw
    ON hw.CONTENT_ID::STRING = f.value:"ContentId"::STRING

WHERE f.value:"ContentId"::STRING = '8243332';

Here we want:

REFERENCED_CONTENT_ID = 8243332
HARDWARE_CONTENT_ID   = 8243332
HARDWARE_JSON         = populated

Then run a reference-integrity check for all currently available Hardware records, not just 8243332:

-- ================================================================
-- 6. ALL AUTH PACKAGE -> HARDWARE MATCHES
-- ================================================================

SELECT
    ap.CONTENT_ID AS AUTH_PACKAGE_CONTENT_ID,
    f.value:"ContentId"::STRING AS REFERENCED_CONTENT_ID,
    f.value:"LevelId"::STRING AS REFERENCED_LEVEL_ID,
    hw.CONTENT_ID AS HARDWARE_CONTENT_ID,

    CASE
        WHEN hw.CONTENT_ID IS NOT NULL THEN 'MATCHED'
        ELSE 'NOT_IN_HARDWARE_RAW'
    END AS MATCH_STATUS

FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW ap,

LATERAL FLATTEN(
    INPUT => ap.CURATED_JSON:"INTERCONNECTIONS"
) f

LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_HARDWARE_RAW hw
    ON hw.CONTENT_ID::STRING = f.value:"ContentId"::STRING

ORDER BY
    ap.CONTENT_ID,
    REFERENCED_CONTENT_ID;

Because your raw Hardware table currently contains only limited records, many references may legitimately show:

NOT_IN_HARDWARE_RAW

That is not a mapper failure. It simply means the referenced Archer records haven't arrived in that raw table yet.

Now get a clean summary:

-- ================================================================
-- 7. REFERENCE COVERAGE SUMMARY
-- ================================================================

WITH REFERENCES AS
(
    SELECT
        ap.CONTENT_ID AS AUTH_PACKAGE_CONTENT_ID,
        f.value:"ContentId"::STRING AS REFERENCED_CONTENT_ID,
        f.value:"LevelId"::STRING AS REFERENCED_LEVEL_ID

    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW ap,

    LATERAL FLATTEN(
        INPUT => ap.CURATED_JSON:"INTERCONNECTIONS"
    ) f
)

SELECT
    COUNT(*) AS TOTAL_REFERENCES,

    COUNT_IF(
        hw.CONTENT_ID IS NOT NULL
    ) AS MATCHED_HARDWARE_RECORDS,

    COUNT_IF(
        hw.CONTENT_ID IS NULL
    ) AS MISSING_FROM_HARDWARE_RAW

FROM REFERENCES r

LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_HARDWARE_RAW hw
    ON hw.CONTENT_ID::STRING = r.REFERENCED_CONTENT_ID;

And because LevelId identifies the Archer level/table, let's see exactly which LevelId accompanies 8243332:

-- ================================================================
-- 8. IDENTIFY LEVEL ID FOR 8243332
-- ================================================================

SELECT DISTINCT
    f.value:"ContentId"::STRING AS CONTENT_ID,
    f.value:"LevelId"::STRING AS LEVEL_ID

FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW ap,

LATERAL FLATTEN(
    INPUT => ap.CURATED_JSON:"INTERCONNECTIONS"
) f

WHERE f.value:"ContentId"::STRING = '8243332';

One fallback check

If SQL #4 returns zero rows, don't conclude anything yet. Search the complete Authorization Package JSON to see whether 8243332 appears under another Archer field:

-- ================================================================
-- 9. FALLBACK - SEARCH FULL AUTH PACKAGE JSON
-- ================================================================

SELECT
    CONTENT_ID AS AUTH_PACKAGE_CONTENT_ID,
    CURATED_JSON
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
WHERE CURATED_JSON::STRING ILIKE '%8243332%';

That tells us whether 8243332 is referenced somewhere other than INTERCONNECTIONS.

The result I care about first is SQL #4/#5. If 8243332 joins successfully from the Authorization Package reference into ARCHER_CONTENT_HARDWARE_RAW, then we have finally proven the architecture the mapper needs:

same-record mapping for ordinary fields + cross-table traversal for Archer references.

Send me the output of #4, #5, and #8. Then we can design the mapper change around the proven ContentId + LevelId → target RAW table relationship rather than continuing to fight components[].component as if it were nested JSON.