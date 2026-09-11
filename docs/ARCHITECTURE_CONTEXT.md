# Architecture Context

## Direction

Build one generic, metadata-driven mapper that can be configured for SSP, POA&M, Assessment Results, Assessment Plan, and Component Definition. Do not create a separate growing notebook for each OSCAL model.

## Approved consolidation - September 11

### Cleaner design reaffirmed - September 11

The owner reaffirmed one model selector, Excel-driven field mappings,
registry-driven hierarchy/identity and reusable transformations. The shared
seven-cell engine remains; do not create a new mapper for each model.

Cell One now exposes only `SELECTED_MODELS` for model selection. Internal
`MODEL_KEYS` and compatibility `CONFIG["OSCAL_MODEL"]` are derived from it.
Destinations belong to each model's storage contract, not a second global
selector. AR-only selection must not retain SSP destination columns.

This selector cleanup is **not full metadata-driven rule migration**. Existing
field-specific SSP dispatch and the AR17 release gates remain. Next, consolidate
the already-approved rules into one versioned mapping contract, with explicit
transform identifiers/parameters and approval status, then migrate shared
dispatch under output-parity checks. Do not infer approval from blank or
"In Progress" statuses, and do not enable rejected/deferred AR rows by deleting
allowlists. Moving constants to another file alone is not a generic mapper.

Keep the seven-cell interface. Sources have explicit table/mapping bindings;
models have explicit policy and storage contracts. One source may feed several
models; do not union sources or deduplicate their record IDs across tables.
Cells Five and Six contain shared graph/write mechanics, not separate SSP and
AR execution pipelines. Cell Four holds reviewed specialized behaviors.
Metadata cannot invent an unknown transform or unspecified collection identity.

Source One SSP and accepted AR17 are the configured parity baseline.
Other sources/models and blocked AR rows are not implicitly supported.
A targetless model can produce a clearly labelled logical preview, never a
write to another model's tables. Global CONFIG stays unchanged by per-route runs.
See [shared workflow scope and run instructions](SHARED_SEVEN_CELL_MAPPER.md).

## Pinned conformance target

- The repository target is NIST OSCAL SSP 1.2.3.
- Version-specific required/optional and controlled-value claims must be
  traceable to the official 1.2.3 metaschemas.
- The version pin is a conformance contract. It does not change deterministic
  graph identity, source-record identity, registry ownership, or DIM/FACT keys.
- A live notebook session started before the pin may be audited read-only, but
  the next full mapper run must use the pinned Cell 1.

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
- Recognized FIPS 199 values normalize to `low`, `moderate`, or `high`.
- Reviewed legacy LOE labels remain strings; the mapper must not invent a FIPS equivalence.
- System status uses an explicit OSCAL crosswalk; `other` includes an explanatory remark.
- Document identifiers and property values must satisfy their OSCAL string contracts.
- Transient helper fields never become OSCAL properties.
- `AUTHORIZATION_PACKAGE_NAME` remains the system-name source and is also the
  approved source for required `metadata.title`; no fallback title is invented.
- The SSP document version is controlled as `1.0`, independently of the OSCAL
  model version `1.2.3`.
- The five approved responsible-party fields become referenced OSCAL roles and
  `person` party objects. The four workbook rows marked `TBD` remain excluded.
- A party UUID is stable across roles within one SSP and must equal the party
  node OSCAL UUID. Every emitted role and party must be referenced exactly.
- `metadata.roles[]` and `metadata.parties[]` must be governed registry rows
  under metadata; the mapper never invents them in notebook memory.
- Extension properties become stable `name`/`value` objects.
- System-characteristics property identity follows the governed source-field
  plus normalized-value rule; list position is not identity.
- System-ID collection identity follows its governed normalized value; the
  generic singleton key is not valid for that collection.
- The SSP component collection is governed by Archer `CONTENT_ID` under the
  `system-implementation` singleton. Source field and list position are never
  component identity.
- A component reference is not a complete OSCAL component. Required title,
  description, and status values must come from the referenced source object
  or an approved lookup contract; the mapper does not invent them.
- The observed SSP component reference contract has two shapes only: an object
  with `ContentId,LevelId`, or a scalar content ID. Component type is declared
  by the six approved mapping rows. A repeated content ID with the same type
  deduplicates; a cross-type collision fails closed.
- A component payload UUID equals its deterministic graph node OSCAL UUID.
- Converging singleton mappings may share one transformed value, but distinct
  populated values require explicit precedence and must fail closed until it
  is approved.
- Helper, TBD, empty, and unapproved values do not become final OSCAL properties.

## Loading and validation

- `EXECUTE_WRITES` is declared once in Cell 1.
- Cell 6 consumes its supplied run configuration and never changes global CONFIG.
- Cell 7 is the normal notebook's orchestrator and execution point. The daily
  revision uses an explicit PREVIEW/COMMIT choice and a per-run configuration
  copy; global EXECUTE_WRITES stays false for all other cells. A release check
  prevents new Cell 7 from enabling an old Cell 6 still loaded in the session.
- The daily SSP DEV upsert path does not delete or truncate. Obsolete keys within
  selected source records block writes until a reconciliation rule is approved;
  source records absent from the current input are preserved, not inferred deleted.
- Daily idempotency compares mapped business values, preserving audit fields
  on unchanged rows. DIM/FACT must share a transaction and saved values/links
  must be verified. Local tests are not live daily-path acceptance.
- A write requires unique and non-null node and edge keys, no dangling edges, unique and non-null target PKs, successful idempotent merges, and post-load count verification.
- Source duplication must be resolved using an explicit technical selection rule. Blind `DISTINCT`, arbitrary `drop_duplicates`, and global-parent shortcuts are prohibited.


## Versioned conformance boundary

- Keep the target OSCAL release pinned explicitly before making required/optional
  claims or changing production emission behavior. The current target is SSP 1.2.3.
- A registry node materialized with `{}` is structural graph state, not proof
  that an optional OSCAL assembly should be emitted in the final document.
- Cardinality must be evaluated at field-occurrence level. An optional
  assembly can still have required children when the assembly is present.
- Graph integrity and mapped-payload shape checks are necessary but do not
  establish complete OSCAL document conformance.
- Write readiness requires assembling each SSP and validating it against the
  pinned release's schema plus applicable OSCAL constraints, in addition to
  the existing DIM/FACT graph and load checks.
- Narrow diagnostics must label their scope and cannot authorize writes.
- One-time source-contract extraction may report aggregate key/type coverage
  when the external Snowflake source shape is not checked into the repository;
  it must not print source identifiers or values.

## Known limitation

Nested collection-to-collection paths require explicit parent-instance context. The consolidated graph builder fails closed when multiple possible parent instances exist and no unique parent-instance key is available. This protects all model routes. The accepted AR results/observations hierarchy now supplies explicit parent-instance context; additional AR paths and POA&M remain unimplemented until their contracts are approved.

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
