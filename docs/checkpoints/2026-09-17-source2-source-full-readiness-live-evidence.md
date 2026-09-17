# Source 2 sources_source full-tab readiness — live evidence — 2026-09-17

## Repository checkpoint

Branch immediately before this checkpoint: `simplify-metadata-boundary` at `d66bbf06ccbf861bbdf70b8e2d97361d2d3751a0` (`Reset next step to finish full Source 2 Source tab`).

## Evidence basis

Owner-provided Snowflake screenshots from running `sql/SOURCE2_SOURCE_FULL_MAPPING_READINESS.sql` on 2026-09-17.

This checkpoint records only values visible in those screenshots. It does not infer source values that were not shown.

## Full 56-row Source worksheet population profile

The screenshots confirm that many rows outside the current 14-row Catalog runtime batch are populated and therefore cannot be closed merely as empty/deferred fields.

Notable populated fields visible in the live profile include:

### Catalog / Catalog metadata / hierarchy-related

- `SOURCE_DESCRIPTION`: 148 populated, VARCHAR
- `SOURCE_TRACKING_ID`: 148 populated, INTEGER
- `SOURCE_LINKS`: 62 populated, ARRAY/NULL_VALUE
- `TOPIC_REFERENCES`: 148 populated, ARRAY
- `CONTROL_STANDARDS`: 6 populated, ARRAY/NULL_VALUE
- `CONTROL_STANDARDS_FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`: 21 populated, ARRAY/NULL_VALUE
- `CONTROL_PROCEDURES`: 22 populated, ARRAY/NULL_VALUE
- `RELATED_CONTROL_PROCEDURES`: 21 populated, ARRAY/NULL_VALUE
- `RELATED_TO_KEY_CONTROLS`: 148 populated, INTEGER
- `DATE_CREATED`: 148 populated, TIMESTAMP_NTZ
- `LAST_UPDATED`: 148 populated, TIMESTAMP_NTZ
- `DEFAULT_RECORD_PERMISSIONS`: 144 populated, OBJECT/NULL_VALUE

Confirmed currently unpopulated among this area:

- `INFORMATION`: 0
- `ATTACHMENTS`: 0
- `MASTER_CONTROLS_AUTHORITATIVE_SOURCES`: 0
- duplicate/alternate `CONTROL_STANDARDS__FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`: 0
- `OFFICIAL_RETIREMENT_DATE`: 0
- `RTX_RETIREMENT_DATE`: 0
- prefixed first-published / last-updated / confirmed-in-Archer fields: 0
- prefixed Source content-id field: 0

### Assessment Results fields

- `COMPLIANCE_RATING`: 148 populated, OBJECT
- `COUNT_OF_NONCOMPLIANT_CONTROLS`: 148 populated, INTEGER
- `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS`: 21 populated, ARRAY/NULL_VALUE

Currently unpopulated in the live snapshot:

- `PCT_OF_NONCOMPLIANT_CONTROLS`: 0
- `_OF_NONCOMPLIANT_CONTROLS`: 0
- `FINDINGS`: 0
- `FINDINGS_AUTHORITATIVE_SOURCES`: 0
- `CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT`: 0
- `DEVIATIONS_AUTHORITATIVE_SOURCES`: 0
- `EVIDENCE_REPOSITORY`: 0

### Component Definition fields

- `POLICIES_AUTHORITATIVE_SOURCE_REFERENCES`: 11 populated, ARRAY/NULL_VALUE
- `POLICY_LEVEL_3_FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`: 23 populated, ARRAY/NULL_VALUE
- `LINKED_TO_POLICY_SOURCE_LEVEL`: 148 populated, OBJECT
- `NUMBER_OF_POLICIES_SOURCE_LEVEL`: 148 populated, INTEGER

Currently unpopulated:

- `POLICY_LEVEL_3`: 0
- duplicate/alternate `POLICY_LEVEL_3__FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`: 0

### Assessment Plan fields

- `ENGAGEMENT_SCOPE_IN_CONTROL_SOURCE`: 148 populated, OBJECT

Currently unpopulated:

- `COMPLIANCE_ENGAGEMENTS_SCOPE_PROCEDURES_FROM_SELECTED_AUTHORITATIVE_SOURCES`: 0
- `QUESTION_LIBRARY`: 0

## Array item-shape evidence

Visible read-only item-type counts:

- `CONTROL_STANDARDS`: INTEGER items, 1,751 occurrences
- `CONTROL_STANDARDS_FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`: OBJECT items, 6,964 occurrences
- `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS`: INTEGER items, 847 occurrences
- `POLICIES_AUTHORITATIVE_SOURCE_REFERENCES`: INTEGER items, 107 occurrences
- `RELATED_CONTROL_PROCEDURES`: OBJECT items, 33,817 occurrences
- `TOPIC_REFERENCES`: OBJECT items, 1,416 occurrences

These counts demonstrate that the remaining relationship fields are not all the same shape and must not be forced through one generic scalar mapping.

## Archer select/object evidence

Visible object-key profiles:

- `AUTH_SOURCES_FILTER`: `OtherText`, `ValuesListIds`
- `COMPLIANCE_RATING`: `OtherText`, `ValuesListIds`
- `CONTENT_SOURCE`: `OtherText`, `ValuesListIds`
- `CRITICALITY`: `OtherText`, `ValuesListIds`
- `ENGAGEMENT_SCOPE_IN_CONTROL_SOURCE`: `OtherText`, `ValuesListIds`
- `LINKED_TO_POLICY_SOURCE_LEVEL`: `OtherText`, `ValuesListIds`
- `SOURCE_TYPE`: `OtherText`, `ValuesListIds`
- `DEFAULT_RECORD_PERMISSIONS`: `GroupList`, `UserList`

The Archer value-list lookup coverage query showed zero unmatched select IDs for every displayed select field, including `COMPLIANCE_RATING`, `ENGAGEMENT_SCOPE_IN_CONTROL_SOURCE`, and `LINKED_TO_POLICY_SOURCE_LEVEL`.

## System metadata result

The final readiness query (query 11) returned zero populated rows for all three system-metadata workbook rows:

- `INSERT_DATE`: 0
- `UPDATE_DATE`: 0
- `CHECKSUM_VALUE`: 0

This confirms these fields are absent from the current `CURATED_JSON` snapshot. They remain outside the OSCAL payload and can be classified as excluded system metadata for this source contract.

## Current status and interpretation

The existing 14-row `Mapping/sources_source_runtime.csv` batch remains committed/read-back verified for Catalog.

The Source worksheet as a whole is **not yet complete**, because several fields assigned by the workbook to Assessment Results, Component Definition, Assessment Plan, Catalog relationships, and additional Catalog metadata are populated in the live source.

However, the live evidence now separates three different cases clearly:

1. populated fields that still need model/grain/relationship implementation,
2. unpopulated fields that can be reviewed and deferred without runtime output for the current snapshot,
3. system metadata fields that are confirmed absent from CURATED_JSON and excluded from OSCAL.

## Next action

Stay on `sources_source` before moving to Topic. Use this live evidence to produce the final 56-row disposition and promote only mappings whose OSCAL model/grain/relationship semantics are supported. In particular, do not treat populated Assessment Results, Component Definition, or Assessment Plan fields as Catalog properties merely to increase mapping coverage.
