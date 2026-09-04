Yes — this looks right. The dry run is doing what we wanted.

For CONTENT_ID = 186731, you can see:

RAW_VALUE for Type 4 = full object with OtherText + ValuesListIds.

CURRENT_CURATED_VALUE = old reduced array such as [62862].

PROPOSED_CURATED_VALUE = full object again. ✅

Null Type-4 values remain null. ✅


One thing: your screenshot shows 164,528 Type-4 rows, while the earlier old-logic count was 138,481. That's reasonable because the dry run includes null Type-4 rows too.

Next check — one count only

Before touching Matillion, run:

WITH x AS (
    -- keep your existing dry-run CTEs through "simulated"
    SELECT *
    FROM simulated
)
SELECT
    VALIDATION_STATUS,
    COUNT(*) AS ROW_COUNT
FROM (
    SELECT *,
        CASE
            WHEN TYPE_ID = 4
                 AND TYPEOF(RAW_VALUE) = 'OBJECT'
                 AND PROPOSED_CURATED_VALUE = RAW_VALUE
                THEN 'TYPE_4_FIX_OK'

            WHEN RAW_VALUE IS NULL
                 OR IS_NULL_VALUE(RAW_VALUE)
                THEN 'SOURCE_NULL'

            ELSE 'REVIEW'
        END AS VALIDATION_STATUS
    FROM x
    WHERE TYPE_ID = 4
)
GROUP BY VALIDATION_STATUS
ORDER BY VALIDATION_STATUS;

The important number is REVIEW. Ideally that is 0.

If REVIEW = 0, I would consider the Type-4 fix validated and then we'll modify the actual ${jv_raw_table_name} Matillion UPDATE.