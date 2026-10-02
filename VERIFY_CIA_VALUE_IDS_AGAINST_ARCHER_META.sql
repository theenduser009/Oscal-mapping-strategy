-- VERIFY CIA / FIPS SELECT VALUE IDS AGAINST ARCHER META
-- Date: 2026-10-02
-- READ ONLY.
--
-- Purpose:
--   Prove what each populated CIA source ValueListId resolves to in
--   RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE.
--
-- Interpretation:
--   META_LABEL_CLASS = CANONICAL_FIPS  -> meta says Low/Moderate/High
--   META_LABEL_CLASS = LEGACY_LOE      -> meta itself says Legacy LOE...
--   META_LABEL_CLASS = OTHER           -> meta says something else
--   META_LABEL_CLASS = META_MISSING    -> no meta row
--   META_LABEL_CLASS = META_AMBIGUOUS  -> duplicate meta rows for same ID
--
-- This query does NOT invent an LOE -> FIPS crosswalk.

WITH field_map AS (
    SELECT *
    FROM VALUES
        ('RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY',
         'security-objective-confidentiality'),
        ('CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE',
         'security-objective-confidentiality'),
        ('RECOMMENDED_INTEGRITY_CONTROL_CATEGORY',
         'security-objective-integrity'),
        ('INTEGRITY_CONTROL_CATEGORY_OVERRIDE',
         'security-objective-integrity'),
        ('AVAILABILITY_CONTROL_CATEGORY_OVERRIDE',
         'security-objective-availability'),
        ('RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY',
         'security-objective-availability'),
        ('PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY',
         'security-objective-integrity'),
        ('PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY',
         'security-objective-availability'),
        ('CNSS_AVAILABILITY_RATING',
         'security-objective-availability'),
        ('CNSS_CONFIDENTIALITY_RATING',
         'security-objective-confidentiality'),
        ('CNSS_INTEGRITY_RATING',
         'security-objective-integrity')
    AS f(SOURCE_FIELD_NAME, OSCAL_MEMBER)
),
source_fields AS (
    SELECT
        r.CONTENT_ID::VARCHAR AS CONTENT_ID,
        f.SOURCE_FIELD_NAME,
        f.OSCAL_MEMBER,
        GET(r.CURATED_JSON, f.SOURCE_FIELD_NAME) AS FIELD_VALUE
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r
    CROSS JOIN field_map f
    WHERE r.CURATED_JSON IS NOT NULL
),
source_ids AS (
    SELECT
        s.CONTENT_ID,
        s.SOURCE_FIELD_NAME,
        s.OSCAL_MEMBER,
        v.INDEX AS VALUE_INDEX,
        TRIM(v.VALUE::VARCHAR) AS SELECT_VALUE_ID
    FROM source_fields s,
         LATERAL FLATTEN(INPUT => GET(s.FIELD_VALUE, 'ValuesListIds')) v
),
resolved_values AS (
    SELECT
        s.CONTENT_ID,
        s.SOURCE_FIELD_NAME,
        rv.INDEX AS VALUE_INDEX,
        rv.VALUE:"ValueId"::VARCHAR AS RESOLVED_VALUE_ID,
        rv.VALUE:"ValueName"::VARCHAR AS RESOLVED_VALUE_NAME,
        rv.VALUE:"LookupStatus"::VARCHAR AS LOOKUP_STATUS
    FROM source_fields s,
         LATERAL FLATTEN(INPUT => GET(s.FIELD_VALUE, 'ResolvedValues')) rv
),
meta_value AS (
    SELECT
        TRIM(SELECT_VALUE_ID::VARCHAR) AS SELECT_VALUE_ID,
        COUNT(*) AS META_ROW_COUNT,
        COUNT(DISTINCT SELECT_VALUE_NAME::VARCHAR) AS DISTINCT_META_LABELS,
        MAX(SELECT_VALUE_NAME::VARCHAR) AS META_VALUE_NAME
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE
    GROUP BY TRIM(SELECT_VALUE_ID::VARCHAR)
),
comparison AS (
    SELECT
        i.CONTENT_ID,
        i.SOURCE_FIELD_NAME,
        i.OSCAL_MEMBER,
        i.SELECT_VALUE_ID,
        r.RESOLVED_VALUE_ID,
        r.RESOLVED_VALUE_NAME,
        r.LOOKUP_STATUS,
        m.META_ROW_COUNT,
        m.DISTINCT_META_LABELS,
        IFF(
            m.META_ROW_COUNT = 1
            AND m.DISTINCT_META_LABELS = 1,
            m.META_VALUE_NAME,
            NULL
        ) AS META_VALUE_NAME,
        CASE
            WHEN m.SELECT_VALUE_ID IS NULL THEN 'META_MISSING'
            WHEN m.META_ROW_COUNT <> 1 OR m.DISTINCT_META_LABELS <> 1
                THEN 'META_AMBIGUOUS'
            WHEN LOWER(TRIM(m.META_VALUE_NAME)) IN ('low','moderate','high')
                THEN 'CANONICAL_FIPS'
            WHEN UPPER(TRIM(m.META_VALUE_NAME)) LIKE 'LEGACY LOE%'
                THEN 'LEGACY_LOE'
            ELSE 'OTHER'
        END AS META_LABEL_CLASS,
        CASE
            WHEN m.SELECT_VALUE_ID IS NULL THEN 'FAIL_META_MISSING'
            WHEN m.META_ROW_COUNT <> 1 OR m.DISTINCT_META_LABELS <> 1
                THEN 'FAIL_META_AMBIGUOUS'
            WHEN r.RESOLVED_VALUE_ID IS NULL
                THEN 'FAIL_RESOLVED_VALUE_MISSING'
            WHEN TRIM(r.RESOLVED_VALUE_ID) <> i.SELECT_VALUE_ID
                THEN 'FAIL_RESOLVED_ID_MISMATCH'
            WHEN r.LOOKUP_STATUS <> 'MATCHED'
                THEN 'FAIL_LOOKUP_STATUS'
            WHEN r.RESOLVED_VALUE_NAME <> m.META_VALUE_NAME
                THEN 'FAIL_RESOLVED_LABEL_MISMATCH'
            ELSE 'PASS'
        END AS RESOLUTION_STATUS
    FROM source_ids i
    LEFT JOIN resolved_values r
      ON r.CONTENT_ID = i.CONTENT_ID
     AND r.SOURCE_FIELD_NAME = i.SOURCE_FIELD_NAME
     AND r.VALUE_INDEX = i.VALUE_INDEX
    LEFT JOIN meta_value m
      ON m.SELECT_VALUE_ID = i.SELECT_VALUE_ID
)

-- RESULT 1:
-- One row per distinct source field + select-value ID.
SELECT
    SOURCE_FIELD_NAME,
    OSCAL_MEMBER,
    SELECT_VALUE_ID,
    META_VALUE_NAME,
    META_LABEL_CLASS,
    RESOLVED_VALUE_NAME,
    RESOLUTION_STATUS,
    COUNT(*) AS SOURCE_OCCURRENCES,
    COUNT(DISTINCT CONTENT_ID) AS DISTINCT_CONTENT_IDS
FROM comparison
GROUP BY
    SOURCE_FIELD_NAME,
    OSCAL_MEMBER,
    SELECT_VALUE_ID,
    META_VALUE_NAME,
    META_LABEL_CLASS,
    RESOLVED_VALUE_NAME,
    RESOLUTION_STATUS
ORDER BY
    SOURCE_FIELD_NAME,
    SELECT_VALUE_ID;


-- RESULT 2:
-- Run this SELECT instead of RESULT 1 if you want only failures.
-- SELECT *
-- FROM comparison
-- WHERE RESOLUTION_STATUS <> 'PASS'
-- ORDER BY SOURCE_FIELD_NAME, CONTENT_ID, SELECT_VALUE_ID;
