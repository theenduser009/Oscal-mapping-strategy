# Mapping Artifact Screenshot Evidence — 2026-09-09

This checkpoint records what is visible in the user's Excel mapping artifact screenshots from `archer_to_oscal_mapping.xlsx`. It is evidence only; the screenshots show a filtered view (`103 of 609 records found`) and therefore do **not** replace a full workbook parse.

## Visible columns

The screenshots show at least these mapping columns:

- `Archer_Field_Name`
- `OSCAL_Model`
- `OSCAL_Element_Path`
- `Mapping_Type`
- `Notes`

## Confirmed visible SSP mappings

### Metadata / system-characteristics

Visible examples include:

```text
ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER
  OSCAL model: SSP - Metadata
  target: system-security-plan.metadata.props
  mapping type: TBD

ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED
  OSCAL model: SSP - Metadata
  target: system-security-plan.metadata.published
  mapping type: Transform

ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED
  OSCAL model: SSP - Metadata
  target: system-security-plan.metadata.last-modified
  mapping type: Transform

TRACKING_ID
  OSCAL model: SSP - Metadata
  target: system-security-plan.metadata.document-ids[].identifier
  mapping type: Direct

FIRST_PUBLISHED
  OSCAL model: SSP - Metadata
  target: system-security-plan.metadata.published
  mapping type: Transform

LAST_UPDATED
  OSCAL model: SSP - Metadata
  target: system-security-plan.metadata.last-modified
  mapping type: Transform

SAP_ID
  OSCAL model: SSP - System Characteristics
  target: system-security-plan.system-characteristics.system-ids[].id
  mapping type: Direct

AUTHORIZATION_PACKAGE_NAME
  OSCAL model: SSP - System Characteristics
  target: system-security-plan.system-characteristics.system-name
  mapping type: Direct

ACRONYM
  OSCAL model: SSP - System Characteristics
  target: system-security-plan.system-characteristics.system-name-short
  mapping type: Direct

OPERATIONAL_STATUS
  OSCAL model: SSP - System Characteristics
  target: system-security-plan.system-characteristics.status.state
  mapping type: Transform

MISSION_PURPOSE
  OSCAL model: SSP - System Characteristics
  target: system-security-plan.system-characteristics.description
  mapping type: Direct

AUTHORIZATION_BOUNDARY_DESCRIPTION
  OSCAL model: SSP - System Characteristics
  target: system-security-plan.system-characteristics.authorization-boundary
  mapping type: Direct

AUTHORIZATION_COMMENTS
  OSCAL model: SSP - System Characteristics
  target: system-security-plan.system-characteristics.status.remarks
  mapping type: Extension Property
```

### Extension properties

The visible artifact intentionally maps many Archer-specific fields to OSCAL `props[]`, including examples such as:

```text
INFORMATION_SYSTEM_TYPE
FISMA_REPORTABLE
FINANCIAL_SYSTEM
MISSION_CRITICAL
CRITICAL_INFRASTRUCTURE
PACKAGE_TYPE
PIA_REQUIRED
INFORMATION_CLASSIFICATION
```

The notes indicate these are intended as extension properties rather than first-class OSCAL fields. This is consistent with the repository rule that approved Archer-specific attributes should be emitted as stable OSCAL `name`/`value` props.

`HELPER_PTA_CALC` is visible as `Calculated`; earlier reviewed logic treats it as transient and it must not become a final OSCAL property.

### FIPS-199 / security-impact candidates

The screenshots confirm that the mapping artifact already contains many source candidates aimed at `system-security-plan.system-characteristics.security-impact-level`, including:

```text
RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY
CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE
RECOMMENDED_INTEGRITY_CONTROL_CATEGORY
INTEGRITY_CONTROL_CATEGORY_OVERRIDE
RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY
AVAILABILITY_CONTROL_CATEGORY_OVERRIDE
PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY
PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY
CNSS_AVAILABILITY_RATING
CNSS_CONFIDENTIALITY_RATING
CNSS_INTEGRITY_RATING
```

These are marked `Direct/Transform` with notes to map to a FIPS-199 impact level such as low/moderate/high. This corroborates the previously implemented FIPS-199 lookup/crosswalk logic and also explains why the mapper must resolve multiple candidate sources deterministically rather than treating each row as an independent OSCAL node.

## Responsible-party mappings visible

The artifact includes several metadata responsible-party candidates targeting:

```text
system-security-plan.metadata.responsible-parties[]
```

Visible fields include:

```text
INFORMATION_OWNER_IO
INFORMATION_SYSTEM_OWNER_ISO
AUTHORIZING_OFFICIAL_AO
INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO
PRIVACY_OFFICER_PO
INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE
INFORMATION_SYSTEM_ADMINISTRATOR_ISA
AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR
SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO
```

