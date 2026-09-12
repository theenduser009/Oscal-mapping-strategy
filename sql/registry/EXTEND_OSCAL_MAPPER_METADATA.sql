-- ONE-TIME DEV REGISTRY LEAN STRUCTURAL METADATA MIGRATION. Run the whole file as SQL.
-- Prepared migration, NOT evidence of a live run. Schedule without other registry writers.
-- Only existing active SSP / ASSESSMENT_RESULTS rows receive retained metadata.
-- No rows are inserted; the original nine columns and all other models stay unchanged.
-- No application DIM/FACT targets are read or written.
--
-- IMPORTANT: ALTER TABLE is DDL and auto-commits; added columns cannot be rolled back
-- by the UPDATE transaction. A failed DDL phase may leave some nullable columns added.
-- Correct the reported schema/contract issue, then rerun; matching metadata is idempotent.
-- Run in a fresh session with no active transaction. Do not retry UNKNOWN outcomes
-- automatically: inspect the registry first. Success does not validate mapper outputs.
-- References:
-- https://docs.snowflake.com/en/sql-reference/transactions
-- https://docs.snowflake.com/en/sql-reference/sql/alter-table
-- https://docs.snowflake.com/en/developer-guide/snowflake-scripting/resultsets
-- https://docs.snowflake.com/en/sql-reference/sql/execute-immediate
-- https://docs.snowflake.com/en/sql-reference/sql/update
-- https://docs.snowflake.com/en/sql-reference/bind-variables#use-bind-variables-with-semi-structured-data
--
-- Seed provenance: accepted frozen behavior plus the existing nine-column
-- hierarchy/identity contract. Only the three non-derivable runtime fields are
-- retained here. Field rules remain in Mapping/ARCHER_OSCAL_MAPPINGS.csv.

EXECUTE IMMEDIATE $$
DECLARE
  seed ARRAY;
  desired ARRAY;
  baseline ARRAY;
  desired_json VARCHAR;
  baseline_json VARCHAR;
  column_specs ARRAY DEFAULT PARSE_JSON('[{"NAME":"OPERATOR","TYPE":"VARCHAR"},{"NAME":"UUID_POLICY","TYPE":"VARCHAR"},{"NAME":"REQUIRED_MEMBERS","TYPE":"VARCHAR"}]')::ARRAY;
  result_rows RESULTSET;
  statement VARCHAR;
  conflict_sql VARCHAR DEFAULT 'WITH desired AS (SELECT value d FROM TABLE(FLATTEN(INPUT => PARSE_JSON(?)))),
current_rows AS (SELECT UPPER(TRIM(OSCAL_MODEL_KEY)) model, TRIM(NODE_PATH) path,
OBJECT_CONSTRUCT_KEEP_NULL(r.*) present FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r WHERE IS_ACTIVE)
SELECT COUNT(*) N FROM desired d JOIN current_rows r
ON r.model=d.d:MODEL::VARCHAR AND r.path=d.d:PATH::VARCHAR,
LATERAL FLATTEN(INPUT=>d.d:META) k
WHERE NOT COALESCE(IS_NULL_VALUE(GET(r.present,k.key)),TRUE)
AND GET(r.present,k.key) IS DISTINCT FROM k.value';
  baseline_sql VARCHAR DEFAULT 'WITH expected AS (SELECT value row_value, COUNT(*) n FROM TABLE(FLATTEN(INPUT=>PARSE_JSON(?))) GROUP BY value),
actual AS (SELECT OBJECT_CONSTRUCT_KEEP_NULL(''OSCAL_MODEL_KEY'', r."OSCAL_MODEL_KEY", ''NODE_PATH'', r."NODE_PATH", ''ELEMENT_TYPE'', r."ELEMENT_TYPE", ''PARENT_NODE_PATH'', r."PARENT_NODE_PATH", ''IS_COLLECTION'', r."IS_COLLECTION", ''INSTANCE_KEY_RULE'', r."INSTANCE_KEY_RULE", ''PROCESS_ORDER'', r."PROCESS_ORDER", ''IS_ACTIVE'', r."IS_ACTIVE", ''ITEM_PATH'', r."ITEM_PATH") row_value, COUNT(*) n FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r GROUP BY row_value)
SELECT COUNT(*) N FROM expected e FULL OUTER JOIN actual a ON e.row_value=a.row_value
WHERE e.n IS DISTINCT FROM a.n';
  update_sql VARCHAR DEFAULT 'UPDATE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY SET
  "OPERATOR" = IFF(IS_NULL_VALUE(d.meta:OPERATOR),NULL,d.meta:OPERATOR::VARCHAR),
  "UUID_POLICY" = IFF(IS_NULL_VALUE(d.meta:UUID_POLICY),NULL,d.meta:UUID_POLICY::VARCHAR),
  "REQUIRED_MEMBERS" = IFF(IS_NULL_VALUE(d.meta:REQUIRED_MEMBERS),NULL,d.meta:REQUIRED_MEMBERS::VARCHAR)
