Yes — looking at this old RAW_DATA → CURATED_JSON SQL, I do see a place where mappings can be missed.

The top-level path is fairly safe: it flattens RequestedObject.FieldContents, joins FIELD_ID to ARCHER_META_FIELD, and falls back to FIELD_<id> if SQL_FIELD_NAME is missing.

But the nested-field branch is stricter. In nested_mapped you have:

LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
    ON TO_NUMBER(amf.FIELD_ID) = TO_NUMBER(nf.FIELD_ID)

WHERE amf.SQL_FIELD_NAME IS NOT NULL

That WHERE effectively turns the left join into an inner join. So if a populated nested field has no matching SQL_FIELD_NAME, that field disappears completely from CURATED_JSON.

There is also another thing worth checking: the ROW_NUMBER() logic for top-level fields chooses one metadata row per REQ_OBJ_ID + FIELD_ID. If the same Archer FIELD_ID exists for different levels, we need to confirm it is consistently choosing the correct LEVEL_ID/SQL_FIELD_NAME.

Since you want SQL-only validation, the next query should test nested populated fields that are being dropped:

WITH norm AS (
    SELECT
        IFF(
            TYPEOF(RAW_DATA) = 'ARRAY',
            RAW_DATA[0],
            RAW_DATA
        ) AS obj
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
    WHERE TYPEOF(RAW_DATA) IN ('ARRAY','OBJECT')
),

nested_flat AS (
    SELECT
        n.obj:"RequestedObject":"Id"::NUMBER      AS REQ_OBJ_ID,
        n.obj:"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID,
        f.key::STRING                            AS FIELD_ID,
        f.path                                   AS JSON_PATH,
        f.value                                  AS RAW_VALUE
    FROM norm n,
         LATERAL FLATTEN(
             INPUT => n.obj:"RequestedObject":"FieldContents",
             RECURSIVE => TRUE
         ) f
    WHERE f.key IS NOT NULL
      AND f.path LIKE '%FieldContents%'
      AND f.key NOT LIKE 'FieldContents'
)

SELECT
    nf.FIELD_ID,
    nf.LEVEL_ID,
    COUNT(*) AS OCCURRENCES,
    COUNT_IF(
        nf.RAW_VALUE IS NOT NULL
        AND nf.RAW_VALUE::STRING NOT IN ('', 'null', '[]', '{}')
    ) AS POPULATED_COUNT,
    amf.SQL_FIELD_NAME
FROM nested_flat nf
LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
    ON TRY_TO_NUMBER(amf.FIELD_ID) = TRY_TO_NUMBER(nf.FIELD_ID)
WHERE amf.SQL_FIELD_NAME IS NULL
GROUP BY
    nf.FIELD_ID,
    nf.LEVEL_ID,
    amf.SQL_FIELD_NAME
HAVING POPULATED_COUNT > 0
ORDER BY POPULATED_COUNT DESC;

If this returns rows, we found actual source data that your old conversion SQL drops before OSCAL mapping even starts.

If it returns zero rows too, then the missing mappings are probably not from FIELD_ID → SQL_FIELD_NAME; next we check the level-selection / ROW_NUMBER() logic.

So run this one first. Don’t modify the conversion SQL yet.