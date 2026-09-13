# POA&M PREVIEW — target schema mismatch

Date posted: **2026-09-13**

Transcribed from the supplied Snowflake notebook screenshot. This is evidence
only; no mapper, registry, mapping CSV, configuration, or Snowflake data was
changed.

```json
{
  "mode": "PREVIEW",
  "status": "FAILED_BEFORE_COMMIT",
  "groups": [],
  "writes_executed": false,
  "commit_attempted": false,
  "failed_route": [
    "source-one",
    "POAM"
  ],
  "error_type": "LoadError",
  "load_error": {
    "release": "oscal-lean-daily-v3.1",
    "model": "POAM",
    "mode": "PREVIEW",
    "writes_executed": false,
    "persisted": false,
    "committed": false,
    "target_dml_attempted": false,
    "pre_write_validation_passed": false,
    "status": "TARGET_SCHEMA_MISMATCH",
    "phase": "PREPARATION"
  }
}
```

The notebook raised `PipelineError: OSCAL pipeline stopped; inspect
OSCAL_PIPELINE_REPORT` from Cell 7. The failure occurred during preparation,
before validation, target DML, persistence, or commit.
