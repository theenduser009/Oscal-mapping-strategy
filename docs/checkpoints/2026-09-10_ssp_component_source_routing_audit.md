# SSP Component Source Routing Audit — 2026-09-10

Source: Snowflake `NB_ARCHER_OSCAL_MAPPER_V2` screenshots supplied during live validation.

## Safety / run state
- Aggregate-only output; no component IDs, source-record IDs, payloads, or source values printed.
- Writes executed: `False`.
- No database objects or rows were changed.

## Core audit counts
- Canonical Excel component mapping rows: 6
- Reference occurrences: 4,804
- Distinct source-record/component/type pairs: 4,792
- Graph component nodes: 4,792
- Distinct component IDs: 1,436
- Invalid reference members: 0
- Unexpected non-array reference roots: 15,632
- Cross-type component IDs: 0
- Source pairs missing from graph: 0
- Graph pairs missing from source: 0
- Invalid graph component nodes: 0
- Lookup source profiling failures: 0
- Accepted-baseline drift checks: 0

## Excel source-field routes observed
### SUBSYSTEMS
- Declared type: system
- Flattened members: 0
- Valid references: 0
- Route: `NO_RUNTIME_REFERENCE_EVIDENCE`

### SOFTWARE
- Declared type: software
- Flattened members: 7
- Valid references: 7
- Distinct component IDs: 7
- `ARCHER_CONTENT_INTERCONNECTIONS_RAW`: 0 matched IDs / rows
- `ARCHER_CONTENT_SOFTWARE_RAW`: 7 matched IDs / 7 rows
- Route: `OWNER_FIELD_APPROVAL_REQUIRED`

### HARDWARE
- Declared type: hardware
- Flattened members: 1
- Valid references: 1
- Distinct component IDs: 1
- No match in either candidate object shown
- Route: `NO_HYDRATION_BEARING_SOURCE`

### INTERCONNECTIONS
- Declared type: interconnection
- Flattened members: 4,444
- Valid references: 4,444
- Distinct component IDs: 1,405
- `ARCHER_CONTENT_INTERCONNECTIONS_RAW`: 1,405 matched distinct IDs / 1,405 lookup rows
- `ARCHER_CONTENT_SOFTWARE_RAW`: 0
- Route: `OWNER_FIELD_APPROVAL_REQUIRED`

### INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM
- Declared type: interconnection
- Flattened members: 352
- Valid references: 352
- Distinct component IDs: 82
- `ARCHER_CONTENT_INTERCONNECTIONS_RAW`: 82 matched distinct IDs / 82 rows
- `ARCHER_CONTENT_SOFTWARE_RAW`: 0
- Route: `OWNER_FIELD_APPROVAL_REQUIRED`

### SAP_INTAKE_FORM_INTERCONNECTIONS
- Declared type: interconnection
- Flattened members: 0
- Valid references: 0
- Route: `NO_RUNTIME_REFERENCE_EVIDENCE`

## Hydration field evidence
### Interconnection candidate
`ARCHER_CONTENT_INTERCONNECTIONS_RAW` matched 1,428 distinct IDs in the hydration evidence section.
- title: `INTERCONNECTION_NAME` — populated matched IDs 1,428
- title: `THIRD_PARTY_NAME` — 31
- description: `DESCRIPTION` — 968
- description: `THIRD_PARTY_DESCRIPTION` — 16
- status category: no populated candidate shown
- Field/transformation approved: False

### Software candidate
`ARCHER_CONTENT_SOFTWARE_RAW` matched 7 distinct IDs.
- title: `SOFTWARE_NAME` — 7
- title: `BUSINESS_NAME` — 7
- description: `DESCRIPTION` — 7
- status: `INSTALL_STATUS` — 7
- status: `OPERATIONAL_STATUS` — 7
- status: `RECORD_STATUS` — 7
- status: `SERVICENOW_LIFE_CYCLE_STAGE_STATUS` — 7
- Field/transformation approved: False

## Routing audit conclusion
Result shown by notebook:

`COMPONENT ROUTING OR FIELD-APPROVAL GAPS REMAIN; NO SOURCE OR TRANSFORMATION WAS APPROVED`

Blocking reason count: 8
1. `AMBIGUOUS_INTERCONNECTION_DESCRIPTION_FIELD_CHOICE`
2. `AMBIGUOUS_INTERCONNECTION_TITLE_FIELD_CHOICE`
3. `AMBIGUOUS_SOFTWARE_STATUS_FIELD_CHOICE`
4. `AMBIGUOUS_SOFTWARE_TITLE_FIELD_CHOICE`
5. `INCOMPLETE_INTERCONNECTION_DESCRIPTION_COVERAGE`
6. `MISSING_HARDWARE_SOURCE`
7. `MISSING_INTERCONNECTION_STATUS_FIELD_CATEGORY`
8. `REFERENCE_SHAPE_GAP`

No lookup source, field, precedence rule, or status transformation was configured by this audit. The audit explicitly remains non-authorizing and read-only.
