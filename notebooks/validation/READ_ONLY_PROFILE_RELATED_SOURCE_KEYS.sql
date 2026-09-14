-- Profile discovery only: list related source keys in CURATED_JSON.
-- Read-only. No target writes and no source values are returned.
SELECT DISTINCT
    f.key::string AS FIELD_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW r,
LATERAL FLATTEN(
    INPUT => TRY_PARSE_JSON(TO_VARCHAR(r.CURATED_JSON))
) f
WHERE UPPER(f.key::string) LIKE ANY (
    '%BASELINE%',
    '%CONTROL_SET%',
    '%PROFILE%',
    '%CATALOG%'
)
ORDER BY FIELD_NAME;
