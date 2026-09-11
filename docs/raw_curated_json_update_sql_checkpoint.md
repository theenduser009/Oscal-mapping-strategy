# Raw `CURATED_JSON` Update SQL Checkpoint

## Source

Transcribed from the six screenshots shared from the current Archer/Snowflake workflow on 2026-09-11. This is preserved as implementation context for Codex. It has **not** been independently executed or validated by ChatGPT; it reflects the SQL visible in the screenshots as closely as possible.

## Purpose

The SQL updates `${jv_raw_table_name}` by:

- normalizing `RAW_DATA` when the root is either an object or a one-element array,
- extracting `RequestedObject.Id` / `LevelId`,
- flattening Archer `FieldContents`,
- resolving Archer `FIELD_ID` values through `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD`,
- choosing one preferred mapped value per `REQ_OBJ_ID + SQL_KEY`,
- casting known Archer field types into Snowflake `VARIANT`,
- recursively capturing nested `FieldContents`,
- rebuilding one `CURATED_JSON` object per requested object,
- deriving `CONTENT_ID` from known identifier fields with `REQ_OBJ_ID` as the fallback,
- updating only rows whose `CURATED_JSON` is currently null.

## Screenshot transcription

```sql
UPDATE ${jv_raw_table_name} AS tgt
SET
    tgt.CURATED_JSON = src.CURATED_JSON,
    tgt.CONTENT_ID   = src.CONTENT_ID
FROM (
    SELECT
        curated.REQ_OBJ_ID AS RECORD_ID,
        curated.CURATED_JSON,
        COALESCE(
            curated.CURATED_JSON:"ssp_uuid"::string,
            curated.CURATED_JSON:"AUTH_PKG_TRACKING_ID"::string,
            curated.CURATED_JSON:"HRTN_ID"::string,
            curated.CURATED_JSON:"TRACKING_ID"::string,
            curated.CURATED_JSON:"CONTENT_ID"::string,
            curated.REQ_OBJ_ID::string
        ) AS CONTENT_ID
    FROM (
        WITH norm AS (
            SELECT
                IFF(
                    TYPEOF(r.RAW_DATA) = 'ARRAY',
                    r.RAW_DATA[0],
                    r.RAW_DATA
                ) AS obj
            FROM ${jv_raw_table_name} r
            WHERE TYPEOF(r.RAW_DATA) IN ('ARRAY', 'OBJECT')
              AND r.CURATED_JSON IS NULL
        ),
        flat AS (
            SELECT
                n.obj:"RequestedObject":"Id"::NUMBER      AS REQ_OBJ_ID,
                n.obj:"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID,
                fc.key::STRING                              AS FIELD_ID,
                fc.value:"Type"::NUMBER                    AS TYPE_ID,
                fc.value:"Value"                           AS V
            FROM norm n,
                 LATERAL FLATTEN(
                     input => n.obj:"RequestedObject":"FieldContents"
                 ) fc
        ),
        mapped AS (
            SELECT
                f.*,
                COALESCE(amf.SQL_FIELD_NAME, 'FIELD_' || f.FIELD_ID) AS SQL_KEY,
                ROW_NUMBER() OVER (
                    PARTITION BY
                        f.REQ_OBJ_ID,
                        COALESCE(amf.SQL_FIELD_NAME, 'FIELD_' || f.FIELD_ID)
                    ORDER BY
                        CASE
                            WHEN COALESCE(amf.KEY_FIELD, 'N') = 'Y' THEN 0
                            ELSE 1
                        END,
                        CASE
                            WHEN amf.LEVEL_ID IS NOT NULL
                             AND amf.LEVEL_ID = f.LEVEL_ID THEN 0
                            ELSE 1
                        END,
                        TO_NUMBER(f.FIELD_ID)
                ) AS rn
            FROM flat f
            LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
                ON TO_NUMBER(amf.FIELD_ID) = TO_NUMBER(f.FIELD_ID)
        ),
        typed AS (
            SELECT
                REQ_OBJ_ID,
                LEVEL_ID,
                SQL_KEY,
                CASE TYPE_ID
                    WHEN 1  THEN TO_VARIANT(NULLIF(V::STRING, ''))
                    WHEN 2  THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
                    WHEN 3  THEN TO_VARIANT(TRY_TO_DATE(NULLIF(V::STRING, '')))
                    WHEN 6  THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
                    WHEN 20 THEN TO_VARIANT(TRY_TO_NUMBER(NULLIF(V::STRING, '')))
                    WHEN 21 THEN TO_VARIANT(TRY_TO_TIMESTAMP_NTZ(NULLIF(V::STRING, '')))
                    WHEN 22 THEN TO_VARIANT(TRY_TO_TIMESTAMP_NTZ(NULLIF(V::STRING, '')))
                    WHEN 4  THEN TO_VARIANT(V)
                    WHEN 8  THEN TO_VARIANT(V)
                    WHEN 9  THEN TO_VARIANT(V)
                    WHEN 11 THEN TO_VARIANT(V)
                    WHEN 23 THEN TO_VARIANT(V)
                    ELSE TO_VARIANT(V)
                END AS TYPED_VALUE
            FROM mapped
            WHERE rn = 1
        ),
        nested_flat AS (
            SELECT
                n.obj:"RequestedObject":"Id"::NUMBER       AS REQ_OBJ_ID,
                n.obj:"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID,
                f.key::STRING                                AS FIELD_ID,
                f.path                                       AS JSON_PATH,
                f.value                                      AS V
            FROM norm n,
                 LATERAL FLATTEN(
                     input     => n.obj:"RequestedObject":"FieldContents",
                     RECURSIVE => TRUE
                 ) f
            WHERE f.key IS NOT NULL
              AND f.path LIKE '%FieldContents%'
              AND f.key NOT LIKE 'FieldContents'  -- skip the container itself
        ),
        nested_mapped AS (
            SELECT
                nf.REQ_OBJ_ID,
                nf.LEVEL_ID,
                COALESCE(amf.SQL_FIELD_NAME, 'FIELD_' || nf.FIELD_ID) AS SQL_KEY,
                nf.V
            FROM nested_flat nf
            LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
                ON TO_NUMBER(amf.FIELD_ID) = TO_NUMBER(nf.FIELD_ID)
            WHERE amf.SQL_FIELD_NAME IS NOT NULL
        ),
        nested_typed AS (
            SELECT
                REQ_OBJ_ID,
                NULL AS LEVEL_ID,
                SQL_KEY,
                TO_VARIANT(
                    CASE TYPEOF(V)
                        WHEN 'OBJECT' THEN V:"Value"
                        WHEN 'ARRAY'  THEN V
                        ELSE V
                    END
                ) AS TYPED_VALUE
            FROM nested_mapped
        ),
        combined AS (
            SELECT REQ_OBJ_ID, LEVEL_ID, SQL_KEY, TYPED_VALUE
            FROM typed

            UNION ALL

            SELECT REQ_OBJ_ID, NULL, SQL_KEY, TYPED_VALUE
            FROM nested_typed
        ),
        curated AS (
            SELECT
                REQ_OBJ_ID,
                OBJECT_AGG(SQL_KEY, TYPED_VALUE) AS CURATED_JSON
            FROM combined
            GROUP BY REQ_OBJ_ID
        )
        SELECT
            c.REQ_OBJ_ID,
            c.CURATED_JSON
        FROM curated c
    ) curated
) AS src
WHERE IFF(
          TYPEOF(tgt.RAW_DATA) = 'ARRAY',
          tgt.RAW_DATA[0],
          tgt.RAW_DATA
      ):"RequestedObject":"Id"::NUMBER = src.RECORD_ID
  AND tgt.CURATED_JSON IS NULL;
```

## Important implementation observations

1. `CONTENT_ID` precedence visible in the screenshots is:
   `ssp_uuid -> AUTH_PKG_TRACKING_ID -> HRTN_ID -> TRACKING_ID -> CONTENT_ID -> REQ_OBJ_ID`.
2. The primary flat extraction uses `RequestedObject.FieldContents` and keeps one value per logical SQL key using `ROW_NUMBER()`.
3. `ARCHER_META_FIELD.KEY_FIELD='Y'` and a matching `LEVEL_ID` are used as precedence signals.
4. Nested content is recursively flattened and only retained when it resolves to a known `SQL_FIELD_NAME`.
5. The final object is built with `OBJECT_AGG(SQL_KEY, TYPED_VALUE)` at `REQ_OBJ_ID` grain.
6. The update is idempotency-protected at the SQL level by `tgt.CURATED_JSON IS NULL`.

## Codex follow-up

Treat this document as a **checkpoint/transcription**, not as proof that the SQL is correct for every Archer value shape. Compare it against the actual Matillion SQL component before changing production logic, especially around recursive nested arrays, duplicate logical keys, and the `CONTENT_ID` fallback chain.
