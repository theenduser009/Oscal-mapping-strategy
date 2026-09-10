# Live Snowflake Mapper Results

## 2026-09-10 — Cell 7 failure after component hydration
Run ID: `20260910T181836Z`; Model: `SSP`.
Component hydration: lookup 1435; interconnection 1428; interconnection descriptions 968; software 7; software descriptions 7.
Failure: `INFORMATION_SYSTEM_TYPE` has no approved transformation handler. Treat as mapping-dispatch gap, not hydration failure.

## 2026-09-10 — Next Cell 7 transformation-handler failure
Run ID: `20260910T183511Z`; Model: `SSP`.
Hydration remained successful. Failure advanced to `ATOIATO_DATE` -> `system-security-plan.system-characteristics.date-authorized`, with no approved transformation handler.

## 2026-09-10 — Mapping contract report
Canonical mapping rows inspected: **54**.
Rows rejected by handler contract regardless of source data: **2**.
No source values were read; no database queries or writes; not a graph acceptance.

Rejected row 1:
- canonical row: 16
- source field: `ATOIATO_DATE`
- OSCAL model: `SSP`
- OSCAL/canonical element path: `system-security-plan.system-characteristics.date-authorized`
- owner element path: `system-security-plan.system-characteristics`
- OSCAL field / relative path: `date-authorized`
- mapping type: `Transform`
- status: `In Progress`
- Notes: `Convert timestamp to DateDatatype`
- mapping notes: null
- transformation logic: null
- rejection: no approved transformation handler for this source/owner/target/mapping-type contract.

Rejected row 2:
- canonical row: 33
- source field: `RECOMMENDED_SECURITY_CATEGORY`
- OSCAL model: `SSP`
- OSCAL/canonical element path: `system-security-plan.system-characteristics.security-impact-level`
- owner element path: `system-security-plan.system-characteristics.security-impact-level`
- OSCAL field name: null
- field relative path: empty
- mapping type: `Extension Property`
- status: `In Progress`
- Notes: `All Nulls`
- mapping notes: null
- transformation logic: null
- rejection: `Security-impact mapping source is not approved`.

Engineering interpretation: the current blocker is explicitly a mapping-governance/handler-contract problem. Do not invent date conversion semantics or approve the security-impact source implicitly. Resolve the approved transform/dispatch contract first.

## 2026-09-10 — Successful SSP graph run after handler fixes
Run ID: `20260910T185412Z`; Model: `SSP`.

Component hydration completed successfully:
- lookup rows: **1435**
- interconnection rows: **1428**
- interconnection descriptions: **968**
- software rows: **7**
- software descriptions: **7**

Graph validation:
- graph nodes: **70,102**
- graph edges: **67,289**
- duplicate node keys: **0**
- duplicate edge keys: **0**
- dangling source edges: **0**
- dangling target edges: **0**
- pre-write validation: **PASSED**
- `EXECUTE_WRITES = False`
- DIM/FACT changes: **none**

Result: `OSCAL MAPPING RUN COMPLETE` with Nodes **70,102**, Edges **67,289**, Writes **False**.

Interpretation: the mapper now completes the in-memory SSP graph and pre-write graph integrity checks successfully at this checkpoint. This is not yet a production write-readiness/conformance claim because writes remain disabled and downstream semantic/schema readiness gates still apply.

## 2026-09-10 — SSP mapped-scope assembly passed
Mapped-scope assembly consumed the successful in-memory graph checkpoint.

- documents assembled: **2,813**
- graph nodes consumed: **70,102**
- graph edges consumed: **67,289**
- root nodes consumed: **2,813**
- writes executed: **False**
- result: **MAPPED-SCOPE ASSEMBLY PASSED**
- complete SSP claim: **False**
- OSCAL schema-valid claim: **False**

Interpretation: all 2,813 SSP source/root records were assembled successfully for the currently mapped scope. This validates mapped-scope assembly only; it deliberately does not claim complete SSP coverage or OSCAL schema validity. No writes were executed.

## 2026-09-10 — Clearer mapping-workbook screenshot reconciliation
The clearer screenshots of `archer_to_oscal_mapping.xlsx` were re-reviewed and supersede the earlier visual transcription where they provide better legibility. This remains screenshot evidence only; the workbook/CSV is authoritative for exact row-level reconciliation.

