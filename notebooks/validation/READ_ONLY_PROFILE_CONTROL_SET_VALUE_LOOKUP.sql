-- Profile discovery only: resolve observed Archer select-value IDs for control-set/version fields.
-- Read-only. No target writes.
SELECT
    SELECT_VALUE_ID,
    SELECT_VALUE_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE
WHERE SELECT_VALUE_ID IN (
    177817, 80611, 83785, 83783, 83784, 162412,
    177818, 84081, 84082
)
ORDER BY SELECT_VALUE_ID;
