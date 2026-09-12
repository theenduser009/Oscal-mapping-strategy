-- ONE-TIME DEV REGISTRY STRUCTURAL METADATA MIGRATION. Run the whole file as SQL.
-- Prepared migration, NOT evidence of a live run. Schedule without other registry writers.
-- Only existing active SSP / ASSESSMENT_RESULTS rows receive new metadata.
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
--
-- Seed provenance: tests/fixtures/mapper_contract_pre_registry.json (accepted
-- structure plus recorded 2026-09-09 collection/setup identity contracts, frozen before removing the production JSON dependency). Field rules
-- remain in Mapping/ARCHER_OSCAL_MAPPINGS.csv, not in this structural seed.

EXECUTE IMMEDIATE $$
DECLARE
  seed ARRAY;
  desired ARRAY;
  baseline ARRAY;
  column_specs ARRAY DEFAULT PARSE_JSON('[{"NAME":"MAPPER_METADATA_VERSION","TYPE":"NUMBER(1,0)"},{"NAME":"MAPPER_ENABLED","TYPE":"BOOLEAN"},{"NAME":"OPERATOR","TYPE":"VARCHAR"},{"NAME":"PARENT_INSTANCE_RULE","TYPE":"VARCHAR"},{"NAME":"UUID_POLICY","TYPE":"VARCHAR"},{"NAME":"EMPTY_POLICY","TYPE":"VARCHAR"},{"NAME":"LIST_INSTANCE_RULE","TYPE":"VARCHAR"},{"NAME":"PROPERTY_NAME_RULE","TYPE":"VARCHAR"},{"NAME":"ASSEMBLY_POLICY","TYPE":"VARCHAR"},{"NAME":"REQUIRED_MEMBERS","TYPE":"VARCHAR"},{"NAME":"DEFAULT_SINGLETON_POLICY","TYPE":"VARCHAR"},{"NAME":"REQUIRED_RULE_IDS","TYPE":"VARCHAR"},{"NAME":"ROLES_PATH","TYPE":"VARCHAR"},{"NAME":"PARTIES_PATH","TYPE":"VARCHAR"},{"NAME":"PARTY_TYPE","TYPE":"VARCHAR"},{"NAME":"PARTY_UUID_PARTS","TYPE":"VARCHAR"},{"NAME":"PARTY_UUID_SOURCE_KEY","TYPE":"VARCHAR"},{"NAME":"REPORT_TARGET_PATH","TYPE":"VARCHAR"}]')::ARRAY;
  result_rows RESULTSET;
  statement VARCHAR;
  conflict_sql VARCHAR DEFAULT 'WITH desired AS (SELECT value d FROM TABLE(FLATTEN(INPUT => ?))),
current_rows AS (SELECT UPPER(TRIM(OSCAL_MODEL_KEY)) model, TRIM(NODE_PATH) path,
OBJECT_CONSTRUCT_KEEP_NULL(r.*) present FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r WHERE IS_ACTIVE)
SELECT COUNT(*) N FROM desired d JOIN current_rows r
ON r.model=d.d:MODEL::VARCHAR AND r.path=d.d:PATH::VARCHAR,
LATERAL FLATTEN(INPUT=>d.d:META) k
WHERE NOT COALESCE(IS_NULL_VALUE(GET(r.present,k.key)),TRUE)
AND GET(r.present,k.key) IS DISTINCT FROM k.value';
  baseline_sql VARCHAR DEFAULT 'WITH expected AS (SELECT value row_value, COUNT(*) n FROM TABLE(FLATTEN(INPUT=>?)) GROUP BY value),
