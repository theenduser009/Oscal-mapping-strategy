# OSCAL Element Registry — collection snapshot

Date: 2026-09-09
Source: Snowflake query screenshot supplied during SSP mapper investigation.

Read-only observation: query filtered the OSCAL element registry to `IS_COLLECTION = TRUE` and returned 13 rows across SSP, POAM, and ASSESSMENT_RESULTS.

## Visible rows

| OSCAL_MODEL_KEY | NODE_PATH | ELEMENT_TYPE | PARENT_NODE_PATH | IS_COLLECTION | INSTANCE_KEY_RULE | PROCESS_ORDER | IS_ACTIVE | ITEM_PATH |
|---|---|---|---|---|---|---:|---|---|
| SSP | system-security-plan.system-characteristics.props[] | props | system-security-plan.system-characteristics | TRUE | SOURCE_FIELD_NAME+VALUE | 3 | TRUE | $ |
| SSP | system-security-plan.metadata.responsible-parties[] | responsible-parties | system-security-plan.metadata | TRUE | SOURCE_FIELD_NAME+ID | 3 | TRUE | UserList[] |
| SSP | system-security-plan.metadata.document-ids[] | document-ids | system-security-plan.metadata | TRUE | VALUE | 3 | TRUE | $ |
| SSP | system-security-plan.system-characteristics.system-ids[] | system-ids | system-security-plan.system-characteristics | TRUE | VALUE | 3 | TRUE | $ |
| SSP | system-security-plan.system-implementation.components[] | components | system-security-plan.system-implementation | TRUE | CONTENT_ID | 3 | TRUE | $ |
| POAM | plan-of-action-and-milestones.poam-items[] | poam-items | plan-of-action-and-milestones | TRUE | CONTENT_ID | 2 | TRUE | null |
| ASSESSMENT_RESULTS | assessment-results.results[] | results | assessment-results | TRUE | SOURCE_RECORD_ID | 2 | TRUE | null |
| ASSESSMENT_RESULTS | assessment-results.results[].props[] | props | assessment-results.results[] | TRUE | SOURCE_FIELD_NAME | 3 | TRUE | null |
| ASSESSMENT_RESULTS | assessment-results.results[].observations[] | observations | assessment-results.results[] | TRUE | SOURCE_FIELD_NAME | 3 | TRUE | null |
| SSP | system-security-plan.system-implementation.components[].component.protocols[] | protocols | system-security-plan.system-implementation.components[].component | TRUE | CONTENT_ID | 8 | TRUE | $ |
| SSP | system-security-plan.system-implementation.components[].component.props[] | props | system-security-plan.system-implementation.components[].component | TRUE | CONTENT_ID | 5 | TRUE | $ |
| SSP | system-security-plan.system-implementation.components[].component.links[] | links | system-security-plan.system-implementation.components[].component | TRUE | CONTENT_ID | 6 | TRUE | $ |
| SSP | system-security-plan.system-implementation.components[].component.responsible-roles[] | responsible-roles | system-security-plan.system-implementation.components[].component | TRUE | CONTENT_ID | 7 | TRUE | $ |

## Why this checkpoint matters

This captures the actual registry collection metadata currently visible in Snowflake so later mapper/Codex work does not have to reconstruct it from phone screenshots. In particular, SSP nested component children currently use `CONTENT_ID`, while top-level SSP collections use distinct identity rules (`SOURCE_FIELD_NAME+VALUE`, `SOURCE_FIELD_NAME+ID`, `VALUE`, and `CONTENT_ID`).

No Snowflake data was changed by creating this checkpoint.