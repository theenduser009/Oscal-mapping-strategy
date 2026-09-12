# OSCAL pipeline routing failure checkpoint — 2026-09-12

Status: **preview blocked safely; no target DML**.

This checkpoint records the visible `OSCAL_PIPELINE_REPORT` from the generic
pipeline run.

## Execution result

```text
ACTIVE_GROUP.MODEL: SSP
ACTIVE_GROUP.SOURCE: source-one
MODE: PREVIEW
FAILED_PHASE: routing
STATUS: PIPELINE_FAILED_NO_TARGET_DML
ERROR_TYPE: ValueError
ERROR_REASON: Mapping routing has blocked rows
COMMIT_ATTEMPTED: false
WRITES_EXECUTED: false
GROUPS: []
```

The notebook raised:

```text
PipelineError: OSCAL pipeline stopped; inspect OSCAL_PIPELINE_REPORT
```

## Routing counts

| Metric | Count |
|---|---:|
| Input rows | 608 |
| Selected rows | 43 |
| Excluded rows | 46 |
| Deferred rows | 60 |
| Blocked rows | 459 |
| Total issue events | 519 |

Issue samples were truncated to 25 rows.

## Reason counts

| Reason | Count | Severity |
|---|---:|---|
| UNKNOWN_MODEL_LABEL | 459 | BLOCKED |
| MISSING_APPROVED_METADATA | 58 | BLOCKED |
| DEFERRED_RELEASE_FIELD | 2 | DEFERRED |

Visible `UNKNOWN_MODEL_LABEL` examples included:

- `SYSTEM_OF_RECORD_NOTICE_SORN`
- `ADD_OVERLAY`
- `PORTS_PROTOCOLS_AND_SERVICES_MANAGEMENT_PPSM`
- `LEGACY_SYSTEM_ENVIRONMENT`
- `RECOMMENDED_SECURITY_CATEGORY`
- `INTAKE_FORM_AND_LEGACY_OVERRIDE_JUSTIFICATION`
- `INTAKE_FORM_AND_LEGACY_SECURITY_CATEGORY_OVERRIDE`
- `BASELINE_RECOMMENDATION`
- `SECURITY_CATEGORY_VERSION_COMBO`
- `MONITORING_STRATEGY`
- `REQUEST_TO_BEGIN_ASSESSMENT`
- `APPROVAL_TO_BEGIN_ASSESSMENT`
- `PREASSESSMENT_REVIEW_COMMENTS`
- `AUTHORIZATION_PACKAGE_SUBMISSION_STATUS`
- `AUTHORIZATION_PACKAGE_SUBMIT_DATE`
- `LOSS_OF_LIFE`
- `ATOIATO_EXPIRATION_DATE`
- `PROGRAMSITE_SECURITY_CATEGORY`
- `NUMBER_OF_VULNERABILITIES`
- `PREASSESSMENT_PROGRESS_VIEW`
- `FINAL_SUBMISSION_PROGRESS_VIEW`
- `HELPER_PIA_CALC`
- `CALC_HELPER_FOR_PREASSESSMENT_APPROVER`
- `RECOVERY_TIME_OBJECTIVE_RTO`
- `RECOVERY_POINT_OBJECTIVE_RPO`

## Interpretation

The routing guard behaved correctly: blocked mapping rows stopped the pipeline
before graph loading or target writes. The next investigation must resolve the
459 unknown model labels and separately account for the 58 rows missing approved
metadata. This checkpoint does not authorize changing those labels, bypassing
the routing guard, or running in commit mode.


## Unknown-model-label diagnostic

A follow-up read-only diagnostic accounted for all 459 `UNKNOWN_MODEL_LABEL`
rows by mapping model-label/target-path pairs:

| Model label | Target path | Rows |
|---|---|---:|
| Multiple - See Notes | Multiple - See Notes | 1 |
| N/A - Calculated | empty | 37 |
| Profile | Multiple - See Notes | 1 |
| Profile | profile.imports[] | 1 |
| Security Assessment Plan | security-assessment-plan.tasks[] | 2 |
| Security Assessment Plan | security-assessment-plan.tasks[].remarks | 1 |
| TBD | empty | 413 |
| TBD | All Nulls | 1 |
| TBD | Multiple - See Notes | 1 |
| TBD | system-security-plan.system-characteristics.security-impact-level | 1 |

The pair counts total 459. Most blocked rows are therefore `TBD` with an empty
target path (413 rows), followed by `N/A - Calculated` with an empty target path
(37 rows). This diagnostic was observational and does not show any target DML.
