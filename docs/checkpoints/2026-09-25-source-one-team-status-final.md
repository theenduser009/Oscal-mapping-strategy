# Source One team status — mapped, excluded, guarded, and remaining — 2026-09-25

## Repository basis
- Repository: theenduser009/Oscal-mapping-strategy
- Branch: simplify-metadata-boundary
- Head inspected before this report: 6ea151680da5cbdb7282bd2049ecb06b9b60f40c
- Source One runtime source: RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
- Source One runtime record count used in accepted runs: 2,813
- Runtime model bindings: SSP, ASSESSMENT_RESULTS, POAM, SECURITY_ASSESSMENT_PLAN
- Mapping CSV current Source One row counts:
  - APPROVED: 139
  - EXCLUDED: 13
  - DEFERRED: 2
  - BLOCKED_IF_POPULATED: 1
  - Total: 155

These are runtime mapping-metadata rows, not the original Excel row count. They include structural/support rows added by the mapper.

## Current runtime acceptance
Latest current per-model committed/read-back verified states:
- SSP: 546,799 DIM nodes / 543,986 FACT edges / 2,813 source records.
- Assessment Results: 109,630 DIM nodes / 106,817 FACT edges / 2,813 source records.
- POA&M: 2,821 DIM nodes / 8 FACT edges / 2,813 source records.
- Security Assessment Plan: 11,252 DIM nodes / 8,439 FACT edges / 2,813 source records.

SSP and Assessment Results were updated and re-verified after the earlier four-route closeout. POA&M and Security Assessment Plan were committed/read-back verified in the accepted multi-route run and were not changed by the later SSP/AR-only mapping updates.

## Source One executable-route status
There are no DEFERRED rows remaining in the four executable Source One routes.

Two DEFERRED rows remain under Profile only:
- ADD_OVERLAY
- BASELINE_RECOMMENDATION

Profile is not bound in Source One MODEL_BINDINGS, so these are outside the four executable Source One routes.

One guard remains:
- RECOMMENDED_SECURITY_CATEGORY — BLOCKED_IF_POPULATED

This is intentionally not an ordinary approved mapping. It prevents silently accepting a future populated value without an approved semantic rule.

## Model-by-model mapping summary

### SSP Metadata — 18 APPROVED
Native/structural mappings:
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED -> metadata.published
- FIRST_PUBLISHED -> metadata.published
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED -> metadata.last-modified
- LAST_UPDATED -> metadata.last-modified
- TRACKING_ID -> metadata.document-ids[].identifier
- AUTHORIZATION_PACKAGE_NAME -> metadata.title (support)
- OSCAL_VERSION -> metadata.oscal-version (support/config)
- SSP_DOCUMENT_VERSION -> metadata.version (support/config)

Responsible-party mappings to metadata.responsible-parties[]:
- INFORMATION_OWNER_IO
- INFORMATION_SYSTEM_OWNER_ISO
- SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO
- AUTHORIZING_OFFICIAL_AO
- INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO
- INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE
- INFORMATION_SYSTEM_ADMINISTRATOR_ISA
- AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR
- PRIVACY_OFFICER_PO

Source-preservation mapping:
- ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER -> metadata.props[]
  Current source is absent/missing in all 2,813 records; mapping is ready for future values. Missing keys emit nothing.

### SSP System Characteristics — 28 APPROVED / 3 EXCLUDED
Direct/native fields:
- SAP_ID -> system-ids[].id
- AUTHORIZATION_PACKAGE_NAME -> system-name
- ACRONYM -> system-name-short
- MISSION_PURPOSE -> description
- AUTHORIZATION_BOUNDARY_DESCRIPTION -> authorization-boundary.description
- OPERATIONAL_STATUS -> status.state via reviewed crosswalk
- AUTHORIZATION_COMMENTS -> status.remarks
- ATOIATO_DATE -> date-authorized
- SECURITY_CATEGORY -> security-sensitivity-level

Extension properties:
- INFORMATION_SYSTEM_TYPE
- FISMA_REPORTABLE
- FINANCIAL_SYSTEM
- MISSION_CRITICAL
- CRITICAL_INFRASTRUCTURE
- PACKAGE_TYPE
- AUTHORIZATION_DECISION
- PIA_REQUIRED

Security-impact objective transforms:
- RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY
- CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE
- CNSS_CONFIDENTIALITY_RATING
- RECOMMENDED_INTEGRITY_CONTROL_CATEGORY
- INTEGRITY_CONTROL_CATEGORY_OVERRIDE
- PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY
- CNSS_INTEGRITY_RATING
- AVAILABILITY_CONTROL_CATEGORY_OVERRIDE
- RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY
- PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY
- CNSS_AVAILABILITY_RATING

