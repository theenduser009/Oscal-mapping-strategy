# Assessment Results PREVIEW — target schema mismatch

Date posted: **2026-09-13**

Transcribed from the supplied Snowflake notebook screenshot.

```json
{
  "mode": "PREVIEW",
  "status": "FAILED_BEFORE_COMMIT",
  "groups": [],
  "writes_executed": false,
  "commit_attempted": false,
  "failed_route": [
    "source-one",
    "ASSESSMENT_RESULTS"
  ],
  "error_type": "LoadError",
  "load_error": {
    "release": "oscal-lean-daily-v3.1",
    "model": "ASSESSMENT_RESULTS",
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

## Error shown

```text
PipelineError: OSCAL pipeline stopped; inspect OSCAL_PIPELINE_REPORT
```

## Traceback shown

```text
File "Cell [cell7]", line 78, in <module>
    MODEL_GRAPHS, PIPELINE_REPORT = run_oscal_pipeline(SOURCE_INPUTS, MAPPING_CONTEXTS, OSCAL_LOAD_MODE)

File "Cell [cell7]", line 73, in run_oscal_pipeline
    raise PipelineError(report) from None
```