actual AS (SELECT OBJECT_CONSTRUCT_KEEP_NULL(''OSCAL_MODEL_KEY'', r."OSCAL_MODEL_KEY", ''NODE_PATH'', r."NODE_PATH", ''ELEMENT_TYPE'', r."ELEMENT_TYPE", ''PARENT_NODE_PATH'', r."PARENT_NODE_PATH", ''IS_COLLECTION'', r."IS_COLLECTION", ''INSTANCE_KEY_RULE'', r."INSTANCE_KEY_RULE", ''PROCESS_ORDER'', r."PROCESS_ORDER", ''IS_ACTIVE'', r."IS_ACTIVE", ''ITEM_PATH'', r."ITEM_PATH") row_value, COUNT(*) n FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r GROUP BY row_value)
SELECT COUNT(*) N FROM expected e FULL OUTER JOIN actual a ON e.row_value=a.row_value
WHERE e.n IS DISTINCT FROM a.n';
  update_sql VARCHAR DEFAULT 'UPDATE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY SET
  "MAPPER_METADATA_VERSION" = IFF(IS_NULL_VALUE(d.meta:MAPPER_METADATA_VERSION),NULL,d.meta:MAPPER_METADATA_VERSION::NUMBER(1,0)),
  "MAPPER_ENABLED" = IFF(IS_NULL_VALUE(d.meta:MAPPER_ENABLED),NULL,d.meta:MAPPER_ENABLED::BOOLEAN),
  "OPERATOR" = IFF(IS_NULL_VALUE(d.meta:OPERATOR),NULL,d.meta:OPERATOR::VARCHAR),
  "PARENT_INSTANCE_RULE" = IFF(IS_NULL_VALUE(d.meta:PARENT_INSTANCE_RULE),NULL,d.meta:PARENT_INSTANCE_RULE::VARCHAR),
  "UUID_POLICY" = IFF(IS_NULL_VALUE(d.meta:UUID_POLICY),NULL,d.meta:UUID_POLICY::VARCHAR),
  "EMPTY_POLICY" = IFF(IS_NULL_VALUE(d.meta:EMPTY_POLICY),NULL,d.meta:EMPTY_POLICY::VARCHAR),
  "LIST_INSTANCE_RULE" = IFF(IS_NULL_VALUE(d.meta:LIST_INSTANCE_RULE),NULL,d.meta:LIST_INSTANCE_RULE::VARCHAR),
  "PROPERTY_NAME_RULE" = IFF(IS_NULL_VALUE(d.meta:PROPERTY_NAME_RULE),NULL,d.meta:PROPERTY_NAME_RULE::VARCHAR),
  "ASSEMBLY_POLICY" = IFF(IS_NULL_VALUE(d.meta:ASSEMBLY_POLICY),NULL,d.meta:ASSEMBLY_POLICY::VARCHAR),
  "REQUIRED_MEMBERS" = IFF(IS_NULL_VALUE(d.meta:REQUIRED_MEMBERS),NULL,d.meta:REQUIRED_MEMBERS::VARCHAR),
  "DEFAULT_SINGLETON_POLICY" = IFF(IS_NULL_VALUE(d.meta:DEFAULT_SINGLETON_POLICY),NULL,d.meta:DEFAULT_SINGLETON_POLICY::VARCHAR),
  "REQUIRED_RULE_IDS" = IFF(IS_NULL_VALUE(d.meta:REQUIRED_RULE_IDS),NULL,d.meta:REQUIRED_RULE_IDS::VARCHAR),
  "ROLES_PATH" = IFF(IS_NULL_VALUE(d.meta:ROLES_PATH),NULL,d.meta:ROLES_PATH::VARCHAR),
  "PARTIES_PATH" = IFF(IS_NULL_VALUE(d.meta:PARTIES_PATH),NULL,d.meta:PARTIES_PATH::VARCHAR),
  "PARTY_TYPE" = IFF(IS_NULL_VALUE(d.meta:PARTY_TYPE),NULL,d.meta:PARTY_TYPE::VARCHAR),
  "PARTY_UUID_PARTS" = IFF(IS_NULL_VALUE(d.meta:PARTY_UUID_PARTS),NULL,d.meta:PARTY_UUID_PARTS::VARCHAR),
  "PARTY_UUID_SOURCE_KEY" = IFF(IS_NULL_VALUE(d.meta:PARTY_UUID_SOURCE_KEY),NULL,d.meta:PARTY_UUID_SOURCE_KEY::VARCHAR),
  "REPORT_TARGET_PATH" = IFF(IS_NULL_VALUE(d.meta:REPORT_TARGET_PATH),NULL,d.meta:REPORT_TARGET_PATH::VARCHAR)