Excluded helper/calculated rows:
- HELPER_PTA_CALC
- PACKAGE_TYPE_HELPER_CALC
- FULL_CONTROL_ASSESSMENT_HELPER

### SSP System Implementation — 6 APPROVED
All map to system-implementation.components[] using reference identity:
- SUBSYSTEMS
- SOFTWARE
- HARDWARE
- INTERCONNECTIONS
- INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM
- SAP_INTAKE_FORM_INTERCONNECTIONS

The current implementation preserves reference identity/type. Software and interconnection routes have approved partial hydration; no unsupported status/default values are invented.

### SSP Control Implementation — 34 APPROVED / 10 EXCLUDED
Actual Level-355 implemented-requirement mappings:
- CONTROL_NUMBER -> control-implementation.implemented-requirements[].control-id
- IMPLEMENTATION_DETAILS -> control-implementation.implemented-requirements[].remarks

The Level-355 parent lineage is Authorization Package CONTENT_ID; child identity is ALLOCATED_CONTROL_ID. CONTROL_NUMBER is the OSCAL control-id, not the child identity.

Assessor/person mappings to metadata.responsible-parties[]:
- SECURITY_CONTROL_ASSESSOR_SCA
- ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA

Thirty package/control-summary/source-preservation fields map to system-characteristics.props[]:
- COUNT_OF_CONTROLS
- CONTROL_SET_VERSION_NUMBER
- COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS
- COUNT_OF_CONTROLS_WITH_OPEN_POAMS_ANDOR_RBDS
- NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS
- CONTROL_OWNER_CO
- ADD_ADDITIONAL_CONTROLS
- ALLOCATED_CONTROLS
- ARCHIVED_CONTROLS
- INHERITED_CONTROL_SELECTION
- INHERITABLE_CONTROLS
- COUNT_OF_FULLY_IMPLEMENTED_CONTROLS
- CONTROL_SET_VERSION_NUMBER_HRC
- GS_LAB_CONTROL_ENTITY
- CONTROL_STANDARDS
- MASTER_CONTROLS
- ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS
- ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA_TEXT
- EXPORT_CONTROL_ASSESSOR_ECA_TEXT
- SECURITY_CONTROL_ASSESSOR_SCA_TEXT
- EXPORT_CONTROLLED_DATA_ITARAR_IF_APPLICABLE
- COUNT_OF_CONTROLS_WITH_OPEN_POAMS
- COUNT_OF_CONTROLS_MISSING_POAMRBD
- ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE
- CONTROL_SET_TO_ASSESS
- CHANGE_CONTROL
- COUNT_OF_INHERITED_CONTROLS
- COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED
- CURRENT_CONTROL_RISK_THRESHOLD
- OF_SATISFIED_CONTROLS

Important source-preservation distinction:
- Some of these are real populated scalar/select/reference values and are preserved as named properties.
- INHERITABLE_CONTROLS and ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS were proved to contain integer array members and are preserved as source-reference property values without inventing target-entity resolution.
- The final 12 previously deferred Control Implementation fields had zero populated rows in the accepted closeout profile. Explicit JSON nulls are preserved as null-valued properties; completely missing fields emit nothing today. These mappings are future-ready but do not claim native OSCAL relationship semantics.

Excluded workflow/helper rows:
- ALLOCATE_BASELINE_CONTROLS
- ARCHIVE_CONTROLS
- LINK_CNSS_CONTROLS_BY_CONFIDENTIALITY_RATING
- LINK_CNSS_CONTROLS_BY_INTEGRITY_RATING
- LINK_CNSS_CONTROLS_BY_AVAILABILITY_RATING
- HELPER_ALLOCATED_CONTROLS (two source-review occurrences)
- PRECONTROL_ALLOCATION_PROGRESS_VIEW
- HELPER_OTS_CONTROLS
- DATE_CONTINUE_TO_CONTROL_IMPLEMENTATION

Note: ARCHIVE_CONTROLS is excluded workflow/action logic; ARCHIVED_CONTROLS is a separate mapped field containing archived-control references.

### System Security Plan — 2 APPROVED
Both map to system-characteristics.props[]:
- INFORMATION_CLASSIFICATION
- DAILY_LOSS_AMOUNT_FROM_OUTAGE

