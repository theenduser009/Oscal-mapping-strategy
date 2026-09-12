# SSP Control Implementation Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

> This is a partial transcription of visible rows. Most listed fields have no approved OSCAL element path in the worksheet and are marked as extension-property or calculated candidates. They require design review before implementation.

## Visible mappings

| Archer field | OSCAL model | OSCAL element path | Mapping type | Notes |
|---|---|---|---|---|
| `COUNT_OF_CONTROLS` | SSP - Control Implementation | Unspecified | Extension Property | Candidate for `props[]` or calculation from `implemented-requirements`. |
| `ALLOCATE_BASELINE_CONTROLS` | SSP - Control Implementation | Unspecified | TBD | Requires mapping decision. |
| `CONTROL_SET_VERSION_NUMBER` | SSP - Control Implementation | `system-security-plan.system-characteristics.props[]` | Extension Property | Add a named property. |
| `COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS` | SSP - Control Implementation | Unspecified | Extension Property | Candidate for `props[]` or calculated value. |
| `COUNT_OF_CONTROLS_WITH_OPEN_POAMS_ANDOR_RBDS` | SSP - Control Implementation | Unspecified | Extension Property | Candidate for `props[]` or calculated value. |
| `NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS` | SSP - Control Implementation | Unspecified | Extension Property | Candidate for `props[]` or calculated value. |
| `ARCHIVE_CONTROLS` | SSP - Control Implementation | Unspecified | Extension Property | Candidate for `props[]` or calculated value. |
| `CONTROL_OWNER_CO` | SSP - Control Implementation | Unspecified | Extension Property | Candidate for a property or derivation from implemented requirements. |
| `SECURITY_CONTROL_ASSESSOR_SCA` | SSP - Control Implementation | Unspecified | Extension Property | Candidate for a property or related party/role design. |

## Additional visible extension-property/calculated candidates

- `ADD_ADDITIONAL_CONTROLS`
- `ALLOCATED_CONTROLS`
- `ARCHIVED_CONTROLS`
- `INHERITED_CONTROL_SELECTION`
- `INHERITABLE_CONTROLS`
- `LINK_CNSS_CONTROLS_BY_CONFIDENTIALITY_RATING`
- `LINK_CNSS_CONTROLS_BY_INTEGRITY_RATING`
- `LINK_CNSS_CONTROLS_BY_AVAILABILITY_RATING`
- `HELPER_ALLOCATED_CONTROLS`
- `PRECONTROL_ALLOCATION_PROGRESS_VIEW`
- `COUNT_OF_FULLY_IMPLEMENTED_CONTROLS`
- `CONTROL_SET_VERSION_NUMBER_HRC`
- `GS_LAB_CONTROL_ENTITY`
- `CONTROL_STANDARDS`
- `MASTER_CONTROLS`
- `ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS`
- `ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA_TEXT`
- `EXPORT_CONTROL_ASSESSOR_ECA_TEXT`
- `SECURITY_CONTROL_ASSESSOR_SCA_TEXT`
- `EXPORT_CONTROLLED_DATA_ITARAR_IF_APPLICABLE`
- `COUNT_OF_CONTROLS_WITH_OPEN_POAMS`
- `COUNT_OF_CONTROLS_MISSING_POAMRBD`
- `ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA`
- `ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE`
- `CONTROL_SET_TO_ASSESS`
- `CHANGE_CONTROL`
- `HELPER_OTS_CONTROLS`
- `COUNT_OF_INHERITED_CONTROLS`
- `COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED`
- `DATE_CONTINUE_TO_CONTROL_IMPLEMENTATION`
- `CURRENT_CONTROL_RISK_THRESHOLD`
- `OF_SATISFIED_CONTROLS`
- `HELPER_ALLOCATED_CONTROLS`

## Safest next action

Define and approve one canonical OSCAL representation for these derived/control-summary fields—prefer calculation from `control-implementation.implemented-requirements` where possible, and use namespaced `props[]` only when no native OSCAL representation exists. Then test the approved mapping in preview/read-only mode before enabling writes.
