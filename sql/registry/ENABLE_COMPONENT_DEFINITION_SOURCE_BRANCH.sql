-- Source 2 sources_source -> Component Definition minimal registry branch
-- Date: 2026-09-18
-- Purpose: create only the registry structure required for Source-level Component Definition mapping.
-- Evidence: owner read-back on 2026-09-18 confirmed no existing COMPONENT_DEFINITION registry rows.
-- This changes OSCAL_ELEMENT_REGISTRY only. No Component DIM/FACT DML.
-- Scope intentionally excludes links[] and control-implementation until their exact target semantics are executable.

EXECUTE IMMEDIATE $$
DECLARE
  tx NUMBER;
  existing_component_rows NUMBER;
  duplicate_paths NUMBER;
  verified NUMBER;
  started BOOLEAN DEFAULT FALSE;
  committing BOOLEAN DEFAULT FALSE;

  active_tx EXCEPTION (-20901, 'COMPONENT_REGISTRY_ACTIVE_TRANSACTION: finish the existing transaction first.');
  conflict EXCEPTION (-20902, 'COMPONENT_REGISTRY_CONFLICT: inspect Component Definition registry before retrying.');
  verification_failed EXCEPTION (-20903, 'COMPONENT_REGISTRY_VERIFICATION_FAILED: expected Source branch was not read back.');
  commit_unknown EXCEPTION (-20904, 'COMPONENT_REGISTRY_COMMIT_UNCONFIRMED: inspect registry before retrying.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_tx; END IF;

  -- Owner read-back showed no Component Definition rows. Re-prove that boundary at execution time.
  SELECT COUNT(*) INTO :existing_component_rows
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE UPPER(COALESCE(TRIM(OSCAL_MODEL_KEY), '')) = 'COMPONENT_DEFINITION'
     OR LOWER(COALESCE(TRIM(NODE_PATH), '')) LIKE 'component-definition%';

  IF (COALESCE(existing_component_rows, 0) > 0) THEN
    RAISE conflict;
  END IF;

  SELECT COUNT(*) INTO :duplicate_paths
  FROM (
    SELECT TRIM(NODE_PATH) AS NODE_PATH
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE TRIM(NODE_PATH) IN (
      'component-definition',
      'component-definition.components[]',
      'component-definition.components[].props[]'
    )
    GROUP BY TRIM(NODE_PATH)
    HAVING COUNT(*) > 1
  );

  IF (COALESCE(duplicate_paths, 0) > 0) THEN
    RAISE conflict;
  END IF;

  BEGIN TRANSACTION;
  started := TRUE;

  MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
  USING (
    SELECT * FROM VALUES
      ('COMPONENT_DEFINITION', 'component-definition', 'component-definition',
       NULL, FALSE, 'SINGLETON', 1, TRUE,
       NULL, 'object', 'node', NULL),

      ('COMPONENT_DEFINITION', 'component-definition.components[]', 'components',
       'component-definition', TRUE, 'SOURCE_RECORD_ID', 2, TRUE,
       NULL, 'optional-record', 'node', NULL),

      ('COMPONENT_DEFINITION', 'component-definition.components[].props[]', 'props',
       'component-definition.components[]', TRUE, 'SOURCE_FIELD_NAME+VALUE', 3, TRUE,
       '$', 'properties', 'omit', NULL)
  ) s(
      OSCAL_MODEL_KEY, NODE_PATH, ELEMENT_TYPE, PARENT_NODE_PATH,
      IS_COLLECTION, INSTANCE_KEY_RULE, PROCESS_ORDER, IS_ACTIVE,
      ITEM_PATH, OPERATOR, UUID_POLICY, REQUIRED_MEMBERS
  )
    ON TRIM(t.NODE_PATH) = s.NODE_PATH
  WHEN MATCHED THEN UPDATE SET
      OSCAL_MODEL_KEY = s.OSCAL_MODEL_KEY,
      ELEMENT_TYPE = s.ELEMENT_TYPE,
      PARENT_NODE_PATH = s.PARENT_NODE_PATH,
      IS_COLLECTION = s.IS_COLLECTION,
      INSTANCE_KEY_RULE = s.INSTANCE_KEY_RULE,
      PROCESS_ORDER = s.PROCESS_ORDER,
      IS_ACTIVE = s.IS_ACTIVE,
      ITEM_PATH = s.ITEM_PATH,
      OPERATOR = s.OPERATOR,
      UUID_POLICY = s.UUID_POLICY,
      REQUIRED_MEMBERS = s.REQUIRED_MEMBERS
  WHEN NOT MATCHED THEN INSERT (
      OSCAL_MODEL_KEY, NODE_PATH, ELEMENT_TYPE, PARENT_NODE_PATH,
      IS_COLLECTION, INSTANCE_KEY_RULE, PROCESS_ORDER, IS_ACTIVE,
      ITEM_PATH, OPERATOR, UUID_POLICY, REQUIRED_MEMBERS
  ) VALUES (
      s.OSCAL_MODEL_KEY, s.NODE_PATH, s.ELEMENT_TYPE, s.PARENT_NODE_PATH,
      s.IS_COLLECTION, s.INSTANCE_KEY_RULE, s.PROCESS_ORDER, s.IS_ACTIVE,
      s.ITEM_PATH, s.OPERATOR, s.UUID_POLICY, s.REQUIRED_MEMBERS
  );

  SELECT COUNT(*) INTO :verified
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) = 'COMPONENT_DEFINITION'
    AND IS_ACTIVE = TRUE
    AND (
      (
        TRIM(NODE_PATH) = 'component-definition'
        AND PARENT_NODE_PATH IS NULL
        AND TRIM(ELEMENT_TYPE) = 'component-definition'
        AND IS_COLLECTION = FALSE
        AND TRIM(INSTANCE_KEY_RULE) = 'SINGLETON'
        AND ITEM_PATH IS NULL
        AND TRIM(OPERATOR) = 'object'
        AND TRIM(UUID_POLICY) = 'node'
        AND PROCESS_ORDER = 1
      )
      OR
      (
        TRIM(NODE_PATH) = 'component-definition.components[]'
        AND TRIM(PARENT_NODE_PATH) = 'component-definition'
        AND TRIM(ELEMENT_TYPE) = 'components'
        AND IS_COLLECTION = TRUE
        AND TRIM(INSTANCE_KEY_RULE) = 'SOURCE_RECORD_ID'
        AND ITEM_PATH IS NULL
        AND TRIM(OPERATOR) = 'optional-record'
        AND TRIM(UUID_POLICY) = 'node'
        AND PROCESS_ORDER = 2
      )
      OR
      (
        TRIM(NODE_PATH) = 'component-definition.components[].props[]'
        AND TRIM(PARENT_NODE_PATH) = 'component-definition.components[]'
        AND TRIM(ELEMENT_TYPE) = 'props'
        AND IS_COLLECTION = TRUE
        AND TRIM(INSTANCE_KEY_RULE) = 'SOURCE_FIELD_NAME+VALUE'
        AND TRIM(ITEM_PATH) = '$'
        AND TRIM(OPERATOR) = 'properties'
        AND TRIM(UUID_POLICY) = 'omit'
        AND PROCESS_ORDER = 3
      )
    );

  IF (verified <> 3) THEN
    RAISE verification_failed;
  END IF;

  committing := TRUE;
  COMMIT;
  started := FALSE;

  RETURN OBJECT_CONSTRUCT(
    'STATUS', 'COMPONENT_DEFINITION_SOURCE_REGISTRY_VERIFIED',
    'ACTIVE_ROWS', verified,
    'PATHS', ARRAY_CONSTRUCT(
      'component-definition',
      'component-definition.components[]',
      'component-definition.components[].props[]'
    ),
    'COMMITTED', TRUE
  );

EXCEPTION
  WHEN OTHER THEN
    IF (committing) THEN RAISE commit_unknown; END IF;
    IF (started) THEN ROLLBACK; END IF;
    RAISE;
END;
$$;
