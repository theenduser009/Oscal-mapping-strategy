-- ONE-TIME GUARDED CLEANUP — deduplicated historical node-key candidates
-- Date: 2026-09-24
--
-- Removes only the previously persisted Level-355 implemented-requirement whose
-- current source row has no defensible control-id.
--
-- IMPORTANT CORRECTION:
-- decoded and JSON-serialized ALLOCATED_CONTROL_ID encodings can produce the
-- same deterministic node key. Candidate hashes are therefore UNION-deduplicated
-- before target matching. The prior script counted both encodings separately and
-- could raise TARGET_IDENTITY_AMBIGUOUS even when both represented one target row.
--
-- No broad delete is allowed.

EXECUTE IMMEDIATE $$
DECLARE
  bad_source_rows NUMBER;
  candidate_key_count NUMBER;
  selected_target_rows NUMBER;
  incoming_fact_count NUMBER;
  outgoing_fact_count NUMBER;
  remaining_dim NUMBER;
  remaining_fact NUMBER;
  started BOOLEAN DEFAULT FALSE;

  bad_source_shape EXCEPTION (-20931, 'LEVEL355_BAD_SOURCE_SHAPE_CHANGED: expected exactly one matched source row without CONTROL_NUMBER.');
  target_identity_ambiguous EXCEPTION (-20932, 'LEVEL355_BAD_TARGET_IDENTITY_AMBIGUOUS: expected exactly one distinct persisted target node to match deduplicated historical key candidates.');
  bad_edge_shape EXCEPTION (-20933, 'LEVEL355_BAD_ROW_EDGE_SHAPE_CHANGED: expected one incoming and zero outgoing edges.');
  verify_failed EXCEPTION (-20934, 'LEVEL355_BAD_ROW_CLEANUP_VERIFY_FAILED.');
BEGIN

  CREATE OR REPLACE TEMP TABLE TMP_LEVEL355_BAD_SOURCE AS
  SELECT
      TRIM(s.CONTENT_ID::STRING) AS PACKAGE_CONTENT_ID,
      s.CURATED_JSON:ALLOCATED_CONTROL_ID::STRING AS ALLOCATED_CONTROL_ID_DECODED,
      TO_JSON(s.CURATED_JSON:ALLOCATED_CONTROL_ID) AS ALLOCATED_CONTROL_ID_SERIALIZED
  FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW s
  JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW p
    ON TRIM(p.CONTENT_ID::STRING) = TRIM(s.CONTENT_ID::STRING)
  WHERE (
        s.CURATED_JSON:CONTROL_NUMBER IS NULL
        OR IS_NULL_VALUE(s.CURATED_JSON:CONTROL_NUMBER)
        OR NULLIF(TRIM(s.CURATED_JSON:CONTROL_NUMBER::STRING), '') IS NULL
  );

  SELECT COUNT(*) INTO :bad_source_rows
  FROM TMP_LEVEL355_BAD_SOURCE;

  IF (bad_source_rows <> 1) THEN
    RAISE bad_source_shape;
  END IF;

  CREATE OR REPLACE TEMP TABLE TMP_LEVEL355_BAD_KEY_CANDIDATES AS
  SELECT
      TO_BINARY(
        MD5(
          'v1_registry_path_instance|ARCHER|ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW|'
          || PACKAGE_CONTENT_ID
          || '|SSP|system-security-plan.control-implementation.implemented-requirements[]|'
          || ALLOCATED_CONTROL_ID_DECODED
        ),
        'HEX'
      ) AS PK_OSCAL_SSP_ELEMENT_HASH
  FROM TMP_LEVEL355_BAD_SOURCE

  UNION

  SELECT
      TO_BINARY(
        MD5(
          'v1_registry_path_instance|ARCHER|ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW|'
          || PACKAGE_CONTENT_ID
          || '|SSP|system-security-plan.control-implementation.implemented-requirements[]|'
          || ALLOCATED_CONTROL_ID_SERIALIZED
        ),
        'HEX'
      ) AS PK_OSCAL_SSP_ELEMENT_HASH
  FROM TMP_LEVEL355_BAD_SOURCE;

  SELECT COUNT(*) INTO :candidate_key_count
  FROM TMP_LEVEL355_BAD_KEY_CANDIDATES;

  CREATE OR REPLACE TEMP TABLE TMP_LEVEL355_BAD_IR AS
  SELECT DISTINCT
      d.PK_OSCAL_SSP_ELEMENT_HASH
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT d
  JOIN TMP_LEVEL355_BAD_KEY_CANDIDATES k
    ON d.PK_OSCAL_SSP_ELEMENT_HASH = k.PK_OSCAL_SSP_ELEMENT_HASH
  WHERE d.ELEMENT_TYPE = 'implemented-requirements'
    AND d.SOURCE_SYSTEM_NAME = 'ARCHER'
    AND d.SOURCE_TABLE_NAME = 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW';

  SELECT COUNT(*) INTO :selected_target_rows
  FROM TMP_LEVEL355_BAD_IR;

  IF (selected_target_rows <> 1) THEN
    RAISE target_identity_ambiguous;
  END IF;

  SELECT COUNT(*) INTO :incoming_fact_count
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f
  JOIN TMP_LEVEL355_BAD_IR b
    ON f.FK_TARGET_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH;

  SELECT COUNT(*) INTO :outgoing_fact_count
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f
  JOIN TMP_LEVEL355_BAD_IR b
    ON f.FK_SOURCE_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH;

  IF (incoming_fact_count <> 1 OR outgoing_fact_count <> 0) THEN
    RAISE bad_edge_shape;
  END IF;

  BEGIN TRANSACTION;
  started := TRUE;

  DELETE FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f
  USING TMP_LEVEL355_BAD_IR b
  WHERE f.FK_TARGET_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH;

  DELETE FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT d
  USING TMP_LEVEL355_BAD_IR b
  WHERE d.PK_OSCAL_SSP_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH;

  COMMIT;
  started := FALSE;

  SELECT COUNT(*) INTO :remaining_dim
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT d
  JOIN TMP_LEVEL355_BAD_IR b
    ON d.PK_OSCAL_SSP_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH;

  SELECT COUNT(*) INTO :remaining_fact
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f
  JOIN TMP_LEVEL355_BAD_IR b
    ON f.FK_TARGET_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH
    OR f.FK_SOURCE_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH;

  IF (remaining_dim <> 0 OR remaining_fact <> 0) THEN
    RAISE verify_failed;
  END IF;

  RETURN OBJECT_CONSTRUCT(
      'STATUS', 'LEVEL355_SINGLE_BAD_IMPLEMENTED_REQUIREMENT_REMOVED',
      'SOURCE_BAD_ROWS', bad_source_rows,
      'DEDUPED_CANDIDATE_KEYS', candidate_key_count,
      'DIM_ROWS_REMOVED', selected_target_rows,
      'FACT_ROWS_REMOVED', incoming_fact_count,
      'READBACK_BAD_DIM', remaining_dim,
      'READBACK_BAD_FACT', remaining_fact,
      'COMMITTED', TRUE
  );

EXCEPTION
  WHEN OTHER THEN
    IF (started) THEN
      ROLLBACK;
    END IF;
    RAISE;
END;
$$;