FROM (SELECT value:MODEL::VARCHAR model, value:PATH::VARCHAR path, value:META meta FROM TABLE(FLATTEN(INPUT=>?))) d
WHERE UPPER(TRIM(OSCAL_MODEL_KEY))=d.model AND TRIM(NODE_PATH)=d.path AND IS_ACTIVE
AND ("MAPPER_METADATA_VERSION" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:MAPPER_METADATA_VERSION),NULL,d.meta:MAPPER_METADATA_VERSION::NUMBER(1,0))
  OR "MAPPER_ENABLED" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:MAPPER_ENABLED),NULL,d.meta:MAPPER_ENABLED::BOOLEAN)
  OR "OPERATOR" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:OPERATOR),NULL,d.meta:OPERATOR::VARCHAR)
  OR "PARENT_INSTANCE_RULE" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARENT_INSTANCE_RULE),NULL,d.meta:PARENT_INSTANCE_RULE::VARCHAR)
  OR "UUID_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:UUID_POLICY),NULL,d.meta:UUID_POLICY::VARCHAR)
  OR "EMPTY_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:EMPTY_POLICY),NULL,d.meta:EMPTY_POLICY::VARCHAR)
  OR "LIST_INSTANCE_RULE" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:LIST_INSTANCE_RULE),NULL,d.meta:LIST_INSTANCE_RULE::VARCHAR)
  OR "PROPERTY_NAME_RULE" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PROPERTY_NAME_RULE),NULL,d.meta:PROPERTY_NAME_RULE::VARCHAR)
  OR "ASSEMBLY_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:ASSEMBLY_POLICY),NULL,d.meta:ASSEMBLY_POLICY::VARCHAR)
  OR "REQUIRED_MEMBERS" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_MEMBERS),NULL,d.meta:REQUIRED_MEMBERS::VARCHAR)
  OR "DEFAULT_SINGLETON_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:DEFAULT_SINGLETON_POLICY),NULL,d.meta:DEFAULT_SINGLETON_POLICY::VARCHAR)
  OR "REQUIRED_RULE_IDS" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_RULE_IDS),NULL,d.meta:REQUIRED_RULE_IDS::VARCHAR)
  OR "ROLES_PATH" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:ROLES_PATH),NULL,d.meta:ROLES_PATH::VARCHAR)
  OR "PARTIES_PATH" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTIES_PATH),NULL,d.meta:PARTIES_PATH::VARCHAR)
  OR "PARTY_TYPE" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_TYPE),NULL,d.meta:PARTY_TYPE::VARCHAR)
  OR "PARTY_UUID_PARTS" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_UUID_PARTS),NULL,d.meta:PARTY_UUID_PARTS::VARCHAR)
  OR "PARTY_UUID_SOURCE_KEY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_UUID_SOURCE_KEY),NULL,d.meta:PARTY_UUID_SOURCE_KEY::VARCHAR)
  OR "REPORT_TARGET_PATH" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REPORT_TARGET_PATH),NULL,d.meta:REPORT_TARGET_PATH::VARCHAR))
