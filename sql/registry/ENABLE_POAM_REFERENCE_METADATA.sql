-- Run the whole statement only after the read-only registry check confirms these rows.
-- Updates two existing POAM rows; no inserts, metadata DDL, resets or DIM/FACT DML.
-- Pause other registry writers. Conflicting populated rules stop this statement.
-- Root identity/ITEM_PATH and hierarchy stay unchanged; item ITEM_PATH becomes '$'.
EXECUTE IMMEDIATE $$
DECLARE
  root_path VARCHAR DEFAULT 'plan-of-action-and-milestones';
  item_path VARCHAR DEFAULT 'plan-of-action-and-milestones.poam-items[]';
  tx NUMBER;
  root_count NUMBER;
  item_count NUMBER;
  valid_count NUMBER;
  updated_count NUMBER;
  transaction_started BOOLEAN DEFAULT FALSE;
  commit_attempted BOOLEAN DEFAULT FALSE;
  active_transaction EXCEPTION (-20201, 'POAM_REGISTRY_ACTIVE_TRANSACTION: no changes attempted.');
  metadata_conflict EXCEPTION (-20202, 'POAM_REGISTRY_CONFLICT: expected two existing, compatible active rows.');
  verification_failed EXCEPTION (-20203, 'POAM_REGISTRY_VERIFICATION_FAILED: changes were not accepted.');
  commit_unknown EXCEPTION (-20204, 'POAM_REGISTRY_COMMIT_UNCONFIRMED: inspect the registry before retrying.');
  rollback_unknown EXCEPTION (-20205, 'POAM_REGISTRY_ROLLBACK_UNCONFIRMED: inspect the transaction before retrying.');
BEGIN
  SELECT CURRENT_TRANSACTION() INTO :tx;
  IF (tx IS NOT NULL) THEN RAISE active_transaction; END IF;
  BEGIN TRANSACTION;
  transaction_started := TRUE;

  SELECT COUNT_IF(TRIM(NODE_PATH) = :root_path), COUNT_IF(TRIM(NODE_PATH) = :item_path),
    COUNT_IF(COALESCE(UPPER(TRIM(OSCAL_MODEL_KEY)) = 'POAM'
      AND (UUID_POLICY IS NULL OR UUID_POLICY = 'node') AND REQUIRED_MEMBERS IS NULL
      AND ((TRIM(NODE_PATH) = :root_path AND PARENT_NODE_PATH IS NULL AND NOT IS_COLLECTION
            AND (OPERATOR IS NULL OR OPERATOR = 'object'))
        OR (TRIM(NODE_PATH) = :item_path AND TRIM(PARENT_NODE_PATH) = :root_path
            AND IS_COLLECTION AND ELEMENT_TYPE = 'poam-items' AND INSTANCE_KEY_RULE = 'CONTENT_ID'
            AND (ITEM_PATH IS NULL OR ITEM_PATH = '$')
            AND (OPERATOR IS NULL OR OPERATOR = 'references'))), FALSE))
    INTO :root_count, :item_count, :valid_count
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE IS_ACTIVE AND TRIM(NODE_PATH) IN (:root_path, :item_path);
  IF (COALESCE(root_count, 0) <> 1 OR COALESCE(item_count, 0) <> 1
      OR COALESCE(valid_count, 0) <> 2) THEN RAISE metadata_conflict; END IF;

  -- Repeat compatibility conditions in the UPDATE to reject intervening changes.
  UPDATE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  SET OPERATOR = IFF(TRIM(NODE_PATH) = :root_path, 'object', 'references'),
      UUID_POLICY = 'node', ITEM_PATH = IFF(TRIM(NODE_PATH) = :item_path, '$', ITEM_PATH)
  WHERE IS_ACTIVE AND UPPER(TRIM(OSCAL_MODEL_KEY)) = 'POAM'
    AND (UUID_POLICY IS NULL OR UUID_POLICY = 'node') AND REQUIRED_MEMBERS IS NULL
    AND ((TRIM(NODE_PATH) = :root_path AND PARENT_NODE_PATH IS NULL AND NOT IS_COLLECTION
          AND (OPERATOR IS NULL OR OPERATOR = 'object'))
      OR (TRIM(NODE_PATH) = :item_path AND TRIM(PARENT_NODE_PATH) = :root_path
          AND IS_COLLECTION AND ELEMENT_TYPE = 'poam-items' AND INSTANCE_KEY_RULE = 'CONTENT_ID'
          AND (ITEM_PATH IS NULL OR ITEM_PATH = '$')
          AND (OPERATOR IS NULL OR OPERATOR = 'references')));
  updated_count := SQLROWCOUNT;
  IF (updated_count IS NULL OR updated_count <> 2) THEN RAISE verification_failed; END IF;

  SELECT COUNT_IF(TRIM(NODE_PATH) = :root_path), COUNT_IF(TRIM(NODE_PATH) = :item_path),
    COUNT_IF(COALESCE(UPPER(TRIM(OSCAL_MODEL_KEY)) = 'POAM' AND UUID_POLICY = 'node'
      AND REQUIRED_MEMBERS IS NULL
      AND ((TRIM(NODE_PATH) = :root_path AND PARENT_NODE_PATH IS NULL AND NOT IS_COLLECTION
            AND OPERATOR = 'object')
        OR (TRIM(NODE_PATH) = :item_path AND TRIM(PARENT_NODE_PATH) = :root_path
            AND IS_COLLECTION AND ELEMENT_TYPE = 'poam-items' AND INSTANCE_KEY_RULE = 'CONTENT_ID'
            AND ITEM_PATH = '$' AND OPERATOR = 'references')), FALSE))
    INTO :root_count, :item_count, :valid_count
  FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
  WHERE IS_ACTIVE AND TRIM(NODE_PATH) IN (:root_path, :item_path);
  IF (COALESCE(root_count, 0) <> 1 OR COALESCE(item_count, 0) <> 1
      OR COALESCE(valid_count, 0) <> 2) THEN RAISE verification_failed; END IF;

  commit_attempted := TRUE;
  COMMIT;
  transaction_started := FALSE;
  RETURN OBJECT_CONSTRUCT('STATUS', 'POAM_REFERENCE_METADATA_VERIFIED',
    'TARGETED_ACTIVE_ROWS', 2, 'UPDATED_ROWS', updated_count, 'COMMITTED', TRUE);
EXCEPTION
  WHEN OTHER THEN
    IF (transaction_started) THEN
      BEGIN
        ROLLBACK;
      EXCEPTION WHEN OTHER THEN RAISE rollback_unknown;
      END;
    END IF;
    IF (commit_attempted) THEN RAISE commit_unknown; END IF;
    RAISE;
END;
$$;
