Yes — the SQL query can give you the actual mapped result, and that’s actually better for proving the lookup before we touch Python.

For the known value list SELECT_ID = 3814, run:

SELECT
    SELECT_VALUE_ID,
    LOWER(SELECT_VALUE_NAME) AS FIPS_199_VALUE
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE
WHERE SELECT_ID = 3814
  AND SELECT_VALUE_ID IN (80654, 80655, 80656)
ORDER BY SELECT_VALUE_ID;

You should get:

80654  low
80655  moderate
80656  high

Then to prove the transformation against your DIM payload, we can join the raw ID from METADATA_JSON to ARCHER_META_VALUE and show the resolved value.

For example, for confidentiality:

SELECT
    d.SOURCE_RECORD_ID,
    d.METADATA_JSON:"security-objective-confidentiality"[0]::NUMBER AS ARCHER_VALUE_ID,
    LOWER(v.SELECT_VALUE_NAME) AS FIPS_199_VALUE
FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT d
LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE v
    ON v.SELECT_VALUE_ID =
       d.METADATA_JSON:"security-objective-confidentiality"[0]::NUMBER
WHERE d.ELEMENT_TYPE = 'security-impact-level'
  AND v.SELECT_ID = 3814
LIMIT 50;

That gives you something like:

SOURCE_RECORD_ID | ARCHER_VALUE_ID | FIPS_199_VALUE
565xxx           | 80654           | low
565yyy           | 80655           | moderate
565zzz           | 80656           | high

So yes: SQL first can prove the mapping end-to-end. Once that looks right, then we wire the exact same lookup behavior into the Python mapper.