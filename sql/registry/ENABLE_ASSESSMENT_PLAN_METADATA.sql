-- Three Assessment Plan registry rows; no registry DDL or DIM/FACT writes.
-- Run the whole statement outside a transaction, with no concurrent registry writer.
-- Retires only unconfigured legacy SAP paths and the unconfigured remarks leaf.
-- Remarks is a task member, not a separate graph node. Conflicting configured rows stop.
EXECUTE IMMEDIATE $$
DECLARE
  tx NUMBER;
  conflicts NUMBER;
  verified NUMBER;
  started BOOLEAN DEFAULT FALSE;
  committing BOOLEAN DEFAULT FALSE;
  active_tx EXCEPTION (-20301, 'SAP_REGISTRY_ACTIVE_TRANSACTION: no changes attempted.');
  conflict EXCEPTION (-20302, 'SAP_REGISTRY_CONFLICT: inspect existing Assessment Plan rows; no changes accepted.');
  commit_unknown EXCEPTION (-20303, 'SAP_REGISTRY_COMMIT_UNCONFIRMED: inspect before retrying.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_tx; END IF;
  BEGIN TRANSACTION;
  started := TRUE;

  -- Existing canonical rows must have one owner and no conflicting execution rules.
  WITH expected(path, operator, uuid_policy, identity_rule, item_path) AS (
    SELECT * FROM VALUES
      ('assessment-plan', 'object', 'node', NULL, NULL),
      ('assessment-plan.tasks[]', 'record', 'node', 'SOURCE_RECORD_ID', NULL),
      ('assessment-plan.tasks[].props[]', 'properties', 'omit', 'SOURCE_FIELD_NAME', '$')
  )
  SELECT COUNT_IF(
    (e.path IS NOT NULL AND (
      COALESCE(UPPER(TRIM(r.OSCAL_MODEL_KEY)), '') <> 'SECURITY_ASSESSMENT_PLAN'
      OR (r.OPERATOR IS NOT NULL AND r.OPERATOR <> e.operator)
      OR (r.UUID_POLICY IS NOT NULL AND r.UUID_POLICY <> e.uuid_policy)
      OR r.REQUIRED_MEMBERS IS NOT NULL
      OR (r.INSTANCE_KEY_RULE IS NOT NULL AND NOT EQUAL_NULL(r.INSTANCE_KEY_RULE, e.identity_rule))
      OR (r.ITEM_PATH IS NOT NULL AND NOT EQUAL_NULL(r.ITEM_PATH, e.item_path))))
    OR (e.path IS NULL AND (
      COALESCE(TRIM(r.NODE_PATH), '') NOT IN ('security-assessment-plan', 'security-assessment-plan.tasks[]',
        'security-assessment-plan.tasks[].props[]', 'security-assessment-plan.tasks[].remarks',
        'assessment-plan.tasks[].remarks')
      OR r.OPERATOR IS NOT NULL OR r.UUID_POLICY IS NOT NULL OR r.REQUIRED_MEMBERS IS NOT NULL))
  ) INTO :conflicts
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY r
  LEFT JOIN expected e ON TRIM(r.NODE_PATH) = e.path
  WHERE (r.IS_ACTIVE AND UPPER(TRIM(r.OSCAL_MODEL_KEY)) = 'SECURITY_ASSESSMENT_PLAN')
     OR e.path IS NOT NULL;
  IF (COALESCE(conflicts, 0) > 0) THEN RAISE conflict; END IF;

  SELECT COUNT(*) INTO :conflicts FROM (
    SELECT TRIM(NODE_PATH) FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE TRIM(NODE_PATH) IN ('assessment-plan', 'assessment-plan.tasks[]', 'assessment-plan.tasks[].props[]')
    GROUP BY TRIM(NODE_PATH) HAVING COUNT(*) > 1
  );
  IF (conflicts > 0) THEN RAISE conflict; END IF;

  UPDATE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY SET IS_ACTIVE = FALSE
  WHERE IS_ACTIVE AND UPPER(TRIM(OSCAL_MODEL_KEY)) = 'SECURITY_ASSESSMENT_PLAN'
    AND TRIM(NODE_PATH) IN ('security-assessment-plan', 'security-assessment-plan.tasks[]',
      'security-assessment-plan.tasks[].props[]', 'security-assessment-plan.tasks[].remarks',
      'assessment-plan.tasks[].remarks')
    AND OPERATOR IS NULL AND UUID_POLICY IS NULL AND REQUIRED_MEMBERS IS NULL;

  MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
  USING (
    SELECT column1 AS path, column2 AS parent, column3 AS element_type,
           column4 AS collection, column5 AS identity_rule, column6 AS item_path,
           column7 AS process_order, column8 AS operator, column9 AS uuid_policy
    FROM VALUES
      ('assessment-plan', NULL, 'assessment-plan', FALSE, NULL, NULL, 1, 'object', 'node'),
      ('assessment-plan.tasks[]', 'assessment-plan', 'tasks', TRUE, 'SOURCE_RECORD_ID', NULL, 2, 'record', 'node'),
      ('assessment-plan.tasks[].props[]', 'assessment-plan.tasks[]', 'props', TRUE, 'SOURCE_FIELD_NAME', '$', 3, 'properties', 'omit')
  ) s ON TRIM(t.NODE_PATH) = s.path
  WHEN MATCHED THEN UPDATE SET OSCAL_MODEL_KEY = 'SECURITY_ASSESSMENT_PLAN', NODE_PATH = s.path,
    PARENT_NODE_PATH = s.parent, ELEMENT_TYPE = s.element_type, IS_COLLECTION = s.collection,
    INSTANCE_KEY_RULE = s.identity_rule, ITEM_PATH = s.item_path, PROCESS_ORDER = s.process_order,
    OPERATOR = s.operator, UUID_POLICY = s.uuid_policy, REQUIRED_MEMBERS = NULL, IS_ACTIVE = TRUE
  WHEN NOT MATCHED THEN INSERT (OSCAL_MODEL_KEY, NODE_PATH, PARENT_NODE_PATH, ELEMENT_TYPE,
    IS_COLLECTION, INSTANCE_KEY_RULE, ITEM_PATH, PROCESS_ORDER, OPERATOR, UUID_POLICY, REQUIRED_MEMBERS, IS_ACTIVE)
    VALUES ('SECURITY_ASSESSMENT_PLAN', s.path, s.parent, s.element_type, s.collection,
      s.identity_rule, s.item_path, s.process_order, s.operator, s.uuid_policy, NULL, TRUE);

  SELECT COUNT(*) INTO :verified FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE IS_ACTIVE AND UPPER(TRIM(OSCAL_MODEL_KEY)) = 'SECURITY_ASSESSMENT_PLAN';
  IF (verified <> 3) THEN RAISE conflict; END IF;
  committing := TRUE;
  COMMIT;
  started := FALSE;
  RETURN OBJECT_CONSTRUCT('STATUS', 'SAP_METADATA_VERIFIED', 'ACTIVE_ROWS', verified, 'COMMITTED', TRUE);
EXCEPTION
  WHEN OTHER THEN
    IF (committing) THEN RAISE commit_unknown; END IF;
    IF (started) THEN ROLLBACK; END IF;
    RAISE;
END;
$$;
