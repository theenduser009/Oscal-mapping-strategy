# Assessment Results COMMIT completed and verified

Date posted: **2026-09-13**

Transcribed from the two supplied Snowflake notebook screenshots.

```json
{
  "mode": "COMMIT",
  "status": "COMMITTED_AND_VERIFIED",
  "groups": [
    {
      "source": "source-one",
      "model": "ASSESSMENT_RESULTS",
      "load": {
        "release": "oscal-lean-daily-v3.1",
        "model": "ASSESSMENT_RESULTS",
        "mode": "COMMIT",
        "writes_executed": true,
        "persisted": true,
        "committed": true,
        "target_dml_attempted": true,
        "pre_write_validation_passed": true,
        "nodes": 73189,
        "edges": 70376,
        "source_records": 2813,
        "validation_passed": true,
        "storage_verified": true,
        "expected_changes": {
          "D": {
            "INSERTS": 73189,
            "UPDATES": 0,
            "UNCHANGED": 0
          },
          "F": {
            "INSERTS": 70376,
            "UPDATES": 0,
            "UNCHANGED": 0
          }
        },
        "verification": {
          "DIM": {
            "INSERTS": 0,
            "UPDATES": 0,
            "UNCHANGED": 73189
          },
          "FACT": {
            "INSERTS": 0,
            "UPDATES": 0,
            "UNCHANGED": 70376
          }
        },
        "status": "COMMITTED_AND_VERIFIED",
        "temporary_cleanup": "REMOVED"
      }
    }
  ],
  "writes_executed": true,
  "commit_attempted": true
}
```