Mapping types are a mix of `Transform` and `TBD`, and notes indicate creation of party/role relationships. Therefore these rows are not safe to emit generically until the approved role mapping and party identity construction are explicit.

## Component reference candidates visible

The screenshots show multiple `Reference` mappings into:

```text
system-security-plan.system-implementation.components[]
```

Visible Archer fields include:

```text
SUBSYSTEMS
SOFTWARE
HARDWARE
INTERCONNECTIONS
INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM
SAP_INTAKE_FORM_INTERCONNECTIONS
```

Notes describe creating component entries with types such as `system`, `software`, `hardware`, or `interconnection`.

This is important because the current runtime audit found six executable component source candidates, 4,804 generated component nodes, but only 944 source records with candidate coverage and 1,869 records without a populated component candidate. The screenshots independently confirm why `components[]` requires deliberate source-candidate reconciliation and real collection-instance identity rather than a simple one-row-to-one-node rule.

## Control-implementation evidence

A large portion of the filtered screenshot is labeled `SSP - Control Implementation`, with many rows marked `Extension Property`, but the visible `OSCAL_Element_Path` cells are blank for those rows.

Visible examples include:

```text
COUNT_OF_CONTROLS
ALLOCATE_BASELINE_CONTROLS
CONTROL_SET_VERSION_NUMBER
COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS
COUNT_OF_CONTROLS_WITH_OPEN_POAMS_ANDOR_RBDS
NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS
ARCHIVE_CONTROLS
BASELINE_CONTROLS_ALLOCATED_DATE
ALLOCATED_CONTROLS
ARCHIVED_CONTROLS
INHERITED_CONTROL_SELECTION
INHERITABLE_CONTROLS
LINK_CNSS_CONTROLS_BY_CONFIDENTIALITY_RATING
LINK_CNSS_CONTROLS_BY_INTEGRITY_RATING
LINK_CNSS_CONTROLS_BY_AVAILABILITY_RATING
COUNT_OF_FULLY_IMPLEMENTED_CONTROLS
CONTROL_RISK_APPETITE
CONTROL_RISK_THRESHOLD
COUNT_OF_CONTROLS_NOT_ASSESSED
COUNT_OF_INHERITED_CONTROLS_THAT_HAVE_BEEN_ARCHIVED
PCT_OF_SATISFIED_CONTROLS
CONTROL_OWNER_CO
SECURITY_CONTROL_ASSESSOR_SCA
ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS
EXPORT_CONTROL_ASSESSOR_ECA_TEXT
SECURITY_CONTROL_ASSESSOR_SCA_TEXT
COUNT_OF_CONTROLS_WITH_OPEN_POAMS
COUNT_OF_CONTROLS_MISSING_POAMRBD
ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA
ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE
CONTROL_SET_TO_ASSESS
CHANGE_CONTROL
HELPER_OTS_CONTROLS
COUNT_OF_INHERITED_CONTROLS
COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED
DATE_CONTINUE_TO_CONTROL_IMPLEMENTATION
CURRENT_CONTROL_RISK_THRESHOLD
OF_SATISFIED_CONTROLS
HELPER_ALLOCATED_CONTROLS
```

This is a major clarification of the current audit result: **the CSV model label `SSP - Control Implementation` is not sufficient to create the OSCAL `control-implementation` branch.** Many rows appear to have no concrete OSCAL target path. The registry and mapping artifact therefore still need an approved structural path and field-level target design before these can participate in the mapper.

Similarly, the current audit's `ADD_STRUCTURAL_REGISTRY_PATH` / `ADD_REGISTRY_AND_MAPPING_SOURCE` findings for `control-implementation` should not be "fixed" by assigning all of these rows blindly to one `props[]` target.

## Mapping-artifact design implications

1. `OSCAL_Model` is a human/domain grouping label, not a reliable target-path contract by itself.
2. `OSCAL_Element_Path` remains the authoritative mapping destination evidence. Blank paths must not be inferred from the model label.
3. Multiple FIPS/security-impact rows intentionally converge on the same semantic target and require precedence/collision rules.
4. Multiple component-reference fields converge on one collection and require real member identity and hydration rules.
5. Several responsible-party rows still require role/party transformation design.
6. Numerous Control Implementation rows are currently conceptual/backlog mappings, not executable OSCAL mappings.
7. `TBD`, helper, calculated, and extension-property classifications must remain fail-closed unless an approved dispatcher rule exists.

## Safety conclusion

These screenshots reinforce the current engineering position: the mapper graph is structurally healthy, but mapping completeness and branch design remain the blockers. Do not enable writes, invent target paths, or infer OSCAL structure solely from `OSCAL_Model` labels.

`EXECUTE_WRITES` remains `False`.
