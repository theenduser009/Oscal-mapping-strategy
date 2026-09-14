-- Profile discovery support: inspect available technical ordering columns on the RAW table.
-- Read-only. This fixes the prior query's unverified assumption about DW_LOAD_TIMESTAMP_TZ.
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    ORDINAL_POSITION
FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ES_ESC_GRC'
  AND TABLE_NAME = 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
  AND COLUMN_NAME IN (
      'CONTENT_ID',
      'CURATED_JSON',
      'DW_LOAD_TIMESTAMP_TZ',
      'DW_LOAD_TIMESTAMP',
      'UPDATED_DATE',
      'LAST_UPDATED_DATE',
      'MODIFIED_DATE',
      'CREATE_DATE'
  )
ORDER BY ORDINAL_POSITION;
