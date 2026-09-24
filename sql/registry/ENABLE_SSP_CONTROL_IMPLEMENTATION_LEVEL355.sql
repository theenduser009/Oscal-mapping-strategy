-- Enable SSP Control Implementation Level-355 joined-record branch
-- Date: 2026-09-24
-- Registry metadata only. No DIM/FACT DML.

EXECUTE IMMEDIATE $$
DECLARE
  tx NUMBER;
  verified NUMBER;
  started BOOLEAN DEFAULT FALSE;

  active_tx EXCEPTION (-20901, 'SSP_CI_ACTIVE_TRANSACTION: finish the existing transaction first.');
  verification_failed EXCEPTION (-20902, 'SSP_CI_REGISTRY_VERIFICATION_FAILED: inspect registry before retrying.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_tx; END IF;

  BEGIN TRANSACTION;
  started := TRUE;

  MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
  USING (
    SELECT * FROM VALUES
      ('SSP',
       'system-security-plan.control-implementation',
       'control-implementation',
       'system-security-plan',
       FALSE,
       'SINGLETON',
       40,
       TRUE,
       NULL,
       'object',
       'omit',
       NULL),
      ('SSP',
       'system-security-plan.control-implementation.implemented-requirements[]',
       'implemented-requirements',
       'system-security-plan.control-implementation',
       TRUE,
       'ALLOCATED_CONTROL_ID',
       41,
       TRUE,
       '$',
       'joined-records',
       'node',
       'control-id')
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
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) = 'SSP'
    AND IS_ACTIVE = TRUE
    AND (
      (TRIM(NODE_PATH) = 'system-security-plan.control-implementation'
       AND TRIM(PARENT_NODE_PATH) = 'system-security-plan'
       AND IS_COLLECTION = FALSE
       AND TRIM(INSTANCE_KEY_RULE) = 'SINGLETON'
       AND TRIM(OPERATOR) = 'object'
       AND TRIM(UUID_POLICY) = 'omit')
      OR
      (TRIM(NODE_PATH) = 'system-security-plan.control-implementation.implemented-requirements[]'
       AND TRIM(PARENT_NODE_PATH) = 'system-security-plan.control-implementation'
       AND IS_COLLECTION = TRUE
       AND TRIM(INSTANCE_KEY_RULE) = 'ALLOCATED_CONTROL_ID'
       AND TRIM(ITEM_PATH) = '$'
       AND TRIM(OPERATOR) = 'joined-records'
       AND TRIM(UUID_POLICY) = 'node'
       AND TRIM(REQUIRED_MEMBERS) = 'control-id')
    );

  IF (verified <> 2) THEN RAISE verification_failed; END IF;

  COMMIT;
  started := FALSE;

  RETURN OBJECT_CONSTRUCT(
    'STATUS', 'SSP_CONTROL_IMPLEMENTATION_LEVEL355_REGISTRY_VERIFIED',
    'ACTIVE_ROWS', verified,
    'COMMITTED', TRUE
  );
EXCEPTION
  WHEN OTHER THEN
    IF (started) THEN ROLLBACK; END IF;
    RAISE;
END;
$$;
