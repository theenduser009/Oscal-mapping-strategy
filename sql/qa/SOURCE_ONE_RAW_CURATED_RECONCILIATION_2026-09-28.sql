-- SOURCE ONE: RAW_DATA -> CURATED_JSON RECONCILIATION
-- Prepared 2026-09-28. Run the WHOLE file in one Snowflake worksheet.
-- SELECT ONLY: no DDL, DML, temporary tables, notebook run, or session changes.
-- Reads the full current Authorization Package table and current field metadata.
-- Output contains aggregate counts only; no source IDs or business values.
--
-- Reference inspected at 2d3610bac3efe33b2ba29638899bf3e3dc0ed0cd:
-- sql/matillion/READ_ONLY_authorization_package_full_conversion_preview.sql
-- sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql
--
-- This is a comparison against the SAVED CONVERSION REFERENCE, not proof that
-- this candidate is the version deployed in Matillion. Differences need review.
-- The reference's type conversion, key precedence, nested extraction, null-key
-- retention, and derived CONTENT_ID precedence are retained. QA uses safe casts
-- for identifiers and flags ambiguous inputs instead of selecting tied winners.
-- A raw RequestedObject.Id is NOT assumed to equal derived CONTENT_ID.
-- Numeric precision/scale and date/timestamp parsing follow the saved reference
-- and current session. Equality with that reference is not business-rule approval.
-- This does not validate upstream vendor-file completeness or OSCAL DIM/FACT.
-- Not executed in live Snowflake when published.

