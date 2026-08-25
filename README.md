Good — this narrows it down a lot. None of those populated fields is an obvious direct `ASSESSMENT_REFERENCE`. Most of the useful candidates are **arrays of Archer ContentIds**, so now we should test whether any of those IDs actually point back to the Authorization Package records.

### Next step only — READ ONLY

Run this:

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
        'QUESTIONNAIRE_TRACKING_ID',
        '889B_QUESTIONNAIRE_FINDINGS',
        'COMPLIANCE_ENGAGEMENT'
    )
)

SELECT
    R.REFERENCE_FIELD,
    COUNT(*) AS TOTAL_REFERENCES,
    COUNT(A.CONTENT_ID) AS AUTH_PACKAGE_MATCHES
FROM FINDING_REFS R
LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW A
    ON TRY_TO_NUMBER(A.CONTENT_ID) = R.REFERENCED_CONTENT_ID
WHERE R.REFERENCED_CONTENT_ID IS NOT NULL
GROUP BY R.REFERENCE_FIELD
ORDER BY AUTH_PACKAGE_MATCHES DESC,
         TOTAL_REFERENCES DESC;
```

This answers exactly one question:

> **Does any Finding relationship field directly point to an Authorization Package `CONTENT_ID`?**

If `AUTH_PACKAGE_MATCHES > 0`, we found our direct bridge.

If they are all `0`, that is also useful — it means Findings connect **through another Archer entity**, very likely Questionnaire/Engagement, and we trace that next.

No mapper or registry changes yet. Show me this result.
