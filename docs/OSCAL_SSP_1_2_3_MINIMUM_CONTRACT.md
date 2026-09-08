# OSCAL SSP 1.2.3 Minimum Contract

Status: repository target pinned on 2026-09-08

This repository targets **NIST OSCAL SSP 1.2.3**. The pin is based on the
official NIST 1.2.3 metaschemas, not on assumptions inferred from the current
Archer mapping artifact.

Primary sources:

- [NIST OSCAL model reference](https://pages.nist.gov/OSCAL-Reference/models/)
- [OSCAL 1.2.3 SSP metaschema](https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_ssp_metaschema.xml)
- [OSCAL 1.2.3 metadata metaschema](https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_metadata_metaschema.xml)
- [OSCAL 1.2.3 implementation-common metaschema](https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_implementation-common_metaschema.xml)

## Minimum required structure

The first audit tier requires the following graph nodes for every source SSP.
It checks **exactly one** node per source record for:

- `system-security-plan`
- `system-security-plan.metadata`
- `system-security-plan.import-profile`
- `system-security-plan.system-characteristics`
- `system-security-plan.system-characteristics.system-information`
- `system-security-plan.system-characteristics.status`
- `system-security-plan.system-characteristics.authorization-boundary`
- `system-security-plan.system-implementation`
- `system-security-plan.control-implementation`

It checks **one or more** nodes per source record for:

- `system-security-plan.system-characteristics.system-ids[]`
- `system-security-plan.system-characteristics.system-information.information-types[]`
- `system-security-plan.system-implementation.components[]`
- `system-security-plan.control-implementation.implemented-requirements[]`

`back-matter` and `security-impact-level` are not in this list because their
assemblies are optional in OSCAL SSP 1.2.3. If an optional assembly is emitted,
it still must satisfy its own internal rules.

## Minimum required fields

| Node | Required fields checked by the first audit tier |
| --- | --- |
| `system-security-plan` | valid `uuid`, represented by the graph `OSCAL_UUID` column |
| `metadata` | `title`, `last-modified`, `version`, and exact `oscal-version = 1.2.3` |
| `import-profile` | `href` |
| `system-characteristics` | `system-name`, `description` |
| `system-ids[]` | `id` |
| `information-types[]` | `title`, `description` |
| `status` | valid `state`; nonblank `remarks` when state is `other` |
| `authorization-boundary` | `description` |
| `components[]` | valid `uuid`, `type`, `title`, `description`, valid `status.state` |
| `control-implementation` | `description` |
| `implemented-requirements[]` | valid `uuid`, `control-id` |

The allowed system-status states used by this audit are `operational`,
`under-development`, `under-major-modification`, `disposition`, and `other`.
Component status uses its narrower OSCAL enumeration: `under-development`,
`operational`, `disposition`, or `other`.

## Representation boundary

The mapper currently stores one OSCAL assembly or field group per graph node.
It does not yet emit one assembled OSCAL JSON document. Consequently:

- OSCAL UUID-bearing nodes use the graph's `OSCAL_UUID` column; their UUID is
  not expected inside `METADATA_JSON`.
- The audit validates node cardinality and the minimum payload contract at the
  graph boundary.
- Passing this audit is necessary but is **not** proof that an assembled SSP is
  schema-valid or constraint-valid.
- An assembly step plus official OSCAL JSON schema and constraint validation is
  still required before any write decision.

## Current remediation rules

- Do not invent defaults for required source-owned values.
- The 42 records currently missing `status.state` require source or business
  resolution; the mapper did not lose populated mapped values.
- `security-impact-level` is optional. For the 90 currently partial assemblies,
  either obtain all missing confidentiality/integrity/availability objectives
  or omit the entire optional assembly. Never emit a partial assembly.
- Existing raw component references are not valid OSCAL components merely
  because they are non-empty. They require hydration into objects containing
  the required component fields and status.
- Keep `EXECUTE_WRITES = False` throughout this work.

## Audit sequence

1. Run Mapper V1 Cells 1 through 7 with writes disabled.
2. Run `RUN_AFTER_07_ssp_v123_minimum_required_scope_audit.py`.
3. Run `RUN_AFTER_07_ssp_v123_required_source_readiness_audit.py` to classify
   each gap as registry, mapping, source-data, controlled-configuration, or
   mapper-output work without displaying source field names or values.
4. Record the aggregate output in `docs/CURRENT_STATUS.md`.
5. Turn every missing path or required-field count into a mapping or source-data
   backlog item.
6. Re-run the audit until the minimum contract passes.
7. Assemble representative SSP JSON and run official schema and constraint
   validation. This remains a separate gate.

