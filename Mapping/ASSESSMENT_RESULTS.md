# Assessment Results Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

> Rows are recorded exactly from the visible row labels. Most risk scores are Archer-specific and are candidates for observations or namespaced properties, not automatically approved native OSCAL fields.

## References

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 5 | `FINDINGS` | `assessment-results.results[].findings[]` | Reference | Link to finding UUIDs in the Assessment Results model. |

## Risk and scoring fields

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 8 | `RISK_ACCEPTANCE_RBDS` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as an observation or property. |
| 41 | `VULNERABILITY_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 42 | `ANTIVIRUS_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 43 | `PATCH_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 44 | `SECURITY_COMPLIANCE_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 45 | `STANDARD_OPERATING_ENVIRONMENT_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 46 | `COMPUTER_PASSWORD_AGE_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 47 | `VULNERABILITY_REPORTING_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 48 | `SECURITY_COMPLIANCE_REPORTING_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 49 | `TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 50 | `AVG_AUTHORIZATION_PACKAGE_RISK_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 51 | `RISK_SCORE_GRADE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 52 | `AVG_VULNERABILITY_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 53 | `AVG_PATCH_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 54 | `AVG_SECURITY_COMPLIANCE_REPORTING_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 55 | `AVG_ANTIVIRUS_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 56 | `AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 57 | `AVG_COMPUTER_PASSWORD_AGE_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 58 | `AVG_VULNERABILITY_REPORTING_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 59 | `AVG_SECURITY_COMPLIANCE_SCORE` | `assessment-results.results[].observations[]` | Extension Property | Archer-specific risk scoring; map as observation. |
| 74 | `TOTAL_PACKAGE_INHERENT_RISK` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 75 | `TOTAL_PACKAGE_RESIDUAL_RISK` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 98 | `ADJUSTED_TOTAL_RISK_SCORE` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 99 | `ADJUSTED_AVERAGE_RISK_SCORE` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 134 | `CURRENT_HIGHEST_DEVICE_RISK_SCORE` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 135 | `CURRENT_AVERAGE_DEVICE_RISK_SCORE` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 136 | `CURRENT_CONTROL_RISK_SCORE` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 141 | `PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 143 | `PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 156 | `BASELINE_HIGHEST_DEVICE_RISK_SCORE` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 157 | `BASELINE_AVERAGE_DEVICE_RISK_SCORE` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 158 | `BASELINE_CONTROL_RISK_SCORE` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 460 | `RISK_ASSESSMENT` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 571 | `CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 573 | `CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 599 | `INITIAL_RISK_ASSESSMENT` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Archer-specific risk scoring; map as observation or property. |
| 604 | `RISK_ASSESSMENT_REPORT` | `assessment-results.results[].observations[]` or `props[]` | Extension Property | Confirm whether this is an observation, property, link, or attachment reference. |

## Workflow/audit extension properties

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 160 | `WORKFLOW_CURRENT_NODE` | `assessment-results.results[].props[]` | Extension Property | Workflow tracking field; map to `props[]` only if needed for audit trail. |
| 161 | `WORKFLOW_PROCESS_VERSION` | `assessment-results.results[].props[]` | Extension Property | Workflow tracking field; map to `props[]` only if needed for audit trail. |
| 162 | `WORKFLOW_JOB_STATUS` | `assessment-results.results[].props[]` | Extension Property | Workflow tracking field; map to `props[]` only if needed for audit trail. |
| 163 | `WORKFLOW_STATUS` | `assessment-results.results[].props[]` | Extension Property | Workflow tracking field; map to `props[]` only if needed for audit trail. |
| 164 | `DUE_DATE` | `assessment-results.results[].props[]` | Extension Property | Confirm datatype and whether a native task/date field is more appropriate. |
| 506 | `WORKFLOW_CURRENT_NODE_HRTN` | `assessment-results.results[].props[]` | Extension Property | Workflow tracking field; map to `props[]` only if needed for audit trail. |
| 551 | `WORKFLOW_STATUS_CHANGED` | `assessment-results.results[].props[]` | Extension Property | Workflow tracking field; map to `props[]` only if needed for audit trail. |

## Validation gate

Define a single reusable observation/property profile for risk scores—including method, subject, timestamp, unit, datatype, and namespace—then validate it in preview mode before enabling writes.
