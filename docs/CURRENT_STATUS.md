# Current Status

Last reconciled: 2026-09-08

## Verified notebook

- Current live Snowflake notebook: `NB_ARCHER_OSCAL_MAPPER_V2`.
- Keep `EXECUTE_WRITES = False` while validating.
- Repository conformance target: NIST OSCAL SSP `1.2.3`, pinned in authoritative Cell 1.

## Latest verified mapper rerun

```text
OSCAL MAPPING RUN
Model: SSP
Run ID: 20260908T220830Z
Graph nodes: 51500
Graph edges: 48687
Duplicate node keys: 0
Duplicate edge keys: 0
Dangling source edges: 0
Dangling target edges: 0
PRE-WRITE VALIDATION PASSED
EXECUTE_WRITES = False; no DIM/FACT changes were made
```

## Narrow security/status review checkpoint

- Source rows / unique source records / unique graph records: 2813 / 2813 / 2813.
- Source/graph intersection: 2813; source-only=0; graph-only=0.
- Duplicate security nodes=0; duplicate status nodes=0; parse/resolution errors=0.
- Optional absent security-impact assemblies: 2453.
- Complete security-impact assemblies: 270.
- Partial security-impact assemblies: 90.
- Missing required security-objective occurrences: 179.
- Missing required `status.state` occurrences: 42.
- Unique records requiring review in this narrow check: 131.
- Records ready within only this narrow check: 2682.
- Security/status source-to-output discrepancies: 0.
- Component hydration remains incomplete: 4452 raw Archer component-reference payloads.

## Latest OSCAL SSP 1.2.3 minimum-required-scope audit

Screenshot-confirmed run after the pinned 1.2.3 mapper checkpoint.

### Run and identity gates

```text
Validator contract: OSCAL SSP 1.2.3
Session CONFIG OSCAL version: 1.2.3
Cell 7 graph validation passed: True
Cell 7 pre-write validation passed: True
Writes executed: False
Source rows: 2813
Unique source records: 2813
Unique graph records: 2813
Source/graph intersection: 2813
Source-only records: 0
Graph-only records: 0
Blank graph record IDs: 0
Source/graph identity gate passed: True
```

### Required path coverage findings

Minimum contract requires 13 paths. Eight are currently present in the registry and five are missing.

Confirmed present examples include:

```text
system-security-plan
system-security-plan.metadata
system-security-plan.system-characteristics
system-security-plan.system-characteristics.status
system-security-plan.system-characteristics.authorization-boundary
system-security-plan.system-implementation
system-security-plan.system-characteristics.system-ids[]
system-security-plan.system-implementation.components[]
```

Required paths shown missing from the registry:

```text
system-security-plan.import-profile
system-security-plan.system-characteristics.system-information
system-security-plan.system-characteristics.system-information.information-types[]
system-security-plan.control-implementation
system-security-plan.control-implementation.implemented-requirements[]
```

The audit reports the missing required paths as cardinality blockers across all 2813 evaluated source records.

`components[]` is present but does not yet satisfy required one-or-more coverage across all source records:

```text
nodes=4804
source_coverage=944
missing_source_records=1869
cardinality_blocked_records=1869
duplicate_excess_nodes=3860
malformed_payloads=0
```

The `duplicate_excess_nodes=3860` value is a cardinality diagnostic for an expected one-or-more collection, not a duplicate node-key defect. Mapper graph duplicate node keys remain zero.

### Required field coverage findings

Confirmed audit observations include:

```text
system-security-plan.OSCAL_UUID: valid=2813, missing=0, invalid=0
metadata.title: valid=0, missing=2813, invalid=0
metadata.last-modified: valid=2813, missing=0, invalid=0
metadata.version: valid=0, missing=2813, invalid=0
metadata.oscal-version: valid=0, missing=2813, invalid=0
system-characteristics.system-name: valid=2813, missing=0, invalid=0
system-characteristics.description: valid=2780, missing=33, invalid=0
status.state: valid=2771, missing=42, invalid=0
status.remarks (required when state=other): valid=57, missing=0, invalid=0
authorization-boundary.description: valid=2519, missing=294, invalid=0
system-ids[].id: valid=2813, missing=0, invalid=0
```

