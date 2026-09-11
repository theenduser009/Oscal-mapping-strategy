# Reviewed mapper metadata

This artifact makes the active seven-cell mapper metadata-driven. It does not add an eighth execution cell. Upload `mapper_contract.v1.json` to Snowflake notebook Files alongside the approved mapping CSV, and deploy the matching seven cells. Cell One refuses a missing/invalid catalog and never fetches remote code or metadata automatically.

## Which input owns what?

| Input | Responsibility |
| --- | --- |
| Original Excel/CSV mapping rows | Archer source field, OSCAL model, target path, mapping type, Notes and original business intent. Preserved without mutation. |
| Live element registry | Active nodes, parent paths, collection flags, instance-key rules and processing order. |
| Reviewed JSON catalog | Executable choices previously recorded in Python: transform identifiers/parameters, element operators, property/reference names, controlled values, source bindings and verified storage contracts. Existing sheet rows must match their reviewed rules. |
| Shared Python | Generic parsing, transformations, registry traversal, keys, validation, guarded persistence and reporting. It does not select active mappings by hardcoded field/model names. |

The catalog is a reviewed deployment artifact, not a replacement for business approval. Existing SSP and accepted AR17 choices were migrated without expanding scope. Historical Python helpers remain for old diagnostics only; Cell One requires metadata policy for every active model.

## Adding an approved mapping

For an existing supported model/operator, add the approved Excel/CSV row with these executable columns, or add its exact reviewed rule to `MAPPING_RULES` in the catalog:

- `APPROVAL_STATUS`: `APPROVED`.
- `TRANSFORM_ID`: a supported reusable transformation below.
- `TRANSFORM_PARAMS`: JSON object; use `{}` when none.
- `REPRESENTATION_PARAMS`: JSON object, such as an explicitly approved property name or reference type.
- Optional `RULE_ID` for stable review traceability; optional `REPRESENTATION` must match the owning element's operator.

Source field, model, original target path and mapping type are still required. The compiler resolves the owner from the registry. Notes remain business evidence, never executable Python. Blank approval or partially supplied executable metadata blocks the row. Existing reviewed rules cannot be overridden by changing a CSV transform alone; revise the governed release deliberately.

For legacy rows without executable columns, a single matching approved catalog rule supplies those choices. Matching checks the original field/path/type and any specific Notes constraints. Required AR17 rule identities must occur exactly once. Unreviewed Source One rows are reported deferred, not silently mapped. The all-null unresolved rule remains `BLOCKED_IF_POPULATED` and rejects populated values.

## Adding another model or source

1. Supply approved source-to-model bindings and an unambiguous mapping artifact/source-column binding in `SOURCES`.
2. Add the model key, root/aliases, `POLICY: metadata-v1`, element operators and reviewed mapping rules in `MODELS`.
3. Confirm the live registry has the correct parents, collections and instance identities.
4. Select that model through Cell One's single `SELECTED_MODELS` setting.
5. Keep its storage contract empty until actual target tables, physical types and provenance are verified. Graph preview is allowed; COMMIT is not.

No source-field or model-name branch is needed for supported behavior. The local tests include a third synthetic model and a never-seen source field through the actual common builder. Unsupported shapes/transforms require a reusable capability plus tests; the engine does not guess them.

## Supported execution vocabulary

Transforms: `direct`, `text`, `canonical-text`, `timestamp`, `date`, `identifier`, `archer-select`, `scalar-score`, `security-objective`, `status-crosswalk`, `reject-populated`, `skip`.

Element operators: `object`, `record`, `properties`, `values`, `observations`, `references`, `roles`, `parties`, `assignments`.

Operators define reusable semantics; metadata selects them. Named properties require a literal `property_name` or an explicit element-level `source-field-slug` naming rule. Crosswalks are data. Required values, optional assembly behavior and controlled configuration/source values are data. Unknown identifiers, incompatible registry identities and ambiguous paths block execution.

Collection parent keys support declared singleton/source-record/no-parent policies. The existing SSP default materializes only singletons without collection ancestors; nested singleton materialization requires explicit metadata. Hydrated reference routes preserve their reviewed array-root shape and require declared lookup bindings; software descriptions remain mandatory. Null handling preserves accepted model behavior without inventing values.

## Preserved boundaries

- One generic graph builder and guarded writer; deterministic source/model-scoped identities, PK/FK checks and repeat-write safeguards remain.
- No metadata SQL/Python evaluation, automatic model approval, schema writes, daily truncation or guessed deletion policy.
- Source One SSP plus AR17 only are configured. Candidate/deferred/rejected AR rows remain outside accepted scope.
- SSP's earlier full DEV reload remains accepted. The old-row reduction is still unexplained.
- AR storage remains unverified. Local parity is not live persistence or complete OSCAL conformance.

See [shared workflow and next preview](../../docs/SHARED_SEVEN_CELL_MAPPER.md) and [current status](../../docs/CURRENT_STATUS.md).
