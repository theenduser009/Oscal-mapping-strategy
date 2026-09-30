# SSP System Characteristics Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

> This is a transcription of the visible rows only. `TBD`, calculated, extension-property, and reference entries require validation before writes are enabled.

## Core system characteristics

| Archer field | OSCAL element path | Mapping type | Notes |
|---|---|---|---|
| `SAP_ID` | `system-security-plan.system-characteristics.system-ids[].id` | Direct | Validate identifier shape against the target OSCAL version. |
| `AUTHORIZATION_PACKAGE_NAME` | `system-security-plan.system-characteristics.system-name` | Direct |  |
| `ACRONYM` | `system-security-plan.system-characteristics.system-name-short` | Direct |  |
| `OPERATIONAL_STATUS` | `system-security-plan.system-characteristics.status.state` | Transform | Map to an allowed OSCAL status value. |
| `INFORMATION_SYSTEM_TYPE` | `system-security-plan.system-characteristics` | Extension Property | Translate the Archer value into a defined system-type property. |
| `FISMA_REPORTABLE` | `system-security-plan.system-characteristics.props[]` | Extension Property | Add a property named `fisma-reportable`. |
| `FINANCIAL_SYSTEM` | `system-security-plan.system-characteristics.props[]` | Extension Property | Add a property named `financial-system`. |
| `MISSION_CRITICAL` | `system-security-plan.system-characteristics.props[]` | Extension Property | Add a property named `mission-critical`. |
| `CRITICAL_INFRASTRUCTURE` | `system-security-plan.system-characteristics.props[]` | Extension Property | Add a property named `critical-infrastructure`. |
| `MISSION_PURPOSE` | `system-security-plan.system-characteristics.description` | Direct |  |
| `PACKAGE_TYPE` | `system-security-plan.system-characteristics.props[]` | Extension Property | Define and approve the property name. |
| `AUTHORIZATION_BOUNDARY_DESCRIPTION` | `system-security-plan.system-characteristics.authorization-boundary.description` | Direct |  |
| `AUTHORIZATION_DECISION` | `system-security-plan.system-characteristics.status.state` | TBD | Confirm whether Archer values can be represented by the OSCAL status enumeration. |
| `HELPER_PTA_CALC` | `system-security-plan.system-characteristics.props[]` | Calculated | Custom calculated property. |
| `PACKAGE_TYPE_HELPER_CALC` | `system-security-plan.system-characteristics.props[]` | Calculated | Transient calculation field; confirm whether it should persist. |
| `AUTHORIZATION_COMMENTS` | `system-security-plan.system-characteristics.status.remarks` | Extension Property | Validate whether native remarks or a property is intended. |
| `PIA_REQUIRED` | `system-security-plan.system-characteristics.props[]` | Extension Property | Add a property named `pia-required`. |
| `ATOIATO_DATE` | `system-security-plan.system-characteristics.date-authorized` | Transform | Convert timestamp to OSCAL date. |

## Security impact mappings

| Archer field | OSCAL element path | Mapping type |
|---|---|---|
| `RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY` | `system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality` | Direct/Transform |
| `CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE` | `system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality` | Direct/Transform |
| `RECOMMENDED_INTEGRITY_CONTROL_CATEGORY` | `system-security-plan.system-characteristics.security-impact-level.security-objective-integrity` | Direct/Transform |
| `INTEGRITY_CONTROL_CATEGORY_OVERRIDE` | `system-security-plan.system-characteristics.security-impact-level.security-objective-integrity` | Direct/Transform |
| `AVAILABILITY_CONTROL_CATEGORY_OVERRIDE` | `system-security-plan.system-characteristics.security-impact-level.security-objective-availability` | Direct/Transform |
| `RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY` | `system-security-plan.system-characteristics.security-impact-level.security-objective-availability` | Direct/Transform |
| `SECURITY_CATEGORY` | `system-security-plan.system-characteristics.security-sensitivity-level` | Direct |
| `PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY` | `system-security-plan.system-characteristics.security-impact-level.security-objective-integrity` | Direct/Transform |
| `PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY` | `system-security-plan.system-characteristics.security-impact-level.security-objective-availability` | Direct/Transform |
| `FULL_CONTROL_ASSESSMENT_HELPER` | `system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality` | Direct/Transform |
| `CNSS_AVAILABILITY_RATING` | `system-security-plan.system-characteristics.security-impact-level.security-objective-availability` | Direct/Transform |
| `CNSS_CONFIDENTIALITY_RATING` | `system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality` | Direct/Transform |
| `CNSS_INTEGRITY_RATING` | `system-security-plan.system-characteristics.security-impact-level.security-objective-integrity` | Direct/Transform |

All impact values must be normalized to the permitted FIPS 199 values: `low`, `moderate`, or `high`.

## Referenced system components

These source fields are shown under SSP System Implementation and reference `system-security-plan.system-implementation.components[]`; they are listed here because they support the system-characteristics inventory.

| Archer field | Mapping type | Component type |
|---|---|---|
| `SUBSYSTEMS` | Reference | `system` |
| `SOFTWARE` | Reference | `software` |
| `HARDWARE` | Reference | `hardware` |
| `INTERCONNECTIONS` | Reference | `interconnection` |
| `INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM` | Reference | `interconnection` |
| `SAP_INTAKE_FORM_INTERCONNECTIONS` | Reference | `interconnection` |

## Review gates

- Confirm the `SAP_ID` target against the active OSCAL schema.
- Approve property names and namespaces for all extension properties.
- Resolve `AUTHORIZATION_DECISION` and calculated-field persistence.
- Define precedence when recommended, override, ProgramSite, and CNSS impact values disagree.
- Validate referenced component UUID generation and deduplication in preview mode before enabling writes.


## Universal source-field lineage props

Owner decision September 30, 2026: source-field lineage is a universal mapper behavior, not a per-field mapping task.

For every approved FIELD mapping, the compiler locates the nearest registered OSCAL `props[]` extension point that encloses the mapped target. When that source field actually maps a value, the graph builder emits one lineage property there:

```json
{
  "name": "source-field",
  "ns": "urn:company:oscal:lineage:v1",
  "class": "<normalized canonical OSCAL target path>",
  "value": "<exact Archer SOURCE_FIELD_NAME>"
}
```

No additional lineage rows are required in `ARCHER_OSCAL_MAPPINGS.csv`. The behavior is registry-driven and applies the same way to every approved source field that has a valid enclosing registered `props[]` collection. Native OSCAL values are unchanged. Multiple agreeing source fields produce multiple lineage props; existing conflicting-singleton validation still fails closed.

If an OSCAL area has no registered enclosing `props[]` extension point, the mapper does not invent one.
