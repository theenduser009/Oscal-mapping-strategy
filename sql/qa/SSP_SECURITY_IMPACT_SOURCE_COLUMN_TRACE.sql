-- READ ONLY: for one SSP source record, show which Archer security-impact
-- source fields are populated and which one(s) match the final DIM value.
SET QA_CONTENT_ID = '866211';

WITH field_map AS (
  SELECT * FROM VALUES
    ('confidentiality','RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY'),
    ('confidentiality','CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE'),
    ('confidentiality','CNSS_CONFIDENTIALITY_RATING'),
    ('integrity','RECOMMENDED_INTEGRITY_CONTROL_CATEGORY'),
    ('integrity','INTEGRITY_CONTROL_CATEGORY_OVERRIDE'),
    ('integrity','PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY'),
    ('integrity','CNSS_INTEGRITY_RATING'),
    ('availability','RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY'),
    ('availability','AVAILABILITY_CONTROL_CATEGORY_OVERRIDE'),
    ('availability','PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY'),
    ('availability','CNSS_AVAILABILITY_RATING')
  AS v(OBJECTIVE, SOURCE_FIELD)
),
src AS (
  SELECT r.CONTENT_ID::STRING AS SOURCE_RECORD_ID,
         f.OBJECTIVE,
         f.SOURCE_FIELD,
         GET(r.CURATED_JSON, f.SOURCE_FIELD) AS RAW_VALUE
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r
  CROSS JOIN field_map f
  WHERE r.CONTENT_ID::STRING = $QA_CONTENT_ID
),
resolved AS (
  SELECT s.*,
         COALESCE(
           TRY_TO_NUMBER(GET(GET(s.RAW_VALUE,'ValuesListIds'),0)::STRING),
           TRY_TO_NUMBER(GET(GET(s.RAW_VALUE,'ValueListIds'),0)::STRING)
         ) AS SELECT_ID
  FROM src s
),
labels AS (
  SELECT r.*,
         COALESCE(
           mv.SELECT_VALUE_NAME,
           IFF(TYPEOF(r.RAW_VALUE)='VARCHAR', r.RAW_VALUE::STRING, NULL)
         ) AS RESOLVED_LABEL
  FROM resolved r
  LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE mv
    ON mv.SELECT_VALUE_ID = r.SELECT_ID
)
SELECT l.SOURCE_RECORD_ID,
       l.OBJECTIVE,
       l.SOURCE_FIELD,
       l.RAW_VALUE,
       l.SELECT_ID,
       l.RESOLVED_LABEL,
       CASE
         WHEN LOWER(TRIM(l.RESOLVED_LABEL)) IN ('low','moderate','high')
           THEN LOWER(TRIM(l.RESOLVED_LABEL))
         ELSE l.RESOLVED_LABEL
       END AS MAPPER_VALUE,
       CASE l.OBJECTIVE
         WHEN 'confidentiality' THEN sil.METADATA_JSON:"security-objective-confidentiality"::STRING
         WHEN 'integrity' THEN sil.METADATA_JSON:"security-objective-integrity"::STRING
         WHEN 'availability' THEN sil.METADATA_JSON:"security-objective-availability"::STRING
       END AS DIM_VALUE
FROM labels l
LEFT JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT sil
  ON sil.SOURCE_RECORD_ID = l.SOURCE_RECORD_ID
 AND sil.ELEMENT_TYPE = 'security-impact-level'
ORDER BY l.OBJECTIVE, l.SOURCE_FIELD;