### SSP metadata and system-characteristics mappings visibly confirmed
- `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER` -> `system-security-plan.metadata.props` — `TBD`.
- `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED` -> `system-security-plan.metadata.published` — `Transform`; note indicates timestamp conversion to DateTimeWithTimezoneDatatype.
- `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED` -> `system-security-plan.metadata.last-modified` — `Transform`; note indicates timestamp conversion to DateTimeWithTimezoneDatatype.
- `SUBSYSTEMS` -> `system-security-plan.system-implementation.components[]` — `Reference`; create component entries with type `system`.
- `TRACKING_ID` -> `system-security-plan.metadata.document-ids[].identifier` — `Direct`.
- `FIRST_PUBLISHED` -> `system-security-plan.metadata.published` — `Transform`.
- `LAST_UPDATED` -> `system-security-plan.metadata.last-modified` — `Transform`.
- `SAP_ID` -> `system-security-plan.system-characteristics.system-ids[].id` — `Direct`.
- `AUTHORIZATION_PACKAGE_NAME` -> `system-security-plan.system-characteristics.system-name` — `Direct`.
- `ACRONYM` -> `system-security-plan.system-characteristics.system-name-short` — `Direct`.
- `OPERATIONAL_STATUS` -> `system-security-plan.system-characteristics.status.state` — `Transform`; note shows mapping to OSCAL status enum values.
- `INFORMATION_SYSTEM_TYPE` -> `system-security-plan.system-characteristics` — `Extension Property`; notes describe recognized system-type semantics.
- `FISMA_REPORTABLE` -> `system-security-plan.system-characteristics.props[]` — `Extension Property`, property name `fisma-reportable`.
- `FINANCIAL_SYSTEM` -> `system-security-plan.system-characteristics.props[]` — `Extension Property`, property name `financial-system`.
- `MISSION_CRITICAL` -> `system-security-plan.system-characteristics.props[]` — `Extension Property`, property name `mission-critical`.
- `CRITICAL_INFRASTRUCTURE` -> `system-security-plan.system-characteristics.props[]` — `Extension Property`, property name `critical-infrastructure`.
- `MISSION_PURPOSE` -> `system-security-plan.system-characteristics.description` — `Direct`.
- `PACKAGE_TYPE` -> `system-security-plan.system-characteristics.props[]` — `Extension Property`.
- `AUTHORIZATION_BOUNDARY_DESCRIPTION` -> `system-security-plan.system-characteristics.authorization-boundary.description` — `Direct`.
- `AUTHORIZATION_DECISION` -> `system-security-plan.system-characteristics.status.state` — `TBD` in the visible workbook row.
- `HELPER_PIA_CALC` -> system-characteristics custom property/props area — `Calculated`; note says helper field maps to a custom property within system-characteristics.
- `PACKAGE_TYPE_HELPER_CALC` -> system-characteristics custom property/props area — `Calculated`; note says transient calculation field, do not map.
- `AUTHORIZATION_COMMENTS` -> `system-security-plan.system-characteristics.status.remarks` — `Extension Property`; note says Archer authorization comments map to remarks in the status block.
- `PIA_REQUIRED` -> `system-security-plan.system-characteristics.props[]` — `Extension Property`, property name `pia-required`.
- `INFORMATION_CLASSIFICATION` -> `system-security-plan.system-characteristics.props[]` — `Extension Property`.
- `DAILY_LOSS_AMOUNT_FROM_OUTAGE` -> `system-security-plan.system-characteristics.props[]` — `TBD`; visible note says `All Nulls`.

### Security-impact mappings visibly confirmed
The clearer screenshots show confidentiality, integrity, and availability candidate mappings under `system-security-plan.system-characteristics.security-impact-level`, generally `Direct/Transform`, with notes to map to FIPS-199 impact level (`low/moderate/high`). Visible source fields include:
- `RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY`
- `CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE`
- `RECOMMENDED_INTEGRITY_CONTROL_CATEGORY`
- `INTEGRITY_CONTROL_CATEGORY_OVERRIDE`
- `AVAILABILITY_CONTROL_CATEGORY_OVERRIDE`
- `RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY`
- `PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY`
- `PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY`
- `CNSS_AVAILABILITY_RATING`
- `CNSS_CONFIDENTIALITY_RATING`
- `CNSS_INTEGRITY_RATING`

`SECURITY_CATEGORY` is also visible as an SSP System Characteristics direct mapping candidate, while `RECOMMENDED_SECURITY_CATEGORY` was separately rejected by the runtime mapping contract earlier and must not be treated as approved merely because related workbook rows exist.

