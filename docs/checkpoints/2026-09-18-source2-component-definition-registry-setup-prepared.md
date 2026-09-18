# Source 2 Component Definition registry setup prepared — 2026-09-18

Repository branch: `simplify-metadata-boundary`
Repository head inspected after registry SQL commit: `7be6d9e659872fe29f2163bd7f41b16ec2a8693c`

## Owner-provided live evidence

The owner ran the Component Definition readiness SQL and confirmed:
- the Component Definition target table exists;
- the Component Definition registry query returned no rows.

This project has no direct Snowflake connection, so those are owner-provided live read-back facts rather than independently queried database results.

## Implemented repository artifact

`sql/registry/ENABLE_COMPONENT_DEFINITION_SOURCE_BRANCH.sql`

The script is registry-only and does not write Component DIM/FACT targets.

It creates exactly three active registry paths:
1. `component-definition` — root singleton
2. `component-definition.components[]` — optional Source-record component node keyed by `SOURCE_RECORD_ID`
3. `component-definition.components[].props[]` — child properties keyed by `SOURCE_FIELD_NAME+VALUE`

The script deliberately does **not** create `links[]` or `control-implementation` branches. Current Source 2 evidence still contains relationship fields whose workbook paths require link/control semantics that are not yet executable without inventing URI/target identity.

## NIST check

NIST OSCAL v1.2.3 defines Component Definition with a `components[]` collection, and component properties are supported. A Component can represent documentary content such as policies/procedures/standards. This checkpoint does not claim a complete schema-valid serialized Component Definition document; it prepares only the graph branch needed for safe Source-level component/property mapping.

## Status

- Component target existence: owner-confirmed.
- Component registry before setup: owner-confirmed empty.
- Registry setup SQL: implemented and committed to GitHub.
- Registry SQL execution in Snowflake: **not yet run/read-back verified**.
- Component model contract in Cell 1: not yet added.
- Source 2 Component runtime rows: not yet added.
- PREVIEW/COMMIT: not run.

## Next action

Run `sql/registry/ENABLE_COMPONENT_DEFINITION_SOURCE_BRANCH.sql` once in Snowflake and return the result object. Expected status:
- `STATUS = COMPONENT_DEFINITION_SOURCE_REGISTRY_VERIFIED`
- `ACTIVE_ROWS = 3`
- `COMMITTED = true`

Do not update the notebook/runtime mapping until that read-back is confirmed.
