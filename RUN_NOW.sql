-- RUN NOW — Source One Assessment Results attachment-ID resolution
-- Date: 2026-09-21
-- READ ONLY. No target DML.
--
-- Why this query:
-- RISK_ASSESSMENT_REPORT is Archer FIELD_TYPE_ID = 11 (Attachment).
-- The Source One payload contains arrays of numeric attachment IDs.
-- ARCHER_CONTENT_DOCUMENT_REPOSITORY is a structured table that exposes
-- DOCUMENT_ID plus document link/URL/name/title columns.
--
-- We are NOT changing the mapping yet.
-- First prove which repository key the attachment IDs actually match.
--
-- Expected source table:
--   RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
-- Expected structured repository table:
--   RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_DOCUMENT_REPOSITORY

WITH attachment_ids AS (
    SELECT
        f.value::NUMBER AS ATTACHMENT_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW s,
         LATERAL FLATTEN(INPUT => s.CURATED_JSON:RISK_ASSESSMENT_REPORT) f
    WHERE f.value IS NOT NULL
),
repo AS (
    SELECT
        DOCUMENT_ID,
        ARCHER_CONTENT_DOCUMENT_REPOSITORY_CONTENT_ID AS CONTENT_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_DOCUMENT_REPOSITORY
)
SELECT
    COUNT(*) AS TOTAL_ATTACHMENT_REFERENCES,
    COUNT(DISTINCT a.ATTACHMENT_ID) AS DISTINCT_ATTACHMENT_IDS,
    COUNT_IF(r_doc.DOCUMENT_ID IS NOT NULL) AS MATCHED_BY_DOCUMENT_ID,
    COUNT_IF(r_content.CONTENT_ID IS NOT NULL) AS MATCHED_BY_CONTENT_ID,
    COUNT_IF(r_doc.DOCUMENT_ID IS NULL AND r_content.CONTENT_ID IS NULL) AS UNMATCHED_REFERENCES
FROM attachment_ids a
LEFT JOIN repo r_doc
    ON a.ATTACHMENT_ID = r_doc.DOCUMENT_ID
LEFT JOIN repo r_content
    ON a.ATTACHMENT_ID = r_content.CONTENT_ID;

-- Optional second result: count how much usable document metadata exists for
-- the key that matched. Do NOT use this until the first result shows which key
-- is authoritative. If DOCUMENT_ID wins, run this block as-is.

WITH attachment_ids AS (
    SELECT DISTINCT
        f.value::NUMBER AS ATTACHMENT_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW s,
         LATERAL FLATTEN(INPUT => s.CURATED_JSON:RISK_ASSESSMENT_REPORT) f
    WHERE f.value IS NOT NULL
)
SELECT
    COUNT(*) AS MATCHED_DOCUMENTS,
    COUNT_IF(NULLIF(TRIM(d.DOCUMENT_URL),'') IS NOT NULL) AS WITH_DOCUMENT_URL,
    COUNT_IF(NULLIF(TRIM(d.DOCUMENT_LINK),'') IS NOT NULL) AS WITH_DOCUMENT_LINK,
    COUNT_IF(NULLIF(TRIM(d.NAME_OF_DOCUMENT),'') IS NOT NULL) AS WITH_NAME,
    COUNT_IF(NULLIF(TRIM(d.TITLE),'') IS NOT NULL) AS WITH_TITLE
FROM attachment_ids a
JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_DOCUMENT_REPOSITORY d
    ON a.ATTACHMENT_ID = d.DOCUMENT_ID;
