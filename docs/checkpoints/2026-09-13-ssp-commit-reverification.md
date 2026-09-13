# SSP COMMIT re-verification

Date posted: **2026-09-13**

Transcribed from the two supplied Snowflake notebook screenshots.

```json
{
  "mode": "COMMIT",
  "status": "COMMITTED_AND_VERIFIED",
  "groups": [
    {
      "source": "source-one",
      "model": "SSP",
      "load": {
        "release": "oscal-lean-daily-v3.1",
        "model": "SSP",
        "mode": "COMMIT",
        "writes_executed": true,
        "persisted": true,
        "committed": true,
        "target_dml_attempted": true,
        "pre_write_validation_passed": true,
        "nodes": 70102,
        "edges": 67289,
        "source_records": 2813,
        "validation_passed": true,
        "storage_verified": true,
        "expected_changes": {
          "D": {
            "INSERTS": 0,
            "UPDATES": 0,
            "UNCHANGED": 70102
          },
          "F": {
            "INSERTS": 0,
            "UPDATES": 0,
            "UNCHANGED": 67289
          }
        },
        "verification": {
          "DIM": {
            "INSERTS": 0,
            "UPDATES": 0,
            "UNCHANGED": 70102
          },
          "FACT": {
            "INSERTS": 0,
            "UPDATES": 0,
            "UNCHANGED": 67289
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