AND (("MAPPER_METADATA_VERSION" IS NULL OR "MAPPER_METADATA_VERSION" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:MAPPER_METADATA_VERSION),NULL,d.meta:MAPPER_METADATA_VERSION::NUMBER(1,0)))
  AND ("MAPPER_ENABLED" IS NULL OR "MAPPER_ENABLED" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:MAPPER_ENABLED),NULL,d.meta:MAPPER_ENABLED::BOOLEAN))
  AND ("OPERATOR" IS NULL OR "OPERATOR" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:OPERATOR),NULL,d.meta:OPERATOR::VARCHAR))
  AND ("PARENT_INSTANCE_RULE" IS NULL OR "PARENT_INSTANCE_RULE" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARENT_INSTANCE_RULE),NULL,d.meta:PARENT_INSTANCE_RULE::VARCHAR))
  AND ("UUID_POLICY" IS NULL OR "UUID_POLICY" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:UUID_POLICY),NULL,d.meta:UUID_POLICY::VARCHAR))
  AND ("EMPTY_POLICY" IS NULL OR "EMPTY_POLICY" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:EMPTY_POLICY),NULL,d.meta:EMPTY_POLICY::VARCHAR))
  AND ("LIST_INSTANCE_RULE" IS NULL OR "LIST_INSTANCE_RULE" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:LIST_INSTANCE_RULE),NULL,d.meta:LIST_INSTANCE_RULE::VARCHAR))
  AND ("PROPERTY_NAME_RULE" IS NULL OR "PROPERTY_NAME_RULE" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PROPERTY_NAME_RULE),NULL,d.meta:PROPERTY_NAME_RULE::VARCHAR))
  AND ("ASSEMBLY_POLICY" IS NULL OR "ASSEMBLY_POLICY" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:ASSEMBLY_POLICY),NULL,d.meta:ASSEMBLY_POLICY::VARCHAR))
  AND ("REQUIRED_MEMBERS" IS NULL OR "REQUIRED_MEMBERS" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_MEMBERS),NULL,d.meta:REQUIRED_MEMBERS::VARCHAR))
  AND ("DEFAULT_SINGLETON_POLICY" IS NULL OR "DEFAULT_SINGLETON_POLICY" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:DEFAULT_SINGLETON_POLICY),NULL,d.meta:DEFAULT_SINGLETON_POLICY::VARCHAR))
  AND ("REQUIRED_RULE_IDS" IS NULL OR "REQUIRED_RULE_IDS" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_RULE_IDS),NULL,d.meta:REQUIRED_RULE_IDS::VARCHAR))
  AND ("ROLES_PATH" IS NULL OR "ROLES_PATH" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:ROLES_PATH),NULL,d.meta:ROLES_PATH::VARCHAR))
  AND ("PARTIES_PATH" IS NULL OR "PARTIES_PATH" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTIES_PATH),NULL,d.meta:PARTIES_PATH::VARCHAR))
  AND ("PARTY_TYPE" IS NULL OR "PARTY_TYPE" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_TYPE),NULL,d.meta:PARTY_TYPE::VARCHAR))
  AND ("PARTY_UUID_PARTS" IS NULL OR "PARTY_UUID_PARTS" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_UUID_PARTS),NULL,d.meta:PARTY_UUID_PARTS::VARCHAR))
  AND ("PARTY_UUID_SOURCE_KEY" IS NULL OR "PARTY_UUID_SOURCE_KEY" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_UUID_SOURCE_KEY),NULL,d.meta:PARTY_UUID_SOURCE_KEY::VARCHAR))
  AND ("REPORT_TARGET_PATH" IS NULL OR "REPORT_TARGET_PATH" IS NOT DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REPORT_TARGET_PATH),NULL,d.meta:REPORT_TARGET_PATH::VARCHAR)))';
  verify_sql VARCHAR DEFAULT 'SELECT COUNT(*) N FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r JOIN (SELECT value:MODEL::VARCHAR model, value:PATH::VARCHAR path, value:META meta FROM TABLE(FLATTEN(INPUT=>?))) d