### Responsible-party mappings visibly confirmed
The screenshots clearly show fields targeting `system-security-plan.metadata.responsible-parties[]`:
- `INFORMATION_OWNER_IO` — `Transform`; create party/link with role-id `system-owner` or `information-owner`.
- `INFORMATION_SYSTEM_OWNER_ISO` — `Transform`; create party/link with role-id `system-owner` or `information-owner`.
- `SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO` — `TBD`; needs analysis.
- `AUTHORIZING_OFFICIAL_AO` — `Transform`; create party/link with role-id `authorizing-official`.
- `INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO` — `Transform`; create party/link with role-id `system-security-officer`.
- `INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE` — `TBD`; needs analysis.
- `INFORMATION_SYSTEM_ADMINISTRATOR_ISA` — `TBD`; needs analysis.
- `AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR` — `TBD`; needs analysis.
- `PRIVACY_OFFICER_PO` — `Transform`; create party/link with role-id `privacy-officer`.

### System Implementation component references visibly confirmed
- `SOFTWARE` -> `system-security-plan.system-implementation.components[]` — `Reference`; create component entries with type `software`.
- `HARDWARE` -> `system-security-plan.system-implementation.components[]` — `Reference`; create component entries with type `hardware`.
- `INTERCONNECTIONS` -> `system-security-plan.system-implementation.components[]` — `Reference`; create component entries with type `interconnection`.
- `INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM` -> `system-security-plan.system-implementation.components[]` — `Reference`.
- `SAP_INTAKE_FORM_INTERCONNECTIONS` -> `system-security-plan.system-implementation.components[]` — `Reference`; create component entries with type `interconnection`.

These component-reference rows are consistent with the runtime component hydration checkpoint (1,435 lookup rows, 1,428 interconnection rows, 7 software rows), but they do not by themselves prove the entire SSP `system-implementation` branch is complete.

### Control Implementation backlog visibly confirmed
The screenshots show a large set of `SSP - Control Implementation` rows, predominantly `Mapping_Type = Extension Property`, with many blank concrete `OSCAL_Element_Path` cells. Repeated note: `May map to props[] or calculated from implemented-requirements count`.

Clearly visible examples include `COUNT_OF_CONTROLS`, `ALLOCATE_BASELINE_CONTROLS`, `CONTROL_SET_VERSION_NUMBER`, `COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS`, `COUNT_OF_CONTROLS_WITH_OPEN_POAMS`, `NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS`, `ARCHIVE_CONTROLS`, `BASELINE_CONTROLS_ALLOCATED_DATE`, `FULL_CONTROL_ASSESSMENT_HELPER`, `CONTROL_RISK_APPETITE`, `PCT_CURRENT_CONTROL_RISK_THRESHOLD`, `CONTROL_RISK_THRESHOLD_HELPER`, `COUNT_OF_CONTROLS_NOT_ASSESSED`, `COUNT_OF_INHERITED_CONTROLS_THAT_HAVE_BEEN_ARCHIVED`, `PCT_OF_SATISFIED_CONTROLS`, `CONTROL_OWNER_CO`, `SECURITY_CONTROL_ASSESSOR_SCA`, `ADD_ADDITIONAL_CONTROLS`, `ALLOCATED_CONTROLS`, `ARCHIVED_CONTROLS`, `INHERITED_CONTROL_SELECTION`, `INHERITABLE_CONTROLS`, `LINK_CNSS_CONTROLS_BY_CONFIDENTIALITY_RATING`, `LINK_CNSS_CONTROLS_BY_INTEGRITY_RATING`, `LINK_CNSS_CONTROLS_BY_AVAILABILITY_RATING`, `HELPER_ALLOCATED_CONTROLS`, `PRECONTROL_ALLOCATION_PROGRESS_VIEW`, `COUNT_OF_FULLY_IMPLEMENTED_CONTROLS`, `CONTROL_SET_VERSION_NUMBER_HRC`, `GS_LAB_CONTROL_ENTITY`, `CONTROL_STANDARDS`, `MASTER_CONTROLS`, `ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS`, `ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA_TEXT`, `EXPORT_CONTROL_ASSESSOR_ECA_TEXT`, `SECURITY_CONTROL_ASSESSOR_SCA_TEXT`, `EXPORT_CONTROLLED_DATA_ITAREAR_IF_APPLICABLE`, `COUNT_OF_CONTROLS_WITH_OPEN_POAMS`, `COUNT_OF_CONTROLS_MISSING_POAMRBD`, `ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA`, `ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE`, `CONTROL_SET_TO_ASSESS`, `CHANGE_CONTROL`, `HELPER_OTS_CONTROLS`, `COUNT_OF_INHERITED_CONTROLS`, `COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED`, `DATE_CONTINUE_TO_CONTROL_IMPLEMENTATION`, `_CURRENT_CONTROL_RISK_THRESHOLD`, `_OF_SATISFIED_CONTROLS`, and `HELPER_ALLOCATED_CONTROLS`.