FROM (SELECT value:MODEL::VARCHAR model, value:PATH::VARCHAR path, value:META meta FROM TABLE(FLATTEN(INPUT=>PARSE_JSON(?)))) d
WHERE UPPER(TRIM(OSCAL_MODEL_KEY))=d.model AND TRIM(NODE_PATH)=d.path AND IS_ACTIVE
AND ("OPERATOR" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:OPERATOR),NULL,d.meta:OPERATOR::VARCHAR)
  OR "UUID_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:UUID_POLICY),NULL,d.meta:UUID_POLICY::VARCHAR)
  OR "REQUIRED_MEMBERS" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_MEMBERS),NULL,d.meta:REQUIRED_MEMBERS::VARCHAR))
AND (("OPERATOR" IS NULL OR "OPERATOR" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:OPERATOR),NULL,d.meta:OPERATOR::VARCHAR))
  AND ("UUID_POLICY" IS NULL OR "UUID_POLICY" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:UUID_POLICY),NULL,d.meta:UUID_POLICY::VARCHAR))
  AND ("REQUIRED_MEMBERS" IS NULL OR "REQUIRED_MEMBERS" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_MEMBERS),NULL,d.meta:REQUIRED_MEMBERS::VARCHAR)))';
  verify_sql VARCHAR DEFAULT 'SELECT COUNT(*) N FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r JOIN (SELECT value:MODEL::VARCHAR model, value:PATH::VARCHAR path, value:META meta FROM TABLE(FLATTEN(INPUT=>PARSE_JSON(?)))) d
