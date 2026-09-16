# Validation 06 live result — System Characteristics core

Date: **2026-09-16**

Evidence: owner-provided Snowflake notebook screenshot from the existing SSP PREVIEW session.

## Live result

Validator: `06_SSP_SYSTEM_CHARACTERISTICS_CORE`
Validator version: `2026-09-15-r1`
Status: **PASS**
Writes performed by validator: **false**
Source key: `source-one`

Reported counts:

- SOURCE_RECORDS: 2,813
- SYSTEM_CHARACTERISTICS_NODES: 2,813
- SYSTEM_ID_NODES: 2,813
- SCALAR_VALUES_CHECKED:
  - system-name: 2,813
  - description: 2,780
  - system-name-short: 1,548
- SYSTEM_IDS_CHECKED: 2,813
- CORE_RELATED_EDGES: 5,626
- FAILURE_COUNTS: `{}`

The screenshot explicitly lists the following as **not tested by Validation 06**:

- System Characteristics props
- status/state/remarks
- authorization boundary
- date-authorized
- security-impact-level
- full OSCAL schema conformance
- business approval of field meanings
- target persistence

## Interpretation

This PASS supports the current mapping-driven core checks for:

- `AUTHORIZATION_PACKAGE_NAME -> system-security-plan.system-characteristics.system-name`
- `ACRONYM -> system-security-plan.system-characteristics.system-name-short`
- `MISSION_PURPOSE -> system-security-plan.system-characteristics.description`
- `SAP_ID -> system-security-plan.system-characteristics.system-ids[].id`

It does **not** broaden approval to the untested System Characteristics mappings listed above.

## Additional owner inspection

The owner also ran the SSP Metadata root-to-leaf drill-down for one source record and observed the expected persisted hierarchy:

- level 1: `system-security-plan`
- level 2: `metadata`
- level 3: `document-ids`, `parties`, `responsible-parties`, `roles`

The displayed payloads showed party UUIDs, responsible-party `party-uuids` and `role-id`, and role `id`/`title` values consistent with the currently mapped Metadata branch. This is targeted inspection evidence, not full-model conformance.

## Current checkpoint

Source 1 core SSP mapping evidence now includes:

- Registry validation: PASS
- CSV/registry compilation validation: PASS
- Document-ID validation: PASS
- Metadata graph/reference validation: PASS
- System Characteristics core validation: PASS
- Timestamp lexical validation: known FAIL, remediation deferred to SME

Next work should remain mapping-driven: validate the remaining approved System Characteristics mappings (props, status/remarks, authorization boundary, date-authorized, security-impact-level) before calling the full SSP mapping scope complete.
