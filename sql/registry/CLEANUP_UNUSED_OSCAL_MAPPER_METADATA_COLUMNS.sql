-- ONE-TIME DEV REGISTRY COLUMN CLEANUP. Run this whole file as one SQL statement.
--
-- Authorized scope: remove exactly the fifteen retired experimental columns from
-- RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY. Preserve every row, the original
-- nine registry columns, and the three active execution columns. No DIM/FACT access.
--
-- This is destructive DDL and cannot be transactionally rolled back. The script
-- fails closed on an unexpected table shape, an active transaction, or a dependent
-- object protected by RESTRICT. Run with other registry writers paused.

EXECUTE IMMEDIATE $$
DECLARE
  tx NUMBER;
  n NUMBER;
  before_rows NUMBER;
  after_rows NUMBER;
  before_hash NUMBER;
  after_hash NUMBER;
  retired_present NUMBER;
  expected_columns ARRAY DEFAULT PARSE_JSON('[
    "OSCAL_MODEL_KEY", "NODE_PATH", "ELEMENT_TYPE", "PARENT_NODE_PATH",
    "IS_COLLECTION", "INSTANCE_KEY_RULE", "PROCESS_ORDER", "IS_ACTIVE",
    "ITEM_PATH", "OPERATOR", "UUID_POLICY", "REQUIRED_MEMBERS"
  ]')::ARRAY;
  retired_columns ARRAY DEFAULT PARSE_JSON('[
    "MAPPER_METADATA_VERSION", "MAPPER_ENABLED", "PARENT_INSTANCE_RULE",
    "EMPTY_POLICY", "LIST_INSTANCE_RULE", "PROPERTY_NAME_RULE",
    "ASSEMBLY_POLICY", "DEFAULT_SINGLETON_POLICY", "REQUIRED_RULE_IDS",
    "ROLES_PATH", "PARTIES_PATH", "PARTY_TYPE", "PARTY_UUID_PARTS",
    "PARTY_UUID_SOURCE_KEY", "REPORT_TARGET_PATH"
  ]')::ARRAY;
  active_transaction EXCEPTION (-20101,
    'REGISTRY_CLEANUP_ACTIVE_TRANSACTION: use a fresh worksheet; no changes attempted.');
  wrong_target EXCEPTION (-20102,
    'REGISTRY_CLEANUP_TARGET_CONFLICT: exact DEV base table was not found.');
  schema_conflict EXCEPTION (-20103,
    'REGISTRY_CLEANUP_SCHEMA_CONFLICT: unexpected, missing, case-colliding, or incompatible columns; no changes attempted.');
  verification_failed EXCEPTION (-20104,
    'REGISTRY_CLEANUP_VERIFICATION_FAILED: inspect the registry before any retry.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_transaction; END IF;

  -- Resolve only the exact governed DEV base table.
  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.TABLES
  WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
    AND TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY'
    AND TABLE_TYPE = 'BASE TABLE';
  IF (n <> 1) THEN RAISE wrong_target; END IF;

  -- The twelve retained columns must exist with their established type families.
  WITH expected(name, family) AS (
    SELECT * FROM VALUES
      ('OSCAL_MODEL_KEY','TEXT'), ('NODE_PATH','TEXT'),
      ('ELEMENT_TYPE','TEXT'), ('PARENT_NODE_PATH','TEXT'),
      ('IS_COLLECTION','BOOLEAN'), ('INSTANCE_KEY_RULE','TEXT'),
      ('PROCESS_ORDER','NUMBER'), ('IS_ACTIVE','BOOLEAN'),
      ('ITEM_PATH','TEXT'), ('OPERATOR','TEXT'),
      ('UUID_POLICY','TEXT'), ('REQUIRED_MEMBERS','TEXT')
  )
  SELECT COUNT(*) INTO :n
  FROM expected e
  LEFT JOIN RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
    ON c.TABLE_SCHEMA = 'ES_ESC_GRC'
   AND c.TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY'
   AND c.COLUMN_NAME = e.name
  WHERE c.COLUMN_NAME IS NULL
     OR c.DATA_TYPE <> e.family
     OR (e.family = 'NUMBER' AND COALESCE(c.NUMERIC_SCALE, -1) <> 0);
  IF (n <> 0) THEN RAISE schema_conflict; END IF;

  -- Fail before DDL if anything exists outside the retained and retired allowlists.
  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
  WHERE c.TABLE_SCHEMA = 'ES_ESC_GRC'
    AND c.TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY'
    AND c.COLUMN_NAME NOT IN (
      SELECT value::VARCHAR FROM TABLE(FLATTEN(INPUT => :expected_columns))
      UNION ALL
      SELECT value::VARCHAR FROM TABLE(FLATTEN(INPUT => :retired_columns))
    );
  IF (n <> 0) THEN RAISE schema_conflict; END IF;

  -- Reject case-only aliases; the DROP below names exact uppercase identifiers.
  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
  JOIN TABLE(FLATTEN(INPUT => ARRAY_CAT(:expected_columns, :retired_columns))) a
    ON UPPER(c.COLUMN_NAME) = a.value::VARCHAR
  WHERE c.TABLE_SCHEMA = 'ES_ESC_GRC'
    AND c.TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY'
    AND c.COLUMN_NAME <> a.value::VARCHAR;
  IF (n <> 0) THEN RAISE schema_conflict; END IF;

  SELECT COUNT(*) INTO :retired_present
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
  JOIN TABLE(FLATTEN(INPUT => :retired_columns)) r
    ON c.COLUMN_NAME = r.value::VARCHAR
  WHERE c.TABLE_SCHEMA = 'ES_ESC_GRC'
    AND c.TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY';

  -- Fingerprint the complete retained row multiset, including NULLs and duplicates.
  SELECT COUNT(*), HASH_AGG(
      OSCAL_MODEL_KEY, NODE_PATH, ELEMENT_TYPE, PARENT_NODE_PATH,
      IS_COLLECTION, INSTANCE_KEY_RULE, PROCESS_ORDER, IS_ACTIVE, ITEM_PATH,
      OPERATOR, UUID_POLICY, REQUIRED_MEMBERS)
    INTO :before_rows, :before_hash
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY;

  -- One allowlisted metadata-only DDL operation. RESTRICT blocks dependencies.
  ALTER TABLE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    DROP COLUMN IF EXISTS
      "MAPPER_METADATA_VERSION", "MAPPER_ENABLED", "PARENT_INSTANCE_RULE",
      "EMPTY_POLICY", "LIST_INSTANCE_RULE", "PROPERTY_NAME_RULE",
      "ASSEMBLY_POLICY", "DEFAULT_SINGLETON_POLICY", "REQUIRED_RULE_IDS",
      "ROLES_PATH", "PARTIES_PATH", "PARTY_TYPE", "PARTY_UUID_PARTS",
      "PARTY_UUID_SOURCE_KEY", "REPORT_TARGET_PATH"
    RESTRICT;

  -- The final table must contain exactly the twelve retained columns.
  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
    AND TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY';
  IF (n <> ARRAY_SIZE(expected_columns)) THEN RAISE verification_failed; END IF;

  SELECT COUNT(*) INTO :n
  FROM TABLE(FLATTEN(INPUT => :expected_columns)) e
  LEFT JOIN RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
    ON c.TABLE_SCHEMA = 'ES_ESC_GRC'
   AND c.TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY'
   AND c.COLUMN_NAME = e.value::VARCHAR
  WHERE c.COLUMN_NAME IS NULL;
  IF (n <> 0) THEN RAISE verification_failed; END IF;

  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS c
  JOIN TABLE(FLATTEN(INPUT => :retired_columns)) r
    ON c.COLUMN_NAME = r.value::VARCHAR
  WHERE c.TABLE_SCHEMA = 'ES_ESC_GRC'
    AND c.TABLE_NAME = 'OSCAL_ELEMENT_REGISTRY';
  IF (n <> 0) THEN RAISE verification_failed; END IF;

  SELECT COUNT(*), HASH_AGG(
      OSCAL_MODEL_KEY, NODE_PATH, ELEMENT_TYPE, PARENT_NODE_PATH,
      IS_COLLECTION, INSTANCE_KEY_RULE, PROCESS_ORDER, IS_ACTIVE, ITEM_PATH,
      OPERATOR, UUID_POLICY, REQUIRED_MEMBERS)
    INTO :after_rows, :after_hash
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY;
  IF (before_rows IS DISTINCT FROM after_rows
      OR before_hash IS DISTINCT FROM after_hash) THEN
    RAISE verification_failed;
  END IF;

  RETURN OBJECT_CONSTRUCT(
    'STATUS', 'REGISTRY_UNUSED_COLUMNS_REMOVED',
    'TARGET', 'RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY',
    'DROPPED_COLUMNS', retired_present,
    'REMAINING_COLUMNS', ARRAY_SIZE(expected_columns),
    'PRESERVED_ROWS', after_rows,
    'PRESERVED_ROW_FINGERPRINT', TRUE,
    'DIM_FACT_ACCESSED', FALSE
  );
END;
$$;

