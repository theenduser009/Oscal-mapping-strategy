# SSP Notebook Progress

Last reconciled: 2026-09-01

## Purpose

This file is the persistent checkpoint for the Archer-to-OSCAL SSP notebook. It records only work confirmed through the mapping inventory, registry, notebook output, or physical Snowflake data.

## Authoritative objects

- SSP registry: `RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY`
- Archer source: `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`
- SSP element DIM: `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT`
- Mapping source of truth: `canonical_mapping_df`
- Existing Archer source dataframe: `source_df`

The registry defines structural hierarchy. The mapping data defines source-to-target field behavior. The DIM shows what has actually been materialized.

## Notebook safety guardrails

- `EXECUTE_WRITES` is defined once, in Cell 1.
- Cell 6 consumes that flag and must not redefine it.
- `EXECUTE_WRITES = False` means zero DIM or FACT writes.
- Perform read-only inspection and canonical validation before changing mapping code or running a MERGE.
- Keep the engine generic and metadata-driven; do not add SSP-specific patches when a registry/mapping rule can express the behavior.
- Preserve deterministic node/edge identities and idempotent MERGE behavior.

The duplicate `EXECUTE_WRITES = True` assignment previously found in Cell 6 was removed. That duplicate explained why a load ran while Cell 1 appeared to be read-only.

## SSP registry hierarchy

The registry contains 18 active SSP paths:

```text
system-security-plan
|-- metadata
|   |-- document-ids[]
|   `-- responsible-parties[]
|-- system-characteristics
|   |-- authorization-boundary
|   |-- props[]
|   |-- security-impact-level
|   |-- status
|   `-- system-ids[]
|-- system-implementation
|   `-- components[]
|       `-- component
|           |-- props[]
|           |-- links[]
|           |-- responsible-roles[]
|           `-- protocols[]
`-- control-implementation
```

## Physical SSP DIM inventory

The last verified DIM inventory contained 12 element types:

| Element type | Rows |
|---|---:|
| `authorization-boundary` | 3,133 |
| `components` | 54,624 |
| `document-ids` | 3,514 |
| `metadata` | 3,514 |
| `props` | 19,452 |
| `responsible-parties` | 23,179 |
| `security-impact-level` | 2,950 |
| `status` | 3,514 |
| `system-characteristics` | 3,514 |
| `system-ids` | 3,514 |
| `system-implementation` | 2,164 |
| `system-security-plan` | 3,514 |

The deeper `component` leaf element types and `control-implementation` were registered but were not yet visible as separate DIM element types.

The last end-to-end load verification reported:

```text
DIM expected / matched: 61,685 / 61,685
FACT expected / matched: 58,872 / 58,872
LOAD VERIFIED
```

## Confirmed completed mappings

### Metadata

- `metadata.published`
- `metadata.last-modified`
- `metadata.document-ids[].identifier`

All currently defined Direct/Transform metadata mappings above were implemented and validated.

### Responsible parties

The five approved transformations were verified across the loaded data:

| Archer source field | OSCAL `role-id` |
|---|---|
| `INFORMATION_OWNER_IO` | `information-owner` |
| `INFORMATION_SYSTEM_OWNER_ISO` | `system-owner` |
| `AUTHORIZING_OFFICIAL_AO` | `authorizing-official` |
| `INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO` | `system-security-officer` |
| `PRIVACY_OFFICER_PO` | `privacy-officer` |

Four architect-marked mappings remain `TBD / Needs analysis` and must not be marked done:

- `SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO`
- `INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE`
- `INFORMATION_SYSTEM_ADMINISTRATOR_ISA`
- `AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR`

For test SSP `565189`, six responsible-party rows were physically present: three correctly transformed OSCAL role objects and three unresolved raw Archer user objects. The raw pass-through rows are loaded but are not complete mappings.

### FIPS-199 security impact

All 10 source mapping rows feeding these three OSCAL targets were implemented and verified, including Low/Moderate/High lookup, legacy LOE values, and null handling:

- `security-objective-confidentiality`
- `security-objective-integrity`
- `security-objective-availability`

## System Characteristics status

The parent `system-characteristics` payload is substantially populated. The loaded records include fields such as description, date-authorized, information-system-type, security-sensitivity-level, system-name, and system-name-short.

For test SSP `565189`:

| Branch | Verified state |
|---|---|
| `system-characteristics` | Parent payload built |
| `system-ids[]` | Built as `565189-InformationSystem` |
| `security-impact-level` | Three-objective structure built; values were null for this record |
| `status.state` | Present as raw Archer value `[80661]`; semantic translation remains |
| `props[]` | Present as raw values `0`, `80658`, `0`; not OSCAL-ready |
| `authorization-boundary` | No row for this record, although rows exist elsewhere in the DIM |

System Characteristics is therefore partially complete, not end-to-end complete.

## Current target: `system-characteristics.props[]`

There are 10 candidate Archer source fields:

```text
FISMA_REPORTABLE
FINANCIAL_SYSTEM
MISSION_CRITICAL
CRITICAL_INFRASTRUCTURE
PACKAGE_TYPE
HELPER_PTA_CALC
PACKAGE_TYPE_HELPER_CALC
PIA_REQUIRED
INFORMATION_CLASSIFICATION
DAILY_LOSS_AMOUNT_FROM_OUTAGE
```

The mapping inventory classifies this group as seven Extension Property rows, two Calculated rows, and one TBD row.

Confirmed design facts:

- Extension fields require OSCAL property objects with stable names such as `fisma-reportable`, `financial-system`, `mission-critical`, `critical-infrastructure`, and `pia-required`.
- `PACKAGE_TYPE = 80658` resolves through Archer metadata to `Information System`; raw lookup IDs are not final OSCAL values.
- `PACKAGE_TYPE_HELPER_CALC` is a transient calculation field and must not be mapped as a final property.
- Empty source fields should not create property rows.
- The final `props[]` implementation must construct meaningful `name`/`value` objects, not persist raw IDs or helper zeros.

## Immediate next step - read-only

Run this temporary cell to count how often each candidate property field is populated across all SSP source records:

```python
from collections import Counter

prop_fields = [
    "FISMA_REPORTABLE",
    "FINANCIAL_SYSTEM",
    "MISSION_CRITICAL",
    "CRITICAL_INFRASTRUCTURE",
    "PACKAGE_TYPE",
    "HELPER_PTA_CALC",
    "PACKAGE_TYPE_HELPER_CALC",
    "PIA_REQUIRED",
    "INFORMATION_CLASSIFICATION",
    "DAILY_LOSS_AMOUNT_FROM_OUTAGE"
]

counts = Counter()

for record in source_df.to_local_iterator():
    source_obj = _parse_source_json(record)

    for field in prop_fields:
        value = resolve_json_path(source_obj, field)

        if value not in (None, "", [], {}):
            counts[field] += 1

print("=== POPULATED PROP FIELD COUNTS ===")

for field in prop_fields:
    print(field, "=", counts[field])
```

Do not modify Cells 4-6 and do not run a write. The count output determines which fields need value-resolution rules and which fields can be excluded before the `props[]` transformation is designed.

## Next decision after the count

For each populated field, confirm its source value shape and then define one explicit rule:

1. Resolve Archer select-value IDs to display values.
2. Normalize calculated boolean-like values where appropriate.
3. Assign the intended OSCAL property name.
4. Omit transient, TBD, and empty values until their mapping is approved.
5. Validate generated property objects for sample SSPs before enabling writes.