### Assessment Results — 45 APPROVED
Thirty-five risk/score fields map to results[].observations[] using scalar-score and named inline property semantics:
- VULNERABILITY_SCORE
- ANTIVIRUS_SCORE
- PATCH_SCORE
- SECURITY_COMPLIANCE_SCORE
- STANDARD_OPERATING_ENVIRONMENT_SCORE
- COMPUTER_PASSWORD_AGE_SCORE
- VULNERABILITY_REPORTING_SCORE
- SECURITY_COMPLIANCE_REPORTING_SCORE
- TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE
- AVG_AUTHORIZATION_PACKAGE_RISK_SCORE
- RISK_SCORE_GRADE
- AVG_VULNERABILITY_SCORE
- AVG_PATCH_SCORE
- AVG_SECURITY_COMPLIANCE_REPORTING_SCORE
- AVG_ANTIVIRUS_SCORE
- AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE
- AVG_COMPUTER_PASSWORD_AGE_SCORE
- AVG_VULNERABILITY_REPORTING_SCORE
- AVG_SECURITY_COMPLIANCE_SCORE
- TOTAL_PACKAGE_INHERENT_RISK
- TOTAL_PACKAGE_RESIDUAL_RISK
- ADJUSTED_TOTAL_RISK_SCORE
- ADJUSTED_AVERAGE_RISK_SCORE
- CURRENT_HIGHEST_DEVICE_RISK_SCORE
- CURRENT_AVERAGE_DEVICE_RISK_SCORE
- CURRENT_CONTROL_RISK_SCORE
- PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD
- PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD
- BASELINE_HIGHEST_DEVICE_RISK_SCORE
- BASELINE_AVERAGE_DEVICE_RISK_SCORE
- BASELINE_CONTROL_RISK_SCORE
- RISK_ASSESSMENT
- _CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD
- _CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD
- INITIAL_RISK_ASSESSMENT

Ten result-level property mappings:
- RISK_ACCEPTANCE_RBDS -> reference-id preservation
- WORKFLOW_CURRENT_NODE
- WORKFLOW_PROCESS_VERSION
- WORKFLOW_JOB_STATUS -> Archer select lookup
- WORKFLOW_STATUS -> Archer select lookup
- DUE_DATE -> date
- WORKFLOW_CURRENT_NODE_HRTN
- WORKFLOW_STATUS_CHANGED -> date
- RISK_ASSESSMENT_REPORT -> canonical json-text property preserving the attachment-ID array
- FINDINGS -> null-preserved property for current Source One state

Important AR distinctions:
- RISK_ASSESSMENT_REPORT does not claim a URL/back-matter resource relationship because current runtime evidence only proves numeric attachment IDs.
- FINDINGS current Source One values are explicit JSON null. The source state is preserved as a result property; native findings[] objects are not fabricated without finding identity/content.

### POA&M — 1 APPROVED
- POAMS -> plan-of-action-and-milestones.poam-items[]

Current scope is a reference graph with deterministic package-scoped item identity. It does not claim full POA&M item-detail hydration.

### Security Assessment Plan — 5 APPROVED
Actual Source One fields:
- REQUEST_TO_BEGIN_ASSESSMENT -> assessment-plan.tasks[].props[]
- APPROVAL_TO_BEGIN_ASSESSMENT -> assessment-plan.tasks[].props[]
- PREASSESSMENT_REVIEW_COMMENTS -> assessment-plan.tasks[].remarks

Structural support rows:
- ASSESSMENT_TASK_TITLE -> tasks[].title
- ASSESSMENT_TASK_TYPE -> tasks[].type

The current design emits one preassessment task per Source One record.

## What is truly left

### Outside the four executable Source One routes
Profile remains deferred:
- ADD_OVERLAY
- BASELINE_RECOMMENDATION

Profile is not part of current Source One MODEL_BINDINGS and has no current runtime contract in Cell 1.

### Intentional guard
- RECOMMENDED_SECURITY_CATEGORY = BLOCKED_IF_POPULATED

This is a fail-closed rule. It is not counted as an ordinary mapped field and is not silently converted if a future value appears.

### Resolved by exclusion
The 13 EXCLUDED rows listed above are not unfinished mappings. They were intentionally removed from executable OSCAL output because they are helper/workflow/calculated mechanics.

## What “Source One complete” means
For the current four executable Source One routes:
- there are no DEFERRED mapping rows;
- current model graphs have committed/read-back verified checkpoints;
- null-only and missing source fields have explicit source-preservation or omission behavior;
- excluded helper/workflow fields are dispositioned.

It does NOT mean:
- every optional OSCAL assembly is fully populated;
- every extension-property preservation mapping is the final preferred native OSCAL semantic model;
- Profile is complete;
- Source Two policy/catalog/cross-reference work is complete;
- a full exported OSCAL document has been independently schema/conformance validated end-to-end.

## Team-ready summary
Source One is complete for its current executable runtime scope. The only open mapping metadata are two Profile rows outside Source One runtime and one fail-closed SSP guard. All other Source One rows are either APPROVED or intentionally EXCLUDED.
