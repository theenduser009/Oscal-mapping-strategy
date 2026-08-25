Exactly — all `AUTH_PACKAGE_MATCHES = 0`.

That means the Finding records do **not** point directly to the Authorization Package. So our next job is to identify **what those referenced ContentIds actually belong to**.

Do just this next, read-only:

```sql
WITH FINDING_REFS AS (

    SELECT
        F.CONTENT_ID AS FINDING_CONTENT_ID,
        X.KEY::STRING AS REFERENCE_FIELD,
        TRY_TO_NUMBER(V.VALUE::STRING) AS REFERENCED_CONTENT_ID
    FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_FINDINGS_RAW F,
         LATERAL FLATTEN(INPUT => F.CURATED_JSON) X,
         LATERAL FLATTEN(
             INPUT => IFF(
                 TYPEOF(X.VALUE) = 'ARRAY',
                 X.VALUE,
                 ARRAY_CONSTRUCT(X.VALUE)
             )
         ) V
    WHERE X.KEY::STRING IN (
        'REQUIRED_QUESTIONNAIRES_COMPLETED',
        '889B_QUESTIONNAIRES',
        'ISSUING_AUTHORITY_FINDING',
        '889B_QUESTIONNAIRE_FINDINGS',
        'COMPLIANCE_ENGAGEMENT'
    )
)

SELECT
    REFERENCE_FIELD,
    REFERENCED_CONTENT_ID
FROM FINDING_REFS
WHERE REFERENCED_CONTENT_ID IS NOT NULL
ORDER BY REFERENCE_FIELD
LIMIT 50;
```

Send me that output.

Then we’ll take a few of those referenced IDs and search across your Archer raw tables to identify **which entity/table owns them**. That will reveal the actual relationship path to Assessment Results.