WITH
raw_rows AS (
    SELECT
        RAW_DATA, CURATED_JSON, CONTENT_ID,
        TYPEOF(RAW_DATA) AS RAW_TYPE,
        CASE WHEN TYPEOF(RAW_DATA) = 'ARRAY'
             THEN ARRAY_SIZE(AS_ARRAY(RAW_DATA)) ELSE 1 END AS ROOT_ITEMS,
        CASE WHEN TYPEOF(RAW_DATA) = 'ARRAY'
             THEN GET(AS_ARRAY(RAW_DATA), 0) ELSE RAW_DATA END AS OBJ
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
),
source_objects AS (
    SELECT r.*, GET(AS_OBJECT(OBJ), 'RequestedObject') AS REQ_OBJ
    FROM raw_rows r
),
source_rows AS (
    SELECT r.*,
        TRY_TO_NUMBER(GET(AS_OBJECT(REQ_OBJ), 'Id')::STRING) AS RAW_ID,
        TRY_TO_NUMBER(GET(AS_OBJECT(REQ_OBJ), 'LevelId')::STRING) AS LEVEL_ID,
        GET(AS_OBJECT(REQ_OBJ), 'FieldContents') AS FIELD_CONTENTS,
        COALESCE(
            RAW_TYPE IN ('OBJECT', 'ARRAY') AND ROOT_ITEMS = 1
            AND TYPEOF(OBJ) = 'OBJECT' AND TYPEOF(REQ_OBJ) = 'OBJECT',
            FALSE
        ) AS ROOT_OK
    FROM source_objects r
),
raw_id_counts AS (
    SELECT RAW_ID, COUNT(*) AS N FROM source_rows GROUP BY RAW_ID
),
stored_id_counts AS (
    SELECT CONTENT_ID, COUNT(*) AS N
    FROM source_rows
    WHERE NULLIF(TRIM(CONTENT_ID), '') IS NOT NULL
    GROUP BY CONTENT_ID
),
norm AS (
    SELECT s.*
    FROM source_rows s
    JOIN raw_id_counts d ON d.RAW_ID = s.RAW_ID
    WHERE s.ROOT_OK AND d.N = 1 AND s.RAW_ID IS NOT NULL
      AND TYPEOF(s.FIELD_CONTENTS) = 'OBJECT'
),
metadata_rows AS (
    SELECT TRY_TO_NUMBER(FIELD_ID::STRING) AS FIELD_ID_NUM,
           SQL_FIELD_NAME, KEY_FIELD,
           TRY_TO_NUMBER(LEVEL_ID::STRING) AS META_LEVEL_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
),
flat AS (
    SELECT n.RAW_ID, n.LEVEL_ID, f.KEY::STRING AS FIELD_ID,
           TRY_TO_NUMBER(f.KEY::STRING) AS FIELD_ID_NUM,
           TRY_TO_NUMBER(GET(AS_OBJECT(f.VALUE), 'Type')::STRING) AS TYPE_ID,
           GET(AS_OBJECT(f.VALUE), 'Value') AS V,
           COALESCE(TYPEOF(f.VALUE) = 'OBJECT', FALSE) AS FIELD_OBJECT_OK
    FROM norm n, LATERAL FLATTEN(INPUT => AS_OBJECT(n.FIELD_CONTENTS)) f
),
mapped AS (
    SELECT f.*,
           COALESCE(m.SQL_FIELD_NAME, 'FIELD_' || f.FIELD_ID) AS SQL_KEY,
           m.SQL_FIELD_NAME IS NULL AS FALLBACK_KEY,
           DENSE_RANK() OVER (
               PARTITION BY f.RAW_ID,
                   COALESCE(m.SQL_FIELD_NAME, 'FIELD_' || f.FIELD_ID)
               ORDER BY CASE WHEN COALESCE(m.KEY_FIELD, 'N') = 'Y'
                             THEN 0 ELSE 1 END,
                        CASE WHEN m.META_LEVEL_ID = f.LEVEL_ID
                             THEN 0 ELSE 1 END,
                        f.FIELD_ID_NUM
           ) AS CHOICE_RANK
    FROM flat f
    LEFT JOIN metadata_rows m ON m.FIELD_ID_NUM = f.FIELD_ID_NUM
),
ambiguous_choices AS (
    SELECT RAW_ID, SQL_KEY FROM mapped
    WHERE CHOICE_RANK = 1
    GROUP BY RAW_ID, SQL_KEY HAVING COUNT(*) > 1
),
multiple_names AS (
    SELECT RAW_ID, FIELD_ID FROM mapped
    GROUP BY RAW_ID, FIELD_ID HAVING COUNT(DISTINCT SQL_KEY) > 1
),
top_typed AS (
    SELECT RAW_ID, SQL_KEY, FIELD_ID, V AS SOURCE_VALUE, TYPE_ID,
        CASE TYPE_ID
            WHEN 1  THEN TO_VARIANT(NULLIF(V::STRING, ''))
            WHEN 2  THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
            WHEN 3  THEN TO_VARIANT(TRY_TO_DATE(NULLIF(V::STRING, '')))
            WHEN 6  THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
            WHEN 20 THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
            WHEN 21 THEN TO_VARIANT(TRY_TO_TIMESTAMP_NTZ(NULLIF(V::STRING, '')))
            WHEN 22 THEN TO_VARIANT(TRY_TO_TIMESTAMP_NTZ(NULLIF(V::STRING, '')))
            ELSE TO_VARIANT(V)
        END AS TYPED_VALUE
    FROM mapped
    WHERE CHOICE_RANK = 1
),
nested_flat AS (
    SELECT n.RAW_ID, f.KEY::STRING AS FIELD_ID,
           TRY_TO_NUMBER(f.KEY::STRING) AS FIELD_ID_NUM, f.VALUE AS V
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => AS_OBJECT(n.FIELD_CONTENTS), RECURSIVE => TRUE
         ) f
    WHERE f.KEY IS NOT NULL
      AND f.PATH LIKE '%FieldContents%'
      AND f.KEY <> 'FieldContents'
),
nested_mapped AS (
    SELECT f.*, m.SQL_FIELD_NAME AS SQL_KEY
    FROM nested_flat f
    LEFT JOIN metadata_rows m ON m.FIELD_ID_NUM = f.FIELD_ID_NUM
),
combined AS (
    SELECT RAW_ID, SQL_KEY, SOURCE_VALUE, TYPED_VALUE FROM top_typed
    UNION ALL
    SELECT RAW_ID, SQL_KEY,
           CASE WHEN TYPEOF(V) = 'OBJECT'
                THEN GET(AS_OBJECT(V), 'Value') ELSE V END AS SOURCE_VALUE,
           TO_VARIANT(CASE WHEN TYPEOF(V) = 'OBJECT'
                           THEN GET(AS_OBJECT(V), 'Value') ELSE V END)
                AS TYPED_VALUE
    FROM nested_mapped WHERE SQL_KEY IS NOT NULL
),
duplicate_keys AS (
    SELECT RAW_ID, SQL_KEY FROM combined
    GROUP BY RAW_ID, SQL_KEY HAVING COUNT(*) > 1
),
blocked_records AS (
    SELECT RAW_ID FROM ambiguous_choices
    UNION SELECT RAW_ID FROM multiple_names
    UNION SELECT RAW_ID FROM duplicate_keys
    UNION SELECT RAW_ID FROM combined WHERE NULLIF(TRIM(SQL_KEY), '') IS NULL
    UNION SELECT RAW_ID FROM flat
          WHERE FIELD_ID_NUM IS NULL OR TYPE_ID IS NULL OR NOT FIELD_OBJECT_OK
),
comparable AS (
    SELECT n.*
    FROM norm n
    WHERE TYPEOF(n.CURATED_JSON) = 'OBJECT'
      AND EXISTS (SELECT 1 FROM combined c WHERE c.RAW_ID = n.RAW_ID)
      AND NOT EXISTS (SELECT 1 FROM blocked_records b WHERE b.RAW_ID = n.RAW_ID)
),
expected AS (
    SELECT c.RAW_ID, c.SQL_KEY, c.SOURCE_VALUE, c.TYPED_VALUE,
           COALESCE(c.TYPED_VALUE, PARSE_JSON('null')) AS EXPECTED_VALUE
    FROM combined c JOIN comparable p ON p.RAW_ID = c.RAW_ID
),
actual AS (
    SELECT p.RAW_ID, f.KEY::STRING AS SQL_KEY, f.VALUE AS ACTUAL_VALUE
    FROM comparable p, LATERAL FLATTEN(INPUT => AS_OBJECT(p.CURATED_JSON)) f
),
compared AS (
    SELECT COALESCE(e.RAW_ID, a.RAW_ID) AS RAW_ID,
           COALESCE(e.SQL_KEY, a.SQL_KEY) AS SQL_KEY,
           e.SOURCE_VALUE, e.TYPED_VALUE, e.EXPECTED_VALUE, a.ACTUAL_VALUE,
           CASE
               WHEN e.RAW_ID IS NULL THEN 'UNEXPECTED_CURATED_KEY'
               WHEN a.RAW_ID IS NULL
                   THEN IFF(IS_NULL_VALUE(e.EXPECTED_VALUE),
                            'MISSING_NULL_KEY', 'MISSING_POPULATED_KEY')
               WHEN NOT EQUAL_NULL(TYPEOF(e.EXPECTED_VALUE), TYPEOF(a.ACTUAL_VALUE))
                   THEN 'TYPE_DIFFERENCE'
               WHEN NOT EQUAL_NULL(e.EXPECTED_VALUE, a.ACTUAL_VALUE)
                   THEN 'VALUE_DIFFERENCE'
               ELSE 'MATCH'
           END AS FIELD_STATUS
    FROM expected e FULL OUTER JOIN actual a
      ON e.RAW_ID = a.RAW_ID AND e.SQL_KEY = a.SQL_KEY
),
id_objects AS (
    -- SQL-null values are omitted here, exactly as in the reference identity input.
    SELECT RAW_ID, OBJECT_AGG(SQL_KEY, TYPED_VALUE) AS ID_SOURCE_JSON
    FROM expected GROUP BY RAW_ID
),
identity_comparison AS (
    SELECT p.RAW_ID, p.CONTENT_ID,
        COALESCE(
            i.ID_SOURCE_JSON:"ssp_uuid"::STRING,
            i.ID_SOURCE_JSON:"AUTH_PKG_TRACKING_ID"::STRING,
            i.ID_SOURCE_JSON:"HRTN_ID"::STRING,
            i.ID_SOURCE_JSON:"TRACKING_ID"::STRING,
            i.ID_SOURCE_JSON:"CONTENT_ID"::STRING,
            p.RAW_ID::STRING
        ) AS REFERENCE_CONTENT_ID
    FROM comparable p JOIN id_objects i ON i.RAW_ID = p.RAW_ID
),
metrics AS (
    SELECT
        (SELECT COUNT(*) FROM source_rows) AS SOURCE_ROWS,
        (SELECT COUNT(*) FROM comparable) AS COMPARED_ROWS,
        (SELECT COUNT(*) FROM source_rows WHERE NOT ROOT_OK) AS BAD_ROOT_ROWS,
        (SELECT COUNT(*) FROM source_rows WHERE RAW_ID IS NULL) AS BAD_RAW_ID_ROWS,
        (SELECT COUNT(*) FROM raw_id_counts WHERE RAW_ID IS NOT NULL AND N > 1)
            AS DUPLICATE_RAW_ID_GROUPS,
        (SELECT COUNT(*) FROM source_rows WHERE NULLIF(TRIM(CONTENT_ID), '') IS NULL)
            AS MISSING_CONTENT_ID_ROWS,
        (SELECT COUNT(*) FROM stored_id_counts WHERE N > 1) AS DUPLICATE_CONTENT_ID_GROUPS,
        (SELECT COUNT(*) FROM source_rows
         WHERE COALESCE(TYPEOF(FIELD_CONTENTS), 'SQL_NULL') <> 'OBJECT')
            AS BAD_FIELD_CONTENTS_ROWS,
        (SELECT COUNT(*) FROM source_rows
         WHERE COALESCE(TYPEOF(CURATED_JSON), 'SQL_NULL') <> 'OBJECT')
            AS BAD_CURATED_ROWS,
        (SELECT COUNT(*) FROM norm n
         WHERE NOT EXISTS (SELECT 1 FROM flat f WHERE f.RAW_ID = n.RAW_ID))
            AS NO_FIELD_ROWS,
        (SELECT COUNT(*) FROM flat
         WHERE FIELD_ID_NUM IS NULL OR TYPE_ID IS NULL OR NOT FIELD_OBJECT_OK)
            AS MALFORMED_FIELDS,
        (SELECT COUNT(*) FROM ambiguous_choices) AS AMBIGUOUS_CHOICES,
        (SELECT COUNT(*) FROM multiple_names) AS MULTIPLE_NAMES,
        (SELECT COUNT(*) FROM duplicate_keys) AS DUPLICATE_OUTPUT_KEYS,
        (SELECT COUNT(*) FROM combined WHERE NULLIF(TRIM(SQL_KEY), '') IS NULL)
            AS INVALID_OUTPUT_KEYS,
        (SELECT COUNT(*) FROM top_typed
         WHERE SOURCE_VALUE IS NOT NULL
           AND NOT COALESCE(IS_NULL_VALUE(SOURCE_VALUE), FALSE)
           AND SOURCE_VALUE::STRING <> '' AND TYPED_VALUE IS NULL)
            AS CONVERSIONS_TO_NULL,
        (SELECT COUNT(*) FROM mapped WHERE CHOICE_RANK = 1 AND FALLBACK_KEY)
            AS FALLBACK_KEY_ROWS,
        (SELECT COUNT(*) FROM mapped WHERE CHOICE_RANK > 1) AS DEPRIORITIZED_ROWS,
        (SELECT COUNT(*) FROM nested_mapped
         WHERE FIELD_ID_NUM IS NOT NULL AND SQL_KEY IS NULL) AS NESTED_UNMAPPED_ROWS,
        (SELECT COUNT(*) FROM nested_flat WHERE FIELD_ID_NUM IS NULL)
            AS NESTED_NONNUMERIC_ROWS,
        (SELECT COUNT(*) FROM compared WHERE FIELD_STATUS = 'MATCH') AS MATCHING_FIELDS,
        (SELECT COUNT(*) FROM compared WHERE FIELD_STATUS = 'MISSING_NULL_KEY')
            AS MISSING_NULL_KEYS,
        (SELECT COUNT(*) FROM compared WHERE FIELD_STATUS = 'MISSING_POPULATED_KEY')
            AS MISSING_POPULATED_KEYS,
        (SELECT COUNT(*) FROM compared WHERE FIELD_STATUS = 'UNEXPECTED_CURATED_KEY')
            AS UNEXPECTED_KEYS,
        (SELECT COUNT(*) FROM compared WHERE FIELD_STATUS = 'TYPE_DIFFERENCE')
            AS TYPE_DIFFERENCES,
        (SELECT COUNT(*) FROM compared WHERE FIELD_STATUS = 'VALUE_DIFFERENCE')
            AS VALUE_DIFFERENCES,
        (SELECT COUNT(*) FROM identity_comparison
         WHERE NOT EQUAL_NULL(CONTENT_ID, REFERENCE_CONTENT_ID)) AS ID_DIFFERENCES,
        (SELECT COUNT(*) FROM compared
         WHERE COALESCE(IS_NULL_VALUE(SOURCE_VALUE), FALSE)
           AND ACTUAL_VALUE IS NOT NULL
           AND NOT COALESCE(IS_NULL_VALUE(ACTUAL_VALUE), FALSE)) AS RAW_NULL_TO_VALUE
),
checks AS (
    SELECT '01' AS CHECK_ORDER, 'Source rows read' AS QA_CHECK,
           SOURCE_ROWS AS OBSERVED_COUNT, 'INFO' AS CHECK_STATUS,
           'Current table rows, not the historical count or vendor-file coverage.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '02' AS CHECK_ORDER, 'Rows compared field by field' AS QA_CHECK,
           COMPARED_ROWS AS OBSERVED_COUNT, 'INFO' AS CHECK_STATUS,
           'Records eligible for unambiguous comparison with the saved reference.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '03' AS CHECK_ORDER, 'Rows NOT compared' AS QA_CHECK,
           SOURCE_ROWS - COMPARED_ROWS AS OBSERVED_COUNT, IFF(SOURCE_ROWS - COMPARED_ROWS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Must be zero for full-table comparison coverage; other checks explain exclusions.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '04' AS CHECK_ORDER, 'Unsupported raw root rows' AS QA_CHECK,
           BAD_ROOT_ROWS AS OBSERVED_COUNT, IFF(BAD_ROOT_ROWS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Expected an object or one-item array containing RequestedObject.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '05' AS CHECK_ORDER, 'Missing or invalid raw record IDs' AS QA_CHECK,
           BAD_RAW_ID_ROWS AS OBSERVED_COUNT, IFF(BAD_RAW_ID_ROWS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'RequestedObject.Id could not be interpreted as a numeric source identity.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '06' AS CHECK_ORDER, 'Duplicate raw record ID groups' AS QA_CHECK,
           DUPLICATE_RAW_ID_GROUPS AS OBSERVED_COUNT, IFF(DUPLICATE_RAW_ID_GROUPS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'No arbitrary latest/winner is selected.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '07' AS CHECK_ORDER, 'Missing stored CONTENT_ID rows' AS QA_CHECK,
           MISSING_CONTENT_ID_ROWS AS OBSERVED_COUNT, IFF(MISSING_CONTENT_ID_ROWS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Stored derived identifiers must not be blank or SQL null.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '08' AS CHECK_ORDER, 'Duplicate stored CONTENT_ID groups' AS QA_CHECK,
           DUPLICATE_CONTENT_ID_GROUPS AS OBSERVED_COUNT, IFF(DUPLICATE_CONTENT_ID_GROUPS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Distinct raw objects must not silently collapse to one stored identifier.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '09' AS CHECK_ORDER, 'Invalid or absent FieldContents objects' AS QA_CHECK,
           BAD_FIELD_CONTENTS_ROWS AS OBSERVED_COUNT, IFF(BAD_FIELD_CONTENTS_ROWS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Raw field coverage cannot be checked for these rows.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '10' AS CHECK_ORDER, 'Non-object CURATED_JSON rows' AS QA_CHECK,
           BAD_CURATED_ROWS AS OBSERVED_COUNT, IFF(BAD_CURATED_ROWS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Includes SQL null, JSON null, strings, arrays, and other non-object roots.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '11' AS CHECK_ORDER, 'Records with no extracted top-level fields' AS QA_CHECK,
           NO_FIELD_ROWS AS OBSERVED_COUNT, IFF(NO_FIELD_ROWS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'An empty expansion is not a successful reconciliation.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '12' AS CHECK_ORDER, 'Malformed raw field definitions' AS QA_CHECK,
           MALFORMED_FIELDS AS OBSERVED_COUNT, IFF(MALFORMED_FIELDS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Invalid FieldID, missing/invalid Type, or non-object field wrapper.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '13' AS CHECK_ORDER, 'Tied mapping winners' AS QA_CHECK,
           AMBIGUOUS_CHOICES AS OBSERVED_COUNT, IFF(AMBIGUOUS_CHOICES = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Reference ordering ties are reported instead of being resolved arbitrarily.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '14' AS CHECK_ORDER, 'Raw fields resolving to multiple output names' AS QA_CHECK,
           MULTIPLE_NAMES AS OBSERVED_COUNT, IFF(MULTIPLE_NAMES = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Review field metadata before trusting candidate reconstruction.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '15' AS CHECK_ORDER, 'Duplicate combined output key groups' AS QA_CHECK,
           DUPLICATE_OUTPUT_KEYS AS OBSERVED_COUNT, IFF(DUPLICATE_OUTPUT_KEYS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Includes top-level/nested collisions; no key is overwritten.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '16' AS CHECK_ORDER, 'Blank output key rows' AS QA_CHECK,
           INVALID_OUTPUT_KEYS AS OBSERVED_COUNT, IFF(INVALID_OUTPUT_KEYS = 0, 'PASS', 'BLOCKED') AS CHECK_STATUS,
           'Empty metadata names cannot be used as trusted output keys.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '17' AS CHECK_ORDER, 'Populated values converted to SQL null' AS QA_CHECK,
           CONVERSIONS_TO_NULL AS OBSERVED_COUNT, IFF(CONVERSIONS_TO_NULL = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Failed reference conversion needs review even when stored output is also null.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '18' AS CHECK_ORDER, 'Selected FIELD_ fallback name rows' AS QA_CHECK,
           FALLBACK_KEY_ROWS AS OBSERVED_COUNT, IFF(FALLBACK_KEY_ROWS = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Reference fallback retains FieldID but is not verified field-name resolution.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '19' AS CHECK_ORDER, 'Lower-priority top-level mapping rows' AS QA_CHECK,
           DEPRIORITIZED_ROWS AS OBSERVED_COUNT, IFF(DEPRIORITIZED_ROWS = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Reported reference precedence exclusions; not automatically source-data defects.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '20' AS CHECK_ORDER, 'Numeric nested field rows without mapped names' AS QA_CHECK,
           NESTED_UNMAPPED_ROWS AS OBSERVED_COUNT, IFF(NESTED_UNMAPPED_ROWS = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Reference nested extraction omits these; investigate field coverage.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '21' AS CHECK_ORDER, 'Non-numeric nested descendants' AS QA_CHECK,
           NESTED_NONNUMERIC_ROWS AS OBSERVED_COUNT, 'INFO' AS CHECK_STATUS,
           'Reported structural descendants; safe casts avoid reference strict-cast errors.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '22' AS CHECK_ORDER, 'Matching key/value/type pairs' AS QA_CHECK,
           MATCHING_FIELDS AS OBSERVED_COUNT, 'INFO' AS CHECK_STATUS,
           'Matches only within eligible records and saved-reference rules.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '23' AS CHECK_ORDER, 'Missing null-valued keys' AS QA_CHECK,
           MISSING_NULL_KEYS AS OBSERVED_COUNT, IFF(MISSING_NULL_KEYS = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Explicit expected JSON null is different from an absent key.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '24' AS CHECK_ORDER, 'Missing populated keys' AS QA_CHECK,
           MISSING_POPULATED_KEYS AS OBSERVED_COUNT, IFF(MISSING_POPULATED_KEYS = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Reference output has a populated key absent from stored JSON.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '25' AS CHECK_ORDER, 'Unexpected curated-only keys' AS QA_CHECK,
           UNEXPECTED_KEYS AS OBSERVED_COUNT, IFF(UNEXPECTED_KEYS = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Stored key is not emitted by the saved conversion reference.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '26' AS CHECK_ORDER, 'Value type differences' AS QA_CHECK,
           TYPE_DIFFERENCES AS OBSERVED_COUNT, IFF(TYPE_DIFFERENCES = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Check number/string/date/container differences; no implicit coercion.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '27' AS CHECK_ORDER, 'Same-type value differences' AS QA_CHECK,
           VALUE_DIFFERENCES AS OBSERVED_COUNT, IFF(VALUE_DIFFERENCES = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Native VARIANT comparison, not serialized object-key ordering.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '28' AS CHECK_ORDER, 'Derived CONTENT_ID differences' AS QA_CHECK,
           ID_DIFFERENCES AS OBSERVED_COUNT, IFF(ID_DIFFERENCES = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Compared with the exact saved reference precedence, not raw-ID equality.' AS DETAIL FROM metrics
    UNION ALL
    SELECT '29' AS CHECK_ORDER, 'Raw JSON null changed to a populated value' AS QA_CHECK,
           RAW_NULL_TO_VALUE AS OBSERVED_COUNT, IFF(RAW_NULL_TO_VALUE = 0, 'PASS', 'REVIEW') AS CHECK_STATUS,
           'Independent source-null check even if the conversion reference also loses null.' AS DETAIL FROM metrics
),
overall AS (
    SELECT '00' AS CHECK_ORDER, 'Overall upstream comparison' AS QA_CHECK,
           SOURCE_ROWS - COMPARED_ROWS AS OBSERVED_COUNT,
           CASE
               WHEN SOURCE_ROWS = 0 THEN 'BLOCKED_EMPTY_SOURCE'
               WHEN COMPARED_ROWS <> SOURCE_ROWS
                    OR MISSING_CONTENT_ID_ROWS + DUPLICATE_CONTENT_ID_GROUPS > 0
                   THEN 'BLOCKED_INCOMPLETE_COMPARISON'
               WHEN CONVERSIONS_TO_NULL + FALLBACK_KEY_ROWS + DEPRIORITIZED_ROWS
                    + NESTED_UNMAPPED_ROWS + MISSING_NULL_KEYS + MISSING_POPULATED_KEYS
                    + UNEXPECTED_KEYS + TYPE_DIFFERENCES + VALUE_DIFFERENCES
                    + ID_DIFFERENCES + RAW_NULL_TO_VALUE > 0
                   THEN 'REVIEW_REQUIRED'
               ELSE 'MATCHED_SAVED_REFERENCE'
           END AS CHECK_STATUS,
           'Counts are observations, not production sign-off. Deployed conversion version and downstream QA remain separate.' AS DETAIL
    FROM metrics
)
SELECT CURRENT_TIMESTAMP() AS QA_EXECUTED_AT, CHECK_ORDER, QA_CHECK,
       OBSERVED_COUNT, CHECK_STATUS, DETAIL
FROM (
    SELECT * FROM overall
    UNION ALL
    SELECT * FROM checks
)
ORDER BY CHECK_ORDER;
