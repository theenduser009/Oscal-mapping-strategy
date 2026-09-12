# Architecture Context

## Direction

One reusable metadata-driven ingestion template for current and future OSCAL
models and approved source tables. Do not create a separate mapper per model.

## Current lean registry-backed release

Field mappings, status, transforms and Notes are maintained once in
[ARCHER_OSCAL_MAPPINGS.csv](../Mapping/ARCHER_OSCAL_MAPPINGS.csv). The original
nine registry columns supply hierarchy and instance identity. Only three sparse
rules extend them: `OPERATOR`, `UUID_POLICY` and `REQUIRED_MEMBERS`, through the
[lean one-time setup](REGISTRY_METADATA_SETUP.md). There is no deployed JSON
catalog or field-rule fallback. Fifteen earlier experimental columns are not
read and are never required or dropped by the lean runtime.

Cell One supplies visible source/lookup bindings, model selection and verified
storage settings. Cell Three compiles these inputs to an inert in-memory plan.
Cell Four executes reusable transforms/operators; Cells Five through Seven keep
the shared graph builder, guarded writer and runner. No metadata is evaluated
as Python or SQL, and prose Notes are not executable.

The three existing required metadata support values are ordinary labelled CSV
rows, not new field approvals. Complete-only CIA assembly uses the single
`REQUIRED_MEMBERS` rule. The released CSV itself is regression-tested to retain
the accepted SSP and AR rows; no hidden registry list duplicates those field
rules. Original SSP/AR behavior stays the parity baseline. Frozen historical
catalogs and engines are tests only.

A future approved field using supported operations needs a mapping row.
A future model also needs governed registry rows and deployment/destination
settings. Unsupported transformation or collection identity behavior must be
implemented once as a reusable capability; model selection does not invent it.

The revised three-column DEV registry extension has not run here. Normal writes
remain disabled. The full DEV reload remains accepted; the daily path and AR
persistence still require live acceptance. Earlier architecture snapshots below
describe history, not current inputs.

### Earlier metadata-engine migration - September 11 (superseded where noted above)

The owner made metadata-driven behavior non-negotiable and authorized the required changes. Cell One now loads the reviewed [deployment catalog](../notebooks/metadata/mapper_contract.v1.json); it exposes one model selector. Source fields, source bindings, model roots, approved transform choices, property names, reference types, controlled values and storage contracts are metadata, not active field/model branches.

Cell Three preserves the original Excel/CSV row and compiles a reviewed executable plan against the live registry. Existing accepted rules are migrated into the catalog without editing the owner's CSV. New rows can carry explicit approved transform/representation metadata; partial, ambiguous, contradictory and unknown contracts fail closed. See [metadata contract](../notebooks/metadata/README.md).

Cell Four executes reusable operators and transforms from that plan. Cell Five still performs one registry traversal; Cell Six remains the shared guarded writer; Cell Seven orchestrates every source/model context. Historical SSP/AR engines are removed from deployed code and preserved only as frozen test oracles; active Cell Four rejects missing compiled contexts instead of falling back. A new field and third synthetic model execute using metadata only.

All 564 local tests pass. Independent tests preserve the exact SSP fixture fingerprint and accepted AR17 business/field-report output. Declarative constraints, the posted 459-row routing failure pattern and mixed-workbook routing are covered. This does not establish a new live Snowflake acceptance or full OSCAL schema completeness. Unsupported new transformations or collection identity patterns require a reusable engine enhancement, not guessed semantics.

Routing is registry-first for present and future models: every active path identifies ownership; recognized labels detect contradictions but unfamiliar display labels do not veto registered paths. Placeholder labels/paths are explicitly deferred through catalog metadata. Unregistered, unreviewed rows follow the existing deferral policy; executable approved rows still require registered ownership. Recognition of another model does not enable its executor, mappings or storage. No per-model routing patch is needed when new governed registry paths are added.

Maintain the seven source cells once and mechanically generate copy-ready V2/combined pages. The engine's compiled plan is generated in memory from approved sheet rows, registry and catalog supplements. The catalog is not an automatically synchronized Excel export; new rules should prefer explicit executable sheet columns, and duplicate/conflicting rule definitions must be reconciled in a reviewed metadata release.

Only Source One SSP and accepted AR17 are configured. Rejected/candidate/deferred mappings remain excluded or blocked; other sources/models require approved metadata. Source identities stay isolated. Storage remains separately verified per source/model, and AR cannot borrow SSP targets. No database changes or reload accompany this refactor.

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


