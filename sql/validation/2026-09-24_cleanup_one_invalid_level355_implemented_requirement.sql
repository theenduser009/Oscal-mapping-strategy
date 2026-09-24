-- ONE-TIME GUARDED CLEANUP
-- Remove the single previously persisted Level-355 implemented-requirement row
-- whose control-id was invalid because JSON null had been serialized as text.
-- Date: 2026-09-24
--
-- This script aborts unless it finds exactly:
--   1 bad DIM implemented-requirement row
--   1 incoming FACT CONTAINS edge
--   0 outgoing FACT edges
--
-- It does not touch any other SSP rows.

EXECUTE IMMEDIATE $$
DECLARE
  bad_dim_count NUMBER;
  incoming_fact_count NUMBER;
  outgoing_fact_count NUMBER;
  remaining_bad_dim NUMBER;
  remaining_bad_fact NUMBER;
  started BOOLEAN DEFAULT FALSE;

  bad_shape EXCEPTION (-20921, 'LEVEL355_BAD_ROW_SHAPE_CHANGED: expected exactly one invalid implemented-requirement.');
  bad_edge_shape EXCEPTION (-20922, 'LEVEL355_BAD_ROW_EDGE_SHAPE_CHANGED: inspect dependency graph before cleanup.');
  verify_failed EXCEPTION (-20923, 'LEVEL355_BAD_ROW_CLEANUP_VERIFY_FAILED.');
BEGIN

  CREATE OR REPLACE TEMP TABLE TMP_LEVEL355_BAD_IR AS
  SELECT
      PK_OSCAL_SSP_ELEMENT_HASH
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME = 'ARCHER'
    AND SOURCE_TABLE_NAME = 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE = 'implemented-requirements'
    AND (
         METADATA_JSON:"control-id" IS NULL
      OR IS_NULL_VALUE(METADATA_JSON:"control-id")
      OR LOWER(TRIM(METADATA_JSON:"control-id"::STRING)) = 'null'
    );

  SELECT COUNT(*) INTO :bad_dim_count
  FROM TMP_LEVEL355_BAD_IR;

  IF (bad_dim_count <> 1) THEN
    RAISE bad_shape;
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

  SELECT COUNT(*) INTO :remaining_bad_dim
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT
  WHERE SOURCE_SYSTEM_NAME = 'ARCHER'
    AND SOURCE_TABLE_NAME = 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
    AND ELEMENT_TYPE = 'implemented-requirements'
    AND (
         METADATA_JSON:"control-id" IS NULL
      OR IS_NULL_VALUE(METADATA_JSON:"control-id")
      OR LOWER(TRIM(METADATA_JSON:"control-id"::STRING)) = 'null'
    );

  SELECT COUNT(*) INTO :remaining_bad_fact
  FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f
  JOIN TMP_LEVEL355_BAD_IR b
    ON f.FK_TARGET_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH
    OR f.FK_SOURCE_ELEMENT_HASH = b.PK_OSCAL_SSP_ELEMENT_HASH;

  IF (remaining_bad_dim <> 0 OR remaining_bad_fact <> 0) THEN
    RAISE verify_failed;
  END IF;

  RETURN OBJECT_CONSTRUCT(
      'STATUS', 'LEVEL355_SINGLE_BAD_IMPLEMENTED_REQUIREMENT_REMOVED',
      'DIM_ROWS_REMOVED', bad_dim_count,
      'FACT_ROWS_REMOVED', incoming_fact_count,
      'READBACK_BAD_DIM', remaining_bad_dim,
      'READBACK_BAD_FACT', remaining_bad_fact,
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
