# SSP Metadata Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

> This is a transcription of the visible rows only. `TBD` and “Needs analysis” entries are unresolved and must not be treated as approved mappings.

## Core metadata

| Archer field | OSCAL element path | Mapping type | Notes |
|---|---|---|---|
| `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER` | `system-security-plan.metadata.props` | TBD | Confirm intended property name and value semantics. |
| `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED` | `system-security-plan.metadata.published` | Transform | Convert timestamp to OSCAL date-time. |
| `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED` | `system-security-plan.metadata.last-modified` | Transform | Convert timestamp to OSCAL date-time. |
| `TRACKING_ID` | `system-security-plan.metadata.document-ids[].identifier` | Transform | Preserve identifier scheme when available. |
| `FIRST_PUBLISHED` | `system-security-plan.metadata.published` | Direct | Validate/normalize as OSCAL date-time. |
| `LAST_UPDATED` | `system-security-plan.metadata.last-modified` | Transform | Convert timestamp to OSCAL date-time. |

## Responsible parties

All visible rows below target `system-security-plan.metadata.responsible-parties[]`.

| Archer field | Mapping type | Notes |
|---|---|---|
| `INFORMATION_OWNER_IO` | Transform | Create a party and link it with the applicable system/information-owner role. |
| `INFORMATION_SYSTEM_OWNER_ISO` | Transform | Create a party and link it with the applicable system/information-owner role. |
| `SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO` | TBD | Needs analysis. |
| `AUTHORIZING_OFFICIAL_AO` | Transform | Create a party and link with `role-id="authorizing-official"`. |
| `INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO` | Transform | Create a party and link with `role-id="system-security-officer"`. |
| `INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE` | TBD | Needs analysis. |
| `INFORMATION_SYSTEM_ADMINISTRATOR_ISA` | TBD | Needs analysis. |
| `AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR` | TBD | Needs analysis. |
| `PRIVACY_OFFICER_PO` | Transform | Create a party and link with `role-id="privacy-officer"`. |

## Review gates

- Define the property name/value for the confirmation flag.
- Resolve each TBD role before enabling generation.
- Deduplicate people represented in more than one Archer field.
- Validate UUIDs, role IDs, and OSCAL date-time formatting.
