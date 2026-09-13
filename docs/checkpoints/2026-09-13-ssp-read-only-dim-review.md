# SSP read-only DIM review

Date posted: **2026-09-13**

Transcribed from the two supplied Snowflake notebook screenshots.

```json
{
  "ACCEPTED_PREVIEW_DIM": {
    "INSERTS": 0,
    "UNCHANGED": 68108,
    "UPDATES": 1994
  },
  "AFFECTED_SOURCE_RECORDS": 1986,
  "ANOMALIES": {
    "CANDIDATE_RUN_MISMATCH": 0,
    "DUPLICATE_JOINED_KEYS": 0,
    "IDENTITY_PROVENANCE_CHANGED": 0,
    "SQL_CHANGED_WITHOUT_JSON_DIFFERENCE": 0
  },
  "BY_ELEMENT_PATH": [
    {
      "AFFECTED_SOURCE_RECORDS": 1958,
      "CHANGED_NODES": 1958,
      "ELEMENT_PATH": "system-security-plan.system-characteristics"
    },
    {
      "AFFECTED_SOURCE_RECORDS": 36,
      "CHANGED_NODES": 36,
      "ELEMENT_PATH": "system-security-plan.system-characteristics.security-impact-level"
    }
  ],
  "BY_JSON_MEMBER": [
    {
      "AFFECTED_SOURCE_RECORDS": 1958,
      "CHANGE": "REMOVED",
      "CHANGED_NODES": 1958,
      "ELEMENT_PATH": "system-security-plan.system-characteristics",
      "JSON_POINTER": "/security-sensitivity-level"
    },
    {
      "AFFECTED_SOURCE_RECORDS": 36,
      "CHANGE": "CHANGED",
      "CHANGED_NODES": 36,
      "ELEMENT_PATH": "system-security-plan.system-characteristics.security-impact-level",
      "JSON_POINTER": "/security-objective-availability"
    },
    {
      "AFFECTED_SOURCE_RECORDS": 36,
      "CHANGE": "CHANGED",
      "CHANGED_NODES": 36,
      "ELEMENT_PATH": "system-security-plan.system-characteristics.security-impact-level",
      "JSON_POINTER": "/security-objective-confidentiality"
    },
    {
      "AFFECTED_SOURCE_RECORDS": 36,
      "CHANGE": "CHANGED",
      "CHANGED_NODES": 36,
      "ELEMENT_PATH": "system-security-plan.system-characteristics.security-impact-level",
      "JSON_POINTER": "/security-objective-integrity"
    }
  ],
  "CANDIDATE_NODES": 70102,
  "COMPARISON": "ACCEPTED_CANDIDATE_VERSUS_CURRENT_TARGET",
  "DIM": {
    "INSERTS": 0,
    "UNCHANGED": 68108,
    "UPDATES": 1994
  },
  "HISTORICAL_TARGET_SNAPSHOT_AVAILABLE": false,
  "MODEL": "SSP",
  "NOTE": "Matching counts do not prove the target is unchanged since PREVIEW; COMMIT is not authorized.",
  "SOURCE_RECORDS": 2813,
  "STATUS": "READ_ONLY_REVIEW_COMPLETE",
  "TARGET_DML_ATTEMPTED": false
}
```

The screenshot also shows this guard line:

```python
raise RuntimeError("READ_ONLY_REVIEW_STOPPED; keep the accepted session open") from None
```
