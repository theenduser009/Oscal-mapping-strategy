Yes — this is much better. 🔥 `ARCHER_CONTENT_FINDINGS_RAW` clearly looks like the **actual Finding entity**. I can see real Finding attributes such as `FINDING_ID`, `FINDING_NAME`, `FINDING_RATING`, remediation fields, and—most importantly—`ASSESSMENT_REFERENCES`.

That `ASSESSMENT_REFERENCES` field is the first thing we should investigate. It may be the bridge back to the Assessment Result / Authorization Package.

### Next step only

Run this **read-only SQL**:

```sql
SELECT
    CONTENT_ID,
    CURATED_JSON:"FINDING_ID"              AS FINDING_ID,
    CURATED_JSON:"FINDING_ID_TEXT"         AS FINDING_ID_TEXT,
    CURATED_JSON:"ASSESSMENT_REFERENCES"   AS ASSESSMENT_REFERENCES,
    CURATED_JSON:"ARCHER_REFERENCE"        AS ARCHER_REFERENCE,
    CURATED_JSON:"SOURCE"                  AS SOURCE
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_FINDINGS_RAW
WHERE CURATED_JSON IS NOT NULL
LIMIT 20;
```

What I want to see is whether `ASSESSMENT_REFERENCES` contains something like:

```text
[
  {
    "ContentId": 123456,
    "LevelId": ...
  }
]
```

If it does, **do not change Cell 4 yet**. We will first prove what that `ContentId` points to. That will tell us exactly how to build:

```text
Assessment Result
      ↓
Finding
```

Send me that result.