ON UPPER(TRIM(r.OSCAL_MODEL_KEY))=d.model AND TRIM(r.NODE_PATH)=d.path AND r.IS_ACTIVE
WHERE r."MAPPER_METADATA_VERSION" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:MAPPER_METADATA_VERSION),NULL,d.meta:MAPPER_METADATA_VERSION::NUMBER(1,0))
  OR r."MAPPER_ENABLED" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:MAPPER_ENABLED),NULL,d.meta:MAPPER_ENABLED::BOOLEAN)
  OR r."OPERATOR" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:OPERATOR),NULL,d.meta:OPERATOR::VARCHAR)
  OR r."PARENT_INSTANCE_RULE" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARENT_INSTANCE_RULE),NULL,d.meta:PARENT_INSTANCE_RULE::VARCHAR)
  OR r."UUID_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:UUID_POLICY),NULL,d.meta:UUID_POLICY::VARCHAR)
  OR r."EMPTY_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:EMPTY_POLICY),NULL,d.meta:EMPTY_POLICY::VARCHAR)
  OR r."LIST_INSTANCE_RULE" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:LIST_INSTANCE_RULE),NULL,d.meta:LIST_INSTANCE_RULE::VARCHAR)
  OR r."PROPERTY_NAME_RULE" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PROPERTY_NAME_RULE),NULL,d.meta:PROPERTY_NAME_RULE::VARCHAR)
  OR r."ASSEMBLY_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:ASSEMBLY_POLICY),NULL,d.meta:ASSEMBLY_POLICY::VARCHAR)
  OR r."REQUIRED_MEMBERS" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_MEMBERS),NULL,d.meta:REQUIRED_MEMBERS::VARCHAR)
  OR r."DEFAULT_SINGLETON_POLICY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:DEFAULT_SINGLETON_POLICY),NULL,d.meta:DEFAULT_SINGLETON_POLICY::VARCHAR)
  OR r."REQUIRED_RULE_IDS" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REQUIRED_RULE_IDS),NULL,d.meta:REQUIRED_RULE_IDS::VARCHAR)
  OR r."ROLES_PATH" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:ROLES_PATH),NULL,d.meta:ROLES_PATH::VARCHAR)
  OR r."PARTIES_PATH" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTIES_PATH),NULL,d.meta:PARTIES_PATH::VARCHAR)
  OR r."PARTY_TYPE" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_TYPE),NULL,d.meta:PARTY_TYPE::VARCHAR)
  OR r."PARTY_UUID_PARTS" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_UUID_PARTS),NULL,d.meta:PARTY_UUID_PARTS::VARCHAR)
  OR r."PARTY_UUID_SOURCE_KEY" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:PARTY_UUID_SOURCE_KEY),NULL,d.meta:PARTY_UUID_SOURCE_KEY::VARCHAR)
  OR r."REPORT_TARGET_PATH" IS DISTINCT FROM IFF(IS_NULL_VALUE(d.meta:REPORT_TARGET_PATH),NULL,d.meta:REPORT_TARGET_PATH::VARCHAR)';
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

  -- BEGIN EXPLICIT SEED: model, existing path, new metadata, ORIGINAL contract.
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT('MODEL',model,'PATH',path,
                                  'META',PARSE_JSON(metadata),'EXPECTED',PARSE_JSON(expected)))
    INTO :seed FROM VALUES
    ('SSP', 'system-security-plan',
     '{"MAPPER_METADATA_VERSION":1,"MAPPER_ENABLED":true,"OPERATOR":"object","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"emit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":"emit-outside-collections","REQUIRED_RULE_IDS":"support:metadata-title|support:oscal-version|support:document-version","ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":null,"is_collection":false}'),
    ('SSP', 'system-security-plan.metadata',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"object","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"emit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan","is_collection":false}'),
    ('SSP', 'system-security-plan.metadata.document-ids[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"object","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"source-field-index","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.metadata","is_collection":true,"instance_key_rule":"VALUE","item_path":"$"}'),
    ('SSP', 'system-security-plan.metadata.roles[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"roles","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.metadata","is_collection":true,"instance_key_rule":"SOURCE_FIELD_NAME","item_path":"$"}'),
    ('SSP', 'system-security-plan.metadata.parties[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"parties","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"instance","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.metadata","is_collection":true,"instance_key_rule":"ID","item_path":"UserList[]"}'),
    ('SSP', 'system-security-plan.metadata.responsible-parties[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"assignments","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":"system-security-plan.metadata.roles[]","PARTIES_PATH":"system-security-plan.metadata.parties[]","PARTY_TYPE":"person","PARTY_UUID_PARTS":"$source_system|$source_record|party|$reference_id","PARTY_UUID_SOURCE_KEY":"source-one","REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.metadata","is_collection":true,"instance_key_rule":"SOURCE_FIELD_NAME+ID","item_path":"UserList[]"}'),
    ('SSP', 'system-security-plan.system-characteristics',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"object","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"emit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan","is_collection":false}'),
    ('SSP', 'system-security-plan.system-characteristics.props[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"properties","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":"source-field-slug","ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.system-characteristics","is_collection":true,"instance_key_rule":"SOURCE_FIELD_NAME+VALUE","item_path":"$"}'),
    ('SSP', 'system-security-plan.system-characteristics.system-ids[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"values","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.system-characteristics","is_collection":true,"instance_key_rule":"VALUE","item_path":"$"}'),
    ('SSP', 'system-security-plan.system-characteristics.security-impact-level',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"object","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"complete-only","REQUIRED_MEMBERS":"security-objective-confidentiality|security-objective-integrity|security-objective-availability","DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.system-characteristics","is_collection":false}'),
    ('SSP', 'system-security-plan.system-characteristics.status',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"object","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"emit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.system-characteristics","is_collection":false}'),
    ('SSP', 'system-security-plan.system-implementation.components[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"references","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"node","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"system-security-plan.system-implementation","is_collection":true,"instance_key_rule":"CONTENT_ID","item_path":"$"}'),
    ('ASSESSMENT_RESULTS', 'assessment-results',
     '{"MAPPER_METADATA_VERSION":1,"MAPPER_ENABLED":true,"OPERATOR":"object","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"node","EMPTY_POLICY":"emit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":"none","REQUIRED_RULE_IDS":"ar17:VULNERABILITY_SCORE|ar17:ANTIVIRUS_SCORE|ar17:PATCH_SCORE|ar17:SECURITY_COMPLIANCE_SCORE|ar17:STANDARD_OPERATING_ENVIRONMENT_SCORE|ar17:COMPUTER_PASSWORD_AGE_SCORE|ar17:VULNERABILITY_REPORTING_SCORE|ar17:SECURITY_COMPLIANCE_REPORTING_SCORE|ar17:TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE|ar17:AVG_AUTHORIZATION_PACKAGE_RISK_SCORE|ar17:RISK_SCORE_GRADE|ar17:AVG_VULNERABILITY_SCORE|ar17:AVG_PATCH_SCORE|ar17:AVG_ANTIVIRUS_SCORE|ar17:AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE|ar17:AVG_COMPUTER_PASSWORD_AGE_SCORE|ar17:AVG_VULNERABILITY_REPORTING_SCORE","ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":"assessment-results.results[].observations[]"}',
     '{"parent_path":null,"is_collection":false}'),
    ('ASSESSMENT_RESULTS', 'assessment-results.results[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"record","PARENT_INSTANCE_RULE":"singleton","UUID_POLICY":"node","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"assessment-results","is_collection":true,"instance_key_rule":"SOURCE_RECORD_ID","item_path":null}'),
    ('ASSESSMENT_RESULTS', 'assessment-results.results[].observations[]',
     '{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"observations","PARENT_INSTANCE_RULE":"source-record","UUID_POLICY":"node","EMPTY_POLICY":"omit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":"source-field-slug","ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}',
     '{"parent_path":"assessment-results.results[]","is_collection":true,"instance_key_rule":"SOURCE_FIELD_NAME","item_path":null}')
    AS seed_rows(model,path,metadata,expected);
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
  -- non-collections whose literal path has no collection ancestor. Unlisted
  -- collections / descendants stay false; AR is the exact three-path whitelist.
  WITH explicit AS (SELECT value s FROM TABLE(FLATTEN(INPUT=>:seed))),
  r AS (SELECT * FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
        WHERE IS_ACTIVE AND UPPER(TRIM(OSCAL_MODEL_KEY)) IN ('SSP','ASSESSMENT_RESULTS'))
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT('MODEL',UPPER(TRIM(r.OSCAL_MODEL_KEY)),
    'PATH',TRIM(r.NODE_PATH),'META',
    CASE WHEN s.s IS NOT NULL THEN s.s:META
      WHEN UPPER(TRIM(r.OSCAL_MODEL_KEY))='SSP' AND NOT r.IS_COLLECTION
        AND POSITION('[]' IN r.NODE_PATH)=0 THEN PARSE_JSON('{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":true,"OPERATOR":"object","PARENT_INSTANCE_RULE":"none","UUID_POLICY":"omit","EMPTY_POLICY":"emit","LIST_INSTANCE_RULE":"none","PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":"normal","REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}')
      ELSE PARSE_JSON('{"MAPPER_METADATA_VERSION":null,"MAPPER_ENABLED":false,"OPERATOR":null,"PARENT_INSTANCE_RULE":null,"UUID_POLICY":null,"EMPTY_POLICY":null,"LIST_INSTANCE_RULE":null,"PROPERTY_NAME_RULE":null,"ASSEMBLY_POLICY":null,"REQUIRED_MEMBERS":null,"DEFAULT_SINGLETON_POLICY":null,"REQUIRED_RULE_IDS":null,"ROLES_PATH":null,"PARTIES_PATH":null,"PARTY_TYPE":null,"PARTY_UUID_PARTS":null,"PARTY_UUID_SOURCE_KEY":null,"REPORT_TARGET_PATH":null}') END))
  INTO :desired FROM r LEFT JOIN explicit s
    ON UPPER(TRIM(r.OSCAL_MODEL_KEY))=s.s:MODEL::VARCHAR AND TRIM(r.NODE_PATH)=s.s:PATH::VARCHAR;

  -- Enabled paths have an enabled parent, except for the two existing roots.
  -- Match the decoder's strict ancestry/root rules; membership alone allows cycles.
  WITH d AS (SELECT value x,
    IFF(value:MODEL::VARCHAR='SSP','system-security-plan','assessment-results') root_path
    FROM TABLE(FLATTEN(INPUT=>:desired)))
  SELECT COUNT(*) INTO :n FROM d
  JOIN RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r
    ON UPPER(TRIM(r.OSCAL_MODEL_KEY))=d.x:MODEL::VARCHAR AND TRIM(r.NODE_PATH)=d.x:PATH::VARCHAR
  LEFT JOIN d p ON p.x:MODEL=d.x:MODEL AND p.x:PATH::VARCHAR=NULLIF(TRIM(r.PARENT_NODE_PATH),'')
  WHERE d.x:META:MAPPER_ENABLED::BOOLEAN AND
    (r.IS_COLLECTION IS NULL OR r.ELEMENT_TYPE IS NULL OR r.PROCESS_ORDER IS NULL
     OR r.IS_COLLECTION IS DISTINCT FROM ENDSWITH(d.x:PATH::VARCHAR,'[]')
     OR (NULLIF(TRIM(r.PARENT_NODE_PATH),'') IS NOT NULL
         AND (NOT COALESCE(p.x:META:MAPPER_ENABLED::BOOLEAN,FALSE)
              OR NOT COALESCE(STARTSWITH(d.x:PATH::VARCHAR,
                NULLIF(TRIM(r.PARENT_NODE_PATH),'') || '.'),FALSE)))
     OR (NULLIF(TRIM(r.PARENT_NODE_PATH),'') IS NULL
         AND d.x:PATH::VARCHAR IS DISTINCT FROM d.root_path)
     OR NOT COALESCE(d.x:PATH::VARCHAR=d.root_path
                    OR STARTSWITH(d.x:PATH::VARCHAR,d.root_path || '.'),FALSE));
  IF (n<>0) THEN RAISE path_error; END IF;

  -- Capture all original rows (including other models) for unchanged-row verification.
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT_KEEP_NULL('OSCAL_MODEL_KEY', r."OSCAL_MODEL_KEY", 'NODE_PATH', r."NODE_PATH", 'ELEMENT_TYPE', r."ELEMENT_TYPE", 'PARENT_NODE_PATH', r."PARENT_NODE_PATH", 'IS_COLLECTION', r."IS_COLLECTION", 'INSTANCE_KEY_RULE', r."INSTANCE_KEY_RULE", 'PROCESS_ORDER', r."PROCESS_ORDER", 'IS_ACTIVE', r."IS_ACTIVE", 'ITEM_PATH', r."ITEM_PATH")) INTO :baseline FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r;
  result_rows := (EXECUTE IMMEDIATE :conflict_sql USING (desired));
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
  result_rows := (EXECUTE IMMEDIATE :baseline_sql USING (baseline));
  FOR migration_row IN result_rows DO n := migration_row.N; END FOR;
  IF (n<>0) THEN RAISE baseline_changed; END IF;
  result_rows := (EXECUTE IMMEDIATE :conflict_sql USING (desired));
  FOR migration_row IN result_rows DO n := migration_row.N; END FOR;
  IF (n<>0) THEN RAISE metadata_conflict; END IF;

  -- UPDATE itself refuses conflicting non-null cells, including concurrent changes.
  -- Read the executed UPDATE's result, not SQLROWCOUNT across dynamic execution.
  result_rows := (EXECUTE IMMEDIATE :update_sql USING (desired));
  n := 0;
  changed_rows := NULL;
  FOR migration_row IN result_rows DO
    n := n + 1;
    changed_rows := migration_row."number of rows updated";
  END FOR;
  IF (n<>1 OR changed_rows IS NULL OR changed_rows<0
      OR changed_rows>ARRAY_SIZE(desired)) THEN RAISE verification_error; END IF;
  result_rows := (EXECUTE IMMEDIATE :verify_sql USING (desired));
  FOR migration_row IN result_rows DO n := migration_row.N; END FOR;
  IF (n<>0) THEN RAISE verification_error; END IF;
  result_rows := (EXECUTE IMMEDIATE :baseline_sql USING (baseline));
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