ON UPPER(TRIM(r.OSCAL_MODEL_KEY))=d.model AND TRIM(r.NODE_PATH)=d.path AND r.IS_ACTIVE
WHERE r."OPERATOR" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:OPERATOR),NULL,d.meta:OPERATOR::VARCHAR)
  OR r."UUID_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:UUID_POLICY),NULL,d.meta:UUID_POLICY::VARCHAR)
  OR r."REQUIRED_MEMBERS" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_MEMBERS),NULL,d.meta:REQUIRED_MEMBERS::VARCHAR)';
  n NUMBER;
  tx NUMBER;
  changed_rows NUMBER DEFAULT 0;
  commit_attempted BOOLEAN DEFAULT FALSE;
  transaction_started BOOLEAN DEFAULT FALSE;
  already_active EXCEPTION (-20001, 'REGISTRY_ACTIVE_TRANSACTION: no changes attempted.');
  schema_error EXCEPTION (-20002, 'REGISTRY_SCHEMA_CONFLICT: inspect original/new column names, types and nullability.');
  path_error EXCEPTION (-20003, 'REGISTRY_PATH_OR_IDENTITY_CONFLICT: missing/duplicate/inactive path or old hierarchy contract differs.');
  metadata_conflict EXCEPTION (-20004, 'REGISTRY_METADATA_CONFLICT: non-null metadata differs; review instead of overwriting.');
  baseline_changed EXCEPTION (-20005, 'REGISTRY_BASELINE_CHANGED: original registry rows changed during migration.');
  verification_error EXCEPTION (-20006, 'REGISTRY_METADATA_VERIFICATION_FAILED.');
  commit_unknown EXCEPTION (-20007, 'REGISTRY_COMMIT_OUTCOME_UNKNOWN: inspect before retry; DDL remains.');
  rollback_unknown EXCEPTION (-20008, 'REGISTRY_ROLLBACK_OUTCOME_UNKNOWN: inspect before retry; DDL remains.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE already_active; END IF;

  -- Validate ORIGINAL columns, without changing their types/defaults/constraints.
  WITH expected(name, family) AS (
    SELECT * FROM VALUES
      ('OSCAL_MODEL_KEY','TEXT'), ('NODE_PATH','TEXT'), ('ELEMENT_TYPE','TEXT'),
      ('PARENT_NODE_PATH','TEXT'), ('IS_COLLECTION','BOOLEAN'),
      ('INSTANCE_KEY_RULE','TEXT'), ('PROCESS_ORDER','NUMBER'),
      ('IS_ACTIVE','BOOLEAN'), ('ITEM_PATH','TEXT')
  )
  SELECT COUNT(*) INTO :n FROM expected e LEFT JOIN RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
    ON c.TABLE_SCHEMA='ES_ESC_GRC' AND c.TABLE_NAME='OSCAL_ELEMENT_REGISTRY' AND c.COLUMN_NAME=e.name
  WHERE c.COLUMN_NAME IS NULL OR c.DATA_TYPE<>e.family
     OR (e.family='NUMBER' AND COALESCE(c.NUMERIC_SCALE,-1)<>0);
  IF (n<>0) THEN RAISE schema_error; END IF;

  -- Reject case-only collisions instead of creating a second similarly named column.
  SELECT COUNT(*) INTO :n FROM TABLE(FLATTEN(INPUT=>:column_specs)) x
  JOIN RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
    ON c.TABLE_SCHEMA='ES_ESC_GRC' AND c.TABLE_NAME='OSCAL_ELEMENT_REGISTRY'
   AND UPPER(c.COLUMN_NAME)=x.value:NAME::VARCHAR
  WHERE c.COLUMN_NAME<>x.value:NAME::VARCHAR;
  IF (n<>0) THEN RAISE schema_error; END IF;

  -- Existing metadata columns must be compatible. No silently changed old types.
  SELECT COUNT(*) INTO :n
  FROM TABLE(FLATTEN(INPUT=>:column_specs)) x
  JOIN RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
    ON c.TABLE_SCHEMA='ES_ESC_GRC' AND c.TABLE_NAME='OSCAL_ELEMENT_REGISTRY'
   AND c.COLUMN_NAME=x.value:NAME::VARCHAR
  WHERE c.IS_NULLABLE<>'YES'
     OR c.DATA_TYPE<>CASE x.value:TYPE::VARCHAR WHEN 'VARCHAR' THEN 'TEXT'
          WHEN 'NUMBER(1,0)' THEN 'NUMBER' ELSE 'BOOLEAN' END
     OR (x.value:TYPE::VARCHAR='NUMBER(1,0)' AND (c.NUMERIC_SCALE<>0 OR c.NUMERIC_PRECISION<1));
  IF (n<>0) THEN RAISE schema_error; END IF;

  -- BEGIN EXPLICIT SEED: model, existing path, retained metadata, ORIGINAL contract.
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT('MODEL',model,'PATH',path,
    'META',OBJECT_CONSTRUCT_KEEP_NULL('OPERATOR',operator_name,
      'UUID_POLICY',uuid_policy,'REQUIRED_MEMBERS',required_members),
    'EXPECTED',PARSE_JSON(expected)))
    INTO :seed FROM VALUES
    ('SSP','system-security-plan','object','omit',NULL,
      '{"parent_path":null,"is_collection":false}'),
    ('SSP','system-security-plan.metadata','object','omit',NULL,
      '{"parent_path":"system-security-plan","is_collection":false}'),
    ('SSP','system-security-plan.metadata.document-ids[]','object','omit',NULL,
      '{"parent_path":"system-security-plan.metadata","is_collection":true,"instance_key_rule":"VALUE","item_path":"$"}'),
    ('SSP','system-security-plan.metadata.roles[]','roles','omit',NULL,
      '{"parent_path":"system-security-plan.metadata","is_collection":true,"instance_key_rule":"SOURCE_FIELD_NAME","item_path":"$"}'),
    ('SSP','system-security-plan.metadata.parties[]','parties','instance',NULL,
      '{"parent_path":"system-security-plan.metadata","is_collection":true,"instance_key_rule":"ID","item_path":"UserList[]"}'),
    ('SSP','system-security-plan.metadata.responsible-parties[]','assignments','omit',NULL,
      '{"parent_path":"system-security-plan.metadata","is_collection":true,"instance_key_rule":"SOURCE_FIELD_NAME+ID","item_path":"UserList[]"}'),
    ('SSP','system-security-plan.system-characteristics','object','omit',NULL,
      '{"parent_path":"system-security-plan","is_collection":false}'),
    ('SSP','system-security-plan.system-characteristics.props[]','properties','omit',NULL,
      '{"parent_path":"system-security-plan.system-characteristics","is_collection":true,"instance_key_rule":"SOURCE_FIELD_NAME+VALUE","item_path":"$"}'),
    ('SSP','system-security-plan.system-characteristics.system-ids[]','values','omit',NULL,
      '{"parent_path":"system-security-plan.system-characteristics","is_collection":true,"instance_key_rule":"VALUE","item_path":"$"}'),
    ('SSP','system-security-plan.system-characteristics.security-impact-level','object','omit',
      'security-objective-confidentiality|security-objective-integrity|security-objective-availability',
      '{"parent_path":"system-security-plan.system-characteristics","is_collection":false}'),
    ('SSP','system-security-plan.system-characteristics.status','object','omit',NULL,
      '{"parent_path":"system-security-plan.system-characteristics","is_collection":false}'),
    ('SSP','system-security-plan.system-implementation.components[]','references','node',NULL,
      '{"parent_path":"system-security-plan.system-implementation","is_collection":true,"instance_key_rule":"CONTENT_ID","item_path":"$"}'),
    ('ASSESSMENT_RESULTS','assessment-results','object','node',NULL,
      '{"parent_path":null,"is_collection":false}'),
    ('ASSESSMENT_RESULTS','assessment-results.results[]','record','node',NULL,
      '{"parent_path":"assessment-results","is_collection":true,"instance_key_rule":"SOURCE_RECORD_ID","item_path":null}'),
    ('ASSESSMENT_RESULTS','assessment-results.results[].observations[]','observations','node',NULL,
      '{"parent_path":"assessment-results.results[]","is_collection":true,"instance_key_rule":"SOURCE_FIELD_NAME","item_path":null}')
    AS seed_rows(model,path,operator_name,uuid_policy,required_members,expected);
  -- END EXPLICIT SEED

  -- NULL/blank active keys cannot survive the desired/verification equality joins.
  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE IS_ACTIVE AND UPPER(TRIM(OSCAL_MODEL_KEY)) IN ('SSP','ASSESSMENT_RESULTS')
    AND NULLIF(TRIM(NODE_PATH),'') IS NULL;
  IF (n<>0) THEN RAISE path_error; END IF;

  -- Ambiguous keys cannot be updated, even if one duplicate happens to be inactive.
  SELECT COUNT(*) INTO :n FROM (
    SELECT UPPER(TRIM(OSCAL_MODEL_KEY)), TRIM(NODE_PATH)
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) IN ('SSP','ASSESSMENT_RESULTS')
    GROUP BY 1,2 HAVING COUNT(*)<>1 OR COUNT_IF(IS_ACTIVE IS NULL)>0
  );
  IF (n<>0) THEN RAISE path_error; END IF;

  -- Every explicit accepted path already exists and matches its old contract.
  WITH r AS (
    SELECT UPPER(TRIM(OSCAL_MODEL_KEY)) model, TRIM(NODE_PATH) path,
      OBJECT_CONSTRUCT_KEEP_NULL('parent_path',NULLIF(TRIM(PARENT_NODE_PATH),''),
        'is_collection',IS_COLLECTION,'instance_key_rule',NULLIF(TRIM(INSTANCE_KEY_RULE),''),
        'item_path',NULLIF(TRIM(ITEM_PATH),'')) contract
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY WHERE IS_ACTIVE
  )
  SELECT COUNT(*) INTO :n FROM TABLE(FLATTEN(INPUT=>:seed)) s
  LEFT JOIN r ON r.model=s.value:MODEL::VARCHAR AND r.path=s.value:PATH::VARCHAR,
  LATERAL FLATTEN(INPUT=>s.value:EXPECTED) k
  WHERE r.path IS NULL OR GET(r.contract,k.key) IS DISTINCT FROM k.value;
  IF (n<>0) THEN RAISE path_error; END IF;

  -- Resolve ALL active selected-model paths. Preserve the old SSP default only:
  -- non-collections whose literal path has no collection ancestor. A non-null
  -- OPERATOR marks a retained executable path; unlisted collections/descendants
  -- receive no explicit override, and AR remains the exact three-path whitelist.
  WITH explicit AS (SELECT value s FROM TABLE(FLATTEN(INPUT=>:seed))),
  r AS (SELECT * FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
        WHERE IS_ACTIVE AND UPPER(TRIM(OSCAL_MODEL_KEY)) IN ('SSP','ASSESSMENT_RESULTS'))
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT('MODEL',UPPER(TRIM(r.OSCAL_MODEL_KEY)),
    'PATH',TRIM(r.NODE_PATH),'META',
    CASE WHEN s.s IS NOT NULL THEN s.s:META
      WHEN UPPER(TRIM(r.OSCAL_MODEL_KEY))='SSP' AND NOT r.IS_COLLECTION
        AND POSITION('[]' IN r.NODE_PATH)=0 THEN
          OBJECT_CONSTRUCT_KEEP_NULL('OPERATOR','object','UUID_POLICY','omit','REQUIRED_MEMBERS',NULL)
      ELSE OBJECT_CONSTRUCT_KEEP_NULL('OPERATOR',NULL,'UUID_POLICY',NULL,'REQUIRED_MEMBERS',NULL) END))
  INTO :desired FROM r LEFT JOIN explicit s
    ON UPPER(TRIM(r.OSCAL_MODEL_KEY))=s.s:MODEL::VARCHAR AND TRIM(r.NODE_PATH)=s.s:PATH::VARCHAR;

  -- Retained executable paths have a retained parent, except for existing roots.
  -- Match the decoder's strict ancestry/root rules; membership alone allows cycles.
  WITH d AS (SELECT value x,
    IFF(value:MODEL::VARCHAR='SSP','system-security-plan','assessment-results') root_path
    FROM TABLE(FLATTEN(INPUT=>:desired)))
  SELECT COUNT(*) INTO :n FROM d
  JOIN RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r
    ON UPPER(TRIM(r.OSCAL_MODEL_KEY))=d.x:MODEL::VARCHAR AND TRIM(r.NODE_PATH)=d.x:PATH::VARCHAR
  LEFT JOIN d p ON p.x:MODEL=d.x:MODEL AND p.x:PATH::VARCHAR=NULLIF(TRIM(r.PARENT_NODE_PATH),'')
  WHERE d.x:META:OPERATOR::VARCHAR IS NOT NULL AND
    (r.IS_COLLECTION IS NULL OR r.ELEMENT_TYPE IS NULL OR r.PROCESS_ORDER IS NULL
     OR r.IS_COLLECTION IS DISTINCT FROM ENDSWITH(d.x:PATH::VARCHAR,'[]')
     OR (NULLIF(TRIM(r.PARENT_NODE_PATH),'') IS NOT NULL
         AND (p.x:META:OPERATOR::VARCHAR IS NULL
              OR NOT COALESCE(STARTSWITH(d.x:PATH::VARCHAR,
                NULLIF(TRIM(r.PARENT_NODE_PATH),'') || '.'),FALSE)))
     OR (NULLIF(TRIM(r.PARENT_NODE_PATH),'') IS NULL
         AND d.x:PATH::VARCHAR IS DISTINCT FROM d.root_path)
     OR NOT COALESCE(d.x:PATH::VARCHAR=d.root_path
                    OR STARTSWITH(d.x:PATH::VARCHAR,d.root_path || '.'),FALSE));
  IF (n<>0) THEN RAISE path_error; END IF;

  -- Capture all original rows (including other models) for unchanged-row verification.
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT_KEEP_NULL('OSCAL_MODEL_KEY', r."OSCAL_MODEL_KEY", 'NODE_PATH', r."NODE_PATH", 'ELEMENT_TYPE', r."ELEMENT_TYPE", 'PARENT_NODE_PATH', r."PARENT_NODE_PATH", 'IS_COLLECTION', r."IS_COLLECTION", 'INSTANCE_KEY_RULE', r."INSTANCE_KEY_RULE", 'PROCESS_ORDER', r."PROCESS_ORDER", 'IS_ACTIVE', r."IS_ACTIVE", 'ITEM_PATH', r."ITEM_PATH")) INTO :baseline FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r;
  -- Dynamic SQL transports semi-structured binds as JSON text; decode in each template.
  desired_json := TO_JSON(TO_VARIANT(desired));
  baseline_json := TO_JSON(TO_VARIANT(baseline));
  result_rows := (EXECUTE IMMEDIATE :conflict_sql USING (desired_json));
  FOR migration_row IN result_rows DO n := migration_row.N; END FOR;
  IF (n<>0) THEN RAISE metadata_conflict; END IF;

  -- Existing VARCHAR capacity must fit each expected metadata value.
  SELECT COUNT(*) INTO :n FROM TABLE(FLATTEN(INPUT=>:desired)) d,
    LATERAL FLATTEN(INPUT=>d.value:META) m,
    RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
  WHERE c.TABLE_SCHEMA='ES_ESC_GRC' AND c.TABLE_NAME='OSCAL_ELEMENT_REGISTRY'
    AND c.COLUMN_NAME=m.key AND c.DATA_TYPE='TEXT'
    AND LENGTH(m.value::VARCHAR)>c.CHARACTER_MAXIMUM_LENGTH;
  IF (n<>0) THEN RAISE schema_error; END IF;

  -- DDL PHASE: outside any transaction. Do not claim rollback of these additions.
  result_rows := (SELECT value:NAME::VARCHAR name, value:TYPE::VARCHAR type
                  FROM TABLE(FLATTEN(INPUT=>:column_specs)) ORDER BY INDEX);
  FOR migration_row IN result_rows DO
    statement := 'ALTER TABLE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY ADD COLUMN IF NOT EXISTS "' ||
                 migration_row.NAME || '" ' || migration_row.TYPE;
    EXECUTE IMMEDIATE :statement;
  END FOR;

  -- UPDATE PHASE: one explicit transaction, no DDL inside it.
  BEGIN TRANSACTION;
  transaction_started := TRUE;
  result_rows := (EXECUTE IMMEDIATE :baseline_sql USING (baseline_json));
  FOR migration_row IN result_rows DO n := migration_row.N; END FOR;
  IF (n<>0) THEN RAISE baseline_changed; END IF;
  result_rows := (EXECUTE IMMEDIATE :conflict_sql USING (desired_json));
  FOR migration_row IN result_rows DO n := migration_row.N; END FOR;
  IF (n<>0) THEN RAISE metadata_conflict; END IF;

  -- UPDATE itself refuses conflicting non-null cells, including concurrent changes.
  -- Read the executed UPDATE's result, not SQLROWCOUNT across dynamic execution.
  result_rows := (EXECUTE IMMEDIATE :update_sql USING (desired_json));
  n := 0;
  changed_rows := NULL;
  FOR migration_row IN result_rows DO
    n := n + 1;
    changed_rows := migration_row."number of rows updated";
  END FOR;
  IF (n<>1 OR changed_rows IS NULL OR changed_rows<0
      OR changed_rows>ARRAY_SIZE(desired)) THEN RAISE verification_error; END IF;
  result_rows := (EXECUTE IMMEDIATE :verify_sql USING (desired_json));
  FOR migration_row IN result_rows DO n := migration_row.N; END FOR;
  IF (n<>0) THEN RAISE verification_error; END IF;
  result_rows := (EXECUTE IMMEDIATE :baseline_sql USING (baseline_json));
  FOR migration_row IN result_rows DO n := migration_row.N; END FOR;
  IF (n<>0) THEN RAISE baseline_changed; END IF;

  commit_attempted := TRUE;
  COMMIT;
  transaction_started := FALSE;
  RETURN OBJECT_CONSTRUCT('STATUS','REGISTRY_METADATA_VERIFIED',
    'TARGET','RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY',
    'UPDATED_ROWS',changed_rows,'TARGETED_ACTIVE_ROWS',ARRAY_SIZE(desired),
    'ORIGINAL_COLUMNS_UNCHANGED',TRUE,'DDL_ROLLBACK_AVAILABLE',FALSE);
EXCEPTION
  WHEN OTHER THEN
    IF (commit_attempted) THEN RAISE commit_unknown; END IF;
    IF (transaction_started) THEN
      BEGIN
        ROLLBACK;
      EXCEPTION WHEN OTHER THEN RAISE rollback_unknown;
      END;
    END IF;
    RAISE;
END;
$$;

