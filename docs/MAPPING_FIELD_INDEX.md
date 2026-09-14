# Current mapping field index

Snapshot: September 14, 2026; generated from the maintained 153-row mapping CSV.
This is a readable index, not another executable mapping file. Update it when the CSV changes.
Original Notes, row coordinates and full execution decisions remain in the [CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
See [the project walkthrough](PROJECT_WALKTHROUGH.md) for counts, identity rules and live evidence.

APPROVED enables a rule; BLOCKED_IF_POPULATED is a deliberate guard; DEFERRED and EXCLUDED do not emit values.
Approval does not prove live population or completed OSCAL coverage. CONFIG rows supply declared structural values.
A dash in the null-policy column means no per-row override; model defaults still apply (including AR explicit-null preservation).
Missing keys remain omitted. Deferred rows with no chosen runtime path show a dash; no target is inferred here.

| CSV line | Source field / support name | Model label | Status | Executable target | Transform | Value source | Null policy | Rule ID |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER | SSP - Metadata | DEFERRED | - | - | FIELD | - | - |
| 3 | ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED | SSP - Metadata | APPROVED | system-security-plan.metadata.published | timestamp | FIELD | - | ssp:ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED:21 |
| 4 | ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED | SSP - Metadata | APPROVED | system-security-plan.metadata.last-modified | timestamp | FIELD | - | ssp:ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED:19 |
| 5 | TRACKING_ID | SSP - Metadata | APPROVED | system-security-plan.metadata.document-ids[].identifier | identifier | FIELD | - | ssp:TRACKING_ID:22 |
| 6 | FIRST_PUBLISHED | SSP - Metadata | APPROVED | system-security-plan.metadata.published | timestamp | FIELD | - | ssp:FIRST_PUBLISHED:20 |
| 7 | LAST_UPDATED | SSP - Metadata | APPROVED | system-security-plan.metadata.last-modified | timestamp | FIELD | - | ssp:LAST_UPDATED:18 |
| 8 | INFORMATION_OWNER_IO | SSP - Metadata | APPROVED | system-security-plan.metadata.responsible-parties[] | direct | FIELD | - | ssp:INFORMATION_OWNER_IO:24 |
| 9 | INFORMATION_SYSTEM_OWNER_ISO | SSP - Metadata | APPROVED | system-security-plan.metadata.responsible-parties[] | direct | FIELD | - | ssp:INFORMATION_SYSTEM_OWNER_ISO:25 |
| 10 | SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO | SSP - Metadata | DEFERRED | - | - | FIELD | - | - |
| 11 | AUTHORIZING_OFFICIAL_AO | SSP - Metadata | APPROVED | system-security-plan.metadata.responsible-parties[] | direct | FIELD | - | ssp:AUTHORIZING_OFFICIAL_AO:26 |
| 12 | INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO | SSP - Metadata | APPROVED | system-security-plan.metadata.responsible-parties[] | direct | FIELD | - | ssp:INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO:27 |
| 13 | INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE | SSP - Metadata | DEFERRED | - | - | FIELD | - | - |
| 14 | INFORMATION_SYSTEM_ADMINISTRATOR_ISA | SSP - Metadata | DEFERRED | - | - | FIELD | - | - |
| 15 | AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR | SSP - Metadata | DEFERRED | - | - | FIELD | - | - |
| 16 | PRIVACY_OFFICER_PO | SSP - Metadata | APPROVED | system-security-plan.metadata.responsible-parties[] | direct | FIELD | - | ssp:PRIVACY_OFFICER_PO:28 |
| 17 | SAP_ID | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.system-ids[].id | direct | FIELD | - | ssp:SAP_ID:23 |
| 18 | AUTHORIZATION_PACKAGE_NAME | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.system-name | text | FIELD | - | ssp:AUTHORIZATION_PACKAGE_NAME:0 |
| 19 | ACRONYM | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.system-name-short | text | FIELD | - | ssp:ACRONYM:1 |
| 20 | OPERATIONAL_STATUS | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.status.state | status-crosswalk | FIELD | - | ssp:OPERATIONAL_STATUS:15 |
| 21 | INFORMATION_SYSTEM_TYPE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.props[] | archer-select | FIELD | - | ssp:INFORMATION_SYSTEM_TYPE:35 |
| 22 | FISMA_REPORTABLE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.props[] | archer-select | FIELD | - | ssp:FISMA_REPORTABLE:36 |
| 23 | FINANCIAL_SYSTEM | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.props[] | archer-select | FIELD | - | ssp:FINANCIAL_SYSTEM:37 |
| 24 | MISSION_CRITICAL | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.props[] | archer-select | FIELD | - | ssp:MISSION_CRITICAL:38 |
| 25 | CRITICAL_INFRASTRUCTURE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.props[] | archer-select | FIELD | - | ssp:CRITICAL_INFRASTRUCTURE:39 |
| 26 | MISSION_PURPOSE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.description | text | FIELD | - | ssp:MISSION_PURPOSE:2 |
| 27 | PACKAGE_TYPE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.props[] | archer-select | FIELD | - | ssp:PACKAGE_TYPE:40 |
| 28 | AUTHORIZATION_BOUNDARY_DESCRIPTION | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.authorization-boundary.description | text | FIELD | - | ssp:AUTHORIZATION_BOUNDARY_DESCRIPTION:3 |
| 29 | AUTHORIZATION_DECISION | SSP - System Characteristics | DEFERRED | - | - | FIELD | - | - |
| 30 | HELPER_PTA_CALC | SSP - System Characteristics | EXCLUDED | - | - | FIELD | - | - |
| 31 | PACKAGE_TYPE_HELPER_CALC | SSP - System Characteristics | EXCLUDED | - | - | FIELD | - | - |
| 32 | AUTHORIZATION_COMMENTS | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.status.remarks | text | FIELD | - | ssp:AUTHORIZATION_COMMENTS:16 |
| 33 | PIA_REQUIRED | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.props[] | archer-select | FIELD | - | ssp:PIA_REQUIRED:41 |
| 34 | ATOIATO_DATE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.date-authorized | date | FIELD | - | ssp:ATOIATO_DATE:17 |
| 35 | RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality | security-objective | FIELD | - | ssp:RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY:4 |
| 36 | CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality | security-objective | FIELD | - | ssp:CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE:5 |
| 37 | RECOMMENDED_INTEGRITY_CONTROL_CATEGORY | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-integrity | security-objective | FIELD | - | ssp:RECOMMENDED_INTEGRITY_CONTROL_CATEGORY:6 |
| 38 | INTEGRITY_CONTROL_CATEGORY_OVERRIDE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-integrity | security-objective | FIELD | - | ssp:INTEGRITY_CONTROL_CATEGORY_OVERRIDE:7 |
| 39 | AVAILABILITY_CONTROL_CATEGORY_OVERRIDE | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-availability | security-objective | FIELD | - | ssp:AVAILABILITY_CONTROL_CATEGORY_OVERRIDE:9 |
| 40 | RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-availability | security-objective | FIELD | - | ssp:RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY:8 |
| 41 | SECURITY_CATEGORY | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-sensitivity-level | direct | FIELD | - | ssp:SECURITY_CATEGORY:restored |
| 42 | PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-integrity | security-objective | FIELD | - | ssp:PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY:10 |
| 43 | PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-availability | security-objective | FIELD | - | ssp:PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY:11 |
| 44 | FULL_CONTROL_ASSESSMENT_HELPER | SSP - System Characteristics | DEFERRED | - | - | FIELD | - | - |
| 45 | CNSS_AVAILABILITY_RATING | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-availability | security-objective | FIELD | - | ssp:CNSS_AVAILABILITY_RATING:12 |
| 46 | CNSS_CONFIDENTIALITY_RATING | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality | security-objective | FIELD | - | ssp:CNSS_CONFIDENTIALITY_RATING:13 |
| 47 | CNSS_INTEGRITY_RATING | SSP - System Characteristics | APPROVED | system-security-plan.system-characteristics.security-impact-level.security-objective-integrity | security-objective | FIELD | - | ssp:CNSS_INTEGRITY_RATING:14 |
| 48 | SUBSYSTEMS | SSP - System Implementation | APPROVED | system-security-plan.system-implementation.components[] | direct | FIELD | - | ssp:SUBSYSTEMS:29 |
| 49 | SOFTWARE | SSP - System Implementation | APPROVED | system-security-plan.system-implementation.components[] | direct | FIELD | - | ssp:SOFTWARE:30 |
| 50 | HARDWARE | SSP - System Implementation | APPROVED | system-security-plan.system-implementation.components[] | direct | FIELD | - | ssp:HARDWARE:31 |
| 51 | INTERCONNECTIONS | SSP - System Implementation | APPROVED | system-security-plan.system-implementation.components[] | direct | FIELD | - | ssp:INTERCONNECTIONS:32 |
| 52 | INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM | SSP - System Implementation | APPROVED | system-security-plan.system-implementation.components[] | direct | FIELD | - | ssp:INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM:33 |
| 53 | SAP_INTAKE_FORM_INTERCONNECTIONS | SSP - System Implementation | APPROVED | system-security-plan.system-implementation.components[] | direct | FIELD | - | ssp:SAP_INTAKE_FORM_INTERCONNECTIONS:34 |
| 54 | COUNT_OF_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 55 | ALLOCATE_BASELINE_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 56 | CONTROL_SET_VERSION_NUMBER | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 57 | COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 58 | COUNT_OF_CONTROLS_WITH_OPEN_POAMS_ANDOR_RBDS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 59 | NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 60 | ARCHIVE_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 61 | CONTROL_OWNER_CO | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 62 | SECURITY_CONTROL_ASSESSOR_SCA | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 63 | ADD_ADDITIONAL_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 64 | ALLOCATED_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 65 | ARCHIVED_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 66 | INHERITED_CONTROL_SELECTION | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 67 | INHERITABLE_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 68 | LINK_CNSS_CONTROLS_BY_CONFIDENTIALITY_RATING | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 69 | LINK_CNSS_CONTROLS_BY_INTEGRITY_RATING | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 70 | LINK_CNSS_CONTROLS_BY_AVAILABILITY_RATING | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 71 | HELPER_ALLOCATED_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 72 | PRECONTROL_ALLOCATION_PROGRESS_VIEW | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 73 | COUNT_OF_FULLY_IMPLEMENTED_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 74 | CONTROL_SET_VERSION_NUMBER_HRC | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 75 | GS_LAB_CONTROL_ENTITY | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 76 | CONTROL_STANDARDS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 77 | MASTER_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 78 | ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 79 | ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA_TEXT | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 80 | EXPORT_CONTROL_ASSESSOR_ECA_TEXT | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 81 | SECURITY_CONTROL_ASSESSOR_SCA_TEXT | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 82 | EXPORT_CONTROLLED_DATA_ITARAR_IF_APPLICABLE | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 83 | COUNT_OF_CONTROLS_WITH_OPEN_POAMS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 84 | COUNT_OF_CONTROLS_MISSING_POAMRBD | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 85 | ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 86 | ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 87 | CONTROL_SET_TO_ASSESS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 88 | CHANGE_CONTROL | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 89 | HELPER_OTS_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 90 | COUNT_OF_INHERITED_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 91 | COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 92 | DATE_CONTINUE_TO_CONTROL_IMPLEMENTATION | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 93 | CURRENT_CONTROL_RISK_THRESHOLD | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 94 | OF_SATISFIED_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 95 | HELPER_ALLOCATED_CONTROLS | SSP - Control Implementation | DEFERRED | - | - | FIELD | - | - |
| 96 | INFORMATION_CLASSIFICATION | System Security Plan | APPROVED | system-security-plan.system-characteristics.props[] | archer-select | FIELD | - | ssp:INFORMATION_CLASSIFICATION:42 |
| 97 | DAILY_LOSS_AMOUNT_FROM_OUTAGE | System Security Plan | APPROVED | system-security-plan.system-characteristics.props[] | direct | FIELD | preserve | ssp:DAILY_LOSS_AMOUNT_FROM_OUTAGE |
| 98 | FINDINGS | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 99 | RISK_ACCEPTANCE_RBDS | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 100 | VULNERABILITY_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:VULNERABILITY_SCORE |
| 101 | ANTIVIRUS_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:ANTIVIRUS_SCORE |
| 102 | PATCH_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:PATCH_SCORE |
| 103 | SECURITY_COMPLIANCE_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:SECURITY_COMPLIANCE_SCORE |
| 104 | STANDARD_OPERATING_ENVIRONMENT_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:STANDARD_OPERATING_ENVIRONMENT_SCORE |
| 105 | COMPUTER_PASSWORD_AGE_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:COMPUTER_PASSWORD_AGE_SCORE |
| 106 | VULNERABILITY_REPORTING_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:VULNERABILITY_REPORTING_SCORE |
| 107 | SECURITY_COMPLIANCE_REPORTING_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:SECURITY_COMPLIANCE_REPORTING_SCORE |
| 108 | TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE |
| 109 | AVG_AUTHORIZATION_PACKAGE_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:AVG_AUTHORIZATION_PACKAGE_RISK_SCORE |
| 110 | RISK_SCORE_GRADE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:RISK_SCORE_GRADE |
| 111 | AVG_VULNERABILITY_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:AVG_VULNERABILITY_SCORE |
| 112 | AVG_PATCH_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:AVG_PATCH_SCORE |
| 113 | AVG_SECURITY_COMPLIANCE_REPORTING_SCORE | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 114 | AVG_ANTIVIRUS_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:AVG_ANTIVIRUS_SCORE |
| 115 | AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE |
| 116 | AVG_COMPUTER_PASSWORD_AGE_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:AVG_COMPUTER_PASSWORD_AGE_SCORE |
| 117 | AVG_VULNERABILITY_REPORTING_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar17:AVG_VULNERABILITY_REPORTING_SCORE |
| 118 | AVG_SECURITY_COMPLIANCE_SCORE | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 119 | TOTAL_PACKAGE_INHERENT_RISK | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 120 | TOTAL_PACKAGE_RESIDUAL_RISK | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:TOTAL_PACKAGE_RESIDUAL_RISK |
| 121 | ADJUSTED_TOTAL_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:ADJUSTED_TOTAL_RISK_SCORE |
| 122 | ADJUSTED_AVERAGE_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:ADJUSTED_AVERAGE_RISK_SCORE |
| 123 | CURRENT_HIGHEST_DEVICE_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:CURRENT_HIGHEST_DEVICE_RISK_SCORE |
| 124 | CURRENT_AVERAGE_DEVICE_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:CURRENT_AVERAGE_DEVICE_RISK_SCORE |
| 125 | CURRENT_CONTROL_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:CURRENT_CONTROL_RISK_SCORE |
| 126 | PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD |
| 127 | PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD |
| 128 | BASELINE_HIGHEST_DEVICE_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:BASELINE_HIGHEST_DEVICE_RISK_SCORE |
| 129 | BASELINE_AVERAGE_DEVICE_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:BASELINE_AVERAGE_DEVICE_RISK_SCORE |
| 130 | BASELINE_CONTROL_RISK_SCORE | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:BASELINE_CONTROL_RISK_SCORE |
| 131 | RISK_ASSESSMENT | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:RISK_ASSESSMENT |
| 132 | _CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar-alt:CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD |
| 133 | _CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar-alt:CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD |
| 134 | INITIAL_RISK_ASSESSMENT | Assessment Results | APPROVED | assessment-results.results[].observations[] | scalar-score | FIELD | - | ar30:INITIAL_RISK_ASSESSMENT |
| 135 | RISK_ASSESSMENT_REPORT | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 136 | WORKFLOW_CURRENT_NODE | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 137 | WORKFLOW_PROCESS_VERSION | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 138 | WORKFLOW_JOB_STATUS | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 139 | WORKFLOW_STATUS | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 140 | DUE_DATE | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 141 | WORKFLOW_CURRENT_NODE_HRTN | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 142 | WORKFLOW_STATUS_CHANGED | Assessment Results | DEFERRED | - | - | FIELD | - | - |
| 143 | POAMS | POA&M | APPROVED | plan-of-action-and-milestones.poam-items[] | direct | FIELD | - | poam:POAMS:references |
| 144 | ADD_OVERLAY | Profile | DEFERRED | - | - | FIELD | - | - |
| 145 | BASELINE_RECOMMENDATION | Profile | DEFERRED | - | - | FIELD | - | - |
| 146 | REQUEST_TO_BEGIN_ASSESSMENT | Security Assessment Plan | APPROVED | assessment-plan.tasks[].props[] | archer-select | FIELD | preserve | sap:REQUEST_TO_BEGIN_ASSESSMENT |
| 147 | APPROVAL_TO_BEGIN_ASSESSMENT | Security Assessment Plan | APPROVED | assessment-plan.tasks[].props[] | archer-select | FIELD | preserve | sap:APPROVAL_TO_BEGIN_ASSESSMENT |
| 148 | PREASSESSMENT_REVIEW_COMMENTS | Security Assessment Plan | APPROVED | assessment-plan.tasks[].remarks | text | FIELD | preserve | sap:PREASSESSMENT_REVIEW_COMMENTS |
| 149 | RECOMMENDED_SECURITY_CATEGORY | SSP | BLOCKED_IF_POPULATED | system-security-plan.system-characteristics.security-impact-level | reject-populated | FIELD | - | ssp:RECOMMENDED_SECURITY_CATEGORY:43 |
| 150 | AUTHORIZATION_PACKAGE_NAME | SSP - Metadata | APPROVED | system-security-plan.metadata.title | text | FIELD | - | support:metadata-title |
| 151 | OSCAL_VERSION | SSP - Metadata | APPROVED | system-security-plan.metadata.oscal-version | text | CONFIG | - | support:oscal-version |
| 152 | SSP_DOCUMENT_VERSION | SSP - Metadata | APPROVED | system-security-plan.metadata.version | canonical-text | CONFIG | - | support:document-version |
| 153 | ASSESSMENT_TASK_TITLE | Security Assessment Plan | APPROVED | assessment-plan.tasks[].title | text | CONFIG | - | support:sap-task-title |
| 154 | ASSESSMENT_TASK_TYPE | Security Assessment Plan | APPROVED | assessment-plan.tasks[].type | text | CONFIG | - | support:sap-task-type |
