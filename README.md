Worked for 22s

Yes — and I’d keep it very close to your existing Matillion SQL, with only the fixes we actually validated:

1. keep ${jv_raw_table_name}


2. compare FIELD_ID as text


3. preserve NULL fields as JSON null


4. for Archer Type 4, preserve the whole object (OtherText + ValuesListIds) instead of only the IDs


5. keep your existing type conversions and CONTENT_ID logic



Use this version:

UPDATE ${jv_raw_table_name} AS tgt

SET
    tgt.CURATED_JSON = src.CURATED_JSON,
    tgt.CONTENT_ID   = src.CONTENT_ID

FROM (
    SELECT
        curated.REQ_OBJ_ID AS RECORD_ID,
        curated.CURATED_JSON,

        COALESCE(
            curated.CURATED_JSON:"ssp_uuid"::STRING,
            curated.CURATED_JSON:"AUTH_PKG_TRACKING_ID"::STRING,
            curated.CURATED_JSON:"HRTN_ID"::STRING,
            curated.CURATED_JSON:"TRACKING_ID"::STRING,
            curated.CURATED_JSON:"CONTENT_ID"::STRING,
            curated.REQ_OBJ_ID::STRING
        ) AS CONTENT_ID

    FROM (

        WITH norm AS (
            SELECT
                IFF(
                    TYPEOF(r.RAW_DATA) = 'ARRAY',
                    r.RAW_DATA[0],
                    r.RAW_DATA
                ) AS obj,
                r.RAW_DATA AS raw_data
            FROM ${jv_raw_table_name} r
            WHERE TYPEOF(r.RAW_DATA) IN ('ARRAY', 'OBJECT')
              AND r.CURATED_JSON IS NULL
        ),

        /* ---------------------------------------------------------
           TOP-LEVEL FIELD CONTENTS
        --------------------------------------------------------- */
        flat AS (
            SELECT
                n.obj:"RequestedObject":"Id"::NUMBER
                    AS REQ_OBJ_ID,

                n.obj:"RequestedObject":"LevelId"::NUMBER
                    AS LEVEL_ID,

                fc.key::STRING
                    AS FIELD_ID,

                fc.value:"Type"::NUMBER
                    AS TYPE_ID,

                fc.value:"Value"
                    AS V

            FROM norm n,
                 LATERAL FLATTEN(
                     INPUT => n.obj:"RequestedObject":"FieldContents"
                 ) fc
        ),

        /* ---------------------------------------------------------
           FIELD ID -> SQL FIELD NAME
        --------------------------------------------------------- */
        mapped AS (
            SELECT
                f.*,

                COALESCE(
                    amf.SQL_FIELD_NAME,
                    'FIELD_' || f.FIELD_ID
                ) AS SQL_KEY,

                ROW_NUMBER() OVER (
                    PARTITION BY
                        f.REQ_OBJ_ID,
                        COALESCE(
                            amf.SQL_FIELD_NAME,
                            'FIELD_' || f.FIELD_ID
                        )

                    ORDER BY
                        CASE
                            WHEN COALESCE(amf.KEY_FIELD, 'N') = 'Y'
                                THEN 0
                            ELSE 1
                        END,

                        CASE
                            WHEN amf.LEVEL_ID IS NOT NULL
                             AND TRIM(amf.LEVEL_ID::STRING)
                                 = TRIM(f.LEVEL_ID::STRING)
                                THEN 0
                            ELSE 1
                        END,

                        TRIM(f.FIELD_ID::STRING)
                ) AS rn

            FROM flat f

            LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
                ON TRIM(amf.FIELD_ID::STRING)
                 = TRIM(f.FIELD_ID::STRING)
        ),

        /* ---------------------------------------------------------
           TYPE CONVERSION

           Important fixes:
           - Preserve source NULL as JSON null
           - TYPE 4 keeps complete object:
             OtherText + ValuesListIds
        --------------------------------------------------------- */
        typed AS (
            SELECT
                REQ_OBJ_ID,
                LEVEL_ID,
                SQL_KEY,

                CASE

                    /* Preserve mapped field even when source Value is null */
                    WHEN V IS NULL OR IS_NULL_VALUE(V)
                        THEN PARSE_JSON('null')

                    ELSE
                        CASE TYPE_ID

                            WHEN 1 THEN
                                TO_VARIANT(
                                    NULLIF(V::STRING, '')
                                )

                            WHEN 2 THEN
                                TO_VARIANT(
                                    TRY_TO_NUMBER(
                                        NULLIF(V::STRING, '')
                                    )
                                )

                            WHEN 3 THEN
                                TO_VARIANT(
                                    TRY_TO_DATE(
                                        NULLIF(V::STRING, '')
                                    )
                                )

                            WHEN 6 THEN
                                TO_VARIANT(
                                    TRY_TO_NUMBER(
                                        NULLIF(V::STRING, '')
                                    )
                                )

                            WHEN 20 THEN
                                TO_VARIANT(
                                    TRY_TO_NUMBER(
                                        NULLIF(V::STRING, '')
                                    )
                                )

                            WHEN 21 THEN
                                TO_VARIANT(
                                    TRY_TO_TIMESTAMP_NTZ(
                                        NULLIF(V::STRING, '')
                                    )
                                )

                            WHEN 22 THEN
                                TO_VARIANT(
                                    TRY_TO_TIMESTAMP_NTZ(
                                        NULLIF(V::STRING, '')
                                    )
                                )

                            /*
                               FIX:
                               Previously:
                                   V:"ValuesListIds"

                               Now preserve:
                               {
                                 "OtherText": ...,
                                 "ValuesListIds": [...]
                               }
                            */
                            WHEN 4 THEN
                                TO_VARIANT(V)

                            WHEN 8 THEN
                                TO_VARIANT(V)

                            WHEN 9 THEN
                                TO_VARIANT(V)

                            WHEN 11 THEN
                                TO_VARIANT(V)

                            WHEN 23 THEN
                                TO_VARIANT(V)

                            ELSE
                                TO_VARIANT(V)

                        END
                END AS TYPED_VALUE

            FROM mapped
            WHERE rn = 1
        ),

        /* ---------------------------------------------------------
           NESTED FIELD CONTENTS
        --------------------------------------------------------- */
        nested_flat AS (
            SELECT
                n.obj:"RequestedObject":"Id"::NUMBER
                    AS REQ_OBJ_ID,

                n.obj:"RequestedObject":"LevelId"::NUMBER
                    AS LEVEL_ID,

                f.key::STRING
                    AS FIELD_ID,

                f.path
                    AS JSON_PATH,

                f.value
                    AS V

            FROM norm n,
                 LATERAL FLATTEN(
                     INPUT     => n.obj:"RequestedObject":"FieldContents",
                     RECURSIVE => TRUE
                 ) f

            WHERE f.key IS NOT NULL
              AND f.path LIKE '%FieldContents%'
              AND f.key NOT LIKE 'FieldContents'
        ),

        nested_mapped AS (
            SELECT
                nf.REQ_OBJ_ID,
                nf.LEVEL_ID,

                amf.SQL_FIELD_NAME
                    AS SQL_KEY,

                nf.V

            FROM nested_flat nf

            LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD amf
                ON TRIM(amf.FIELD_ID::STRING)
                 = TRIM(nf.FIELD_ID::STRING)

            /*
               Keep this filter.
               Recursive flatten also sees keys such as
               Value / Type / OtherText, which are NOT Field IDs.
            */
            WHERE amf.SQL_FIELD_NAME IS NOT NULL
        ),

        nested_typed AS (
            SELECT
                REQ_OBJ_ID,
                NULL AS LEVEL_ID,
                SQL_KEY,

                CASE

                    WHEN V IS NULL OR IS_NULL_VALUE(V)
                        THEN PARSE_JSON('null')

                    WHEN TYPEOF(V) = 'OBJECT' THEN
                        CASE
                            WHEN V:"Value" IS NULL
                              OR IS_NULL_VALUE(V:"Value")
                                THEN PARSE_JSON('null')
                            ELSE TO_VARIANT(V:"Value")
                        END

                    WHEN TYPEOF(V) = 'ARRAY'
                        THEN TO_VARIANT(V)

                    ELSE
                        TO_VARIANT(V)

                END AS TYPED_VALUE

            FROM nested_mapped
        ),

        /* ---------------------------------------------------------
           COMBINE
        --------------------------------------------------------- */
        combined_raw AS (

            SELECT
                REQ_OBJ_ID,
                LEVEL_ID,
                SQL_KEY,
                TYPED_VALUE,
                1 AS SOURCE_PRIORITY
            FROM typed

            UNION ALL

            SELECT
                REQ_OBJ_ID,
                NULL AS LEVEL_ID,
                SQL_KEY,
                TYPED_VALUE,
                2 AS SOURCE_PRIORITY
            FROM nested_typed
        ),

        /*
           Make sure OBJECT_AGG gets only one value
           per record + SQL field name.

           Prefer:
             1. non-null value
             2. top-level value
        */
        combined AS (
            SELECT
                REQ_OBJ_ID,
                SQL_KEY,
                TYPED_VALUE

            FROM combined_raw

            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY REQ_OBJ_ID, SQL_KEY

                ORDER BY
                    CASE
                        WHEN TYPED_VALUE IS NULL
                          OR IS_NULL_VALUE(TYPED_VALUE)
                            THEN 1
                        ELSE 0
                    END,

                    SOURCE_PRIORITY
            ) = 1
        ),

        /* ---------------------------------------------------------
           BUILD CURATED_JSON
        --------------------------------------------------------- */
        curated AS (
            SELECT
                REQ_OBJ_ID,

                OBJECT_AGG(
                    SQL_KEY,
                    CASE
                        WHEN TYPED_VALUE IS NULL
                            THEN PARSE_JSON('null')
                        ELSE TYPED_VALUE
                    END
                ) AS CURATED_JSON

            FROM combined

            WHERE SQL_KEY IS NOT NULL

            GROUP BY REQ_OBJ_ID
        )

        SELECT
            c.REQ_OBJ_ID,
            c.CURATED_JSON
        FROM curated c

    ) curated

) src

WHERE
    IFF(
        TYPEOF(tgt.RAW_DATA) = 'ARRAY',
        tgt.RAW_DATA[0],
        tgt.RAW_DATA
    ):"RequestedObject":"Id"::NUMBER = src.RECORD_ID

AND tgt.CURATED_JSON IS NULL;

The two most important changes are these:

ON TRIM(amf.FIELD_ID::STRING)
 = TRIM(f.FIELD_ID::STRING)

and:

WHEN 4 THEN TO_VARIANT(V)

So your example will now remain:

"HELPER_DEFINED_IMP_DETAILS": {
  "OtherText": null,
  "ValuesListIds": [84046]
}

instead of being reduced to:

"HELPER_DEFINED_IMP_DETAILS": [84046]

And a mapped source field whose Archer value is null can remain explicitly represented as:

"FISMA_REPORTABLE": null

One important thing before you run this in Matillion: because your final condition still says AND tgt.CURATED_JSON IS NULL, it will only populate rows whose curated JSON is currently null. It will not repair already-populated old rows. I kept that intentionally because that matches your existing pipeline and avoids overwriting production data unexpectedly.