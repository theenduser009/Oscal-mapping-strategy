-- SSP metadata extension properties
-- Date: 2026-09-25
-- Purpose: enable system-security-plan.metadata.props[] for the final Source One
-- confirmation-field source-preservation mapping.
-- Registry metadata only; no DIM/FACT DML. Run once in a fresh session.

EXECUTE IMMEDIATE $$
DECLARE
  tx NUMBER;
  n NUMBER;
  started BOOLEAN DEFAULT FALSE;
  committing BOOLEAN DEFAULT FALSE;

  active_tx EXCEPTION (-20951, 'SSP_METADATA_PROPS_ACTIVE_TRANSACTION: finish the existing transaction first.');
  conflict EXCEPTION (-20952, 'SSP_METADATA_PROPS_REGISTRY_CONFLICT: inspect the existing metadata props path.');
  verification_failed EXCEPTION (-20953, 'SSP_METADATA_PROPS_REGISTRY_VERIFICATION_FAILED.');
  commit_unknown EXCEPTION (-20954, 'SSP_METADATA_PROPS_COMMIT_UNCONFIRMED: inspect registry before retrying.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_tx; END IF;

  -- Parent metadata object must already be the accepted SSP path.
  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY))='SSP'
    AND TRIM(NODE_PATH)='system-security-plan.metadata'
    AND COALESCE(TRIM(PARENT_NODE_PATH),'')='system-security-plan'
    AND COALESCE(IS_COLLECTION,FALSE)=FALSE
    AND COALESCE(TRIM(OPERATOR),'')='object'
    AND IS_ACTIVE=TRUE;
  IF (n<>1) THEN RAISE verification_failed; END IF;

  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE TRIM(NODE_PATH)='system-security-plan.metadata.props[]';
  IF (n>1) THEN RAISE conflict; END IF;

  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE TRIM(NODE_PATH)='system-security-plan.metadata.props[]'
    AND (
      UPPER(COALESCE(TRIM(OSCAL_MODEL_KEY),''))<>'SSP'
      OR COALESCE(TRIM(PARENT_NODE_PATH),'')<>'system-security-plan.metadata'
    );
  IF (n>0) THEN RAISE conflict; END IF;

  BEGIN TRANSACTION;
  started := TRUE;

  MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
  USING (
    SELECT
      'SSP' AS OSCAL_MODEL_KEY,
      'system-security-plan.metadata.props[]' AS NODE_PATH,
      'props' AS ELEMENT_TYPE,
      'system-security-plan.metadata' AS PARENT_NODE_PATH,
      TRUE AS IS_COLLECTION,
      'SOURCE_FIELD_NAME' AS INSTANCE_KEY_RULE,
      2 AS PROCESS_ORDER,
      TRUE AS IS_ACTIVE,
      '$' AS ITEM_PATH,
      'properties' AS OPERATOR,
      'omit' AS UUID_POLICY,
      NULL AS REQUIRED_MEMBERS
  ) s
    ON TRIM(t.NODE_PATH)=s.NODE_PATH
  WHEN MATCHED THEN UPDATE SET
      OSCAL_MODEL_KEY=s.OSCAL_MODEL_KEY,
      ELEMENT_TYPE=s.ELEMENT_TYPE,
      PARENT_NODE_PATH=s.PARENT_NODE_PATH,
      IS_COLLECTION=s.IS_COLLECTION,
      INSTANCE_KEY_RULE=s.INSTANCE_KEY_RULE,
      PROCESS_ORDER=s.PROCESS_ORDER,
      IS_ACTIVE=s.IS_ACTIVE,
      ITEM_PATH=s.ITEM_PATH,
      OPERATOR=s.OPERATOR,
      UUID_POLICY=s.UUID_POLICY,
      REQUIRED_MEMBERS=s.REQUIRED_MEMBERS
  WHEN NOT MATCHED THEN INSERT (
      OSCAL_MODEL_KEY,NODE_PATH,ELEMENT_TYPE,PARENT_NODE_PATH,
      IS_COLLECTION,INSTANCE_KEY_RULE,PROCESS_ORDER,IS_ACTIVE,
      ITEM_PATH,OPERATOR,UUID_POLICY,REQUIRED_MEMBERS
  ) VALUES (
      s.OSCAL_MODEL_KEY,s.NODE_PATH,s.ELEMENT_TYPE,s.PARENT_NODE_PATH,
      s.IS_COLLECTION,s.INSTANCE_KEY_RULE,s.PROCESS_ORDER,s.IS_ACTIVE,
      s.ITEM_PATH,s.OPERATOR,s.UUID_POLICY,s.REQUIRED_MEMBERS
  );

  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY))='SSP'
    AND TRIM(NODE_PATH)='system-security-plan.metadata.props[]'
    AND TRIM(ELEMENT_TYPE)='props'
    AND TRIM(PARENT_NODE_PATH)='system-security-plan.metadata'
    AND IS_COLLECTION=TRUE
    AND TRIM(INSTANCE_KEY_RULE)='SOURCE_FIELD_NAME'
    AND PROCESS_ORDER=2
    AND IS_ACTIVE=TRUE
    AND TRIM(ITEM_PATH)='$'
    AND TRIM(OPERATOR)='properties'
    AND TRIM(UUID_POLICY)='omit'
    AND REQUIRED_MEMBERS IS NULL;
  IF (n<>1) THEN RAISE verification_failed; END IF;

  committing := TRUE;
  COMMIT;
  started := FALSE;

  RETURN OBJECT_CONSTRUCT(
    'STATUS','SSP_METADATA_PROPS_REGISTRY_VERIFIED',
    'ACTIVE_ROWS',n,
    'PATH','system-security-plan.metadata.props[]',
    'COMMITTED',TRUE
  );
EXCEPTION
  WHEN OTHER THEN
    IF (committing) THEN RAISE commit_unknown; END IF;
    IF (started) THEN ROLLBACK; END IF;
    RAISE;
END;
$$;
