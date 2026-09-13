# SSP read-only value reconciliation

Date posted: **2026-09-13**

Transcribed from the five supplied Snowflake notebook screenshots.

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
    "_it should be inserts": 0,
    "UNCHANGED": 68108,
    "UPDATES": 1994
  },
  "HISTORICAL_TARGET_SNAPSHOT_AVAILABLE": false,
  "MODEL": "SSP",
  "NOTE": "Matching counts do not prove the target is unchanged since PREVIEW; COMMIT is not authorized.",
  "SOURCE_RECORDS": 2813,
  "STATUS": "READ_ONLY_REVIEW_COMPLETE",
  "TARGET_DML_ATTEMPTED": false,
  "VALUE_RECONCILIATION": {
    "COMMIT_AUTHORIZED": false,
    "COUNTS_MATCH_POSTED_PREVIEW": true,
    "IMPACT_NODES": 36,
    "IMPACT_PAYLOAD_SOURCE_CHECKS": {
      "MATCH": 36
    },
    "IMPACT_SOURCE_CHECKS": [
      {
        "ACCEPTED_TRANSFORM": "MATCH",
        "LOWERCASE_LOOKUP_TRANSFORM": "CASE_NORMALIZATION_NEEDED",
        "NODES": 36,
        "OBJECTIVE": "security-objective-availability"
      },
     _it should be {
        "ACCEPTED_TRANSFORM": "MATCH",
        "LOWERCASE_LOOKUP_TRANSFORM": "CASE_NORMALIZATION_NEEDED",
        "NODES": 36,
        "OBJECTIVE": "security-objective-confidentiality"
      },
      {
        "ACCEPTED_TRANSFORM": "MATCH",
        "LOWERCASE_LOOKUP_TRANSFORM": "CASE_NORMALIZATION_NEEDED",
        "NODES": 36,
        "OBJECTIVE": "security-objective-integrity"
      }
    ],
    "IMPACT_SOURCE_FIELDS": [
      {
        "FIELD": "AVAILABILITY_CONTROL_CATEGORY_OVERRIDE",
        "NODES": 36,
        "RESOLUTION": "SINGLE_LOOKUP"
      },
      {
        "FIELD": "CNSS_AVAILABILITY_RATING",
        "NODES": 36,
        "RESOLUTION": "EMPTY"
      },
      {
        "FIELD": "CNSS_CONFIDENTIALITY_RATING",
        "NODES": 36,
        "RESOLUTION": "EMPTY"
      },
      {
        "FIELD": "CNSS_INTEGRITY_RATING",
        "NODES": 36,
        "RESOLUTION": "EMPTY"
      },
      {
        "FIELD": "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE",
        "NODES": 36,
        "RESOLUTION": "SINGLE_LOOKUP"
      },
      {
        "FIELD": "INTEGRITY_CONTROL_CATEGORY_OVERRIDE",
        "NODES": 36,
        "RESOLUTION": "SINGLE_LOOKUP"
      },
      {
        "FIELD": "PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY",
        "NODES": 36,
        "RESOLUTION": "EMPTY"
      },
      {
        "FIELD": "PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY",
        "NODES": 36,
        "RESOLUTION": "EMPTY"
      },
      {
        "FIELD": "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY",
        "NODES": 36,
        "RESOLUTION": "EMPTY"
      },
      {
        "FIELD": "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY",
        "NODES": 36,
        "RESOLUTION": "EMPTY"
      },
      {
        "FIELD": "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY",
        "NODES": 36,
        "RESOLUTION": "EMPTY"
      }
    ],
    "IMPACT_VALUE_TRANSITIONS": [
      {
        "NEW": "Low",
        "NODES": 36,
        "OBJECTIVE": "security-objective-availability",
        "OLD": "low",
        "RELATION": "CASE_ONLY"
      },
      {
        "NEW": "Low",
        "NODES": 36,
        "OBJECTIVE": "security-objective-confidentiality",
        "OLD": "low",
        "RELATION": "CASE_ONLY"
      },
      {
        "NEW": "Low",
        "NODES": 36,
        "OBJECTIVE": "security-objective-integrity",
        "OLD": "low",
        "RELATION": "CASE_ONLY"
      }
    ],
    "NOTE": "Frozen source: accepted context and separate lowercase-lookup comparison. No sensitivity approval, fallback, graph rebuild or write readiness.",
    "SENSITIVITY_REMOVALS": 1958,
    "SENSITIVITY_SOURCE": [
      {
        "NODES": 1958,
        "PRESENCE": "POPULATED",
        "RESOLUTION": "DIRECT_TEXT",
        "SHAPE": "STR",
        "SOURCE_VS_REMOVED_VALUE": "EXACT_MATCH"
      }
    ],
    "STATUS": "READ_ONLY_VALUE_RECONCILIATION"
  }
}
```

> Transcription note: only fields visible in the supplied screenshots are included.