Component required payload fields remain absent in the current reference-only representation:

```text
components[].OSCAL_UUID: valid=4804, missing=0, invalid=0
components[].type: valid=0, missing=4804, invalid=0
components[].title: valid=0, missing=4804, invalid=0
components[].description: valid=0, missing=4804, invalid=0
components[].status.state: valid=0, missing=4804, invalid=0
components[] records_blocked_by_fields_or_payload: 944
```

This confirms that component hydration is a real Phase-2 requirement rather than merely a cosmetic payload-shape issue.

### Static scope summary

```text
Required paths in minimum contract: 13
Required paths present in registry: 8
Required paths missing from registry: 5
Required paths with mapping owner: 6
Required paths without mapping owner: 7
```

Mapping-owner absence is evidence only; path/field results determine blocking.

### Current minimum contract result

```text
Unique source records evaluated: 2813
Records blocked by minimum required structure/fields: 2813
Records meeting the current minimum contract: 0
Result: NOT READY
```

The audit explicitly states that it never authorizes writes. Even a future PASS still requires assembled OSCAL JSON schema and constraint validation before any write decision.

## Current interpretation

The graph engine itself remains structurally healthy: 51,500 nodes, 48,687 edges, zero duplicate node/edge keys and zero dangling edges. The new minimum-contract audit changes the focus from graph mechanics to **SSP completeness**.

The primary blockers are now precisely identified:

1. Five minimum-contract registry branches are absent: `import-profile`, `system-information`, `information-types[]`, `control-implementation`, and `implemented-requirements[]`.
2. Required root metadata fields are absent, notably `metadata.title`, `metadata.version`, and `metadata.oscal-version`.
3. Existing required payload gaps remain: 33 missing system descriptions, 42 missing status states, and 294 missing authorization-boundary descriptions.
4. `components[]` only covers 944 of 2813 source records and is still reference-only; required component payload fields (`type`, `title`, `description`, `status.state`) are not hydrated.
5. The earlier 2453 empty security-impact assemblies remain optional under OSCAL SSP 1.2.3 and should not be confused with these minimum-contract blockers.
6. `EXECUTE_WRITES=False`; writes remain blocked.

## Next source-readiness checkpoint prepared

The repository now contains the read-only
[OSCAL SSP 1.2.3 required-source readiness audit](../notebooks/validation/RUN_AFTER_07_ssp_v123_required_source_readiness_audit.py).
It has passed Python syntax validation, representative in-memory execution
tests, and an independent classification review. It has not yet been run in
Snowflake, so no source-readiness counts are claimed here.

The diagnostic inspects the original mapping artifact as well as the current
canonical mappings. For each hard-coded required OSCAL path and field it keeps
four axes separate: registry presence, executable mapping candidates, aggregate
populated-source coverage, and generated valid coverage. It also detects
candidate collisions, current owner misalignment, exact duplicate artifact
rows, nested-payload shaping needs, and collection all-member validity. It
prints no record IDs, Archer field names, source values, payloads, hashes, or
lookup labels.

## Immediate next action

In the same live Snowflake notebook session, copy and run the complete
[required-source readiness audit](../notebooks/validation/RUN_AFTER_07_ssp_v123_required_source_readiness_audit.py)
in one new Python cell. Do not rerun Mapper Cells 1-7 or the minimum-scope audit
solely for this step.

Paste the complete aggregate output into this status file and report
`check status`. The import-profile decision gate will show whether the mapping
artifact contains a populated candidate or whether an approved controlled
`SSP_IMPORT_PROFILE_HREF` value must be supplied. No URI or source value is
invented. Keep `EXECUTE_WRITES = False`.
