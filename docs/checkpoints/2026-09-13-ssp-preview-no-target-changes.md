# SSP PREVIEW — no target changes

Date posted: **2026-09-13**

Transcribed from the supplied Snowflake notebook screenshot.

```json
{
  "mode": "PREVIEW",
  "status": "PREVIEW_COMPLETE",
  "groups": [
    {
      "source": "source-one",
      "model": "SSP",
      "load": {
        "release": "oscal-lean-daily-v3.1",
        "model": "SSP",
        "mode": "PREVIEW",
        "writes_executed": false,
        "persisted": false,
        "committed": false,
        "target_dml_attempted": false,
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
        "status": "PREVIEW_PASSED_NO_TARGET_DML",
        "temporary_cleanup": "REMOVED"
      }
    }
  ],
  "writes_executed": false,
  "commit_attempted": false
}
```
