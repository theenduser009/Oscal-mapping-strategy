# SSP System Characteristics LINEAGE_REQUIRED metadata

Date: 2026-10-01
Branch: simplify-metadata-boundary
Mapping commit: 9a221cb86c0e52cf11c1b845cbc0084835cf1e00
Status: MAPPING METADATA UPDATED; RUNTIME DOES NOT YET CONSUME THIS COLUMN.

## Decision

Add one simple mapping-sheet column:

LINEAGE_REQUIRED = Y | N

Default is N.

For SSP System Characteristics, Y is used only where the approved native OSCAL
value is produced by a semantic translation/crosswalk and the exact Archer source
field should remain visible in a provenance prop.

Y rows:
- OPERATIONAL_STATUS -> status.state (status-crosswalk)
- 11 security-objective candidates feeding confidentiality/integrity/availability

All other current mapping rows are N in this first pass.

## Why other transforms remain N

- archer-select rows whose approved destination is props[] are already business
  properties. Their property name/value preserve the business concept; they do
  not need an additional lineage prop just because the select ID is resolved.
- ATOIATO_DATE -> date-authorized is a one-to-one format conversion, not a
  multi-source/semantic crosswalk.
- text/direct/identifier one-to-one mappings remain N.

## Meaning of notes such as "Add a property named fisma-reportable"

That note means the approved OSCAL destination itself is a business extension
property under the mapped props[] collection. The mapper should emit a property
conceptually like:

{"name":"fisma-reportable","value":"<resolved Archer value>"}

The property is the business data itself, not lineage. The source field is
FISMA_REPORTABLE and the stable property-name rule derives fisma-reportable.

This is different from LINEAGE_REQUIRED=Y, where the business value stays in
its native OSCAL member and only source identity is additionally preserved as
provenance.

## No runtime claim

This commit changes only the mapping CSV metadata. It does not yet change Cell 3,
Cell 4, Cell 5, Snowflake output, or previously persisted target rows.

Next action: update the universal compiler/runtime to consume LINEAGE_REQUIRED
without any field-specific branches, then test locally before Snowflake PREVIEW.
