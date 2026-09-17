# Source 2 sources_source Assessment Results current-snapshot scope closure — 2026-09-17

## Repository version

Branch: `simplify-metadata-boundary`
Repository head immediately before this checkpoint: `0dd355325100e72884f84ab3b49edd77439ea7a0`.

## Evidence basis

This checkpoint uses the owner-provided live Snowflake readiness screenshots and the Source 2 source mapping row definitions in `Mapping/SOURCE2_SOURCE_MAPPING.csv`, together with the successful Source 2 Assessment Results PREVIEW and COMMIT/read-back verification from 2026-09-17.

## Implemented and committed

`COUNT_OF_NONCOMPLIANT_CONTROLS` is implemented as a result-level property:

- source field: `COUNT_OF_NONCOMPLIANT_CONTROLS`
- target: `assessment-results.results[].props[]`
- property name: `noncompliant-count`
- live source population: 148/148
- Source 2 graph: 444 DIM nodes / 296 FACT edges
- PREVIEW: passed
- COMMIT: passed
- post-write read-back: verified

## Remaining populated Assessment Results rows

### COMPLIANCE_RATING

The source workbook maps this field to a reviewed-control property and describes it as an overall compliance rating for the source. The live source shape is one Archer select object per authoritative-source record and the lookup IDs resolve cleanly.

The workbook target requires a reviewed-control identity (`reviewed-control[@control-id]`), but the Source-level record does not provide the specific control identity required to attach that rating to a reviewed-control instance. Therefore this field is explicitly **blocked by target grain / missing control identity** for the current Source-level route. It must not be attached to an arbitrary reviewed control or silently remapped to a different result-level target.

### DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS

The live source contains this relationship for 21 Source records, while `DEVIATIONS_AUTHORITATIVE_SOURCES` itself is unpopulated in the current snapshot. The workbook target is under a finding/deviation relationship path. Materializing the linked-control rows without the required deviation/finding parent would create unsupported orphan semantics.

Therefore this field is explicitly **blocked by missing parent finding/deviation context** for the current Source-level route. Preserve it as relationship evidence; do not emit orphan Assessment Results nodes.

## Unpopulated Assessment Results rows

The remaining Assessment Results fields observed as unpopulated in the current Source snapshot remain deferred. No runtime output is emitted for them until owner-provided source data appears and the required parent/grain contract can be verified.

## Current-snapshot completion statement

For `sources_source`, the Assessment Results scope is now closed for the current snapshot as follows:

- one executable mapping implemented, committed, and read-back verified;
- populated fields that cannot be represented at their workbook-declared grain are explicitly blocked with evidence;
- unpopulated fields are explicitly deferred;
- no populated Assessment Results field is silently dropped or reassigned to another OSCAL target.

This is a current-snapshot closure, not a permanent exclusion. New source evidence can reopen the blocked/deferred rows.

## Next action

Proceed to the populated Component Definition rows from `sources_source`, beginning with read-only identity/relationship discovery before adding registry/runtime mappings.