Interpretation: these rows remain unresolved mapping-design backlog. A `props[]`/calculated suggestion in Notes is not an approved target contract and must not be converted into Control Implementation nodes automatically.

### Assessment Results mappings visibly confirmed
The workbook contains a substantial Assessment Results section. Visible risk/scoring fields target `assessment-results.results[].observations[].props[]` (path text is visually truncated in places but the observations/property branch is clear) and are generally `Extension Property`, with notes stating Archer-specific risk scoring maps as observation.

Clearly visible examples include `RISK_ACCEPTANCE_RBDS`, `VULNERABILITY_SCORE`, `ANTIVIRUS_SCORE`, `PATCH_SCORE`, `SECURITY_COMPLIANCE_SCORE`, `STANDARD_OPERATING_ENVIRONMENT_SCORE`, `COMPUTER_PASSWORD_AGE_SCORE`, `VULNERABILITY_REPORTING_SCORE`, `SECURITY_COMPLIANCE_REPORTING_SCORE`, `TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE`, `AVG_AUTHORIZATION_PACKAGE_RISK_SCORE`, `RISK_SCORE_GRADE`, `AVG_VULNERABILITY_SCORE`, `AVG_PATCH_SCORE`, `AVG_SECURITY_COMPLIANCE_REPORTING_SCORE`, `AVG_ANTIVIRUS_SCORE`, `AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE`, `AVG_COMPUTER_PASSWORD_AGE_SCORE`, `AVG_VULNERABILITY_REPORTING_SCORE`, `AVG_SECURITY_COMPLIANCE_SCORE`, `TOTAL_PACKAGE_INHERENT_RISK`, `TOTAL_PACKAGE_RESIDUAL_RISK`, `ADJUSTED_TOTAL_RISK_SCORE`, `ADJUSTED_AVERAGE_RISK_SCORE`, `CURRENT_HIGHEST_DEVICE_RISK_SCORE`, `CURRENT_AVERAGE_DEVICE_RISK_SCORE`, `CURRENT_CONTROL_RISK_SCORE`, `PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD`, `PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD`, `BASELINE_HIGHEST_DEVICE_RISK_SCORE`, `BASELINE_AVERAGE_DEVICE_RISK_SCORE`, `BASELINE_CONTROL_RISK_SCORE`, `CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD`, `CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD`, `INITIAL_RISK_ASSESSMENT`, and `RISK_ASSESSMENT_REPORT`.

### Other model evidence visible
- `FINDINGS` is visible as an Assessment Results reference row targeting a findings branch.
- `POAMS` is visible as a POA&M reference row.
- `REPORT_TO_BEGIN_ASSESSMENT`, `APPROVAL_TO_BEGIN_ASSESSMENT`, and `PREASSESSMENT_REVIEW_COMMENTS` are visible under Security Assessment Plan-related mappings.
- `BASELINE_RECOMMENDATION` is visible under Profile with target `profile.imports[]` and `Extension Property` semantics.

### Accuracy / completion conclusion
These clearer screenshots materially improve the transcription of the workbook. They confirm that SSP metadata, system-characteristics, responsible-party, security-impact, and component-reference mappings have substantial concrete target coverage, while the Control Implementation area still contains a large unresolved mapping backlog. Assessment Results is a separate model area and must not be counted toward SSP completion.

Do **not** claim full SSP completion from this workbook evidence. The correct next completion proof remains generated DIM/FACT + registry reconciliation for the `system-implementation`, `control-implementation`, and `implemented-requirements` branches, followed by assembled OSCAL schema/constraint validation.

Accuracy guardrail: no obscured/truncated value is treated as exact unless sufficiently legible in the clearer screenshots. Exact workbook/CSV values take precedence over this visual transcription.

Source: clearer phone screenshots supplied in ChatGPT conversation on 2026-09-10.