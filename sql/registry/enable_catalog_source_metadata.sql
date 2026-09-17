-- Source 2 / Source -> Catalog Metadata registry extension.
-- Prepared: 2026-09-17 after owner-confirmed pilot registry result:
--   catalog
--   catalog.metadata
-- This adds only catalog.metadata.props[] for the reviewed Source-level runtime batch.
-- No DIM/FACT DML. No registry DDL. No seven-cell execution.

EXECUTE IMMEDIATE $$
DECLARE
  tx NUMBER;
  conflicts NUMBER;
  verified NUMBER;
  started BOOLEAN DEFAULT FALSE;
  committing BOOLEAN DEFAULT FALSE;

  active_tx EXCEPTION (-20501, 'CATALOG_SOURCE_REGISTRY_ACTIVE_TRANSACTION: no changes attempted.');
  conflict EXCEPTION (-20502, 'CATALOG_SOURCE_REGISTRY_CONFLICT: inspect Catalog registry rows; no changes accepted.');
  verification_failed EXCEPTION (-20503, 'CATALOG_SOURCE_REGISTRY_VERIFICATION_FAILED: changes were not accepted.');
  commit_unknown EXCEPTION (-20504, 'CATALOG_SOURCE_REGISTRY_COMMIT_UNCONFIRMED: inspect before retrying.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_tx; END IF;

  BEGIN TRANSACTION;
  started := TRUE;

  -- Existing Catalog rows must be exactly compatible with the reviewed three-path branch.
  WITH expected(path, parent, element_type, collection, identity_rule, item_path,
                process_order, operator, uuid_policy) AS (
    SELECT * FROM VALUES
      ('catalog', NULL, 'catalog', FALSE, 'SINGLETON', NULL, 1, 'object', 'node'),
      ('catalog.metadata', 'catalog', 'metadata', FALSE, 'SINGLETON', NULL, 2, 'object', 'omit'),
      ('catalog.metadata.props[]', 'catalog.metadata', 'props', TRUE, 'SOURCE_FIELD_NAME+VALUE', '$', 3, 'properties', 'omit')
  )
  SELECT COUNT_IF(
    e.path IS NULL
    OR COALESCE(UPPER(TRIM(r.OSCAL_MODEL_KEY)), '') <> 'CATALOG'
    OR NOT EQUAL_NULL(NULLIF(TRIM(r.PARENT_NODE_PATH), ''), e.parent)
    OR COALESCE(TRIM(r.ELEMENT_TYPE), '') <> e.element_type
    OR COALESCE(r.IS_COLLECTION, FALSE) <> e.collection
    OR NOT EQUAL_NULL(NULLIF(TRIM(r.INSTANCE_KEY_RULE), ''), e.identity_rule)
    OR NOT EQUAL_NULL(NULLIF(TRIM(r.ITEM_PATH), ''), e.item_path)
    OR COALESCE(r.PROCESS_ORDER, -1) <> e.process_order
    OR (r.OPERATOR IS NOT NULL AND TRIM(r.OPERATOR) <> e.operator)
    OR (r.UUID_POLICY IS NOT NULL AND TRIM(r.UUID_POLICY) <> e.uuid_policy)
    OR r.REQUIRED_MEMBERS IS NOT NULL
  ) INTO :conflicts
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r
  LEFT JOIN expected e ON TRIM(r.NODE_PATH) = e.path
  WHERE UPPER(COALESCE(TRIM(r.OSCAL_MODEL_KEY), '')) = 'CATALOG'
     OR LOWER(COALESCE(TRIM(r.NODE_PATH), '')) LIKE 'catalog%';

  IF (COALESCE(conflicts, 0) > 0) THEN RAISE conflict; END IF;

  SELECT COUNT(*) INTO :conflicts
  FROM (
    SELECT TRIM(NODE_PATH) AS NODE_PATH
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE TRIM(NODE_PATH) IN ('catalog', 'catalog.metadata', 'catalog.metadata.props[]')
    GROUP BY TRIM(NODE_PATH)
    HAVING COUNT(*) > 1
  );
  IF (COALESCE(conflicts, 0) > 0) THEN RAISE conflict; END IF;

  MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
  USING (
    SELECT 'catalog.metadata.props[]' AS path,
           'catalog.metadata' AS parent,
           'props' AS element_type,
           TRUE AS collection,
           'SOURCE_FIELD_NAME+VALUE' AS identity_rule,
           '$' AS item_path,
           3 AS process_order,
           'properties' AS operator,
           'omit' AS uuid_policy
  ) s
    ON TRIM(t.NODE_PATH) = s.path
  WHEN MATCHED THEN UPDATE SET
      OSCAL_MODEL_KEY = 'CATALOG',
      NODE_PATH = s.path,
      ELEMENT_TYPE = s.element_type,
      PARENT_NODE_PATH = s.parent,
      IS_COLLECTION = s.collection,
      INSTANCE_KEY_RULE = s.identity_rule,
      PROCESS_ORDER = s.process_order,
      IS_ACTIVE = TRUE,
      ITEM_PATH = s.item_path,
      OPERATOR = s.operator,
      UUID_POLICY = s.uuid_policy,
      REQUIRED_MEMBERS = NULL
  WHEN NOT MATCHED THEN INSERT (
      OSCAL_MODEL_KEY, NODE_PATH, ELEMENT_TYPE, PARENT_NODE_PATH,
      IS_COLLECTION, INSTANCE_KEY_RULE, PROCESS_ORDER, IS_ACTIVE,
      ITEM_PATH, OPERATOR, UUID_POLICY, REQUIRED_MEMBERS
  ) VALUES (
      'CATALOG', s.path, s.element_type, s.parent,
      s.collection, s.identity_rule, s.process_order, TRUE,
      s.item_path, s.operator, s.uuid_policy, NULL
  );

  WITH expected(path, parent, element_type, collection, identity_rule, item_path,
                process_order, operator, uuid_policy) AS (
    SELECT * FROM VALUES
      ('catalog', NULL, 'catalog', FALSE, 'SINGLETON', NULL, 1, 'object', 'node'),
      ('catalog.metadata', 'catalog', 'metadata', FALSE, 'SINGLETON', NULL, 2, 'object', 'omit'),
      ('catalog.metadata.props[]', 'catalog.metadata', 'props', TRUE, 'SOURCE_FIELD_NAME+VALUE', '$', 3, 'properties', 'omit')
  )
  SELECT COUNT(*) INTO :verified
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r
  JOIN expected e ON TRIM(r.NODE_PATH) = e.path
  WHERE r.IS_ACTIVE
    AND UPPER(TRIM(r.OSCAL_MODEL_KEY)) = 'CATALOG'
    AND EQUAL_NULL(NULLIF(TRIM(r.PARENT_NODE_PATH), ''), e.parent)
    AND TRIM(r.ELEMENT_TYPE) = e.element_type
    AND r.IS_COLLECTION = e.collection
    AND EQUAL_NULL(NULLIF(TRIM(r.INSTANCE_KEY_RULE), ''), e.identity_rule)
    AND EQUAL_NULL(NULLIF(TRIM(r.ITEM_PATH), ''), e.item_path)
    AND r.PROCESS_ORDER = e.process_order
    AND TRIM(r.OPERATOR) = e.operator
    AND TRIM(r.UUID_POLICY) = e.uuid_policy
    AND r.REQUIRED_MEMBERS IS NULL;

  IF (verified <> 3) THEN RAISE verification_failed; END IF;

  SELECT COUNT(*) INTO :conflicts
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE IS_ACTIVE
    AND UPPER(TRIM(OSCAL_MODEL_KEY)) = 'CATALOG'
    AND TRIM(NODE_PATH) NOT IN ('catalog', 'catalog.metadata', 'catalog.metadata.props[]');
  IF (COALESCE(conflicts, 0) > 0) THEN RAISE verification_failed; END IF;

  committing := TRUE;
  COMMIT;
  started := FALSE;

  RETURN OBJECT_CONSTRUCT(
    'STATUS', 'CATALOG_SOURCE_METADATA_REGISTRY_VERIFIED',
    'ACTIVE_ROWS', verified,
    'PATHS', ARRAY_CONSTRUCT('catalog', 'catalog.metadata', 'catalog.metadata.props[]'),
    'COMMITTED', TRUE
  );
EXCEPTION
  WHEN OTHER THEN
    IF (committing) THEN RAISE commit_unknown; END IF;
    IF (started) THEN ROLLBACK; END IF;
    RAISE;
END;
$$;
