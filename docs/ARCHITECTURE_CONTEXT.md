# Architecture Context

## Direction

Build one generic, metadata-driven mapper that can be configured for SSP, POA&M, Assessment Results, Assessment Plan, and Component Definition. Do not create a separate growing notebook for each OSCAL model.

## Contracts

- Archer `CURATED_JSON` is the transformation source of truth.
- RAW data is lineage and troubleshooting evidence.
- Archer `CONTENT_ID` is the source record identity.
- The mapping CSV defines source-to-target field behavior.
- A CSV row is not automatically an OSCAL node; mappings must be grouped by element ownership.
- `OSCAL_ELEMENT_REGISTRY` owns hierarchy and root-first processing.
- DIM stores canonical element nodes.
- FACT stores parent-child dependencies.

## Identity

- Identity must be deterministic and versioned.
- Node identity includes source system, source table, source record, OSCAL model, element path, and instance key.
- Collection nodes require real instance identity.
- Edge identity derives from the exact parent node, child node, and dependency type.
- Do not introduce random UUIDs or silent hashing changes.
- Never link a collection child to a globally selected parent from another source record or instance.

## Transformations

- Direct mappings preserve approved source values.
- Transform mappings must execute through the shared dispatcher before payload construction.
- Archer select IDs resolve through `ARCHER_META_VALUE`.
- FIPS 199 values normalize to `low`, `moderate`, or `high`.
- Approved responsible-party fields become OSCAL role objects.
- Extension properties become stable `name`/`value` objects.
- Helper, TBD, empty, and unapproved values do not become final OSCAL properties.

## Loading and validation

- `EXECUTE_WRITES` is declared once in Cell 1.
- Cell 6 consumes the flag and never redefines it.
- Cell 7 is the only orchestrator and execution point.
- A write requires unique and non-null node and edge keys, no dangling edges, unique and non-null target PKs, successful idempotent merges, and post-load count verification.
- Source duplication must be resolved using an explicit technical selection rule. Blind `DISTINCT`, arbitrary `drop_duplicates`, and global-parent shortcuts are prohibited.

## Known limitation

Nested collection-to-collection paths require explicit parent-instance context. The consolidated graph builder fails closed when multiple possible parent instances exist and no unique parent-instance key is available. This protects SSP data and makes the remaining POA&M and Assessment Results enhancement explicit.

## Sprint completion evidence

Coverage must be measurable at field level:

- Archer field
- OSCAL model
- OSCAL element path
- Mapping type
- Status
- Has source data
- Populated record count and population percentage

Approved status values should distinguish completed work, in-progress work, more information required, no source data, and not applicable.

