-- Assessment Results result-level extension properties
-- Date: 2026-09-21
-- Purpose: enable assessment-results.results[].props[] for Source One result metadata.
-- Registry metadata only; no DIM/FACT DML. Run in a fresh session.
--
-- Identity uses SOURCE_FIELD_NAME so a later value change updates the same property
-- rather than creating value-keyed obsolete rows. Null source values remain omitted
-- unless an individual CSV mapping explicitly requests preservation.

EXECUTE IMMEDIATE $$
DECLARE
  tx NUMBER;
  n NUMBER;
  started BOOLEAN DEFAULT FALSE;
  committing BOOLEAN DEFAULT FALSE;

  active_tx EXCEPTION (-20901, 'AR_PROPS_ACTIVE_TRANSACTION: finish the existing transaction first.');
  conflict EXCEPTION (-20902, 'AR_PROPS_REGISTRY_CONFLICT: inspect the Assessment Results result/property rows.');
  verification_failed EXCEPTION (-20903, 'AR_PROPS_REGISTRY_VERIFICATION_FAILED.');
  commit_unknown EXCEPTION (-20904, 'AR_PROPS_COMMIT_UNCONFIRMED: inspect registry before retrying.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_tx; END IF;

  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY))='ASSESSMENT_RESULTS'
    AND TRIM(NODE_PATH)='assessment-results.results[]'
    AND TRIM(PARENT_NODE_PATH)='assessment-results'
    AND IS_COLLECTION=TRUE
    AND TRIM(INSTANCE_KEY_RULE)='SOURCE_RECORD_ID'
    AND COALESCE(TRIM(OPERATOR),'')='record'
    AND IS_ACTIVE=TRUE;
  IF (n<>1) THEN RAISE verification_failed; END IF;

  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE TRIM(NODE_PATH)='assessment-results.results[].props[]';
  IF (n>1) THEN RAISE conflict; END IF;

  SELECT COUNT(*) INTO :n
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE TRIM(NODE_PATH)='assessment-results.results[].props[]'
    AND (
      UPPER(COALESCE(TRIM(OSCAL_MODEL_KEY),''))<>'ASSESSMENT_RESULTS'
      OR COALESCE(TRIM(PARENT_NODE_PATH),'')<>'assessment-results.results[]'
    );
  IF (n>0) THEN RAISE conflict; END IF;

  BEGIN TRANSACTION;
  started := TRUE;

  MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
  USING (
    SELECT
      'ASSESSMENT_RESULTS' AS OSCAL_MODEL_KEY,
      'assessment-results.results[].props[]' AS NODE_PATH,
      'props' AS ELEMENT_TYPE,
      'assessment-results.results[]' AS PARENT_NODE_PATH,
      TRUE AS IS_COLLECTION,
      'SOURCE_FIELD_NAME' AS INSTANCE_KEY_RULE,
      3 AS PROCESS_ORDER,
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
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY))='ASSESSMENT_RESULTS'
    AND TRIM(NODE_PATH)='assessment-results.results[].props[]'
    AND TRIM(ELEMENT_TYPE)='props'
    AND TRIM(PARENT_NODE_PATH)='assessment-results.results[]'
    AND IS_COLLECTION=TRUE
    AND TRIM(INSTANCE_KEY_RULE)='SOURCE_FIELD_NAME'
    AND PROCESS_ORDER=3
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
    'STATUS','AR_RESULT_PROPS_REGISTRY_VERIFIED',
    'ACTIVE_ROWS',n,
    'PATH','assessment-results.results[].props[]',
    'COMMITTED',TRUE
  );
EXCEPTION
  WHEN OTHER THEN
    IF (committing) THEN RAISE commit_unknown; END IF;
    IF (started) THEN ROLLBACK; END IF;
    RAISE;
END;
$$;
