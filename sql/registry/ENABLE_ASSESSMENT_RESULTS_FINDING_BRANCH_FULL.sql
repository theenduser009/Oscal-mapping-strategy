-- Source 2 sources_source Assessment Results finding branch
-- Date: 2026-09-17
-- Purpose: make the Source-level Assessment Results finding branch executable without duplicating target fields.
-- This changes registry metadata only; no DIM/FACT DML.

EXECUTE IMMEDIATE $$
DECLARE
  tx NUMBER;
  duplicate_paths NUMBER;
  bad_parent NUMBER;
  verified NUMBER;
  started BOOLEAN DEFAULT FALSE;
  committing BOOLEAN DEFAULT FALSE;

  active_tx EXCEPTION (-20801, 'AR_FULL_ACTIVE_TRANSACTION: finish the existing transaction first.');
  conflict EXCEPTION (-20802, 'AR_FULL_REGISTRY_CONFLICT: inspect Assessment Results registry before retrying.');
  verification_failed EXCEPTION (-20803, 'AR_FULL_REGISTRY_VERIFICATION_FAILED: expected finding branch was not read back.');
  commit_unknown EXCEPTION (-20804, 'AR_FULL_COMMIT_UNCONFIRMED: inspect registry before retrying.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_tx; END IF;

  -- Existing result collection is the accepted parent and must remain unchanged.
  SELECT COUNT(*) INTO :verified
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) = 'ASSESSMENT_RESULTS'
    AND TRIM(NODE_PATH) = 'assessment-results.results[]'
    AND TRIM(PARENT_NODE_PATH) = 'assessment-results'
    AND IS_COLLECTION = TRUE
    AND TRIM(INSTANCE_KEY_RULE) = 'SOURCE_RECORD_ID'
    AND COALESCE(TRIM(OPERATOR), '') = 'record'
    AND IS_ACTIVE = TRUE;
  IF (verified <> 1) THEN RAISE verification_failed; END IF;

  -- Never tolerate duplicate registry rows for either canonical path.
  SELECT COUNT(*) INTO :duplicate_paths
  FROM (
    SELECT TRIM(NODE_PATH) AS NODE_PATH
    FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
    WHERE TRIM(NODE_PATH) IN (
      'assessment-results.results[].findings[]',
      'assessment-results.results[].findings[].props[]'
    )
    GROUP BY TRIM(NODE_PATH)
    HAVING COUNT(*) > 1
  );
  IF (COALESCE(duplicate_paths, 0) > 0) THEN RAISE conflict; END IF;

  -- If either path already exists, only the expected model/parent ownership is accepted.
  SELECT COUNT(*) INTO :bad_parent
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE TRIM(NODE_PATH) IN (
      'assessment-results.results[].findings[]',
      'assessment-results.results[].findings[].props[]'
    )
    AND (
      UPPER(COALESCE(TRIM(OSCAL_MODEL_KEY), '')) <> 'ASSESSMENT_RESULTS'
      OR (TRIM(NODE_PATH) = 'assessment-results.results[].findings[]'
          AND COALESCE(TRIM(PARENT_NODE_PATH), '') <> 'assessment-results.results[]')
      OR (TRIM(NODE_PATH) = 'assessment-results.results[].findings[].props[]'
          AND COALESCE(TRIM(PARENT_NODE_PATH), '') <> 'assessment-results.results[].findings[]')
    );
  IF (COALESCE(bad_parent, 0) > 0) THEN RAISE conflict; END IF;

  BEGIN TRANSACTION;
  started := TRUE;

  MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
  USING (
    SELECT * FROM VALUES
      ('ASSESSMENT_RESULTS', 'assessment-results.results[].findings[]', 'findings',
       'assessment-results.results[]', TRUE, 'SOURCE_RECORD_ID', 5, TRUE,
       NULL, 'optional-record', 'node', NULL),
      ('ASSESSMENT_RESULTS', 'assessment-results.results[].findings[].props[]', 'props',
       'assessment-results.results[].findings[]', TRUE, 'SOURCE_FIELD_NAME+VALUE', 6, TRUE,
       '$', 'properties', 'omit', NULL)
  ) s(OSCAL_MODEL_KEY, NODE_PATH, ELEMENT_TYPE, PARENT_NODE_PATH,
      IS_COLLECTION, INSTANCE_KEY_RULE, PROCESS_ORDER, IS_ACTIVE,
      ITEM_PATH, OPERATOR, UUID_POLICY, REQUIRED_MEMBERS)
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
  WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) = 'ASSESSMENT_RESULTS'
    AND IS_ACTIVE = TRUE
    AND (
      (TRIM(NODE_PATH) = 'assessment-results.results[].findings[]'
       AND TRIM(PARENT_NODE_PATH) = 'assessment-results.results[]'
       AND TRIM(ELEMENT_TYPE) = 'findings'
       AND IS_COLLECTION = TRUE
       AND TRIM(INSTANCE_KEY_RULE) = 'SOURCE_RECORD_ID'
       AND ITEM_PATH IS NULL
       AND TRIM(OPERATOR) = 'optional-record'
       AND TRIM(UUID_POLICY) = 'node'
       AND PROCESS_ORDER = 5)
      OR
      (TRIM(NODE_PATH) = 'assessment-results.results[].findings[].props[]'
       AND TRIM(PARENT_NODE_PATH) = 'assessment-results.results[].findings[]'
       AND TRIM(ELEMENT_TYPE) = 'props'
       AND IS_COLLECTION = TRUE
       AND TRIM(INSTANCE_KEY_RULE) = 'SOURCE_FIELD_NAME+VALUE'
       AND TRIM(ITEM_PATH) = '$'
       AND TRIM(OPERATOR) = 'properties'
       AND TRIM(UUID_POLICY) = 'omit'
       AND PROCESS_ORDER = 6)
    );
  IF (verified <> 2) THEN RAISE verification_failed; END IF;

  committing := TRUE;
  COMMIT;
  started := FALSE;

  RETURN OBJECT_CONSTRUCT(
    'STATUS', 'AR_FULL_FINDING_BRANCH_REGISTRY_VERIFIED',
    'ACTIVE_ROWS', verified,
    'FINDING_PATH', 'assessment-results.results[].findings[]',
    'PROPS_PATH', 'assessment-results.results[].findings[].props[]',
    'COMMITTED', TRUE
  );
EXCEPTION
  WHEN OTHER THEN
    IF (committing) THEN RAISE commit_unknown; END IF;
    IF (started) THEN ROLLBACK; END IF;
    RAISE;
END;
$$;
